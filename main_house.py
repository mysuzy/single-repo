import requests
from bs4 import BeautifulSoup
from airtable import insert_line, connect_to_table, fetch_all
from pyairtable.utils import attachment
from datetime import datetime
from dateutil.parser import parse as date_parse

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
API_KEY = "keyECvHHQ7YECHBy7"
TOKEN = "patqmwV7hrU86hqYI.27fd1e12ce830b4306ac7bf5658fcb1929804783df1d4c3a0b579110e22a6b78"
DEFAULT_HOUSE_IMAGE = "https://img.freepik.com/free-photo/3d-model-residential-building_23-2150761232.jpg?t=st=1694059079~exp=1694062679~hmac=9e76115d813fa2be0d2c21e82d92ec48633bd5a895224514098fb820cd79d804&w=1060"
STOP = False


def parse_page(url, base_id, table_name):
    table = connect_to_table(API_KEY, base_id, table_name)

    response = requests.get(url)
    bs4 = BeautifulSoup(response.content, 'html.parser')
    result = bs4.find('ul', class_="board_list")

    already_registered = fetch_all(table)
    already_registered = [x['fields']['내용'] for x in already_registered if x['fields'].get('내용') ]
    candidates = []
    for li in result.find_all('li'):
        if li.find(class_="title_subject") is not None or li.find(class_='subject') is None:
            continue
        subject = li.find(class_='subject').text
        price = float(li.find(class_='price').text.replace('$', '').replace(',', ''))
        writer = li.find(class_='writer').text
        date = li.find(class_='date').text

        STOP = (datetime.now() - date_parse(date)).days >= 7
        if STOP:
            break

        obj = {'제목': subject, '글쓴이': writer, '가격($)': price, '올린 날짜': date}

        if li.find('a').attrs['href'] is None:
            continue

        if 'bulletin' in li.find('a').attrs['href']:
            postfix = li.find('a').attrs['href'].split('/')[2:]
            postfix = "/" + "/".join(postfix)
        else:
            postfix = li.find('a').attrs['href'][2:]
        prefix = "https://www.radiokorea.com/bulletin"
        item_url = prefix + postfix

        if 'sca' in item_url:
            continue

        item_response = requests.get(item_url)
        item_soup = BeautifulSoup(item_response.content, 'html.parser')
        items = item_soup.find(class_='feature100p')
        if items is None:
            items = item_soup.find(class_='feature')
        items = items.find_all('div', class_='item')

        for item in items:
            if item.find('div', class_='title') is None or item.find('div', class_='detail') is None:
                continue
            titles = item.find_all('div', class_='title')
            details = item.find_all('div', class_='detail')

            for title, detail in zip(titles, details):

                title = title.text
                detail = detail.text

                if title in ['지역', '종류', '연락처']:
                    obj[title] = detail

        desc = item_soup.find('div', class_='dscr')

        obj['내용'] = desc.text.strip().replace('\n', '\\n').strip() if desc.text.strip().replace('\n', '\\n').strip() else "내용없음"
        if obj['내용'] in already_registered or obj['내용'] in candidates:
            continue
        obj['원문 링크'] = item_url

        if item_soup.find('div', class_='pic_large_item') is not None:
            postfix = item_soup.find('div', class_='pic_large_item').find('img').attrs['src'][2:]
            image_prefix = "https://www.radiokorea.com/bulletin"
            image = image_prefix + postfix
        else:
            image = DEFAULT_HOUSE_IMAGE
        image = attachment(image)

        obj['image'] = [image]
        candidates.append(obj)

    print(candidates)
    if candidates:
        insert_line(table, candidates)
        return True
    else:
        return False


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    for number in range(1, 40):
        if not STOP:
            url = f"https://www.radiokorea.com/bulletin/bbs/board.php?bo_table=c_realestate&page={number}"
            print(url)
            base_id = 'appEFU0dGebqwXavr'
            table_name = 'tbliy81ve2bjUb3it'
            result = parse_page(url, base_id, table_name)
            if not result:
                STOP = True

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
