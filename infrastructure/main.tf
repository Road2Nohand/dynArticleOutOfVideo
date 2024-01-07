provider "aws" {
    region = "eu-central-1"
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

resource "aws_s3_object" "index_upload" {
    bucket          = aws_s3_bucket.website_bucket.id
    key             = var.html_file_name
    source          = "../${var.html_file_name}" # Pfad zur lokalen index.html-Datei
    content_type    = "text/html"
}

output "website_url" {
    value = "https://${aws_s3_bucket.website_bucket.bucket_regional_domain_name}/${var.html_file_name}"
}