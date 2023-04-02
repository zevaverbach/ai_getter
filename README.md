# A CLI for Requesting AI-Generated Things!

## Installation

`pip install ai_getter`

## Usage

```bash
   aig help
   aig image <prompt> [--clip] --num-images <num_images> [--save-path <path>] [--s3]
   aig text <prompt> [--clip] [--save-path <path>] [--s3]

   --clip will get the prompt from your clipboard's contents, in addition to <prompt> if you supply one
   --s3 will upload the result to your AI_GETTER_S3_BUCKET
   set env var AI_GETTER_ALWAYS_SAVE_TO_S3=1 to save to s3 by default
```

# Environment Variables

- `OPENAI_ORG`
- `OPENAI_TOKEN`
- `AI_GETTER_SAVE_PATH`
- `AI_GETTER_S3_BUCKET`
- `AI_GETTER_ALWAYS_SAVE_TO_S3` (0 or 1)

# Credentials

Make sure you have credentials in an `~/.aws` directory if you want to upload any outputs to S3.
