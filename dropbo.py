import os
import dropbox
from PIL import Image
import rawpy
import piexif

# =========🔐 Dropbox Access Token =========
ACCESS_TOKEN = "sl.u.AFpgcabLcSbH_VQ7yzwB50C6S2iklNnKJd2MjOmfjFb4qGAWg4m5f_C-JIoTCwZnbVrfBx_roqDTwfWEl67NTCdGgabP1Azgovsr5aJs3C1znlioFwjCcZsaSYkA5907sIt9Y_VRz2LgtpUK-6IR_wYllzdwbKpHS3-QvZRyMzBUy_yWPEgVdI7qYtrwjm_8kVNuMkyi1VK4wg40H3FaEgXe4lS91qD0601ijLgBL38m7tVZrH3FQJQ912lVJEhE-WKykK5Jl6O3CL3U194s6L7NO8P_FK0XNYbIp765IHzv4V9U4aOXfQH1Eu1c-fTST-c2G1cMM_p9evjqDYXnAsFUdU8FpgKmhzBddcMqEhxXU6v_4Z7omIH-S9utqbwNWkrF53UmMK5e59XOQruaWJfGdR6KvO4B8c2Vb-snrI-QERbQKxOL7n2TcdogLMpwAWI3ti6xKIf4eZi1B9I060tN4ocvKwUIGZalYmx01VwdwV6hk6wu2C61GouMTVcPsvmapZs9agpmEoECdqo3FwPW7pBMPsJzepiQPaN8nkQaFv6eTJhvP7uXioX1fw2O1JmZO_m9pNHoK9OptQ50z6HZoogYyDu21NZSFEC7jZ4CCSZSS94yTumKcmbH1WBJew-PkqpvaVs7O8pigHSja1_e_r1j5GmB5Z7xi2wgcBfnFlg1VHF4depklc3i1F9YmRIbXmqAwEmbZw74htEoKgjGKQvrHyaVTB9JdryJ2abjY1-Dy5JDzpOb1rWKd_IMOdkpBvtB_XIOWh5ZPf7Ad9KgrudOF8F0Q2L5E6F3Sh9HhXZRPEl8CHJXBcnGPO6Je9QQgV8b4tJSUM-TkAOJDHSgSAPXvxIyp3oR-bEqFZB8SWysjNS8TtrQL9l1ntO0Cwe7wk9y2sWFStMx-DDrTH4B7LeLTH1ynRB1K_E78vhYyEzymnSbptBlkFDWZdkMa621qNhgufH3j7ZhBCstcqCLtjCMGo_GN1EtEE47J7-JxSE8Ywr3ugwhXQ6wKqib892yR4AIobnKDm890gMBmGeMyX4TeHiAJdAnRslTO_Gp1jjD24XsFGD_HdAJQDDDnq5aZiNIRQUSJFZ5E5p8QkeQNkeyeOIxUqAsQiLaz4kJzrmNHK2AJhY9fb0ofttnbTVtE49gk2ay5leoQwI_3k2z4-d5CvpXTC16PLXTS6yhL5E2VEN9d6-joboHmKcIqhlQXedvaEVanhLQTod-E-HndHRlgULz09XKKFF8RudCczj0V6D7Oksn4rI4kDu4H6vgGShmSp_0e8HBO2k2rIaCZqcIitOnhRJQEvBN-RMPIPEzKEUJ8mSNRvk5FEfrkT5u1pWDX4eVekR2A1kS1GDYSuAjRTEIkMLOw1R8FN2aHF-yY-qX78XQUNrSI39LdfBj2sDib_D2Uj681U0GwvOX "# <- Replace this
dbx = dropbox.Dropbox(ACCESS_TOKEN)

# =========🔧 Settings =========
DEFAULT_QUALITY = 10  # JPEG quality (0–100)
NUM_LATEST_FILES = 10  # How many recent files to process
DOWNLOAD_FOLDER = "downloads"
COMPRESSED_FOLDER = "compressed_images"

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(COMPRESSED_FOLDER, exist_ok=True)

