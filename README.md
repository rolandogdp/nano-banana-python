# Nano Banana Python - Image Mixer

This project demonstrates how to remix 1 to 5 images using Google Generative AI.

It now also includes a postcard-style pipeline that:

-   Analyzes two or more reference style images (e.g., postcards) to summarize the desired look.
-   Combines that summary with a base prompt and requests user approval.
-   Applies the approved style prompt to a list of target photos.

## Setup

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd nano-banana-python
    ```

2.  **Install dependencies using `uv`:**

    ```bash
    uv sync
    ```

3.  **Set your Google Gemini API Key:**
    Ensure you have your `GEMINI_API_KEY` or `GOOGLE_API_KEY` set as an environment variable.

    ```bash
    export GEMINI_API_KEY="YOUR_API_KEY"
    # OR
    export GOOGLE_API_KEY="YOUR_API_KEY"
    ```

## Usage

Run the `mix_images.py` script with 1 to 5 input images and an optional prompt. The remixed image(s) will be saved in the `output` directory (or a custom directory if specified).

-   If one image is provided without a prompt, the default prompt will be to "Turn this image into a professional quality studio shoot with better lighting and depth of field.".
-   If multiple images are provided without a prompt, the default prompt will be to "Combine these images in a way that makes sense.".
-   If a prompt is explicitly provided, it will always be used.

### Example 1: Improve a single image (default prompt)

```bash
uv run python src/mix_images.py -i images/man.jpeg
```

### Example 2: Combine two images (default prompt)

```bash
uv run python src/mix_images.py -i images/man.jpeg -i images/cap.jpeg
```

### Example 3: Combine multiple images with a custom prompt

```bash
uv run python src/mix_images.py -i images/man.jpeg -i images/cap.jpeg -i images/soda.jpeg --prompt "Create a product advertisement with the man, cap, and soda."
```

### Example 4: Specify Output Directory

```bash
uv run python src/mix_images.py -i images/man.jpeg -i images/cap.jpeg --prompt "Remix these two images." --output-dir my_custom_output
```

## Style pipeline for postcard-like outputs

Use `src/style_pipeline.py` to summarize two or more reference style images and restyle a batch of photos with user approval of the generated prompt.

```bash
uv run python src/style_pipeline.py \
  --style-image images/postcard_a.jpeg \
  --style-image images/postcard_b.jpeg \
  --photo images/vacation_1.jpeg \
  --photo images/vacation_2.jpeg \
  --base-prompt "Turn each photo into a vintage travel postcard layout with matching typography." \
  --output-dir styled_output
```

The script will:

1.  Generate a concise bullet list describing the shared style of the reference postcards.
2.  Present the combined style-aware prompt for approval before any image generation.
3.  Apply the approved prompt to each photo, writing results to per-photo folders inside `styled_output/`.

## Streamlit UI

Launch a simple browser-based UI to upload images, enter an optional prompt, and remix them with the Gemini model:

```bash
uv run streamlit run src/ui_app.py
```

Make sure `GEMINI_API_KEY` is set in your environment before starting the app.
