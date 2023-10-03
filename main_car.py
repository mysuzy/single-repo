import requests
import time
from bs4 import BeautifulSoup
from airtable import insert_line, connect_to_table, fetch_all, delete_line
from pyairtable.utils import attachment
from datetime import datetime
from dateutil.parser import parse as date_parse

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
API_KEY = "keyECvHHQ7YECHBy7"
TOKEN = "patqmwV7hrU86hqYI.27fd1e12ce830b4306ac7bf5658fcb1929804783df1d4c3a0b579110e22a6b78"
DEFAULT_CAR_IMAGE = "https://cdn-icons-png.flaticon.com/512/2554/2554936.png"
STOP = False


def parse_page(url, base_id, table_name):
    table = connect_to_table(API_KEY, base_id, table_name)

    response = requests.get(url)
    bs4 = BeautifulSoup(response.content, 'html.parser')
    result = bs4.find('ul', class_="board_list")

    already_registered = fetch_all(table)

    # 502 Server Error: Bad Gateway for url
    # error handling => TypeError: 'bool' object is not iterable
    if already_registered:
        already_registered = [x['fields']['내용'] for x in already_registered]
    else:
        already_registered = []

    candidates = []
    del_candidates = []

    for li in result.find_all('li'):
        if li.find(class_='title_info') is not None or li.find(class_='aoa') is not None:
            continue
        subject = li.find(class_='model').text
        try:
            age = subject.split(' ')[0]
            age = int(age)
        except Exception as e:
            print('no age', subject)
            age = 0
        try:
            price = float(li.find(class_='price').text.replace('$', '').replace(',', ''))
        except Exception as e:
            continue
        writer = li.find(class_='seller').text
        date = li.find(class_='date').text
        miles = float(li.find(class_='miles').text.replace(',', '').replace('mi', ''))

        STOP = (datetime.now() - date_parse(date)).days >= 7
        if STOP:
            break

        obj = {'차량정보': subject, '글쓴이': writer, '가격($)': price, '올린 날짜': date, '주행거리': miles, '연식': age}

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
        item_detail = items.find('div', class_='detail')

        for item in item_detail.find_all('ul'):
            for li in item.find_all('li'):
                if '등록일자' in li.text:
                    detail = li.text.split('· 등록일자:')[1]
                    title = '등록일자'
                else:
                    title, detail = li.text.split(':')
                title = title.replace('·', '').strip()
                if title in ['사고여부/타이틀', '등록일자', '연락처', '색상']:
                    obj[title] = detail

        desc = item_soup.find('div', class_='dscr')

        obj['내용'] = desc.text.strip().replace('\n', '\\n').strip()
        if obj['내용'] in already_registered or obj['내용'] in candidates:
            continue
        obj['원문 링크'] = item_url

        if item_soup.find('div', class_='pic_large_item') is not None:
            postfix = item_soup.find('div', class_='pic_large_item').find('img').attrs['src'][2:]
            image_prefix = "https://www.radiokorea.com/bulletin"
            image = image_prefix + postfix
        else:
            image = DEFAULT_CAR_IMAGE
        image = attachment(image)

        obj['image'] = [image]
        candidates.append(obj)

    print(candidates)
    if candidates:
        insert_line(table, candidates)
        records = table.all(sort=['올린 날짜'])
        delete(records, del_candidates, table, candidates)
        return True
    else:
        return False

def delete(records, del_candidates, table, candidates):
    count = 0

    for i in records:
        #print("올린 날짜:", i['fields']['올린 날짜'])
        #datetime.now() - date_parse(i['fields']['올린 날짜'])).days >= 7
        obj = {i['id']}
        del_candidates.append(obj)
        if count == len(candidates)-1:
            print("car_del_candidates", len(candidates), del_candidates)
            break
        count += 1
        time.sleep(5)  # 1000 = 16min, 10000 seconds = 2.7 hours
    print("car_delete_line:",delete_line(table, del_candidates))

# Press the green button in the gutter to run the script.
#if __name__ == '__main__':
def run():
    global STOP
    STOP = False
    for number in range(1, 40):
        if not STOP:
            url = f"https://www.radiokorea.com/bulletin/bbs/board.php?bo_table=c_car_owner&page={number}"
            print(url)
            base_id = 'appEFU0dGebqwXavr'
            table_name = 'tbloMaYMXxcM4NrAd'
            result = parse_page(url, base_id, table_name)
            #print("Car :",result)
            if not result:
                STOP = True
    #time.sleep(5)  # 1000 = 16min, 10000 seconds = 2.7 hours
    #print("Car stop:", STOP)
    #print("Car :",time.ctime())


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
