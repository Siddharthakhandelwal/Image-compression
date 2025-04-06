import requests
import numpy as np
import base64
from PIL import Image
import io
import os 

# Get input from user
image_input = input("Enter image path: ")
text_data = input("Enter text to embed in metadata (press Enter to skip): ")

# Prepare payload
payload = {
    "quality": 70,
    "format": "jpeg"
}

# Handle image input (either path or URL)
if os.path.isfile(image_input):  # Check if it's a local file
    with open(image_input, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode('utf-8')
    payload["image_base64"] = image_base64
else:  # Treat as URL
    payload["image_base64"] = image_input

# Add text data if provided
if text_data:
    payload["text_data"] = text_data

# Send request to API
response = requests.post(
    "http://localhost:8000/compress/",
    json=payload
)

# Check response
if response.status_code == 200:
    print(f"Original size: {response.headers.get('X-Original-Size')} bytes")
    print(f"Compressed size: {response.headers.get('X-Compressed-Size')} bytes")
    print(f"Compression ratio: {response.headers.get('X-Compression-Ratio')}x")

    # Save compressed image
    output_dir = "../OneDrive/Desktop"
    os.makedirs(output_dir, exist_ok=True)

    file_name = "compressed.jpg"
    output_path = os.path.join(output_dir, file_name)
    with open(output_path, "wb") as f:
        f.write(response.content)
    print(f"Compressed image saved to: {output_path}")
    
    # Verify metadata
    try:
        from PIL import Image
        import piexif
        
        img = Image.open(output_path)
        if "exif" in img.info:
            exif_dict = piexif.load(img.info["exif"])
            if piexif.ExifIFD.UserComment in exif_dict["Exif"]:
                embedded_text = exif_dict["Exif"][piexif.ExifIFD.UserComment].decode('utf-8')
                print(f"Embedded metadata: {embedded_text}")
        else:
            print("No EXIF metadata found. Format may not support metadata.")
    except Exception as e:
        print(f"Could not verify metadata: {str(e)}")
else:
    print(f"Error: {response.json()}")