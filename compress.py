from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
import numpy as np
import cv2
import io
import base64
import rawpy
import tifffile
from typing import Optional
import uvicorn
import requests
from PIL import Image, ImageDraw, ImageFont, ExifTags
import re
import piexif
import json

app = FastAPI(title="Image Compression API")

class ImageData(BaseModel):
    image: Optional[list] = None  
    image_base64: Optional[str] = None  
    text_data: Optional[str] = None  # Field for text to embed in metadata
    raw_format: Optional[str] = None 
    target_size_kb: Optional[float] = None 
    target_reduction: Optional[float] = None  
    quality: Optional[int] = 80 
    format: Optional[str] = "jpeg" 

def is_url(string):
    url_pattern = re.compile(
        r'^(https?://)?'  # http:// or https://
        r'([a-zA-Z0-9.-]+)'  # domain
        r'(\.[a-zA-Z]{2,})'  # top-level domain
        r'(/[^\s]*)?$'  # path
    )
    return bool(url_pattern.match(string))

def add_metadata_to_image(image_array, text_data, image_format):
    """Add text data to image metadata instead of drawing it on the image"""
    # Convert numpy array to PIL Image
    if len(image_array.shape) == 3:
        pil_image = Image.fromarray(cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB))
    else:
        pil_image = Image.fromarray(image_array)
    
    # Create a bytes buffer to hold the image
    buffer = io.BytesIO()
    
    if image_format.lower() in ["jpeg", "jpg"]:
        # For JPEG, we can use EXIF data
        # Create EXIF data
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        
        # Add text to UserComment field
        exif_dict["Exif"][piexif.ExifIFD.UserComment] = text_data.encode('utf-8')
        
        # Convert to bytes
        exif_bytes = piexif.dump(exif_dict)
        
        # Save image with EXIF data
        pil_image.save(buffer, format=image_format.upper(), exif=exif_bytes)
    
    elif image_format.lower() == "png":
        # For PNG, we can use text chunks
        metadata = PngInfo()
        metadata.add_text("Description", text_data)
        pil_image.save(buffer, format="PNG", pnginfo=metadata)
    
    elif image_format.lower() == "webp":
        # WebP has limited metadata support
        pil_image.save(buffer, format="WEBP", metadata=[("Description", text_data)])
    
    elif image_format.lower() in ["tif", "tiff"]:
        # For TIFF, we can use EXIF data
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        exif_dict["Exif"][piexif.ExifIFD.UserComment] = text_data.encode('utf-8')
        exif_bytes = piexif.dump(exif_dict)
        pil_image.save(buffer, format="TIFF", exif=exif_bytes)
    
    buffer.seek(0)
    return buffer.getvalue()

@app.post("/compress/")
async def compress_image(data: ImageData):
    try:
        image_array = None
        
        # Handle image input (either URL or base64)
        if data.image_base64:
            if is_url(data.image_base64):
                # If it's a URL, download the image
                response = requests.get(data.image_base64)
                if response.status_code != 200:
                    raise HTTPException(status_code=400, detail="Failed to download image from URL")
                binary_data = response.content
                image_array = cv2.imdecode(np.frombuffer(binary_data, np.uint8), cv2.IMREAD_UNCHANGED)
            else:
                # If it's base64, decode it
                binary_data = base64.b64decode(data.image_base64)
                
                # Handle RAW images
                if data.raw_format and data.raw_format.lower() in ['cr2', 'nef', 'arw', 'dng', 'raw']:
                    with rawpy.imread(io.BytesIO(binary_data)) as raw:
                        image_array = raw.postprocess()
                
                # Handle TIFF images
                elif data.raw_format and data.raw_format.lower() in ['tif', 'tiff']:
                    image_array = tifffile.imread(io.BytesIO(binary_data))
                    image_array = (image_array / 65535 * 255).astype(np.uint8) if image_array.max() > 255 else image_array.astype(np.uint8)
                
                else:
                    image_array = cv2.imdecode(np.frombuffer(binary_data, np.uint8), cv2.IMREAD_UNCHANGED)
        
        # Handle direct NumPy array input
        elif data.image is not None:
            image_array = np.array(data.image, dtype=np.uint8)
        
        if image_array is None or image_array.ndim not in [2, 3]:
            raise HTTPException(status_code=400, detail="Invalid image dimensions. Expected 2D or 3D array.")
        
        original_size = image_array.nbytes  # Original size in bytes
        target_size = int(data.target_size_kb * 1024) if data.target_size_kb else None
        
        # Set initial quality
        quality = max(1, min(100, data.quality))
        
        # First compress the image
        encode_params = []
        if data.format.lower() in ["jpeg", "jpg"]:
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
            ext = '.jpg'
        elif data.format.lower() == "png":
            encode_params = [cv2.IMWRITE_PNG_COMPRESSION, min(9, quality // 10)]
            ext = '.png'
        elif data.format.lower() == "webp":
            encode_params = [cv2.IMWRITE_WEBP_QUALITY, quality]
            ext = '.webp'
        elif data.format.lower() in ["tif", "tiff"]:
            ext = '.tiff'
            with io.BytesIO() as tiff_buffer:
                tifffile.imwrite(tiff_buffer, image_array, compress=1)
                tiff_buffer.seek(0)
                img_bytes = tiff_buffer.getvalue()
        else:
            raise HTTPException(status_code=400, detail="Unsupported format. Use 'jpeg', 'png', 'webp', or 'tiff'.")
        
        if data.format.lower() not in ["tiff", "tif"]:
            _, encoded_img = cv2.imencode(ext, image_array, encode_params)
            img_bytes = encoded_img.tobytes()
        
        # Now add metadata if text_data is provided
        if data.text_data:
            # Convert back to image array for metadata processing
            temp_img_array = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_UNCHANGED)
            # Add metadata and get the final bytes
            img_bytes = add_metadata_to_image(temp_img_array, data.text_data, data.format)
        
        # Compute compression statistics
        compressed_size = len(img_bytes)
        compression_ratio = original_size / compressed_size if compressed_size > 0 else 0
        reduction_percent = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
        
        headers = {
            "X-Original-Size": str(original_size),
            "X-Compressed-Size": str(compressed_size),
            "X-Compression-Ratio": str(round(compression_ratio, 2)),
            "X-Reduction-Percent": str(round(reduction_percent, 2)),
            "X-Quality-Used": str(quality)
        }
        
        return Response(content=img_bytes, media_type=f"image/{data.format}", headers=headers)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Image Compression API is running. Use /compress/ endpoint to compress images."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)