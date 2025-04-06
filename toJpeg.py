import os
from PIL import Image
import rawpy
import piexif

def convert_and_compress_to_jpeg(input_path, output_folder, url, quality=50):
    ext = os.path.splitext(input_path)[1].lower()
    filename_wo_ext = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(output_folder, f"{filename_wo_ext}.jpg")

    os.makedirs(output_folder, exist_ok=True)

    if ext in ['.nef', '.cr2', '.arw', '.dng']:  # RAW formats
        with rawpy.imread(input_path) as raw:
            rgb = raw.postprocess()
            image = Image.fromarray(rgb)
    else:
        image = Image.open(input_path).convert('RGB')  # Convert to RGB for JPEG

    # Save JPEG with compression
    image.save(output_path, "JPEG", quality=quality)

    # Embed the URL in the UserComment field of EXIF
    exif_dict = piexif.load(output_path)
    user_comment = url.encode('utf-8')
    exif_dict['Exif'][piexif.ExifIFD.UserComment] = b'\x00\x00' + user_comment
    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, output_path)

    print(f"Saved compressed JPEG with URL to: {output_path}")
    return output_path

# # ======== USAGE ========
# input_image = "downloads\TIFF.tiff"  # any image format
# output_dir = "compressed_images"
# url_to_embed = "https://your-url.com/xyz"

convert_and_compress_to_jpeg(input_image, output_dir, url_to_embed)
