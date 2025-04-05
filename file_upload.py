import requests

def upload_to_gofile(zip_path, token, folder_id=None):
    upload_url = f"https://upload.gofile.io/uploadFile"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    files = {
        "file": open(zip_path, "rb")
    }
    data = {}
    if folder_id:
        data["folderId"] = folder_id
    resp = requests.post(upload_url, headers=headers, files=files, data=data).json()
    if resp["status"] == "ok":
        file_info = resp["data"]
        return {
            "downloadPage": file_info["downloadPage"],
            "fileId": file_info["id"],
            "fileName": file_info["name"],
            "folderId": file_info["parentFolder"],
        }
    else:
        raise Exception("Upload failed", resp)