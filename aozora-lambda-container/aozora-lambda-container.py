#!/usr/bin/env python3

"""This script uses Beautiful Soup and MeCab to create UTF-8,
plain-text, word-tokenized versions of Aozora Bunko HTML files. The results
are also stripped of all ruby glosses, markup tags, and inline metadata.

Output files basically look the same as the source HTML file when rendered
by a web browser, but with spaces inserted between words by MeCab.

(Exception: inline metadata can't be reliably isolated in very old,
non-standard source files. It gets retained and tokenized along with the work
text for the output versions of these.)

Author: Molly Des Jardin
License: MIT
More info: https://github.com/mollydesjardin/aozora-lambda/

"""

import logging
import os
import re
import sys
import uuid
import warnings
from typing import Any, Match
from urllib.parse import unquote_plus

import boto3
import botocore.exceptions
import MeCab
from bs4 import BeautifulSoup as bs
from bs4 import XMLParsedAsHTMLWarning

logger = logging.getLogger()
logger.setLevel("INFO")
DICT_DIR = "unidic-kindai-bungo"

def create_tagger(dict_config: str) -> MeCab.Tagger:
    try:
        tagger = MeCab.Tagger(f"-r {os.devnull!s} -d {dict_config!s} -Owakati")
        logger.info("Mecab Tagger created")
        return tagger
    except RuntimeError as e:
        if "dicrc" in str(e):
            logger.critical("MeCab Tagger can't be created due to a "
                            "dictionary config problem. Exiting without "
                            "processing any files")
            logger.critical(e, stack_info=True)
        else:
            logger.critical("MeCab Tagger can't be created. Exiting without "
                            "processing any files")
            logger.critical(e, stack_info=True)
        sys.exit(1)
    except Exception as e:
        logger.critical("MeCab Tagger can't be created. Exiting without "
                        "processing any files")
        logger.critical(e, stack_info=True)
        sys.exit(1)

# Create MeCab tagger to reuse for all texts
tagger = create_tagger(DICT_DIR)
# Suppress Beautiful Soup warnings (false positives)
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


ruby = {"start": "<ruby><rb>", "end": "</rb>"}
ruby_old = {"start": "<!R>", "end": "（"}
ruby_pattern = "<ruby><rb>.*?</rb><rp>.*?</ruby>"
ruby_pattern_old = "<!R>.*?（.*?）"

def strip_ruby(text: str) -> str:
    """Strip ruby annotations and markup from Aozora HTML files.

    Parameters
    -------
    text : str
        Text with Aozora HTML and ruby markup

    Returns
    -------
    str
        Original input text (including ruby-glossed base phrases inline),
        stripped of ruby markup and gloss content

    """

    if ruby["start"] in text:
        return re.sub(ruby_pattern, ruby_replace, text)
    elif ruby_old["start"] in text:
        return re.sub(ruby_pattern_old, ruby_replace_old, text)
    # No ruby markup found, return input as-is
    else:
        return text


def ruby_replace(matchobj: Match) -> str:
    """Extract base phrase from ruby pattern matches in standard Aozora files.

    Parameters
    -------
    matchobj : Match
        Individual ruby pattern regex match from standard Aozora HTML

    Returns
    -------
    str
        Base phrase only, stripped of markup and glosses

    """

    return matchobj.group(0).lstrip(ruby["start"]).split(ruby["end"])[0]


def ruby_replace_old(matchobj: Match) -> str:
    """Extract base phrase from ruby pattern matches in oldest Aozora files.

    Parameters
    -------
    matchobj : Match
        Individual ruby pattern regex match from non-standard Aozora HTML

    Returns
    -------
    str
        Base phrase only, stripped of markup and glosses

    """

    return matchobj.group(0).lstrip(ruby_old["start"]).split(ruby_old[
                                                                 "end"])[0]


def extract_work(html_text: str) -> str:
    """Return work (sakuhin) content, stripped of HTML markup and metadata

    Parameters
    -------
    html_text : str
        Aozora HTML file contents

    Returns
    -------
    str
        Plain text of work only

    """

    # Clean up <br /> to avoid excessive line breaks in final output
    html_text = html_text.replace("<br />", "")
    html_text = strip_ruby(html_text)
    try:
        soup = bs(html_text, "html5lib").select(".main_text")
        # Aozora standard HTML contains exactly ONE div with "main_text" class
        if len(soup) == 1:
            return soup[0].text
        # For older files, return markup-stripped text from <body>
        elif len(soup) == 0:
            soup = bs(html_text, "html5lib").find("body")
            if soup:
                return soup.text
        # Do not process if unexpected structure
        return ""
    except(AttributeError, KeyError, UnicodeEncodeError) as e:
        logger.error(f"Beautiful Soup encountered "
                     f"{type(e).__name__!s} trying to extract work "
                     f"content as plain text. Skipping further processing, "
                     f"won't attempt tokenizing or saving output")
        logger.error(e, stack_info=True)
    except Exception as e:
        logger.error(e, stack_info=True)
    return ""


