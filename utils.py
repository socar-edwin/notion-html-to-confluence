import os
import re
import glob
from urllib.parse import unquote
from bs4 import BeautifulSoup

from api.page import Page
from api.content import Content

page_api = Page()
content_api = Content()

def resolve_image_path(html_folder, image_src):
    decoded_src = unquote(image_src)
    result_path = os.path.join(html_folder, decoded_src)
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
