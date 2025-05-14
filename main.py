from api.space import Space
from api.page import Page
from api.folder import Folder
from utils import process_html_and_images


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
    process_html_and_images(html_path, space_id, created_folder_id, file_name_postfix="(from Notion)")



if __name__ == "__main__":
    main()