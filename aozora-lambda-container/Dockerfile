# This file was expanded from templates provided by AWS:
# https://github.com/aws-samples/aws-lambda-inference-cdk-compute-blog/blob/main/ml-images/oci/Dockerfile
# https://docs.aws.amazon.com/lambda/latest/dg/python-image.html
#
# I also used the following as examples
# https://docs.astral.sh/uv/guides/integration/aws-lambda/#deploying-a-docker-image
# https://recruit.cct-inc.co.jp/tecblog/aws/lambda-container-image-mecab/


# Download and unzip dictionary files for copying into {LAMBDA_TASK-ROOT}
FROM public.ecr.aws/lambda/python:3.13 AS downloader

RUN dnf install -y unzip && dnf clean all
RUN curl -L "https://clrd.ninjal.ac.jp/unidic_archive/2308/unidic-kindai-bungo-v202308.zip" -o unidic-kindai-bungo.zip \
    && unzip unidic-kindai-bungo.zip -d ${LAMBDA_TASK_ROOT} \
    && rm -rf unidic-kindai-bungo.zip


# Install needed packages for copying into {LAMBDA_TASK_ROOT}
FROM public.ecr.aws/lambda/python:3.13 AS builder

COPY requirements.txt .
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy runtime dependencies and dictionary files from builder and downloader stages
FROM public.ecr.aws/lambda/python:3.13
COPY --from=downloader ${LAMBDA_TASK_ROOT} ${LAMBDA_TASK_ROOT}
COPY --from=builder ${LAMBDA_TASK_ROOT} ${LAMBDA_TASK_ROOT}

# Copy application code
COPY aozora_lambda_container.py ${LAMBDA_TASK_ROOT}

# Set the AWS Lambda handler
CMD ["aozora_lambda_container.lambda_handler"]
