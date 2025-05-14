import json
import requests

from api.base import BaseApi


class Page(BaseApi):
    def __init__(self):
        super().__init__()
        self.url = f"{self.domain}/wiki/api/v2/pages"

    def get(self, url=None, all_pages=None, params=None):
        if all_pages is None:
            all_pages = []
        if url is None:
            url = self.url

        response = requests.get(url, headers=self.default_header, auth=self.auth, params=params)

        if response.status_code == 200:
            data = response.json()
            all_pages.extend(data.get("results", []))

            next_link = data.get("_links", {}).get("next")
            if next_link:
                next_url = self.domain + next_link
                return self.get(url=next_url, all_pages=all_pages, params=params)
            else:
                return all_pages

        else:
            print(f"Error: {response.status_code}, {response}")
            return all_pages

    def get_folder_by_page_name(self, space_id, page_name):
        _params = {
            "space-id": space_id,
            "title": page_name
        }
        pages = self.get(params=_params)
        if pages:
            return pages[0]["parentId"]
        return None

    def create(self, space_id, title, parent_id, html_content):
        while True:
            existing_titles = self.get(params={"space-id": space_id, "title": title})
            if existing_titles:
                title += " - New"
            else:
                break

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        body = {
            "representation": "storage",  # HTML 형식으로 저장
            "value": html_content  # HTML 콘텐츠
        }
        payload = json.dumps({
            "spaceId": space_id,
            "title": title,
            "parentId": parent_id,
            "body": body
        })

        response = requests.post(self.url, headers=headers, auth=self.auth, data=payload)

        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"Error: {response.status_code}, {response.text}")