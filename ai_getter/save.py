import datetime as dt
import pathlib as pl

import boto3
from requests import get


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
    return save_path / prompt_fn


def save_images_from_openai(
    description: str,
    res: dict,
    save_path: pl.Path,
):
    file_paths = download_images(description, res, save_path)  # type: ignore
    return file_paths


def upload_to_s3(bucket_name: str, file_path: str, key: str):
    s3c = boto3.client("s3")
    s3c.upload_file(file_path, bucket_name, key)


def download_images(prompt: str, res: dict, save_path: pl.Path) -> list[str]:
    fns = []
    for idx, image_dict in enumerate(res["data"]):
        fn = make_fp_from_prompt(prompt, save_path, index=idx, ext="jpg")
        download(image_dict["url"], fn)
        fns.append(fn)
    return fns


def download(url: str, fp: pl.Path):
    fp.write_bytes(get(url).content)
