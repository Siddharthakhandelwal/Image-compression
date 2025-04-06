import os
import io
import rawpy
import piexif
import tifffile 
from PIL import Image

SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.webp', '.tiff', '.tif', '.raw', '.nef', '.cr2', '.arw']

def compress_image(img: Image.Image, ext: str) -> bytes:
    buffer = io.BytesIO()
    quality = 70  # Compression quality

    if ext in ['.jpg', '.jpeg']:
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
    elif ext == '.png':
        img.save(buffer, format='PNG', optimize=True)
    elif ext == '.webp':
        img.save(buffer, format='WEBP', quality=quality)
    elif ext in ['.tiff', '.tif']:
        img.save(buffer, format='TIFF', compression='tiff_lzw')
    else:
        img.save(buffer, format='JPEG', quality=quality)

    buffer.seek(0)
    return buffer.read()

def add_metadata_piexif(file_path, metadata_text):
    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext in ['.tif', '.tiff']:
            with tifffile.TiffWriter(file_path, append=True) as tif:
                tif.write_description(metadata_text)
        elif ext in ['.jpg', '.jpeg']:
            exif_dict = {"0th": {piexif.ImageIFD.ImageDescription: metadata_text.encode("utf-8")}}
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, file_path)
        else:
            print(f"No EXIF metadata support for {ext}, skipping metadata.")
    except Exception as e:
        print(f"Metadata error: {e}")

def process_image(file_path, metadata_text="Compressed by script"):
    ext = os.path.splitext(file_path)[1].lower()
    filename = os.path.basename(file_path)

    if ext not in SUPPORTED_FORMATS:
        print(f"Unsupported format: {filename}")
        return

    print(f"Processing {filename}...")

    try:
        if ext in ['.raw', '.nef', '.cr2', '.arw']:
            with rawpy.imread(file_path) as raw:
                rgb = raw.postprocess()
                img = Image.fromarray(rgb)
                ext = '.jpg'
                file_path = file_path.rsplit('.', 1)[0] + '.jpg'
        else:
            img = Image.open(file_path)

        compressed_data = compress_image(img, ext)

        # Save compressed image
        with open(file_path, 'wb') as f:
            f.write(compressed_data)

        # Add metadata
        add_metadata_piexif(file_path, metadata_text)
        print(f"Saved and added metadata to {filename}")

    except Exception as e:
        print(f"Error processing {filename}: {e}")

# Example usage
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compress and add metadata to image.")
    parser.add_argument("image_path", help="Path to the image file")
    parser.add_argument("--meta", help="Metadata text to embed", default="Compressed by script")
    args = parser.parse_args()

    process_image(args.image_path, args.meta)
