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

app = FastAPI(title="Image Compression API")

class ImageData(BaseModel):
    image: Optional[list] = None  # 3D List (NumPy array)
    image_base64: Optional[str] = None  # Base64 string
    raw_format: Optional[str] = None  # RAW format (e.g., cr2, dng)
    target_size_kb: Optional[float] = None  # Target size in KB
    target_reduction: Optional[float] = None  # Reduction percentage (0-100)
    quality: Optional[int] = 80  # JPEG/WEBP quality (1-100)
    format: Optional[str] = "jpeg"  # Output format

@app.post("/compress/")
async def compress_image(data: ImageData):
    try:
        image_array = None
        
        # Handle direct NumPy array input
        if data.image is not None:
            image_array = np.array(data.image, dtype=np.uint8)
        
        # Handle Base64 input
        elif data.image_base64 is not None:
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
        
        if image_array is None or image_array.ndim not in [2, 3]:
            raise HTTPException(status_code=400, detail="Invalid image dimensions. Expected 2D or 3D array.")
        
        original_size = image_array.nbytes  # Original size in bytes
        target_size = int(data.target_size_kb * 1024) if data.target_size_kb else None
        
        # Set initial quality
        quality = max(1, min(100, data.quality))
        
        # Encode with specified format
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