# =========📁 Get Files from Dropbox =========
def get_latest_files(folder_path="", limit=NUM_LATEST_FILES):
    try:
        entries = dbx.files_list_folder(folder_path).entries
        files = [f for f in entries if isinstance(f, dropbox.files.FileMetadata)]
        files.sort(key=lambda x: x.server_modified, reverse=True)
        return files[:limit]
    except Exception as e:
        print(f"❌ Error fetching files: {e}")
        return []

# =========🔗 Get/Generate Shared Link =========
def get_shared_link(path):
    try:
        links = dbx.sharing_list_shared_links(path=path).links
        if links:
            return links[0].url
        shared_link_metadata = dbx.sharing_create_shared_link_with_settings(path)
        return shared_link_metadata.url
    except Exception as e:
        print(f"❌ Error generating shared link for {path}: {e}")
        return ""

# =========🗜️ Compress and Embed URL =========
def compress_image(input_path, output_path, metadata_url, quality=DEFAULT_QUALITY):
    ext = os.path.splitext(input_path)[1].lower()

    try:
        # Handle RAW formats
        if ext in [".cr2", ".nef", ".arw", ".dng", ".raw", ".cr3"]:
            try:
                with rawpy.imread(input_path) as raw:
                    rgb = raw.postprocess()
                    img = Image.fromarray(rgb)
                    ext = ".jpg"
                    output_path = os.path.splitext(output_path)[0] + ".jpg"
            except Exception as e:
                print(f"❌ Error reading RAW file {input_path}: {e}")
                return None
        else:
            img = Image.open(input_path).convert("RGB")

        # Prepare EXIF with embedded URL
        exif_dict = {"0th": {piexif.ImageIFD.ImageDescription: metadata_url.encode("utf-8")}}
        exif_bytes = piexif.dump(exif_dict)

        # Save as JPEG with EXIF metadata
        img.save(output_path, format="JPEG", quality=quality, optimize=True, exif=exif_bytes)

        original_size = os.path.getsize(input_path)
        compressed_size = os.path.getsize(output_path)
        ratio = round(compressed_size / original_size, 3)

        print(f"\n🖼️ File: {os.path.basename(input_path)}")
        print(f"📦 Original Size: {original_size} bytes")
        print(f"🗜️ Compressed Size: {compressed_size} bytes")
        print(f"📉 Compression Ratio: {ratio}")
        print(f"🔗 Embedded URL: {metadata_url}")

        return output_path

    except Exception as e:
        print(f"❌ Compression error: {e}")
        return None

# =========🔍 Extract Embedded URL =========
def extract_url_from_jpeg(jpeg_path):
    try:
        exif_dict = piexif.load(jpeg_path)
        image_description = exif_dict['0th'].get(piexif.ImageIFD.ImageDescription)

        if image_description:
            url = image_description.decode('utf-8', errors='ignore')
            print(f"🔍 Extracted URL from {jpeg_path}: {url}")
            return url
        else:
            print(f"ℹ️ No URL found in EXIF of {jpeg_path}")
            return None
    except Exception as e:
        print(f"❌ Error reading EXIF from {jpeg_path}: {e}")
        return None

# =========🚀 Main Process =========
def download_and_compress():
    files = get_latest_files(limit=NUM_LATEST_FILES)

    for file in files:
        try:
            path = file.path_lower
            name = file.name
            local_path = os.path.join(DOWNLOAD_FOLDER, name)
            compressed_path = os.path.join(COMPRESSED_FOLDER, name)

            # Download from Dropbox
            dbx.files_download_to_file(local_path, path)

            # Get Dropbox shared URL
            url = get_shared_link(path)

            # Compress image and embed URL
            final_compressed_path = compress_image(local_path, compressed_path, url)

            # Extract and verify embedded URL
            if final_compressed_path and final_compressed_path.lower().endswith((".jpg", ".jpeg")):
                extract_url_from_jpeg(final_compressed_path)

        except Exception as e:
            print(f"❌ Error in download_and_compress: {e}")

# =========🔧 Run =========
if __name__ == "__main__":
    download_and_compress()
