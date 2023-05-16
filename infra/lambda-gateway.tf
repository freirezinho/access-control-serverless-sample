terraform {
  required_version = "~> 1.3.3"
}

provider "aws" {
  access_key                  = "test"
  secret_key                  = "test"
  region                      = "us-east-1"
  s3_force_path_style         = false
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    apigateway     = "http://localhost:4566"
    apigatewayv2   = "http://localhost:4566"
    cloudformation = "http://localhost:4566"
    cloudwatch     = "http://localhost:4566"
    dynamodb       = "http://localhost:4566"
    ec2            = "http://localhost:4566"
    es             = "http://localhost:4566"
    elasticache    = "http://localhost:4566"
    firehose       = "http://localhost:4566"
    iam            = "http://localhost:4566"
    kinesis        = "http://localhost:4566"
    lambda         = "http://localhost:4566"
    rds            = "http://localhost:4566"
    redshift       = "http://localhost:4566"
    route53        = "http://localhost:4566"
    s3             = "http://s3.localhost.localstack.cloud:4566"
    secretsmanager = "http://localhost:4566"
    ses            = "http://localhost:4566"
    sns            = "http://localhost:4566"
    sqs            = "http://localhost:4566"
    ssm            = "http://localhost:4566"
    stepfunctions  = "http://localhost:4566"
    sts            = "http://localhost:4566"
  }
}

# resource "aws_iam_role" "iam_for_lambda_fix" {
#   name = "iam_for_lambda_fix"

#   assume_role_policy = <<EOF
# {
#   "Version": "2012-10-17",
#   "Statement": [
#     {
#       "Action": "sts:AssumeRole",
#       "Principal": {
#         "Service": "lambda.amazonaws.com"
#       },
#       "Effect": "Allow",
#       "Sid": ""
#     }
#   ]
# }
# EOF
# }

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "../src/lambda.py"
  output_path = "lambda.zip"

}

resource "aws_lambda_function" "lambda" {
  filename         = "lambda.zip"
  function_name    = "GetKeys"
  role             = "arn:aws:iam::000000000000:role/lambda-role"
  handler          = "lambda.get_key"
  source_code_hash = "${filebase64sha256("../src/lambda.py")}"
  runtime          = "python3.8"
  timeout = 30

  depends_on = [data.archive_file.lambda_zip]
}

resource "aws_lambda_function_url" "function_url" {

  function_name = aws_lambda_function.lambda.function_name
  authorization_type = "NONE"

}

output "url" {
  value = aws_lambda_function_url.function_url
}