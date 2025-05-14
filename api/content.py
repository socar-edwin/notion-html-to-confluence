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