def mecab_parse(text: str) -> str:
    """Tokenize Japanese text by word, using MeCab wakati option.

    Parameters
    -------
    text : str
        Plain text to be tokenized

    Returns
    -------
    str
        Input text with whitespace inserted between words
    """

    text_lines = text.split("\n")
    try:
        parsed_text = "\n".join([tagger.parse(line).strip() for line in
                             text_lines]).strip()
        return parsed_text
    except RuntimeError as e:
        logger.error("Mecab couldn't parse the work contents. Skipping "
                     "further processing, won't save output")
        logger.error(e, stack_info=True)
    except Exception as e:
        logger.error(e, stack_info=True)    # return an empty string if MeCab or other error
    return ""


def convert_html_txt(input_path: str, output_path: str) -> bool:
    """Transform Aozora works to word-tokenized, plain-text versions from HTML.

    Parameters
    -------
    input_path : str
        Path of input Aozora .html file
    output_path : str
        Path to write converted result as .txt file
    """

    with open(input_path, mode="r", encoding="Shift-JIS",
              errors="ignore") as html_file:
        text = html_file.read()
        work_only = extract_work(text)
        if work_only:
            parsed_text = mecab_parse(work_only)
            if parsed_text:
                with open(output_path, mode="w", encoding="utf-8") as txt_file:
                    txt_file.write(parsed_text)
                return True
            else:
                logger.error("MeCab parsing failed, returning False to "
                             "handler without saving output")
                return False
        else:
            logger.error("Beautiful Soup couldn't process unexpected file "
                         "structure. Returning False to handler without "
                         "parsing or saving output")
            return False


def generate_output_key(original_key: str) -> str:
    """Create output version of filename.html, as filename_tokenized.txt

    Parameters
    -------
    original_key : str
        Filename of input HTML file ending in `.html`

    Returns
    -------
    str
        Filename of output TXT file, ending in `_tokenized.txt`
    """

    filename = original_key.rstrip(".html")
    return f"{filename!s}_tokenized.txt"


def check_output(s3_client, output_bucket: str, output_key: str) -> bool:
    """Check whether it is OK to write output to the destination bucket and key

    Parameters
    -------
    s3_client
        Open S3 client to use for object check
    output_bucket : str
        Output S3 bucket name
    output_key : str
        Output key name ending in .txt

    Returns
    -------
    bool
        True if OK to proceed and write output to this bucket/key
        False if the output key exists already, or any other error
    """

    try:
        s3_client.get_object(Bucket=output_bucket, Key=output_key)
        logger.warning(f"Found existing output named {output_key!s}, "
                       f"skipping further processing")
        return False
    except botocore.exceptions.ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchKey":
            return True
        else:
            logger.error(f"Skipped processing because of error with S3 "
                         f"bucket {output_bucket!s}")
            logger.error(error_code)
    except Exception as e:
        logger.error(e, stack_info=True)
    return False


def lambda_handler(event: dict, context: Any) -> None:
    s3_client = boto3.client("s3")
    success_count = 0

    # Iterate over the S3 event object and get all event file keys
    # Assume the S3 trigger is set to only process .html suffix files
    for record in event["Records"]:
        # Remove URL-encoded characters from S3 object name
        key = unquote_plus(record["s3"]["object"]["key"])

        output_key = generate_output_key(key)
        bucket = record["s3"]["bucket"]["name"]
        output_bucket = f"{bucket!s}-converted"

        # Only proceed if output does NOT already exist, for each file in event
        if check_output(s3_client, output_bucket, output_key):
            # Create working paths in the Lambda tmp directory
            download_path = f"/tmp/{uuid.uuid4()}.html"
            upload_path = f"/tmp/tokenized-{uuid.uuid4()}.txt"
            try:
                s3_client.download_file(bucket, key, download_path)
                if convert_html_txt(download_path, upload_path):
                    s3_client.upload_file(upload_path, output_bucket, output_key)
                    logger.info(f"Processed {key!s} and saved output as"
                                f" {output_key!s} in {output_bucket!s}")
                    success_count += 1
                else:
                    logger.error(f"Failed to process {key!s}, didn't save output")
            except botocore.exceptions.ClientError as s3_error:
                logger.error(f"Couldn't process {key!s} due to S3 problem")
                logger.error(s3_error)
            except Exception as e:
                logger.error(f"Couldn't process {key!s}")
                logger.error(e, stack_info=True)
    if success_count >= 1:
        logger.info(f"Finished trying to process {success_count!s} files")
    else:
        logger.warning("No files met the processing criteria")
