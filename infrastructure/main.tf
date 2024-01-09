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



#region website_bucket

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

# access_block ist nicht mandatory, erhöht aber die Sicherheit
resource "aws_s3_bucket_public_access_block" "public_access_block" {
    bucket                  = aws_s3_bucket.website_bucket.id
    depends_on              = [aws_s3_bucket.website_bucket]
    block_public_acls       = true # der public access für bestimmte Dateien wird später durch die public policy überschrieben
    block_public_policy     = false # auf false, weil wir eine public policy anwenden
    ignore_public_acls      = true # öffentliche ACLs auf dem Bucket website_bucket ignoriert. Dies gilt auch für Objekte, die später im Bucket erstellt werden.
    restrict_public_buckets = false # wenn true, können nur autorisierte user zugreifen
}

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
          "transcribe:GetCallAnalyticsJob"
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

# Damit die ARN der lambda_transcribe_role immer aktuell bleibt, auch wenn Änderungen an der ARN vorgenommen werden, wenn Terraform apply mehrmals ausgeführt wird
data "aws_iam_role" "transcribe_role" {
  name = "transcribe_role"
  depends_on = [aws_iam_role.transcribe_role]
}

# Lambda-Funktion für Transkription
resource "aws_lambda_function" "transcribe_lambda_function" {
    function_name = "1_transcribe_function"
    filename      = "1_transcribe__function.zip"
    runtime       = "python3.9"
    role          = aws_iam_role.lambda_transcribe_role.arn
    handler       = "1_transcribe_function.handler"
    timeout       = 900  # Setzt das Timeout auf 15 Minuten, Lambdas laufen per default nur 3 Sekunden

    # für den Zugriff aus der 1_transcribe_function.py, damit Transcribe-Function in den Bucket schreiben kann
    environment {
        variables = {
            WEBSITE_BUCKET_NAME = aws_s3_bucket.website_bucket.bucket,
            DATA_ACCESS_ROLE_ARN = data.aws_iam_role.transcribe_role.arn,
            VIDEO_BUCKET_NAME = aws_s3_bucket.video_bucket.bucket
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





#region GitHub Actions

/* GitHub Repo und Github-Actions Workflow selbst auch über Terraform anlegen lassen, falls Änderungen am Repo oder am Workflow commitet werden

# User für S3 Bucket Zugriff anlegen

resource "aws_iam_user" "github_actions_user" {
  name = "github-actions-user"
}

resource "aws_iam_access_key" "github_actions_access_key" {
  user = aws_iam_user.github_actions_user.name
}

resource "aws_iam_user_policy_attachment" "github_actions_user_policy" {
  user       = aws_iam_user.github_actions_user.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

output "github_actions_user_access_key" {
    value = "AWS S3 Github Actions User AccessKey: ${aws_iam_access_key.github_actions_access_key.secret}"
}


# Github Repo und Actions-Workflow anlegen

provider "github" {
  token = "YOUR_GITHUB_TOKEN" # Sicherheitstechnisch schlecht, weil im eigenen Repo der Token für den ganzen Github-Account liegt. Aber das Repo kann nicht ausversehen public werden, da das eben IaC sicherstellt.
}

resource "github_repository" "terraform_repo" {
  name        = "SportsVideoToArticle"
  private     = true
}

resource "github_actions_workflow" "terraform_workflow" {
  name     = "terraform-workflow"
  repository = github_repository.terraform_repo.name

  on = "push"

  # Hier kannst du die Konfiguration für deine GitHub Actions definieren
  content = <<-YAML
    name: Terraform Continuous Integration
    
    on:
      push:
        branches:
          - main
    
    jobs:
      terraform_ci:
        runs-on: ubuntu-latest
    
        defaults:
          run:
            working-directory: ./infrastructure
    
        steps:
          - name: Checkout repository
            uses: actions/checkout@v3
            
          - name: Configure AWS CLI
            uses: aws-actions/configure-aws-credentials@v1
            with:
              aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
              aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
              aws-region: eu-central-1
    
          - name: Set up Terraform
            uses: hashicorp/setup-terraform@v2
            with:
              terraform_version: latest
    
          # Den Workspace Wechsel, sollte man später branch-abhängig machen DEV -> develop und PROD -> main
          - name: Terraform Init
            run: |
              ls -al
              terraform init -backend-config="bucket=terraform-state-sportsvideo-to-article" -backend-config="region=eu-central-1" -backend-config="key=terraform-state"
              terraform workspace select DEV
            env:
              TF_LOG: "DEBUG"
    
          - name: Terraform Validate
            run: |
              ls -al
              terraform validate
    
          - name: Terraform Apply 1st
            run: |
              ls -al
              terraform apply -auto-approve || true
    
          - name: Terraform Apply 2nd
            run: |
              ls -al
              terraform apply -auto-approve
    
          # Der Bucket-Name muss später auch Workspace, also Branch abhängig gesetzt
          - name: Upload HTML to S3
            run: |
              ls -al
              aws s3 cp ../index.html s3://s3-bucket-with-static-index-html-dev/
  YAML
}

*/

#endregion GitHub Actions