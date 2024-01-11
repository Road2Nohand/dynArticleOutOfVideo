provider "aws" {
    region = "eu-central-1"
}

terraform {
  backend "s3" {
    bucket = "terraform-state-sportsvideo-to-article"
    region = "eu-central-1"
    key = "terraform-state"
  }
}


#region Variables

variable "website_bucket_name" {
    type = string
}

variable "html_file_name" {
    type = string
}

variable "video_bucket_name" {
    type = string
}

#endregion Variables



#region GitHub OIDC Provider
/*
resource "aws_iam_role" "r2n_github_federated_idp_role" {
  name        = "r2nGitHubFederatedIDPRole"
  description = "This role is used to allow GitHub Actions to access AWS resources."

  assume_role_policy = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Federated": "arn:aws:iam::${var.aws_account_id}:oidc-provider/token.actions.githubusercontent.com"
        },
        "Action": "sts:AssumeRoleWithWebIdentity",
        "Condition": {
          "StringEquals": {
            "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
          },
          "StringLike": {
            "token.actions.githubusercontent.com:sub": "repo:Road2Nohand/dynArticleOutOfVideo"
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "github_federated_idp_role_policy_attachment" {
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
  role       = aws_iam_role.r2n_github_federated_idp_role.name
}

data "tls_certificate" "github_federated_idp_config_tls_certificate" {
  url = "https://token.actions.githubusercontent.com"
}

resource "aws_iam_openid_connect_provider" "github_federated_idp_config" {
  url = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
  thumbprint_list = data.tls_certificate.github_federated_idp_config_tls_certificate.certificates[*].sha1_fingerprint
}
*/
#endregion GitHub OIDC Provider



#region website_bucket

/* klappt nicht, deswegen als Workaround für AWS's "Eventually Consistent Nature of AWS Services" -> den ganzen Bucket public machen, ist auch gut für das Polling() vom der index.html per JS
# index.html im website_bucket ist öffentlich lesbar
resource "aws_s3_bucket_policy" "policy_website_bucket_public_read_access_to_specific_files" {
    bucket                  = aws_s3_bucket.website_bucket.id
    depends_on              = [aws_s3_bucket.website_bucket]
    policy                  = jsonencode({
        "Version": "2012-10-17",
        "Statement": [
            {
            "Sid": "PublicRead",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::${var.website_bucket_name}-${lower(terraform.workspace)}/${var.html_file_name}" # nur für die index.html wird der Read zugriff von Public erlaubt, für alle anderen Objekte gibt es keinen public access.
            }
        ]
    })
}
*/

resource "aws_s3_bucket" "website_bucket" {
    bucket          = "${var.website_bucket_name}-${lower(terraform.workspace)}"
    force_destroy   = true # weil sonst nur leere Buckets gelöscht werden können
}

resource "aws_s3_bucket_website_configuration" "webseite" {
    bucket = aws_s3_bucket.website_bucket.id
    index_document {
      suffix = var.html_file_name
    }
}

resource "aws_s3_bucket_ownership_controls" "website_bucket_ownership_controls" {
  bucket = aws_s3_bucket.website_bucket.id
  rule {
    object_ownership = "BucketOwnerPreferred" # bewirkt das der Bucket-Besitzer auch der Besitzer der Objekte im Bucket ist, wenn ein anderer User die Objekte hochlädt (z.B. die Lambda-Funktion), ansonsten können User über das Internet Objekte in den Bucket hochladen und sind dann auch der Besitzer der Objekte, da sie die Objekte hochgeladen haben.
  }
}

# access_block ist nicht mandatory, erhöht aber die Sicherheit
resource "aws_s3_bucket_public_access_block" "public_access_block" {
    bucket                  = aws_s3_bucket.website_bucket.id
    block_public_acls       = false # der public access für bestimmte Dateien wird später durch die public policy überschrieben
    block_public_policy     = false # auf false, weil wir eine public policy anwenden
    ignore_public_acls      = false # öffentliche ACLs auf dem Bucket website_bucket ignoriert. Dies gilt auch für Objekte, die später im Bucket erstellt werden.
    restrict_public_buckets = false # wenn true, können nur autorisierte user zugreifen
}

resource "aws_s3_bucket_acl" "website_bucket_acl" {
  depends_on = [
    aws_s3_bucket.website_bucket,
    aws_s3_bucket_ownership_controls.website_bucket_ownership_controls,
    aws_s3_bucket_public_access_block.public_access_block,
  ]

  bucket = aws_s3_bucket.website_bucket.id
  acl    = "public-read-write"
}

