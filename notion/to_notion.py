import os
import requests
import json
from bs4 import BeautifulSoup
import markdown2

# Constants
NOTION_API_KEY = os.environ['NOTION_API_KEY']
NOTION_DATABASE_ID = os.environ['NOTION_DATABASE_ID']

# 스크립트 위치 기준 절대경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def roman_to_number(roman):
    rdict = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    nv = roman[0]
    number = rdict[nv]
    for i in range(1, len(roman)):
        bv = nv
        nv = roman[i]
        if rdict[bv] >= rdict[nv]:
            number += rdict[nv]
        else:
            number += rdict[nv] - 2 * rdict[bv]
    return number


def get_icon_url(teir, grade):
    TIER_DICT = {'Bronze': 0, 'Silver': 1, 'Gold': 2,
                 'Platinum': 3, 'Diamond': 4, 'Ruby': 5}
    teir_score = TIER_DICT[teir] * 5 - roman_to_number(grade) + 6
    return f'https://static.solved.ac/tier_small/{teir_score}.svg'


def parse_problem_details(markdown_file, answer_file):
    with open(markdown_file, 'r', encoding='utf8') as f:
        markdown_text = f.read()
        html = markdown2.markdown(markdown_text)

    with open(answer_file, 'r', encoding='utf8') as f:
        answer = f.read()

    soup = BeautifulSoup(html, 'html.parser')
    teir, title = soup.find('h1').get_text().replace('[', '').split(']')
    teir, grade = teir.split()
    link = soup.find('a').attrs['href']
    icon = get_icon_url(teir, grade)

    p = soup.find_all('p', limit=3)
    memory, time = map(lambda x: x.split(': ')[1], p[1].get_text().replace('[', '').split(', '))
    category = [{"name": c} for c in p[2].get_text().split(', ')]

    LANGUAGE_DICT = {'py': 'python', 'java': 'java'}
    language = LANGUAGE_DICT[os.path.splitext(answer_file)[1][1:]]

    return {
        'title': title,
        'link': link,
        'icon': icon,
        'teir': teir,
        'grade': grade,
        'category': category,
        'memory': memory,
        'time': time,
        'language': language,
        'answer': answer
    }


def create_database_page(data):
    template_path = os.path.join(BASE_DIR, 'notion', 'template.json')
    with open(template_path, 'r', encoding='UTF-8') as json_file:
        json_data = json.load(json_file)

    json_data['parent']['database_id'] = NOTION_DATABASE_ID
    json_data['properties']['Title']['title'] = [{'text': {'content': data['title']}}]
    json_data['properties']['URL']['url'] = data['link']
    json_data['properties']['Tier']['select']['name'] = data['teir']
    json_data['properties']['Grade']['select']['name'] = data['grade']
    json_data['properties']['Category']['multi_select'] = data['category']
    json_data['icon']['external']['url'] = data['icon']

    for i in range(0, len(data['answer']), 2000):
        json_data['children'][3]['code']['rich_text'].append({
            'type': 'text',
            'text': {'content': data['answer'][i:i+2000]}
        })
    json_data['children'][3]['code']['language'] = data['language']

    json_data['children'][1]["table"]['children'][1]['table_row']['cells'][0][0]['text']['content'] = data['memory']
    json_data['children'][1]["table"]['children'][1]['table_row']['cells'][1][0]['text']['content'] = data['time']
    return json_data


def read_problems_file():
    problems_path = os.path.join(BASE_DIR, 'notion', 'problems.json')
    with open(problems_path, 'r', encoding="UTF-8") as problems_file:
        problems = json.load(problems_file)
        solved = problems['problems']
    return solved, problems


def write_problems_file(problems):
    problems_path = os.path.join(BASE_DIR, 'notion', 'problems.json')
    with open(problems_path, 'w', encoding="UTF-8") as f:
        f.write(json.dumps(problems, ensure_ascii=False))


def create_pages():
    headers = {
        "Authorization": "Bearer " + NOTION_API_KEY,
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    solved, problems = read_problems_file()
    print(f"[DEBUG] BASE_DIR: {BASE_DIR}")
    print(f"[DEBUG] solved 목록: {solved}")

    baekjoon_path = os.path.join(BASE_DIR, "백준")
    print(f"[DEBUG] 탐색 경로: {baekjoon_path}")

    for (root, directories, files) in os.walk(baekjoon_path):
        print(f"[DEBUG] root={root}, dirs={directories}")
        for d in directories:
            d_path = os.path.join(root, d)
            if d_path not in solved:
                readme, answer = "", ""
                for i in os.listdir(d_path):
                    if i.endswith('.md'):
                        readme = os.path.join(d_path, i)
                    elif i.endswith('.py') or i.endswith('.java'):
                        answer = os.path.join(d_path, i)

                if not readme or not answer:
                    print(f"[DEBUG] 스킵 (readme/answer 없음): {d_path}")
                    print(f"[DEBUG] 폴더 내 파일 목록: {os.listdir(d_path)}")  # 이 줄 추가
                    continue        

                print(f"[DEBUG] 처리 중: {d_path}")
                data = parse_problem_details(readme, answer)
                json_data = json.dumps(create_database_page(data))

                url = "https://api.notion.com/v1/pages"
                response = requests.post(url=url, headers=headers, data=json_data)
                print(f"[DEBUG] 응답 코드: {response.status_code}")

                if response.status_code != 200:
                    print(f"ERROR: {response.text}")
                    break

                solved.append(d_path)
                problems['problems'] = solved
                write_problems_file(problems)
                print(f"[DEBUG] 완료: {data['title']}")


create_pages()
