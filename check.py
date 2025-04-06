import piexif

def has_embedded_url(image_path):
    """
    Checks if a URL is embedded in the ImageDescription EXIF tag of a JPEG image.

    Parameters:
        image_path (str): Path to the JPEG image.

    Returns:
        bool: True if a URL is embedded, False otherwise.
    """
    try:
        exif_dict = piexif.load(image_path)
        image_description = exif_dict['0th'].get(piexif.ImageIFD.ImageDescription)

        if image_description:
            decoded = image_description.decode("utf-8", errors="ignore")
            if decoded.strip().startswith("http"):
                print(f"✅ URL is embedded in {image_path}")
                print(decoded)
                return True
            else:
                print(f"ℹ️ EXIF description exists but doesn't look like a URL: {decoded}")
        else:
            print(f"ℹ️ No ImageDescription tag found in {image_path}")

    except Exception as e:
        print(f"❌ Error checking EXIF metadata in {image_path}: {e}")
    
    return False

# ======== USAGE ========
image_path = "compressed_images\TIFF.tiff"  # Update this path
has_embedded_url(image_path)
