import datetime as dt
import pathlib as pl
import typing as t

import boto3
from requests import get
import trans


def save_output(prompt: str, content: str, save_path: pl.Path) -> pl.Path:
    fp = make_fp_from_prompt(prompt, save_path, ext="txt")
    fp.write_text(content)
    return fp


def make_fp_from_prompt(
    prompt: str,
    save_path: pl.Path,
    ext: str,
    index: int | None = None,
) -> pl.Path:
    prompt_fn = (
        prompt.replace(" ", "")
        .replace("'", "")
        .replace('"', "")
        .replace(".", "")
        .replace(",", "")
        .replace("<", "")
        .replace(">", "")
        .replace("\\", "")
        .replace(";", "")
        .replace("!", "")
        .replace("{", "")
        .replace("}", "")
        .replace("/", "")
        .lower()
    )[: 100 - len(str(save_path))]
    if index is not None:
        prompt_fn = f"{prompt_fn}{index}"
    prompt_fn = f"{prompt_fn}-{dt.datetime.now()}"
    prompt_fn = f"{prompt_fn}.{ext}"
    return save_path / prompt_fn.replace(" ", "")


def save_images_from_openai(
    description: str,
    res: dict,
    save_path: pl.Path,
):
    file_paths = download_images(description, res, save_path)  # type: ignore
    return file_paths


def transform_prompt_for_aws_metadata(prompt: str) -> str:
    MAX_NUM_PYTHON_CHARS_IN_S3_METADATA = (
        1849  # not sure why, but this is close to 1.9kb
        # AWS's limit is supposedly 2kb
    )
    truncated = prompt[:MAX_NUM_PYTHON_CHARS_IN_S3_METADATA]
    backslashes_removed = truncated.replace("\n", "").replace("\t", "")
    return trans.trans(backslashes_removed)


def upload_to_s3(
    bucket_name: str,
    file_path: str,
    key: str,
    prompt: str,
    typ: t.Literal["image", "text"],
    vendor: str,
):
    s3c = boto3.client("s3")
    transformed_prompt = transform_prompt_for_aws_metadata(prompt)
    s3c.upload_file(
        file_path,
        bucket_name,
        key,
        ExtraArgs={
            "Metadata": {
                "prompt": transformed_prompt,
                "date": str(dt.datetime.now()),
                "type": typ,
                "vendor": vendor,
            }
        },
    )


def download_images(prompt: str, res: dict, save_path: pl.Path) -> list[pl.Path]:
    fns = []
    for idx, image_dict in enumerate(res["data"]):
        fn = make_fp_from_prompt(prompt, save_path, index=idx, ext="jpg")
        url = image_dict["url"]
        print(f"Downloading image {idx + 1}")
        download(url, fn)
        fns.append(fn)
    return fns


def download(url: str, fp: pl.Path):
    fp.write_bytes(get(url).content)
