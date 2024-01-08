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

variable "website_bucket_name" {
    type = string
}

variable "video_bucket_name" {
    type = string
}

variable "html_file_name" {
    type = string
}


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

resource "aws_s3_bucket_policy" "public_access" {
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

/* Outputs */

output "website_url" {
    value = "https://${aws_s3_bucket.website_bucket.bucket_regional_domain_name}/${var.html_file_name}"
}



# Bucket für die Videos
resource "aws_s3_bucket" "video_bucket" {
    bucket          = "${var.video_bucket_name}-${lower(terraform.workspace)}"
    force_destroy   = true # weil sonst nur leere Buckets gelöscht werden können
}

# Lambda-Functions:

data "archive_file" "bundle" {
    type = "zip"
    source_dir = "lambda_functions"
    output_path = "1_transcribe__function.zip"
}

resource "aws_iam_role" "lambda_role" {
    assume_role_policy = jsonencode({
        "Version": "2012-10-17",
        "Statement": [
            {
            "Action": "sts:AssumeRole",
            "Principal": {
                "Service": "lambda.amazonaws.com"
                },
            "Effect": "Allow"
            }
        ]
    })

    managed_policy_arns = ["arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"]
}

resource "aws_lambda_function" "transcribe_lambda_function" {
    function_name = "1_transcribe_function"
    filename = "1_transcribe__function.zip"
    runtime = "python3.9"
    role = aws_iam_role.lambda_role.arn
    handler = "1_transcribe_function.handler"
}

# URL sollte später abgebaut werden, da öffenltich zugänglich
resource "aws_lambda_function_url" "transcribe_lambda_function_url" {
    authorization_type = "NONE"
    function_name = aws_lambda_function.transcribe_lambda_function.function_name
    depends_on = [aws_lambda_function.transcribe_lambda_function]
}

# Lambda die Rechte den S3 Bucket lesen zu dürfen
resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.transcribe_lambda_function.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.video_bucket.arn
}


resource "aws_s3_bucket_notification" "lambda_trigger" {
  bucket = aws_s3_bucket.video_bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.transcribe_lambda_function.arn
    events = ["s3:ObjectCreated:*"]
    filter_suffix       = ".mp4"
  }
}





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