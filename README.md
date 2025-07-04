# Aozora Corpus Builder for AWS Lambda

## Introduction

This is a collection of Python scripts that create plain-text versions of Japanese-language HTML files from the digital archive [Aozora Bunko](https://www.aozora.gr.jp). It's designed to be run as an AWS Lamdba function, using two S3 buckets (input and output), triggered by an HTML file-creation event -- and to stay within Free Tier constraints as much as humanly possible.

The resulting output files are intended to be compatible with popular analysis software by doing the following:

- Conversion from Shift-JIS to UTF-8 encoding (implicitly
- Removal of annotations and inline metadata, including ruby glosses and HTML tags
- Inserting spaces between words

This is adapted from [my existing Aozora Corpus Builder project](https://github.com/mollydesjardin/aozora), which I created to run locally on an archive of all Aozora HTML files in bulk. Here are the key differences with this AWS Lambda edition:

- Each subdirectory contains a different deployment option, with all necessary files:
    - `aozora-lambda-container` is a Docker image built from the AWS Lambda base image and includes MeCab tokenizing with `unidic-kindai-bungo` dictionary from NINJAL
        - Dictionary files are downloaded/extracted as part of the multi-stage build process
        - This option isn't Free Tier compatible because of the large image size, but is very inexpensive to store and pull from Amazon ECR (1599.11 MB as of this writing)
    - `aozora-lambda-zip-nodict` is a Lambda-only zip deployment that does not perform any tokenizing
        - Why? The dictionary files (an ML model for the tokenizing/inference stage) are 2GB
        - Stay tuned for a full version that uses MeCab with EFS for dictionary access
- Runs on individual files as they're uploaded to S3
- Does NOT do anything related to metadata
- Just converts the file contents


## Project and Documentation Status

This document and the project itself are in-progress. All code has been tested in AWS with an S3 file creation trigger.

My highest priorities for adding to the project are:
- Fleshing out the documentation
- Sharing code for a Lambda zip deployment version that uses MeCab dictionary files stored in EFS
- Creating an AWS configuration guide to use with each version, including RAM/timeout tuning
- IaC deployment resources


## Further Resources

Please see my older [Aozora Corpus Builder](https://github.com/mollydesjardin/aozora) project for more extensive documentation about the code and data pre-processing with Japanese sources more generally. The logic of converting the file contents is largely the same!

In creating this project, I found these examples helpful:
- [AWS-CDK ML Inference](https://github.com/aws-samples/aws-lambda-inference-cdk-compute-blog) and accompanying [blog post](https://aws.amazon.com/blogs/compute/choosing-between-storage-mechanisms-for-ml-inferencing-with-aws-lambda/)
- [AWS Lambda with Container Image で MeCab (NEologd) を動かしてみた](https://recruit.cct-inc.co.jp/tecblog/aws/lambda-container-image-mecab/)
