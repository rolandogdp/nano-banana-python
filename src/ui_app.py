"""Streamlit UI for the Nano Banana image remixer.

This app lets users upload 1-5 images, provide an optional prompt,
and generate remixed images using the Gemini model.
"""

import os
import tempfile
from typing import Iterable

import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
from google import genai
from google.genai import types

from mix_images import MODEL_NAME, _get_mime_type


def _save_uploads(uploaded_files: Iterable[UploadedFile]) -> list[str]:
    """Persist uploaded files to temporary paths and return their locations."""
    temp_dir = tempfile.mkdtemp(prefix="remix_uploads_")
    saved_paths: list[str] = []
    for uploaded in uploaded_files:
        file_path = os.path.join(temp_dir, uploaded.name)
        with open(file_path, "wb") as f:
            f.write(uploaded.getbuffer())
        saved_paths.append(file_path)
    return saved_paths


def _process_stream_to_memory(stream) -> tuple[list[bytes], list[str]]:
    """Read a streaming response, returning image bytes and text parts."""
    images: list[bytes] = []
    texts: list[str] = []
    for chunk in stream:
        if (
            chunk.candidates is None
            or chunk.candidates[0].content is None
            or chunk.candidates[0].content.parts is None
        ):
            continue

        for part in chunk.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                images.append(part.inline_data.data)
            elif part.text:
                texts.append(part.text)
    return images, texts


def _build_prompt(prompt: str, num_images: int) -> str:
    if prompt.strip():
        return prompt.strip()
    if num_images == 1:
        return "Turn this image into a professional quality studio shoot with better lighting and depth of field."
    return "Combine the subjects of these images in a natural way, producing a new image."


def _remix_images(image_paths: list[str], prompt: str, api_key: str) -> tuple[list[bytes], list[str]]:
    contents = []
    for image_path in image_paths:
        with open(image_path, "rb") as f:
            image_data = f.read()
        contents.append(
            types.Part(inline_data=types.Blob(data=image_data, mime_type=_get_mime_type(image_path)))
        )
    contents.append(types.Part.from_text(text=prompt))

    client = genai.Client(api_key=api_key)
    stream = client.models.generate_content_stream(
        model=MODEL_NAME,
        contents=contents,
        config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
    )
    return _process_stream_to_memory(stream)


def main():
    st.set_page_config(page_title="Nano Banana Image Mixer", page_icon="🍌")
    st.title("Nano Banana Image Mixer")
    st.markdown(
        "Upload 1-5 images, optionally enter a prompt, and remix them using the Gemini model."
    )

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        st.warning("Set the GEMINI_API_KEY environment variable to use this app.")

    uploaded_images = st.file_uploader(
        "Upload between 1 and 5 images",
        accept_multiple_files=True,
        type=["png", "jpg", "jpeg", "webp", "bmp"],
        help="Provide multiple files to blend their subjects together.",
    )

    prompt_input = st.text_area(
        "Optional prompt",
        help="Leave blank for a helpful default based on the number of images.",
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        generate = st.button("Remix images", type="primary")
    with col2:
        st.caption("Outputs appear below and can be downloaded once generated.")

    if generate:
        if not api_key:
            st.error("Please set GEMINI_API_KEY before running the remix.")
            return
        if not uploaded_images:
            st.error("Upload at least one image to begin.")
            return
        if len(uploaded_images) > 5:
            st.error("Please upload no more than five images.")
            return

        prompt = _build_prompt(prompt_input, len(uploaded_images))
        with st.spinner("Remixing images..."):
            saved_paths = _save_uploads(uploaded_images)
            images, texts = _remix_images(saved_paths, prompt, api_key)

        if texts:
            st.subheader("Model messages")
            for text in texts:
                st.write(text)

        if images:
            st.subheader("Remixed images")
            for idx, image_bytes in enumerate(images, start=1):
                st.image(image_bytes, caption=f"Result {idx}")
                st.download_button(
                    label=f"Download image {idx}",
                    data=image_bytes,
                    file_name=f"remixed_image_{idx}.png",
                    mime="image/png",
                    use_container_width=True,
                )
        else:
            st.info("No images were returned by the model. Try again with a different prompt or inputs.")


if __name__ == "__main__":
    main()
