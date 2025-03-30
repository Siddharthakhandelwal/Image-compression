# Image Compression API

A FastAPI-based service for compressing images while preserving original colors with precise control over file size reduction.

## Overview

This API accepts image data in array format and returns a compressed version of the image using various compression algorithms. It focuses on reducing file size while maintaining the original color information, with multiple ways to specify your target compression level.

## Features

- Compress images using JPEG, PNG, or WebP formats
- Preserve original colors and image content
- Three ways to control compression:
  - Set a target file size in KB
  - Specify a reduction percentage
  - Manually control quality level
- Automatically determine optimal compression settings
- Get detailed compression statistics in response headers

## Installation

1. Clone this repository:

   ```
   git clone https://github.com/yourusername/image-compression-api.git
   cd image-compression-api
   ```

2. Install required dependencies:

   ```
   pip install fastapi uvicorn numpy opencv-python pydantic
   ```

3. For testing with the client example, also install:
   ```
   pip install requests pillow
   ```

## Usage

### Starting the Server

Run the server with:

```
python app.py
```

The API will be available at `http://localhost:8000`.

### API Endpoints

#### `POST /compress/`

Accepts an image array and returns a compressed version.

**Request Body:**

```json
{
  "image": [[[R,G,B], [R,G,B], ...], ...],  // 3D array of image data
  "target_size_kb": 200,                    // (Optional) Target file size in KB
  "target_reduction": 75,                   // (Optional) Target reduction percentage (0-100)
  "quality": 80,                            // (Optional) Compression quality (1-100, default: 80)
  "format": "jpeg"                          // (Optional) Output format: "jpeg", "png", "webp" (default: "jpeg")
}
```

**Notes:**

- If you specify `target_size_kb`, the API will try to compress the image to that size
- If you specify `target_reduction`, the API will try to reduce the file size by that percentage
- If neither target is specified, it will use the `quality` parameter directly
- Providing both targets will prioritize `target_size_kb`

**Response:**

- Content: The compressed image binary data
- Content-Type: Appropriate media type for the format (e.g., "image/jpeg")
- Headers:
  - X-Original-Size: Original image size in bytes
  - X-Compressed-Size: Compressed image size in bytes
  - X-Compression-Ratio: Compression ratio
  - X-Reduction-Percent: Percentage by which the file was reduced
  - X-Quality-Used: The quality setting that was used

## Controlling Compression Level

### Option 1: Target File Size

Specify a target file size in kilobytes:

```python
response = requests.post(
    "http://localhost:8000/compress/",
    json={
        "image": image_array.tolist(),
        "target_size_kb": 200,  # Target: 200 KB
        "format": "jpeg"
    }
)
```

### Option 2: Target Reduction Percentage

Specify how much you want to reduce the file size:

```python
response = requests.post(
    "http://localhost:8000/compress/",
    json={
        "image": image_array.tolist(),
        "target_reduction": 75,  # Target: 75% reduction
        "format": "jpeg"
    }
)
```

### Option 3: Manual Quality Setting

Directly control the compression quality:

```python
response = requests.post(
    "http://localhost:8000/compress/",
    json={
        "image": image_array.tolist(),
        "quality": 70,  # Lower value = more compression
        "format": "jpeg"
    }
)
```

## Preserving Original Colors

The API is designed to maintain the original colors of your images. It achieves this by:

1. **No color space conversions**: The image array is processed in its original color format
2. **Direct encoding**: The array is directly encoded to the output format without intermediate transformations

If you're working with different color formats (RGB vs BGR), make sure your input array matches your expectations.

## Example Client Code

```python
import requests
import numpy as np
from PIL import Image

# Load an image
img = np.array(Image.open("your_image.jpg"))

# Send to API with target reduction
response = requests.post(
    "http://localhost:8000/compress/",
    json={
        "image": img.tolist(),
        "target_reduction": 70,  # Reduce file size by 70%
        "format": "jpeg"
    }
)

# Check compression stats
print(f"Original size: {response.headers.get('X-Original-Size')} bytes")
print(f"Compressed size: {response.headers.get('X-Compressed-Size')} bytes")
print(f"Reduction: {response.headers.get('X-Reduction-Percent')}%")
print(f"Quality used: {response.headers.get('X-Quality-Used')}")

# Save the compressed image
with open("compressed.jpg", "wb") as f:
    f.write(response.content)
```
