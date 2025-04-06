import os
from PIL import Image
import piexif
import rawpy

def extract_url_from_image(image_path):
    """
    Extract and print the embedded URL from an image's metadata
    """
    try:
        ext = os.path.splitext(image_path)[1].lower()
        
        # Handle RAW formats
        if ext in [".cr2", ".nef", ".arw", ".dng", ".raw"]:
            print(f"ℹ️ RAW file detected: {image_path}")
            print("Note: URL extraction from RAW files might not be supported as they were converted to JPG during compression")
            return

        # Open the image
        img = Image.open(image_path)
        
        # Try to get EXIF data
        if "exif" in img.info:
            exif_dict = piexif.load(img.info["exif"])
            
            # Check for URL in ImageDescription field
            if piexif.ImageIFD.ImageDescription in exif_dict["0th"]:
                url = exif_dict["0th"][piexif.ImageIFD.ImageDescription].decode("utf-8")
                print(f"\n🖼️  File: {os.path.basename(image_path)}")
                print(f"🔗 URL: {url}")
            else:
                print(f"\n🖼️  File: {os.path.basename(image_path)}")
                print("ℹ️ No URL found in metadata")
        else:
            print(f"\n🖼️  File: {os.path.basename(image_path)}")
            print("ℹ️ No EXIF data found in image")

    except Exception as e:
        print(f"\n❌ Error processing {image_path}: {e}")

def check_folder_for_urls(folder_path="compressed_images"):
    """
    Check all images in a folder for embedded URLs
    """
    if not os.path.exists(folder_path):
        print(f"❌ Folder not found: {folder_path}")
        return

    print(f"🔍 Scanning folder: {folder_path}")
    
    # Supported image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.tiff', 
                       '.cr2', '.nef', '.arw', '.dng', '.raw'}
    
    # Scan folder for images
    for filename in os.listdir(folder_path):
        if os.path.splitext(filename)[1].lower() in image_extensions:
            image_path = os.path.join(folder_path, filename)
            extract_url_from_image(image_path)

if __name__ == "__main__":
    # You can change the folder path if needed
    folder_to_check = "compressed_images"
    check_folder_for_urls(folder_to_check)