# hochladen von Dateien wird später in der CICD mit GitHub Actions gemacht und der s3api gemacht
# aws s3 cp ../index.html s3://dyn-bucket-for-static-article-website-dev/ --acl public-read


output "website_url" {
    value = "https://${aws_s3_bucket.website_bucket.bucket_regional_domain_name}/${var.html_file_name}"
}

#endregion website_bucket



#region transcribe_function und video_bucket

# video_bucket für die .mp4's
resource "aws_s3_bucket" "video_bucket" {
    bucket          = "${var.video_bucket_name}-${lower(terraform.workspace)}"
    force_destroy   = true
}

# IAM-Rolle für die Lambda-Funktion, damit sie Events an "CloudWatch" senden kann, wird später noch um Policies für Video-Bucket und Website-Bucket Rechte erweitert
resource "aws_iam_role" "lambda_transcribe_role" {
    assume_role_policy = jsonencode({
        Version = "2012-10-17",
        Statement = [
            {
                Action = "sts:AssumeRole",
                Effect = "Allow", # erlaubt der Lambda-Funktion diese Rolle anzunehmen
                Principal = {
                    Service = "lambda.amazonaws.com" # nur Lambda-Funktionen dürfen diese Rolle annehmen
                }
            }
        ]
    })

    managed_policy_arns = ["arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"] # AWS Managed Policy für Lambda-Funktionen
}

# IAM-Rolle für AWS Transcribe, die später per PassRole von der transcribe_function an AWS Transcribe weitergegeben wird
resource "aws_iam_role" "transcribe_role" {
    name = "transcribe_role"
    assume_role_policy = jsonencode({
        Version = "2012-10-17",
        Statement = [
            {
                Effect = "Allow",
                Principal = {
                    Service = "transcribe.amazonaws.com" # Nur Transcribe Ressourcen dürfen diese Rolle annehmen
                },
                Action = "sts:AssumeRole"
            }
        ]
    })
}

