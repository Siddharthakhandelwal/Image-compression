import os
import io
import dropbox
from PIL import Image, TiffImagePlugin
from rawpy import imread as raw_imread
from datetime import datetime
from PIL.PngImagePlugin import PngInfo

DROPBOX_ACCESS_TOKEN = "sl.u.AFoFV5KFkADbq39PdbhBUTmgB9SbvX6Qz5EwkxjBkkXPZgzr2OGoX_poTe5tfP18FVDYwWQqLVbhRFRERNjC_Ldl3hys-SRB2V4eZMUs_WzfDs3RnMGsFXOMXXd-DA-m3F4oGrqF77stzZSiKQ10NwpZoFZbZHhE99R0D2h_SJwwO5X5PGrFJYMZAitWnxRJcKCoIjU0rtwrdQIrGdn6KF_lPo2C_TG7gvbItfwXDTPfJso7iWymeAZkgxsYf4TGhW1xAEMlgstqysx-Z-H27v60_sk00ELJPCDEIHeidCkWQnw1wWFk4D0cNCYftulVMH0ytoWc4Plvwlr3a52fEKtvI8n9f62HCq_sTCG_bECCdXJI0hhGQuVahfGekqSPVLo5FifG9BCjjss2W0dlYdgLHMIH2KpIRqZSUy0HKgDEuyqD-GgNBrTIeKEuNH0TTklGoNEAmlU5isi0i3rQpLD7zOorXXU80hUbjA3ou8caX7dEDdQo-1labwX5T-P-Lz8ExGgxb4p2pHVWU7eDE43N-vAmB2rVxibFvSxJLGFKfeBZAkUh9Rr-1p7AXprWaDc6egDxl_wInPL7pp8xdEEGINDmv0pkR7Il_r4iCwjm_E1tH2zTY__-Xoh1Hqram26_VsfOcbOTFl6aTriB22rSyN3NSvnBIolIwFKcQ28RCRaGDN6pdwjrwYWGX7zenx8elX8Sr3lynQnun-44y9d1tn3EM3hsrCTn-qtwMBfAh_eEld6yOJJcIGG3sgxd5wAUjDzkFoq08hxbIt_jpEnGOQfxxpKyHZrN_ZMAanc8FRGIkSlfsRVgMJCYwsdrB6AW5_Qo97c8le_BRcbIns7ZZvtVvXriSgZw1Y8A00k5d-C-4bAFFBrWil3BnZuhNej0ksb_XvdIE1fSpcyoBEusdX9MmONEXEsYptk7hvHMqiew_NRfgrDw0FNKEVCHWVzZnKqjlJdoM1K_o2MgHzr3K6B3rN4WqhfoOanVDPzTuecHr2_9kXXdwr8-C2iELOcaVIXQWh4tTnDcJdMrhbgZ1mncukSxGeg-zOIWlwI88VCRUiGC08ASaCIzeRKUYRezVjhwtKRoIdIrY0DO2ll7ei1Y6kXNH_OmN4Fjumz0A9A6GOwQwpHjOHvPCbtnizhOY44mP-Bv8oiNEd5ODcFU3YJE3JYhTKbvPrk_kzPyPDV5CbG0rVEMwMNBssUhC-V1ot7ORfMtY4J61noXyP3AMyizHFqcgl0eRSqjv6By7ky6DHGxh_GXgUwdoWBOsEjMSRCQQ7Onj7PEWLJkwBZ8oPAF3fiFsNm64XLk-p1cQIL36ZoZ5opmCcNeBkgyS9XAjvnFUwPV13M9YptRd6A6VCKrRsRuSLxZs-Au_Zc0fGFyIC1hu6JkCVlusKaV4vh9TAofGcsEWsOGfnTQgOop"
DROPBOX_FOLDER = ''  # Change this to your folder path
LOCAL_DOWNLOAD_FOLDER = 'downloads'
LOCAL_COMPRESSED_FOLDER = 'compressed_images'

SUPPORTED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.tiff', '.tif', '.raw', '.nef', '.cr2', '.arw', '.dng')

os.makedirs(LOCAL_DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(LOCAL_COMPRESSED_FOLDER, exist_ok=True)

dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def get_latest_files(folder_path):
    entries = dbx.files_list_folder(folder_path).entries
    files = [f for f in entries if isinstance(f, dropbox.files.FileMetadata) and f.name.lower().endswith(SUPPORTED_EXTENSIONS)]
    files.sort(key=lambda f: f.server_modified, reverse=True)
    return files[:5]  # Change if you want more

def get_shared_link(path):
    try:
        metadata = dbx.sharing_create_shared_link_with_settings(path)
        return metadata.url.replace('?dl=0', '?raw=1')
    except dropbox.exceptions.ApiError as e:
        if e.error.is_shared_link_already_exists():
            links = dbx.sharing_list_shared_links(path=path, direct_only=True).links
            if links:
                return links[0].url.replace('?dl=0', '?raw=1')
        raise e

def compress_image(file_path, output_path, metadata_url):
    ext = os.path.splitext(file_path)[1].lower()
    original_size = os.path.getsize(file_path)

    if ext in ['.raw', '.nef', '.cr2', '.arw', '.dng']:
        with open(file_path, 'rb') as f:
            raw = raw_imread(f)
            img = Image.fromarray(raw.postprocess())
    else:
        img = Image.open(file_path)

    # Prepare metadata
    meta = PngInfo()
    meta.add_text("Source URL", metadata_url)

    if ext in ['.tiff', '.tif']:
        # Embed metadata for TIFF
        tiff_info = TiffImagePlugin.ImageFileDirectory_v2()
        tiff_info[270] = f"Source URL: {metadata_url}"  # Tag 270 is ImageDescription
        img.save(output_path, format='TIFF', tiffinfo=tiff_info)
    elif ext in ['.png']:
        img.save(output_path, format='PNG', optimize=True, pnginfo=meta)
    elif ext in ['.jpg', '.jpeg', '.webp']:
        img.save(output_path, format=img.format, quality=85, optimize=True)
    else:
        # Save RAW as TIFF with metadata
        output_path = output_path.replace(ext, ".tiff")
        tiff_info = TiffImagePlugin.ImageFileDirectory_v2()
        tiff_info[270] = f"Source URL: {metadata_url}"
        img.save(output_path, format='TIFF', tiffinfo=tiff_info)

    compressed_size = os.path.getsize(output_path)
    ratio = round(compressed_size / original_size, 3)

    print(f"\n🖼️  File: {os.path.basename(file_path)}")
    print(f"📦 Original Size: {original_size} bytes")
    print(f"🗜️  Compressed Size: {compressed_size} bytes")
    print(f"📉 Compression Ratio: {ratio}")
    print(f"🔗 Embedded URL: {metadata_url}\n")

def download_and_compress():
    files = get_latest_files(DROPBOX_FOLDER)
    if not files:
        print("No supported image files found.")
        return

    for file in files:
        dropbox_path = file.path_lower
        local_path = os.path.join(LOCAL_DOWNLOAD_FOLDER, file.name)
        compressed_path = os.path.join(LOCAL_COMPRESSED_FOLDER, file.name)

        with open(local_path, "wb") as f:
            metadata, res = dbx.files_download(path=dropbox_path)
            f.write(res.content)

        url = get_shared_link(dropbox_path)
        compress_image(local_path, compressed_path, url)

if __name__ == "__main__":
    download_and_compress()
