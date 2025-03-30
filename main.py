import requests
import numpy as np
from PIL import Image

# Load an image
img = np.array(Image.open("mine.jpeg"))


response = requests.post(
    "http://localhost:8000/compress/",
    json={"image": img.tolist(), "quality": 70, "format": "jpeg"}
)


print(f"Original size: {response.headers.get('X-Original-Size')} bytes")
print(f"Compressed size: {response.headers.get('X-Compressed-Size')} bytes")
print(f"Compression ratio: {response.headers.get('X-Compression-Ratio')}x")

# Save the compressed image
with open("compressed.jpg", "wb") as f:
    f.write(response.content)