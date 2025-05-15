from api.space import Space
from api.page import Page
from api.folder import Folder
from utils import collect_page_links, update_main_page_links_only


def main():
    space_api = Space()
    page_api = Page()
    folder_api = Folder()

    space_name = "데이터프로덕트그룹"
    # 빈 폴더를 찾을수 없어 수동으로 파일 생성 후 parent_id를 찾는 형식으로 진행
    target_page_for_folder = "api 테스트-1"
    # 파일을 올릴 폴더 생성
    new_folder_title = "데이터엔지니어링 그룹 노션 문서(from Notion)"
    html_path = "./docs"  # 최상위 폴더 지정

    my_space = space_api.get_by_title(space_name)
    space_id = my_space["id"]

    folder_id = page_api.get_folder_by_page_name(space_id=space_id, page_name=target_page_for_folder)
    # print(folder_id)
    # folder_id = "3201892850"
    new_folder = folder_api.create_folder(space_id=space_id, title=new_folder_title, parent_id=folder_id)
    # print(new_folder)
    created_folder_id = new_folder["id"]
    # created_folder_id = "3204882148"

    title_to_page_id_map = {}
    notion_id_to_confluence_url = {}
    base_confluence_url = "https://socarcorp.atlassian.net/wiki"

    # 1단계: 모든 Notion HTML → Confluence로 업로드 + 링크 매핑
    collect_page_links(
        base_folder="docs/zip_test/개인 페이지 & 공유된 페이지",
        _space_id=space_id,
        parent_page_id=created_folder_id,
        file_name_postfix="(from Notion)",
        title_to_page_id_map=title_to_page_id_map,
        notion_id_to_confluence_url=notion_id_to_confluence_url,
        base_confluence_url=base_confluence_url
    )

    # 2단계: 메인 페이지 본문에 포함된 notion 링크 → confluence 링크로 업데이트
    update_main_page_links_only(
        html_path="docs/zip_test/개인 페이지 & 공유된 페이지/유저 활용 동적 재배치 14d599ae9e4180278bf6da1ae21e4ad0.html",
        page_id=title_to_page_id_map["유저 활용 동적 재배치 14d599ae9e4180278bf6da1ae21e4ad0.html"],
        title_to_page_id_map=title_to_page_id_map,
        notion_id_to_confluence_url=notion_id_to_confluence_url,
        base_confluence_url=base_confluence_url
    )


if __name__ == "__main__":
    main()