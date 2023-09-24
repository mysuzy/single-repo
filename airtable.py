from pyairtable import Api

def connect_to_table(api_key, base_id, table_name):
    api = Api(api_key)
    table = api.table(base_id=base_id,table_name=table_name)
    return table

def insert_line(table,entities):
    try:
        table.batch_create(entities)
    except Exception as e:
        print(e)
        return False
    return True

def fetch_all(table):
    try:
        result = table.all(sort=['-올린 날짜'])
    except Exception as e:
        print(e)
        return False

    return result

if __name__ == '__main__':
    API_KEY = "patqmwV7hrU86hqYI.27fd1e12ce830b4306ac7bf5658fcb1929804783df1d4c3a0b579110e22a6b78"

    table = connect_to_table(API_KEY,base_id,table_name)
    table.create({'subject': '\nCerritos, 하우스- 원룸 렌트\n하우스\nCerritos\n', 'writer': 'Imsoo', 'price': '$750\xa0', 'date': '09.01.23'})