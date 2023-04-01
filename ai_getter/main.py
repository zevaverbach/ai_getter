import datetime as dt
import os
import pathlib as pl
import sys

import openai
import pyperclip
from rich.pretty import pprint

from .save import save_images_from_openai, upload_to_s3, save_output

openai.organization = os.getenv("OPENAI_ORG")
openai.api_key = os.getenv("OPENAI_TOKEN")

S3_BUCKET = os.getenv("AI_GETTER_S3_BUCKET")
SAVE_PATH = pl.Path(os.getenv("AI_GETTER_SAVE_PATH") or os.path.expanduser("~"))

class NoBucket(Exception):
    pass


def chat(prompt: str, save_path: pl.Path = SAVE_PATH, save_to_s3: bool = False) -> str:
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
    )
    content = response["choices"][0]["message"]["content"]  # type: ignore
    fp = save_output(prompt, content, save_path)
    if save_to_s3:
        if S3_BUCKET is None:
            raise NoBucket("Please provide AI_GETTER_S3_BUCKET in .env")
        upload_to_s3(S3_BUCKET, str(fp), str(fp))
    pprint(response)
    return content # type: ignore


def generate_images(prompt: str, num_images: int, save_path: pl.Path = SAVE_PATH, save_to_s3: bool = False) -> dict:
    if num_images > 10:
        raise ValueError("num_images must be <= 10")
    res = openai.Image.create(prompt=prompt, n=num_images)  # type: ignore
    file_paths = save_images_from_openai(prompt, res, save_path)  # type: ignore
    if save_to_s3:
        if S3_BUCKET is None:
            raise NoBucket("Please provide AI_GETTER_S3_BUCKET in .env")
        for idx, fp in enumerate(file_paths):
            upload_to_s3(S3_BUCKET, fp, f"{prompt}-{dt.date.today()}-{idx}")
    pprint(res)
    return res  # type: ignore


def print_help():
    print("""
Usage:
   aig help
   aig image <prompt> [--clip] --num-images <num_images> [--save-path <path>] [--s3]
   aig text <prompt> [--clip] [--save-path <path>] [--s3]

   (--clip will get the prompt from your clipboard's contents)
    """)



def main():
    args = sys.argv
    if len(args) < 3 or args[1] == "help":
        return print_help()

    typ, prompt, *the_rest = args[1:]

    if typ not in "image text".split():
        return print_help()

    if len(the_rest) == 0 and prompt == "--clip":
        prompt = pyperclip.paste()
    elif "--clip" in the_rest:
        prompt = prompt + " " + pyperclip.paste()

    save_path = SAVE_PATH
    if "--save-path" in the_rest:
        try:
            save_path = pl.Path(the_rest[the_rest.index("--save-path") + 1])
        except IndexError:
            print("Please provide a path after --save-path")
            return

    save_to_s3 = False
    if "--s3" in the_rest:
        if S3_BUCKET is None:
            print("Please provide AI_GETTER_S3_BUCKET in .env")
            return
        save_to_s3 = True


    match typ:
        case "image":
            if "--num-images" not in args:
                print("Please provide --num-images")
                return
            num_images = int(args[args.index("--num-images") + 1])
            try:
                generate_images(prompt, num_images, save_path, save_to_s3)
            except ValueError as e:
                print(str(e))
                return
        case "text":
            chat(prompt, save_path, save_to_s3)
        case _:
            return print_help()
    print("Okay, we're done!")

if __name__ == "__main__":
    main()
