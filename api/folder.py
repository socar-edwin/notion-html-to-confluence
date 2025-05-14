import json
import requests

from api.base import BaseApi


class Folder(BaseApi):
    def __init__(self):
        super().__init__()
        self.url = f"{self.domain}/wiki/api/v2/folders"

    def get(self, _id=None):
        if _id is not None:
            url = f"{self.url}/{_id}"
        else:
            raise ValueError("ID is required to get a folder")

        response = requests.get(url, headers=self.default_header, auth=self.auth)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")

    def create_folder(self, space_id, title, parent_id):
        payload = {
            "spaceId": space_id,
            "title": title,
            "parentId": parent_id
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        response = requests.post(self.url, headers=headers, auth=self.auth, data=json.dumps(payload))

        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"Error: {response.status_code}")