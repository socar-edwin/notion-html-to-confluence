import os
import re
import glob
import requests
import unicodedata
from urllib.parse import unquote
from bs4 import BeautifulSoup

from api.page import Page
from api.content import Content

page_api = Page()
content_api = Content()

def resolve_image_path(html_folder, image_src):
    decoded_src = unquote(image_src)
    normalized_src = unicodedata.normalize('NFC', decoded_src)
    result_path = os.path.join(html_folder, normalized_src)

    if os.path.exists(result_path):
        return result_path

    print(f"이미지 파일을 찾을 수 없습니다: {decoded_src}")
    return None


def replace_all_image_links_in_html(html_content, html_folder, page_id):
    soup = BeautifulSoup(html_content, "html.parser")
    image_map = {}
    default_width = 800
    default_height = "auto"
    # 1. 커버 이미지 제거 (class="page-cover-image")
    for img in soup.find_all("img", class_="page-cover-image"):
        img.decompose()

    # 2. 제목 앞의 이모지 제거 (class="page-header-icon page-header-icon-with-cover")
    for icon in soup.find_all(class_="page-header-icon page-header-icon-with-cover"):
        icon.decompose()

    # 3. 코드 블록 변환
    for code_block in soup.find_all(["pre", "code"]):
        if "class" in code_block.attrs:
            language = "plain"
            for class_name in code_block["class"]:
                if class_name.startswith("language-"):
                    language = class_name.replace("language-", "")
                    break
            code_text = code_block.get_text()
            # Confluence 코드 블록 매크로로 변환
            confluence_code_block = f"""
            <ac:structured-macro ac:name="code">
                <ac:parameter ac:name="language">{language}</ac:parameter>
                <ac:parameter ac:name="theme">Confluence</ac:parameter>
                <ac:parameter ac:name="linenumbers">true</ac:parameter>
                <ac:plain-text-body><![CDATA[
{code_text}
                ]]></ac:plain-text-body>
            </ac:structured-macro>
            """

            # 기존 코드 블록을 코드 블록 매크로로 치환
            code_block.replace_with(BeautifulSoup(confluence_code_block, "html.parser"))

    # 4. 이미지 링크 치환
    for img in soup.find_all("img"):
        image_src = img.get("src")
        resolved_path = resolve_image_path(html_folder, image_src)
        if resolved_path and resolved_path not in image_map:
            uploaded_response = content_api.create_or_update(page_id, resolved_path)
            if uploaded_response:
                download_url = uploaded_response['results'][0]['_links']['download']
                base_url = uploaded_response['_links']['base']
                full_image_url = base_url + download_url

                img['src'] = full_image_url
                img['data-image-src'] = full_image_url
                img['loading'] = 'lazy'
                img['width'] = str(default_width)
                img['height'] = default_height
                img['style'] = f"width: {default_width}px; height: auto;"

                image_map[resolved_path] = full_image_url
                # print(f"이미지 링크 치환: {image_src} -> {full_image_url}")

    return str(soup)


def process_html_and_images(base_folder, _space_id, parent_page_id, file_name_postfix=""):
    # for _html_path in glob.glob(os.path.join(base_folder, "*.html")):
    for h in os.listdir(base_folder):
        if not h.endswith(".html"):
            continue
        _html_path = os.path.join(base_folder, h)
        parent_id = parent_page_id
        with open(_html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        html_folder = _html_path.replace(".html", "")
        html_content = replace_all_image_links_in_html(html_content, base_folder, parent_id)
        page_title = os.path.basename(_html_path).replace(".html", "")
        page_title = re.sub(r"\s*\b[a-fA-F0-9]{32}\b", "", page_title)

        try:
            print(f"Creating Page: {page_title}")
            page_title = page_title + file_name_postfix
            page_response = page_api.create(_space_id, page_title, parent_id, html_content)
            if page_response:
                print(f"Created Page: {page_title}")
                parent_id = page_response.get('id')
            else:
                print(f"Failed to create page for {page_title}.")
        except Exception as e:
            print(f"Failed to create page for {page_title}.\nError: {str(e)}")
            raise
        print(f"Processing subfolder: {html_folder}")
        if os.path.exists(html_folder) and os.path.isdir(html_folder):
            print(f"Processing now subfolder: {html_folder}")
            process_html_and_images(html_folder, _space_id, parent_id,  file_name_postfix)


def collect_page_links(base_folder,
                       _space_id,
                       parent_page_id,
                       file_name_postfix="",
                       title_to_page_id_map=None,
                       notion_id_to_confluence_url=None,
                       base_confluence_url=None,
                       root_folder=None):
    if root_folder is None:
        root_folder = base_folder

    for entry in os.listdir(base_folder):
        if not entry.endswith(".html"):
            continue

        html_path = os.path.join(base_folder, entry)
        html_dir = html_path.replace(".html", "")
        parent_id = parent_page_id

        with open(html_path, "r", encoding="utf-8") as f:
            html_src = f.read()

        rel_path = os.path.relpath(html_path, start=root_folder)
        key = unicodedata.normalize("NFC", unquote(rel_path)).replace(os.sep, "/")

        raw_title = os.path.splitext(os.path.basename(entry))[0]
        page_title = re.sub(r"\s*\b[a-fA-F0-9]{32}\b", "", raw_title).strip()
        page_title += file_name_postfix

        print(f"Creating Page: {page_title}")
        resp = page_api.create(_space_id, page_title, parent_id, html_src)
        if not resp:
            print(f"Failed to create page for {page_title}")
            continue

        new_id = resp["id"]
        if title_to_page_id_map is not None:
            title_to_page_id_map[key] = new_id

        notion_id = extract_notion_id_from_filename(entry)
        if notion_id and notion_id_to_confluence_url is not None:
            webui = resp['_links']['webui']
            full_url = f"{base_confluence_url}{webui}"
            notion_id_to_confluence_url[notion_id] = full_url

        parent_id = new_id

        if os.path.isdir(html_dir):
            collect_page_links(
                html_dir,
                _space_id,
                parent_id,
                file_name_postfix,
                title_to_page_id_map,
                notion_id_to_confluence_url,
                base_confluence_url,
                root_folder
            )


def update_main_page_links_only(
    html_path: str,
    page_id: str,
    title_to_page_id_map: dict,
    notion_id_to_confluence_url: dict,
    base_confluence_url: str
):
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    updated_html = replace_all_image_links_in_html(
        html_content,
        html_folder=os.path.dirname(html_path),
        page_id=page_id,
        title_to_page_id_map=title_to_page_id_map,
        base_confluence_url=base_confluence_url,
        notion_id_to_confluence_url=notion_id_to_confluence_url
    )

    from api.content import Content
    content_api = Content()

    # 기존 페이지 내용 가져오기
    get_url = f"{content_api.url}/{page_id}?expand=body.storage,version,title"
    resp = requests.get(get_url, auth=content_api.auth)
    if resp.status_code != 200:
        print(f"❌ Failed to retrieve page content: {resp.status_code}")
        return

    data = resp.json()
    current_html = data["body"]["storage"]["value"]

    # 변경이 있는 경우에만 업데이트
    if updated_html.strip() != current_html.strip():
        content_api.update(page_id, updated_html)
        print("✅ 메인 페이지 본문 업데이트 완료")
    else:
        print("⚠️ 메인 페이지 내용 동일, 업데이트 생략")