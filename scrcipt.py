import rawpy
import tifffile
import io
from PIL import Image
import numpy as np
import os
import sys

def add_url_to_tiff_metadata(input_path: str, url: str, output_path: str):
    with tifffile.TiffFile(input_path) as tif:
        image = tif.asarray()
    
    tifffile.imwrite(
        output_path,
        image,
       description=f'{{"url": "{url}"}}'
    )
    print(f"URL added to TIFF metadata and saved to: {output_path}")


def convert_raw_to_tiff_with_url(input_path: str, url: str, output_path: str):
    with rawpy.imread(input_path) as raw:
        rgb = raw.postprocess()
    
    tifffile.imwrite(
        output_path,
        rgb,
        description=f'{{"url": "{url}"}}'
    )
    print(f"RAW image converted and URL added to TIFF metadata at: {output_path}")


def process_image(input_path: str, url: str):
    ext = os.path.splitext(input_path)[-1].lower()

    output_path = os.path.splitext(input_path)[0] + "_with_url.tiff"

    if ext in [".tif", ".tiff"]:
        add_url_to_tiff_metadata(input_path, url, output_path)
    elif ext in [".cr2", ".nef", ".arw", ".dng", ".raw"]:
        convert_raw_to_tiff_with_url(input_path, url, output_path)
    else:
        print(" Unsupported format. Please provide a TIFF or RAW image.")


# Example usage:
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python add_url_metadata.py <image_path> <url>")
    else:
        image_path = sys.argv[1]
        url = sys.argv[2]
        process_image(image_path, url)
