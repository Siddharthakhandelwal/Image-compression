from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
import numpy as np
import cv2
import io
from typing import List, Optional, Union
import uvicorn

app = FastAPI(title="Image Compression API")

class ImageData(BaseModel):
    image: List[List[List[int]]]
    target_size_kb: Optional[float] = None  # Target size in KB
    target_reduction: Optional[float] = None  # Target reduction percentage (0-100)
    quality: Optional[int] = 80  # Initial quality if using target approach
    format: Optional[str] = "jpeg"

@app.post("/compress/")
async def compress_image(data: ImageData):
    try:
        # Convert list to numpy array
        image_array = np.array(data.image, dtype=np.uint8)
        
        # Check if valid image dimensions
        if len(image_array.shape) < 2 or len(image_array.shape) > 3:
            raise HTTPException(status_code=400, detail="Invalid image dimensions. Expected 2D or 3D array.")
        
        # Validate format
        if data.format.lower() not in ["jpeg", "jpg", "png", "webp"]:
            raise HTTPException(status_code=400, detail="Unsupported format. Use 'jpeg', 'png', or 'webp'.")
            
        # Get original image size in bytes
        original_size = image_array.nbytes
        
        # Determine target size if specified
        target_size = None
        if data.target_size_kb is not None:
            target_size = int(data.target_size_kb * 1024)  # Convert KB to bytes
        elif data.target_reduction is not None:
            if not 0 <= data.target_reduction <= 100:
                raise HTTPException(status_code=400, detail="Target reduction must be between 0 and 100 percent")
            target_size = int(original_size * (1 - data.target_reduction/100))
        
        # Set initial quality
        quality = max(1, min(100, data.quality))
        
        # If target size is specified, use binary search to find appropriate quality
        if target_size is not None:
            min_q = 1
            max_q = 100
            best_quality = quality
            best_diff = float('inf')
            best_result = None
            
            for _ in range(10):  # Max 10 iterations for binary search
                # Encode with current quality
                if data.format.lower() in ["jpeg", "jpg"]:
                    _, encoded_img = cv2.imencode('.jpg', image_array, [cv2.IMWRITE_JPEG_QUALITY, quality])
                elif data.format.lower() == "png":
                    _, encoded_img = cv2.imencode('.png', image_array, [cv2.IMWRITE_PNG_COMPRESSION, min(9, quality // 10)])
                elif data.format.lower() == "webp":
                    _, encoded_img = cv2.imencode('.webp', image_array, [cv2.IMWRITE_WEBP_QUALITY, quality])
                
                # Get current size
                current_size = len(encoded_img.tobytes())
                diff = abs(current_size - target_size)
                
                # Check if this is closer to target
                if diff < best_diff:
                    best_diff = diff
                    best_quality = quality
                    best_result = encoded_img
                
                # If close enough or can't improve further, break
                if diff <= 1024 or max_q - min_q <= 1:  # Within 1KB or can't narrow further
                    break
                
                # Adjust quality based on current size
                if current_size > target_size:
                    max_q = quality
                    quality = (min_q + quality) // 2
                else:
                    min_q = quality
                    quality = (max_q + quality) // 2
            
            # Use the best quality we found
            quality = best_quality
            encoded_img = best_result
        else:
            # Simple quality-based compression
            if data.format.lower() in ["jpeg", "jpg"]:
                _, encoded_img = cv2.imencode('.jpg', image_array, [cv2.IMWRITE_JPEG_QUALITY, quality])
                content_type = "image/jpeg"
            elif data.format.lower() == "png":
                _, encoded_img = cv2.imencode('.png', image_array, [cv2.IMWRITE_PNG_COMPRESSION, min(9, quality // 10)])
                content_type = "image/png"
            elif data.format.lower() == "webp":
                _, encoded_img = cv2.imencode('.webp', image_array, [cv2.IMWRITE_WEBP_QUALITY, quality])
                content_type = "image/webp"
        
        # Set content type based on format
        if data.format.lower() in ["jpeg", "jpg"]:
            content_type = "image/jpeg"
        elif data.format.lower() == "png":
            content_type = "image/png"
        elif data.format.lower() == "webp":
            content_type = "image/webp"
            
        # Get the bytes
        img_bytes = encoded_img.tobytes()
        
        # Calculate stats
        compressed_size = len(img_bytes)
        compression_ratio = original_size / compressed_size if compressed_size > 0 else 0
        reduction_percent = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
        
        # Include compression statistics in headers
        headers = {
            "X-Original-Size": str(original_size),
            "X-Compressed-Size": str(compressed_size),
            "X-Compression-Ratio": str(round(compression_ratio, 2)),
            "X-Reduction-Percent": str(round(reduction_percent, 2)),
            "X-Quality-Used": str(quality)
        }
        
        return Response(content=img_bytes, media_type=content_type, headers=headers)
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Image Compression API is running. Use /compress/ endpoint to compress images."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)