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
DEFAULT_HOUSE_IMAGE = "https://img.freepik.com/free-photo/3d-model-residential-building_23-2150761232.jpg?t=st=1694059079~exp=1694062679~hmac=9e76115d813fa2be0d2c21e82d92ec48633bd5a895224514098fb820cd79d804&w=1060"
STOP = False


def parse_page(url, base_id, table_name):
    try:
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
                price = float(li.select_one('a > span:nth-child(3)').text.replace('$', '').replace(',', ''))
            except Exception as e:
                continue
            writer = li.select_one('a > span:nth-child(5)').text #지역으로 대체 표기
            date = li.select_one('a > span:nth-child(6)').text

            STOP = (datetime.now() - date_parse(date)).days >= 7
            if STOP:
                break

            obj = {'제목': subject, '글쓴이': writer, '가격($)': price, '올린 날짜': date}

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
            #obj = {'제목': subject, '글쓴이': writer, '가격($)': price, '올린 날짜': date}
            for item in item_detail:
                email = ""
                phone = ""
                #print("92:", item.text)
                if '작성일' in item.text:
                    detail = item.text.split('\n작성일')[0]
                    title = '올린 날짜'
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
                if '지역' in item.text:
                    detail = item.text.split('\n')[2]
                    title = "지역"
                    obj[title] = detail
                if '구분' in item.text:
                    detail = item.text.split('\n')[2]
                    title = "종류"
                else:
                    if item.text.count('\n') > 1:
                        title, detail = "", item.text.split('\n')[2]
                    else:
                        title, detail = "", item.text.split('\n')[0]
                ##title = title.replace('·', '').strip()
                if title in ['지역', '종류', '연락처']:
                    obj[title] = detail
                    if '연락처' in title:
                        obj[title] = phone+"/"+email
                        #print("129",phone+"/"+email)

            desc = item_soup.find('div', class_='detail_content')

            obj['내용'] = desc.text.strip().replace('\n', '\\n').strip()
            #if desc.text.strip().replace('\n', '\\n').strip() else "내용없음"
            if obj['내용'] in already_registered or obj['내용'] in candidates:
                #print("104", obj['내용'])
                continue
            obj['원문 링크'] = item_url

            img_url = item_soup.find('span', class_='zoomimg')

            if img_url is not None:
                postfix = img_url.find('img').attrs['src'][36:]
                image_prefix = "https://m.musalist.com:441/fileServer/ImageServer/upload/busi3"
                image = image_prefix + postfix
                if image_prefix.find("fileServer/ImageServer/upload/") == -1:
                    image = "https://m.musalist.com:441/mainpage/image/photo580_435.gif"
            else:
                image = DEFAULT_HOUSE_IMAGE
            image = attachment(image)

            obj['image'] = [image]
            candidates.append(obj)
            #print("117mhouse:", obj)

        print("119mhouse:candidates:", candidates)

        if candidates:
            insert_line(table, candidates)
            records = table.all(sort=['Last Modified'])
            #print("#145 records:", records)
            if len(records) >= 410:
                delete(records, del_candidates, table, candidates)
            return True
        else:
            return False

    except Exception as e:
        return False

def delete(records, del_candidates, table, candidates):
    count = 0

    for i in records:
        #print("올린 날짜:", i['fields']['올린 날짜'])
        #datetime.now() - date_parse(i['fields']['올린 날짜'])).days >= 7
        obj = {i['id']}
        del_candidates.append(obj)
        if count == len(candidates)-1:
            print("mhouse_del_candidates", len(candidates), del_candidates)
            break
        count += 1
        time.sleep(5)  # 1000 = 16min, 10000 seconds = 2.7 hours
    print("mhouse_delete_line:",delete_line(table, del_candidates))

# Press the green button in the gutter to run the script.
#if __name__ == '__main__':
def m_run():
    global STOP
    STOP = False
    for number in range(1, 40):
        if not STOP:
            url = f"https://m.musalist.com:441/mainpage/boards/board_list.asp?section=land&id=busi3&wflag=C&page={number}"

            print("4:", url)
            base_id = 'appEFU0dGebqwXavr'
            table_name = 'tbliy81ve2bjUb3it'
            result = parse_page(url, base_id, table_name)
            #print("House :",result)
            if not result:
                STOP = True
    #time.sleep(5)  # 1000 = 16min, 10000 seconds = 2.7 hours
    #print("House stop:", STOP)
    #print("House :",time.ctime())


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
