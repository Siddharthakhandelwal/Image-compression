
import dropbox
import os
import base64
import requests

ACCESS_TOKEN ="sl.u.AFoFV5KFkADbq39PdbhBUTmgB9SbvX6Qz5EwkxjBkkXPZgzr2OGoX_poTe5tfP18FVDYwWQqLVbhRFRERNjC_Ldl3hys-SRB2V4eZMUs_WzfDs3RnMGsFXOMXXd-DA-m3F4oGrqF77stzZSiKQ10NwpZoFZbZHhE99R0D2h_SJwwO5X5PGrFJYMZAitWnxRJcKCoIjU0rtwrdQIrGdn6KF_lPo2C_TG7gvbItfwXDTPfJso7iWymeAZkgxsYf4TGhW1xAEMlgstqysx-Z-H27v60_sk00ELJPCDEIHeidCkWQnw1wWFk4D0cNCYftulVMH0ytoWc4Plvwlr3a52fEKtvI8n9f62HCq_sTCG_bECCdXJI0hhGQuVahfGekqSPVLo5FifG9BCjjss2W0dlYdgLHMIH2KpIRqZSUy0HKgDEuyqD-GgNBrTIeKEuNH0TTklGoNEAmlU5isi0i3rQpLD7zOorXXU80hUbjA3ou8caX7dEDdQo-1labwX5T-P-Lz8ExGgxb4p2pHVWU7eDE43N-vAmB2rVxibFvSxJLGFKfeBZAkUh9Rr-1p7AXprWaDc6egDxl_wInPL7pp8xdEEGINDmv0pkR7Il_r4iCwjm_E1tH2zTY__-Xoh1Hqram26_VsfOcbOTFl6aTriB22rSyN3NSvnBIolIwFKcQ28RCRaGDN6pdwjrwYWGX7zenx8elX8Sr3lynQnun-44y9d1tn3EM3hsrCTn-qtwMBfAh_eEld6yOJJcIGG3sgxd5wAUjDzkFoq08hxbIt_jpEnGOQfxxpKyHZrN_ZMAanc8FRGIkSlfsRVgMJCYwsdrB6AW5_Qo97c8le_BRcbIns7ZZvtVvXriSgZw1Y8A00k5d-C-4bAFFBrWil3BnZuhNej0ksb_XvdIE1fSpcyoBEusdX9MmONEXEsYptk7hvHMqiew_NRfgrDw0FNKEVCHWVzZnKqjlJdoM1K_o2MgHzr3K6B3rN4WqhfoOanVDPzTuecHr2_9kXXdwr8-C2iELOcaVIXQWh4tTnDcJdMrhbgZ1mncukSxGeg-zOIWlwI88VCRUiGC08ASaCIzeRKUYRezVjhwtKRoIdIrY0DO2ll7ei1Y6kXNH_OmN4Fjumz0A9A6GOwQwpHjOHvPCbtnizhOY44mP-Bv8oiNEd5ODcFU3YJE3JYhTKbvPrk_kzPyPDV5CbG0rVEMwMNBssUhC-V1ot7ORfMtY4J61noXyP3AMyizHFqcgl0eRSqjv6By7ky6DHGxh_GXgUwdoWBOsEjMSRCQQ7Onj7PEWLJkwBZ8oPAF3fiFsNm64XLk-p1cQIL36ZoZ5opmCcNeBkgyS9XAjvnFUwPV13M9YptRd6A6VCKrRsRuSLxZs-Au_Zc0fGFyIC1hu6JkCVlusKaV4vh9TAofGcsEWsOGfnTQgOop"
DROPBOX_FOLDER_PATH = ""
LOCAL_DOWNLOAD_DIR = "downloaded_images"
COMPRESSED_DIR = "compressed_images"
API_ENDPOINT = "http://localhost:8000/compress/"

def get_shared_link(dbx, dropbox_path):
    # Get or create a public shared link
    try:
        links = dbx.sharing_list_shared_links(path=dropbox_path, direct_only=True).links
        if links:
            return links[0].url.replace("?dl=0", "?raw=1")  # make it direct
        else:
            shared_link = dbx.sharing_create_shared_link_with_settings(dropbox_path)
            return shared_link.url.replace("?dl=0", "?raw=1")
    except Exception as e:
        print(f"Failed to get shared link: {e}")
        return None

def download_and_compress_images(num_files):
    dbx = dropbox.Dropbox(ACCESS_TOKEN)

    os.makedirs(LOCAL_DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(COMPRESSED_DIR, exist_ok=True)

    result = dbx.files_list_folder(DROPBOX_FOLDER_PATH)
    entries = result.entries[:num_files]

    for idx, entry in enumerate(entries):
        if isinstance(entry, dropbox.files.FileMetadata):
            file_name = entry.name
            local_path = os.path.join(LOCAL_DOWNLOAD_DIR, file_name)
            dropbox_path = entry.path_lower

            # Get public Dropbox URL
            dropbox_url = get_shared_link(dbx, dropbox_path)
            if not dropbox_url:
                continue

            # Download the file
            with open(local_path, "wb") as f:
                metadata, res = dbx.files_download(dropbox_path)
                f.write(res.content)
            print(f"\n🔹 Downloaded ({idx+1}/{num_files}): {file_name}")

            original_size = os.path.getsize(local_path)

            # Prepare payload
            ext = os.path.splitext(file_name)[1].lower().replace('.', '')
            with open(local_path, "rb") as f:
                image_base64 = base64.b64encode(f.read()).decode("utf-8")

            payload = {
                "image_base64": image_base64,
                "text_data": dropbox_url,
                "format": ext if ext in ["jpg", "jpeg", "png", "webp", "tiff", "tif"] else "jpeg",
                "quality": 50
            }

            # Call compression API
            response = requests.post(API_ENDPOINT, json=payload)
            if response.status_code == 200:
                compressed_path = os.path.join(COMPRESSED_DIR, file_name)
                with open(compressed_path, "wb") as out:
                    out.write(response.content)

                compressed_size = os.path.getsize(compressed_path)
                ratio = round((compressed_size / original_size) * 100, 2)

                print(f"✅ Compressed and saved: {compressed_path}")
                print(f"📏 Original Size: {original_size / 1024:.2f} KB")
                print(f"📉 Compressed Size: {compressed_size / 1024:.2f} KB")
                print(f"📊 Compression Ratio: {ratio}%")
                print(f"📝 Embedded Metadata (Dropbox URL): {dropbox_url}")
            else:
                print(f"❌ Failed to compress {file_name}: {response.status_code} - {response.text}")

    if len(entries) < num_files:
        print(f"⚠️ Only {len(entries)} file(s) found in Dropbox folder.")

if __name__ == "__main__":
    try:
        n = int(input("Enter the number of images to download and compress: "))
        if n <= 0:
            raise ValueError("Number must be positive.")
        download_and_compress_images(n)
    except ValueError as ve:
        print("❌ Invalid input:", ve)
