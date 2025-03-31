import requests
import numpy as np
import base64
from PIL import Image
import io
import os 
# Load image
image_path =input("enter image path:")  # Change to your image file
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
     # Define the output file path  
    output_dir="../OneDrive/Desktop"
    # output_dir = "../OneDrive/Desktop"
    os.makedirs(output_dir, exist_ok=True)

   
    file_name = "compressed.jpg"
    output_path = os.path.join(output_dir,file_name)
    with open(output_path, "wb") as f:
        f.write(response.content)
else:
    print(f"Error: {response.json()}")
