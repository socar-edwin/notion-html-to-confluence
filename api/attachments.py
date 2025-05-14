import requests

from api.base import BaseApi


class Attachments(BaseApi):
    def __init__(self):
        super().__init__()
        self.url = f"{self.domain}/wiki/api/v2/attachments"

    def get(self, url=None, all_attachments=None, params=None):
        if all_attachments is None:
            all_attachments = []
        if url is None:
            url = self.url

        response = requests.get(url, headers=self.default_header, auth=self.auth, params=params)

        if response.status_code == 200:
            data = response.json()
            all_attachments.extend(data.get("results", []))

            next_link = data.get("_links", {}).get("next")
            if next_link:
                next_url = self.domain + next_link
                return self.get(url=next_url, all_attachments=all_attachments, params=params)
            else:
                return all_attachments

        else:
            print(f"Error: {response.status_code}, {response}")
            return all_attachments