# IAM-Policy für Read-Access auf den Video-Bucket von der transcribe_function
resource "aws_iam_policy" "policy_transcribe_function_can_read_video_bucket_files" {
    name = "policy_transcribe_function_can_read_video_bucket_files"

    policy = jsonencode({
        Version = "2012-10-17",
        Statement = [
            {
                Action = [
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                Effect = "Allow",
                Resource = [
                    aws_s3_bucket.video_bucket.arn,
                    "${aws_s3_bucket.video_bucket.arn}/*"
                ]
            }
        ]
    })
}

# IAM-Policy für Write-Access auf den Website-Bucket, für Transkribierungsergebnisse
resource "aws_iam_policy" "policy_transcribe_function_can_write_to_website_bucket" {
    name = "policy_transcribe_function_can_write_to_website_bucket"

    policy = jsonencode({
        Version = "2012-10-17",
        Statement = [
            {
                Action = [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:ListBucket",
                    "s3:DeleteObject"
                ],
                Effect = "Allow",
                Resource = [
                    aws_s3_bucket.website_bucket.arn,
                    "${aws_s3_bucket.website_bucket.arn}/*"
                ]
            }
        ]
    })
}

# IAM-Policy für PassRole-Aktion
resource "aws_iam_policy" "lambda_pass_role_policy" {
    name = "lambda_pass_role_policy"
    policy = jsonencode({
        Version = "2012-10-17",
        Statement = [
            {
                Effect = "Allow",
                Action = "iam:PassRole",
                Resource = aws_iam_role.transcribe_role.arn
            }
        ]
    })
}

resource "aws_iam_policy" "lambda_transcribe_policy" {
  name = "lambda_transcribe_policy"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "transcribe:StartCallAnalyticsJob",
          "transcribe:GetCallAnalyticsJob",
          "transcribe:StartTranscriptionJob",
          "transcribe:GetTranscriptionJob"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_policy" "policy_transcribe_service_access_to_video_and_website_bucket" {
    name = "transcribe_access_policy"

    policy = jsonencode({
        Version = "2012-10-17",
        Statement = [
            {
                Action = [
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                Effect = "Allow",
                Resource = [
                    aws_s3_bucket.video_bucket.arn,
                    "${aws_s3_bucket.video_bucket.arn}/*"
                ]
            },
            {
                Action = [
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                Effect = "Allow",
                Resource = [
                    aws_s3_bucket.website_bucket.arn,
                    "${aws_s3_bucket.website_bucket.arn}/*"
                ]
            }
        ]
    })
}



# Anhängen der IAM-Policies an die Lambda-Rolle
resource "aws_iam_role_policy_attachment" "attach_video_bucket_policy" {
    policy_arn = aws_iam_policy.policy_transcribe_function_can_read_video_bucket_files.arn
    role       = aws_iam_role.lambda_transcribe_role.name
}
resource "aws_iam_role_policy_attachment" "attach_website_bucket_policy" {
    policy_arn = aws_iam_policy.policy_transcribe_function_can_write_to_website_bucket.arn
    role       = aws_iam_role.lambda_transcribe_role.name
}
resource "aws_iam_role_policy_attachment" "attach_pass_role_policy" {
    policy_arn = aws_iam_policy.lambda_pass_role_policy.arn
    role       = aws_iam_role.lambda_transcribe_role.name
}
resource "aws_iam_role_policy_attachment" "attach_lambda_transcribe_policy" {
  policy_arn = aws_iam_policy.lambda_transcribe_policy.arn
  role       = aws_iam_role.lambda_transcribe_role.name
}
resource "aws_iam_role_policy_attachment" "attach_transcribe_service_policy" {
    policy_arn = aws_iam_policy.policy_transcribe_service_access_to_video_and_website_bucket.arn
    role       = aws_iam_role.transcribe_role.name
}


# Data Block zum Zippen des Lambda-Funktionscodes
data "archive_file" "lambda_function_zip" {
    type        = "zip"
    source_dir  = "lambda_functions"
    output_path = "${path.module}/1_transcribe__function.zip"
}

# OpenAI Lib als Layer der Lambda-Funktion hinzufügen
resource "aws_lambda_layer_version" "openai_layer" {
  filename   = "lambda_functions/openai_layer.zip"
  layer_name = "openai_layer"
  compatible_runtimes = ["python3.10"]
}

# Damit die ARN der lambda_transcribe_role immer aktuell bleibt, auch wenn Änderungen an der ARN vorgenommen werden, wenn Terraform apply mehrmals ausgeführt wird
data "aws_iam_role" "transcribe_role" {
  name = "transcribe_role"
  depends_on = [aws_iam_role.transcribe_role]
}

# Lambda-Funktion für Transkription
resource "aws_lambda_function" "transcribe_lambda_function" {
    function_name = "1_transcribe_function"
    filename      = "1_transcribe__function.zip"
    runtime       = "python3.10"
    role          = aws_iam_role.lambda_transcribe_role.arn
    handler       = "1_transcribe_function.handler"
    timeout       = 900  # Setzt das Timeout auf 15 Minuten, Lambdas laufen per default nur 3 Sekunden
    layers = [aws_lambda_layer_version.openai_layer.arn]

    # für den Zugriff aus der 1_transcribe_function.py, damit Transcribe-Function in den Bucket schreiben kann
    environment {
        variables = {
            WEBSITE_BUCKET_NAME = aws_s3_bucket.website_bucket.bucket,
            DATA_ACCESS_ROLE_ARN = data.aws_iam_role.transcribe_role.arn,
            VIDEO_BUCKET_NAME = aws_s3_bucket.video_bucket.bucket,
            OPEN_AI_API_KEY = "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"
        }
    }
}

# Video-Bucket erlauben Transcribe-Function zu triggern bei .mp4 Upload
resource "aws_lambda_permission" "allow_video_bucket_to_trigger_transcribe_function" {
    statement_id  = "AllowExecutionFromS3Bucket"
    action        = "lambda:InvokeFunction"
    function_name = aws_lambda_function.transcribe_lambda_function.function_name
    principal     = "s3.amazonaws.com"
    source_arn    = aws_s3_bucket.video_bucket.arn
}

# S3 Event wenn .mp4 in Video-Bucket hochgeladen wird
resource "aws_s3_bucket_notification" "lambda_mp4_upload_trigger" {
    bucket = aws_s3_bucket.video_bucket.id

    lambda_function {
        lambda_function_arn = aws_lambda_function.transcribe_lambda_function.arn
        events              = ["s3:ObjectCreated:*"]
        filter_suffix       = ".mp4"
    }
}

#endregion transcribe_function und video_bucket