import requests
import numpy as np
import base64
from PIL import Image
import io

# Load image
image_path = "WhatsApp Image 2025-03-27 at 10.22.33_1ae424aa.tiff"  # Change to your image file
with open(image_path, "rb") as img_file:
    image_bytes = img_file.read()

# Convert to Base64
image_base64 = base64.b64encode(image_bytes).decode('utf-8')

# Send request to API
response = requests.post(
    "http://localhost:8000/compress/",
    json={"image_base64": image_base64, "quality": 70, "format": "jpeg"}
)

# Check response
if response.status_code == 200:
    print(f"Original size: {response.headers.get('X-Original-Size')} bytes")
    print(f"Compressed size: {response.headers.get('X-Compressed-Size')} bytes")
    print(f"Compression ratio: {response.headers.get('X-Compression-Ratio')}x")

    # Save compressed image
    with open("compressed.jpg", "wb") as f:
        f.write(response.content)
else:
    print(f"Error: {response.json()}")
