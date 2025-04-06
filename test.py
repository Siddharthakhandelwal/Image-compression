import tifffile
import os

def embed_url_in_tiff(tiff_path, url):
    try:
        # Load existing image data
        with tifffile.TiffFile(tiff_path) as tif:
            img_data = tif.asarray()

        # Delete the old TIFF before rewriting
        os.remove(tiff_path)

        # Write the image back with new metadata (ImageDescription tag)
        with tifffile.TiffWriter(tiff_path) as tiff_writer:
            tiff_writer.write(
                img_data,
                description=url
            )
        print(f"✅ Embedded URL into {tiff_path}")
    except Exception as e:
        print(f"❌ Error embedding URL into {tiff_path}: {e}")

def check_url_in_tiff(tiff_path):
    try:
        with tifffile.TiffFile(tiff_path) as tif:
            description = tif.pages[0].description
            if description and description.startswith("http"):
                print(f"✅ Found embedded URL in {tiff_path}: {description}")
            else:
                print(f"🚫 No embedded URL found in {tiff_path}")
    except Exception as e:
        print(f"❌ Error reading TIFF metadata: {e}")

if __name__ == "__main__":
    # Example usage
    tiff_file = "compressed_images/TIFF.tiff"
    dropbox_url = "https://www.dropbox.com/scl/fi/zckw27mapf19nztduos2f/TIFF.tiff?rlkey=zspwszvy1obrwgpr9ts53ygj6&dl=0"

    # Step 1: Embed
    embed_url_in_tiff(tiff_file, dropbox_url)

    # Step 2: Check
    check_url_in_tiff(tiff_file)
