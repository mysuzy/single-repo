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
    result = bs4.find('ul', class_="pr_list")

    already_registered = fetch_all(table)

    # 502 Server Error: Bad Gateway for url
    # error handling => TypeError: 'bool' object is not iterable
    if already_registered:
        already_registered = [x['fields']['내용'] for x in already_registered]
    else:
        already_registered = []

    candidates = []
    del_candidates = []

    count= 0
    #1. from list page
    for li in result.find_all('li'):

        subject = li.select_one('a > span:nth-child(2)').get_text() #pr_title_thum
        #print("42", subject)
        try:
            age = subject.split(' ')[0]  #상세페이지에서 재설정
            age = int(age)
        except Exception as e:
            #print('no age', subject)
            age = 0
        try:
            price = float(li.select_one('a > span:nth-child(3)').text.replace('$', '').replace(',', ''))
        except Exception as e:
            continue
        writer = li.select_one('a > span:nth-child(5)').text #지역으로 대체 표기
        date = li.select_one('a > span:nth-child(6)').text
        miles = 0   # 상세페이지에서 재설정

        STOP = (datetime.now() - date_parse(date)).days >= 7
        if STOP:
            break

        obj = {'차량정보': subject, '글쓴이': writer, '가격($)': price, '올린 날짜': date, '주행거리': miles, '연식': age}

        if li.find('a').attrs['href'] is None:
            continue

        if 'mainpage' in li.find('a').attrs['href']: #상세조회 링크
            postfix = li.find('a').attrs['href'].split('/')[2:]
            postfix = "/" + "/".join(postfix)
        else:
            postfix = li.find('a').attrs['href'][2:]
        prefix = "https://m.musalist.com:441/mainpage"
        item_url = prefix + postfix

        item_response = requests.get(item_url)
        item_soup = BeautifulSoup(item_response.content, 'html.parser')

        items = item_soup.find('div', id='post_cont')
        #print("#80", items)
        if items is None:
            items = item_soup.find('basic_tbl')
            #print("#83", items)
        item_detail = items.find_all('tr')
        #print("#85", item_detail)

        #2. from detail page
        #obj = {'차량정보': subject, '글쓴이': writer, '가격($)': price, '올린 날짜': date, '주행거리': miles, '연식': age}
        for item in item_detail:
            email = ""
            phone = ""
            #print("92:", item.text)
            if '작성일' in item.text:
                detail = item.text.split('\n작성일')[0]
                title = '올린 날짜'
            if '주행거리' in item.text:
                detail = item.text.split('\n')[2]
                title = "주행거리"
                obj[title] = float(detail.replace(" mi", ""))
                # print("93 ", detail)
            if '연식' in item.text:
                detail = item.text.split('\n')[2]  # 연식(Year)
                title = "연식"
                obj[title] = int(detail)
                # print("94 ", detail)
            if '이름' in item.text:
                detail = item.text.split('\n')[2].replace("쪽지", "") + " " + writer.replace("\n", "")
                title = "글쓴이"
                obj[title] = detail
            if '전화번호' in item.text:  # 전화번호
                detail = item.text.split('\n')[3].replace(" ", "")
                title = "연락처"
                phone = detail
                obj[title] = detail
            if '이메일' in item.text:  # 전화번호
                detail = item.text.split('\n')[2]
                email = detail
            if '색상' in item.text:
                detail = item.text.split('\n')[2]
                title = "색상"
                obj[title] = detail
            if '상태' in item.text:
                if item.text.count('\n') > 1:
                    title, detail = "사고여부/타이틀", item.text.split('\n')[2]
                else:
                    title, detail = "사고여부/타이틀", item.text.split('\n')[0]
            else:
                if item.text.count('\n') > 1:
                    title, detail = "", item.text.split('\n')[2]
                else:
                    title, detail = "", item.text.split('\n')[0]
            ##title = title.replace('·', '').strip()
            if title in ['사고여부/타이틀', '올린 날짜', '연락처', '색상']:
                obj[title] = detail
                if '연락처' in title:
                    obj[title] = phone+"/"+email
                #print("129",obj)

        desc = item_soup.find('div', class_='detail_content')

        obj['내용'] = desc.text.strip().replace('\n', '\\n').strip()
        if obj['내용'] in already_registered or obj['내용'] in candidates:
            #print("104", obj['내용'])
            continue
        obj['원문 링크'] = item_url

        img_url = item_soup.find('span', class_='zoomimg')

        if img_url is not None:
            postfix = img_url.find('img').attrs['src'][36:]
            image_prefix = "https://m.musalist.com:441/fileServer/ImageServer/upload/busi2"
            image = image_prefix + postfix
            if image_prefix.find("fileServer/ImageServer/upload/busi2") == -1:
                image = "https://m.musalist.com:441/mainpage/image/photo580_435.gif"
        else:
            image = DEFAULT_CAR_IMAGE
        image = attachment(image)

        obj['image'] = [image]
        candidates.append(obj)
        #print("117mcar:", obj)

    print("119mcar:candidates:", candidates)

    if candidates:
        insert_line(table, candidates)
        records = table.all(sort=['올린 날짜'])
        if len(records) >= 60:
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
            print("mcar_del_candidates", len(candidates), del_candidates)
            break
        count += 1
        time.sleep(5)  # 1000 = 16min, 10000 seconds = 2.7 hours
    print("mcar_delete_line:",delete_line(table, del_candidates))

# Press the green button in the gutter to run the script.
#if __name__ == '__main__':
def m_run():
    global STOP
    STOP = False
    for number in range(1, 40):
        if not STOP:
            url = f"https://m.musalist.com:441/mainpage/boards/board_list.asp?section=cars&id=busi2&wflag=C&page={number}"
            print("5:", url)
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
