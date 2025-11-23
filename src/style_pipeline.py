"""Style transfer pipeline using Nano Banana (Gemini) image model.

This script accepts reference style images and a list of target photos. It
summarizes the reference style, asks the user to approve the generated prompt,
then applies the style to each target photo.
"""

import argparse
import os
import pathlib
import sys
from typing import Iterable

from google import genai
from google.genai import types

from mix_images import (
    MODEL_NAME,
    _load_image_parts,
    _process_api_stream_response,
)

STYLE_SUMMARY_INSTRUCTIONS = """
You are an art director. Summarize the shared visual style, typography, color
palette, texture, and any notable graphic elements in these reference
postcards. Return 3-5 concise bullet points highlighting the style traits.
"""


class StylePipelineError(Exception):
    """Domain specific errors for the style pipeline."""


class StylePipeline:
    def __init__(self, api_key: str, model_name: str = MODEL_NAME):
        if not api_key:
            raise StylePipelineError("GEMINI_API_KEY environment variable not set.")
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name

    def summarize_style(self, style_images: list[str]) -> str:
        """Generate a concise description of the reference style images."""
        contents = _load_image_parts(style_images)
        contents.append(types.Part.from_text(text=STYLE_SUMMARY_INSTRUCTIONS))

        response = self._client.models.generate_content(
            model=self._model_name,
            contents=contents,
            config=types.GenerateContentConfig(response_modalities=["TEXT"]),
        )

        if not response.candidates or not response.candidates[0].content:
            raise StylePipelineError("No style description returned by the model.")

        description_parts = []
        for part in response.candidates[0].content.parts or []:
            if part.text:
                description_parts.append(part.text.strip())

        style_description = "\n".join(description_parts).strip()
        if not style_description:
            raise StylePipelineError("Received an empty style description.")
        return style_description

    def build_prompt(self, base_prompt: str, style_description: str) -> str:
        """Construct the final prompt incorporating the style description."""
        return (
            f"{base_prompt}\n\n"
            "Apply the following postcard style details to the target photo while \n"
            "preserving the primary subject and composition: \n"
            f"{style_description}"
        )

    def apply_style(
        self,
        style_images: list[str],
        target_photos: Iterable[str],
        base_prompt: str,
        output_dir: str,
    ) -> None:
        """Run the full pipeline against all target photos."""
        style_description = self.summarize_style(style_images)
        final_prompt = self.build_prompt(base_prompt, style_description)

        print("Generated style description:\n")
        print(style_description)
        print("\nProposed prompt:\n")
        print(final_prompt)

        approval = input("Proceed with this prompt? [y/N]: ").strip().lower()
        if approval not in {"y", "yes"}:
            print("Aborting without generating images.")
            return

        os.makedirs(output_dir, exist_ok=True)

        for photo_path in target_photos:
            if not os.path.exists(photo_path):
                print(f"Skipping missing photo: {photo_path}")
                continue

            print(f"\nProcessing {photo_path}...")
            parts = _load_image_parts([*style_images, photo_path])
            parts.append(types.Part.from_text(text=final_prompt))

            stream = self._client.models.generate_content_stream(
                model=self._model_name,
                contents=parts,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                ),
            )

            target_name = pathlib.Path(photo_path).stem
            target_output_dir = os.path.join(output_dir, target_name)
            os.makedirs(target_output_dir, exist_ok=True)
            _process_api_stream_response(
                stream,
                output_dir=target_output_dir,
            )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize reference postcard styles, ask for approval, and apply the "
            "style to each target photo."
        )
    )
    parser.add_argument(
        "--style-image",
        dest="style_images",
        action="append",
        required=True,
        help="Paths to reference style images (at least two).",
    )
    parser.add_argument(
        "--photo",
        dest="photos",
        action="append",
        required=True,
        help="Paths to target photos to restyle.",
    )
    parser.add_argument(
        "--base-prompt",
        default=(
            "Recreate this photo as a postcard illustration while preserving the "
            "main subject and proportions."
        ),
        help="Base prompt to combine with the derived style description.",
    )
    parser.add_argument(
        "--output-dir",
        default="styled_output",
        help="Directory where styled images will be written.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    if len(args.style_images) < 2:
        print("Please provide at least two reference style images.")
        return 1

    api_key = os.environ.get("GEMINI_API_KEY")
    try:
        pipeline = StylePipeline(api_key=api_key)
        pipeline.apply_style(
            style_images=args.style_images,
            target_photos=args.photos,
            base_prompt=args.base_prompt,
            output_dir=args.output_dir,
        )
    except StylePipelineError as exc:
        print(f"Error: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
