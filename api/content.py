import os
import json
import requests

from api.base import BaseApi


class Content(BaseApi):
    def __init__(self):
        super().__init__()
        self.url = f"{self.domain}/wiki/rest/api/content"

    def create_or_update(self, page_id, image_path):
        url = f"{self.url}/{page_id}/child/attachment"
        headers = {
            "Accept": "application/json",
            "X-Atlassian-Token": "no-check"
        }

        files = {
            'file': (os.path.basename(image_path), open(image_path, 'rb'), 'image/png')
        }

        response = requests.put(url, headers=headers, auth=self.auth, files=files)

        if response.status_code == 200 or response.status_code == 201:
            print("File uploaded successfully.")
            return response.json()
        else:
            print("Failed to upload file.")
            print(response.text)
            return None

    def update(self, page_id, new_html):
        import json
        import requests

        # 1. 현재 페이지 정보 조회
        get_url = f"{self.url}/{page_id}?expand=body.storage,version,title"
        response = requests.get(get_url, auth=self.auth)

        if response.status_code != 200:
            print(f"[❌] Failed to retrieve page content: {response.status_code}")
            print(response.text)
            return None

        data = response.json()
        version = data["version"]["number"] + 1
        title = data["title"]

        print(f"[📄] Updating page: {title} (id: {page_id}, version: {version})")

        # 2. HTML 본문 업데이트 payload
        payload = {
            "id": page_id,
            "type": "page",
            "title": title,
            "version": { "number": version },
            "body": {
                "storage": {
                    "value": new_html,
                    "representation": "storage"  # 기본은 storage (Confluence source HTML)
                }
            }
        }

        put_url = f"{self.url}/{page_id}"
        headers = { "Content-Type": "application/json" }

        put_response = requests.put(put_url, headers=headers, auth=self.auth, data=json.dumps(payload))

        if put_response.status_code == 200:
            print(f"[✅] Successfully updated page {page_id}")
        else:
            print(f"[❌] Failed to update page {page_id}: {put_response.status_code}")
            print(put_response.text)

        return put_response.json() if put_response.status_code == 200 else None