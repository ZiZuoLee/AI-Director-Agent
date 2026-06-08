"""Compose individual shot images into a horizontal storyboard."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Sequence

from PIL import Image, ImageDraw, ImageFont


def merge_storyboard(
    image_paths: Sequence[str],
    *,
    output_path: Path | str,
    labels: Optional[Sequence[str]] = None,
    padding: int = 16,
    label_height: int = 36,
    background_color: str = "#111111",
    label_color: str = "#f5f5f5",
) -> Path:
    """Merge shot images side-by-side and write a storyboard PNG."""

    paths = [Path(path) for path in image_paths if path]
    if not paths:
        raise ValueError("At least one image path is required to merge a storyboard.")

    images: List[Image.Image] = []
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(f"Storyboard source image not found: {path}")
        images.append(Image.open(path).convert("RGB"))

    max_height = max(image.height for image in images)
    resized: List[Image.Image] = []
    for image in images:
        if image.height != max_height:
            scale = max_height / image.height
            new_width = max(1, int(image.width * scale))
            resized.append(image.resize((new_width, max_height), Image.Resampling.LANCZOS))
        else:
            resized.append(image)

    total_width = sum(image.width for image in resized) + padding * (len(resized) + 1)
    canvas_height = max_height + label_height + padding * 2
    canvas = Image.new("RGB", (total_width, canvas_height), background_color)
    draw = ImageDraw.Draw(canvas)

    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except OSError:
        font = ImageFont.load_default()

    x_offset = padding
    for index, image in enumerate(resized):
        y_offset = padding + label_height
        canvas.paste(image, (x_offset, y_offset))
        label = labels[index] if labels and index < len(labels) else f"Shot {index + 1}"
        draw.text((x_offset + 4, padding), label, fill=label_color, font=font)
        x_offset += image.width + padding

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination, format="PNG")
    return destination
