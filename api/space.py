import requests

from api.base import BaseApi

class Space(BaseApi):
    def __init__(self):
        super().__init__()
        self.url = f"{self.domain}/wiki/api/v2/spaces"

    def get(self, url=None, all_spaces=None, _id=None):
        if all_spaces is None:
            all_spaces = []

        if url is None:
            url = self.url

        if _id is not None:
            url = f"{url}/{_id}"

        response = requests.get(url, headers=self.default_header, auth=self.auth)

        if response.status_code == 200:
            data = response.json()
            if _id is None:
                all_spaces.extend(data.get("results", []))
            else:
                all_spaces.append(data)

            next_link = data.get("_links", {}).get("next")
            if next_link:
                next_url = self.domain + next_link
                return self.get(url=next_url, all_spaces=all_spaces)
            else:
                return all_spaces

        else:
            print(f"Error: {response.status_code}, {response}")
            return all_spaces

    def get_by_title(self, title):
        spaces = self.get()
        for space in spaces:
            if space.get("name") == title:
                return space
        return None

    def get_pages(self, space_id, url=None, all_pages=None, params=None):
        if all_pages is None:
            all_pages = []
        if url is None:
            url = f"{self.url}/{space_id}/pages"
        response = requests.get(url, headers=self.default_header, auth=self.auth, params=params)

        if response.status_code == 200:
            data = response.json()
            all_pages.extend(data.get("results", []))

            next_link = data.get("_links", {}).get("next")
            if next_link:
                next_url = self.domain + next_link
                return self.get_pages(space_id, url = next_url, all_pages=all_pages, params=params)
            else:
                return all_pages

        else:
            print(f"Error: {response.status_code}, {response}")
            return all_pages



