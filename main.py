import datetime as dt
import os
import pathlib as pl
import sys

import openai

from save import save_images_from_openai, upload_to_s3, save_output

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
    return res  # type: ignore



def main():
    args = sys.argv
    if len(args) < 3:
        print("Please provide <image/text> and a prompt")
        sys.exit()

    typ, prompt = args[1:3]
    if typ not in "image text".split():
        print("Please provide <image/text> and a prompt")
        sys.exit()

    if "--save-path" in args:
        save_path = pl.Path(args[args.index("--save-path") + 1])
    else:
        save_path = SAVE_PATH

    save_to_s3 = False
    if "--save-to-s3" in args:
        save_to_s3 = True

    if save_to_s3 and S3_BUCKET is None:
        print("Please provide AI_GETTER_S3_BUCKET in .env")
        sys.exit()

    match typ:
        case "image":
            if "--num-images" not in args:
                print("Please provide --num-images")
                sys.exit()
            num_images = int(args[args.index("--num-images") + 1])
            try:
                generate_images(prompt, num_images, save_path, save_to_s3)
            except ValueError as e:
                print(str(e))
                sys.exit()
        case "text":
            chat(prompt, save_path, save_to_s3)
        case _:
            print("Please provide <image/text> and a prompt")
            sys.exit()
    print("Okay, we're done!")

if __name__ == "__main__":
    main()
