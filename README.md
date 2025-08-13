# Aozora Corpus Builder for AWS Lambda

## Introduction

This is a collection of Python scripts that create plain-text versions of Japanese-language HTML files from the digital archive [Aozora Bunko](https://www.aozora.gr.jp). It's designed to be run as AWS Lambda functions and stay within Free Tier constraints as much as humanly possible.

The resulting output files are intended to be compatible with popular analysis software by doing the following:

1. Conversion from Shift-JIS to UTF-8 encoding (implicitly)
2. Removal of annotations and inline metadata, including ruby glosses and HTML tags
3. Inserting spaces between words

This is adapted from [my existing Aozora Corpus Builder project](https://github.com/mollydesjardin/aozora), which I created to run locally on all Aozora HTML files as a large collection. Here are the key differences with this AWS Lambda edition:

- Each subdirectory contains a different deployment option, with all necessary files:
    - `aozora-lambda-container`: Docker image built from the AWS Lambda base image with NINJAL `unidic-kindai-bungo` dictionary bundled in
        - Dictionary files are downloaded/extracted as part of the multi-stage build process
        - This option isn't Free Tier compatible because of the large image size, but is very inexpensive to store and pull from Amazon ECR (1599.11 MB as of this writing)
    - `aozora-lambda-efs`: Lambda zip deployment that accesses the `unidic-kindai-bungo` dictionary stored in an EFS filesystem
        - Free Tier compatible
        - Much more complicated to set up in AWS, compared with the Docker version
        - Uses Lambda Layer for dependencies
    - `aozora-lambda-zip-nodict`: Lambda zip deployment that does everything except tokenizing with MeCab
        - Uses Lambda Layer for dependencies
        - _Why no tokenizing?_ The dictionary files (an ML model for the tokenizing/inference stage) are 2GB, way too big if not using one of the above two options and impractical to retrieve from S3 in init
- Runs on individual files as they're uploaded to `<input_s3_bucket>` like `<original_filename>.html`
- Converts the file contents per the 3 steps above, and saves them as `<original_filename>_tokenized.txt` in output bucket `<input_s3_bucket>-converted`
- _Does NOT do anything related to metadata, yet_


## Project and Documentation Status

This document and the project itself are in-progress. All code has been tested in AWS with an S3 file creation trigger.

My highest priorities for adding to the project are:
- Fleshing out the documentation
- Recommendations on configuration, ex. Lambda memory and timeout settings
- Adding file metadata and management components using DynamoDB, S3, and Lambda
- IaC deployment resources


## Further Resources

For more background and documentation, please see my older [Aozora Corpus Builder](https://github.com/mollydesjardin/aozora) project for now. The logic of converting the file contents is still the same!

Helpful examples I used in the development process:
- [AWS-CDK ML Inference](https://github.com/aws-samples/aws-lambda-inference-cdk-compute-blog) and accompanying [blog post](https://aws.amazon.com/blogs/compute/choosing-between-storage-mechanisms-for-ml-inferencing-with-aws-lambda/)
- [AWS Lambda with Container Image で MeCab (NEologd) を動かしてみた](https://recruit.cct-inc.co.jp/tecblog/aws/lambda-container-image-mecab/)
