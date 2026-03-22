import os
from urllib import parse
import requests
from datetime import datetime

# 1. 환경 변수 설정 (GitHub Secrets에서 가져옴)
NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
DATABASE_ID = os.environ.get('NOTION_DATABASE_ID')

HEADER = """# 📚 백준 & 프로그래머스 문제 풀이 목록\n"""

def add_to_notion(problem_title, problem_link, tier=""):
    """노션 데이터베이스에 행을 추가하는 함수"""
    if not NOTION_TOKEN or not DATABASE_ID:
        print("노션 설정이 되어 있지 않습니다.")
        return

    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # 노션 데이터베이스 속성 이름에 맞춰 구성 (사용자님의 표 속성 이름 기준)
    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "문제 번호": {"title": [{"text": {"content": problem_title}}]},
            "문제 링크": {"url": f"https://www.acmicpc.net/problem/{problem_title.split('.')[0]}" if "백준" in problem_link else ""},
            "티어": {"rich_text": [{"text": {"content": tier}}]}
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        print(f"✅ 노션 업데이트 성공: {problem_title}")
    else:
        print(f"❌ 노션 업데이트 실패: {response.status_code}, {response.text}")

def main():
    content = HEADER
    directories = []
    solveds = []

    for root, dirs, files in os.walk("."):
        dirs.sort()
        if root == '.' or '.git' in root or '.github' in root:
            continue

        category = os.path.basename(root)
        if category == 'images': continue
        
        directory = os.path.basename(os.path.dirname(root))
        if directory == '.': continue
            
        if directory not in directories:
            content += f"\n## {directory}\n| 문제번호 | 링크 |\n| ----- | ----- |\n"
            directories.append(directory)

        for file in files:
            if category not in solveds:
                file_path = parse.quote(os.path.join(root, file))
                content += f"|{category}|[링크]({file_path})|\n"
                solveds.append(category)
                
                # ✨ 핵심: 노션으로 전송하는 함수 실행!
                add_to_notion(category, file_path, tier=directory)

    with open("README.md", "w", encoding="utf-8") as fd:
        fd.write(content)
        
if __name__ == "__main__":
    main()
