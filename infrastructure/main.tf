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

/* Wird im Actions Workflow gepushed, weil es ein Artefakt ist und dann kann man auch nur für pushes auf das Artefakt einen deploy workflow bauen 
resource "aws_s3_object" "index_upload" {
    bucket          = aws_s3_bucket.website_bucket.id
    key             = var.html_file_name
    source          = "../${var.html_file_name}" # Pfad zur lokalen index.html-Datei
    content_type    = "text/html"
}
*/






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
    name: Terraform Workflow

    on:
      push:
        branches:
          - main

    jobs:
      terraform:
        runs-on: ubuntu-latest

        steps:
        - name: Checkout repository
          uses: actions/checkout@v2

        - name: Set up Terraform
          uses: hashicorp/setup-terraform@v1
          with:
            terraform_version: latest

        - name: Terraform Init
          run: terraform init -backend-config="bucket=your-s3-bucket-name" -backend-config="key=terraform-state"

        - name: Terraform Apply
          run: terraform apply -auto-approve

        - name: Terraform Apply
          run: terraform apply -auto-approve
  YAML
}

*/










/* Outputs */

output "website_url" {
    value = "https://${aws_s3_bucket.website_bucket.bucket_regional_domain_name}/${var.html_file_name}"
}

