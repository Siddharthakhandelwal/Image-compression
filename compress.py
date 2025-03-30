from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
import numpy as np
import cv2
import io
from typing import List, Optional
import uvicorn

app = FastAPI(title="Image Compression API")

class ImageData(BaseModel):
    image: List[List[List[int]]]
    quality: Optional[int] = 80
    format: Optional[str] = "jpeg"

@app.post("/compress/")
async def compress_image(data: ImageData):
    try:
        # Convert list to numpy array
        image_array = np.array(data.image, dtype=np.uint8)
        
        # Check if valid image dimensions
        if len(image_array.shape) < 2 or len(image_array.shape) > 3:
            raise HTTPException(status_code=400, detail="Invalid image dimensions. Expected 2D or 3D array.")

        if data.format.lower() not in ["jpeg", "jpg", "png", "webp"]:
            raise HTTPException(status_code=400, detail="Unsupported format. Use 'jpeg', 'png', or 'webp'.")
            
        quality = max(1, min(100, data.quality))

        buffer = io.BytesIO()
        # keeping original color space
        if data.format.lower() in ["jpeg", "jpg"]:
            success, encoded_img = cv2.imencode('.jpg', image_array, [cv2.IMWRITE_JPEG_QUALITY, quality])
            content_type = "image/jpeg"
        elif data.format.lower() == "png":
            success, encoded_img = cv2.imencode('.png', image_array, [cv2.IMWRITE_PNG_COMPRESSION, min(9, quality // 10)])
            content_type = "image/png"
        elif data.format.lower() == "webp":
            success, encoded_img = cv2.imencode('.webp', image_array, [cv2.IMWRITE_WEBP_QUALITY, quality])
            content_type = "image/webp"

        if not success:
            raise HTTPException(status_code=500, detail="Failed to encode image")
            
        # Get the bytes
        img_bytes = encoded_img.tobytes()
        

        original_size = image_array.nbytes
        compressed_size = len(img_bytes)
        compression_ratio = original_size / compressed_size if compressed_size > 0 else 0
        
        headers = {
            "X-Original-Size": str(original_size),
            "X-Compressed-Size": str(compressed_size),
            "X-Compression-Ratio": str(round(compression_ratio, 2))
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