import requests
import base64
import os
from PIL import Image
import io
import piexif
import tifffile
from PIL import PngImagePlugin
import re

# User input
image_input = input("Enter image path: ")
text_data = input("Enter text to embed in metadata (press Enter to skip): ")

# Prepare payload
payload = {
    "quality": 50,
    "format": "jpeg"  # default
}

# Handle image input
if os.path.isfile(image_input):
    ext = os.path.splitext(image_input)[1].lower().replace('.', '')
    payload["format"] = ext if ext in ["jpg", "jpeg", "png", "webp", "tiff", "tif"] else "jpeg"
    with open(image_input, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode("utf-8")
    payload["image_base64"] = image_base64
else:
    payload["image_base64"] = image_input  # assume it's URL

# Add text to payload if available
if text_data:
    payload["text_data"] = text_data

# Send to API
response = requests.post("http://localhost:8000/compress/", json=payload)

# Process response
if response.status_code == 200:
    print(f"Original size: {response.headers.get('X-Original-Size')} bytes")
    print(f"Compressed size: {response.headers.get('X-Compressed-Size')} bytes")
    print(f"Compression ratio: {response.headers.get('X-Compression-Ratio')}x")

    # Determine extension
    content_type = response.headers.get("Content-Type", "image/jpeg")
    file_extension = content_type.split("/")[-1].split(";")[0]
    if file_extension == "jpeg":
        file_extension = "jpg"

    # Save the file
    output_dir = "../OneDrive/Desktop"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"compressed.{file_extension}")
    with open(output_path, "wb") as f:
        f.write(response.content)
    print(f"Compressed image saved to: {output_path}")

    # Try reading embedded metadata
    try:
        if file_extension in ["jpg", "jpeg"]:
            exif_dict = piexif.load(output_path)
            user_comment = exif_dict["Exif"].get(piexif.ExifIFD.UserComment)
            if user_comment:
                print("Embedded metadata:", user_comment.decode("utf-8", errors="ignore"))
            else:
                print("No user comment found in EXIF metadata.")
        elif file_extension == "png":
            with Image.open(output_path) as img:
                info = img.info
                print("Embedded metadata:", info.get("Description", "Not found."))
        elif file_extension == "tiff":
            with tifffile.TiffFile(output_path) as tif:
                desc = tif.pages[0].tags.get("ImageDescription")
                if desc:
                    print("Embedded metadata:", desc.value)
                else:
                    print("No metadata found in TIFF.")
        else:
            print("Metadata reading not supported for this format.")
    except Exception as e:
        print(f"Could not verify metadata: {str(e)}")

else:
    print(f"Error: {response.status_code} - {response.text}")
