import requests
import time
from datetime import datetime
import json
import sys
import sqlite3
import os

'''
number = 100
timestamp = 1422019499
url="https://ctftime.org/api/v1/events/?limit=100&start=1422019499&finish=1423029499"
#url = "https://ctftime.org/api/v1/events/?limit={number}&start={timestamp}&finish={timestamp}"
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}

response = requests.get(url, headers=headers)

print(response.content)
'''
total_ctftime = []
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}
db_column = ["Alert", "Title", "StartTime", "FinishTime", "Duration", "Url", "Desc", "Or_id", "Or_name", "Event_id", "Ctf_id"]
discord_webhook = "https://discord.com/api/webhooks/1090314519781314731/L9HzIIXjVxuOkLGOUNDt9sxcCOHhZFqaQAErKb2bgYTnZJrcJCskMqsWWgik_yB6Gbj3"
discord_headers={
    'Content-Type': 'application/json'
}

def collect_imgurl(url):
    start = False
    add_path = ''
    
    responses = requests.get(url, headers=headers)
    response = responses.content.decode('utf-8')[1:-1]
    for r in response.split('\n'):
        if '<div class="span2">' in r:
            start = True
            continue
        elif start and '</div>' in r:
            start = False
        
        if start:
            add_path += r
    
    add_path = add_path.replace(' ','')
    src = add_path.split("\"")[1]
    return_url = "https://ctftime.org" + src
    
    return return_url

def alert_ctftime():
    # db에 저장된 ctftime데이터 전부 탐색
    conn = sqlite3.connect('ctftime.db')
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM CtfTime WHERE alert = 'X'") # 1. select로 alert가 'x'인 데이터 필터링
    rows = cur.fetchall()
    
    for row in rows: # (그 데이터를 하나씩 반복)
        list_row = list(row)
        # 2. 이미지 크롤링해서 전달
        # 3. 데이터를 webhook으로 전달
        
        # ctf id 이용 / event id 이용
        ctf_url = "https://ctftime.org/ctf/" + str(list_row[10])
        image_url = collect_imgurl(ctf_url)
        
        # 메시지와 함께 전송될 미리보기 생성
        data = {
            "content": "",
            "embeds": [
                {
                    "image": {"url": image_url}
                }
            ]
        }

        # POST 요청으로 메시지와 미리보기 전송
        headers = {"Content-Type": "application/json"}
        response = requests.post(discord_webhook, data=json.dumps(data), headers=discord_headers)
        
        '''
        # 응답 확인
        if response.status_code == 204:
            print(f"Alert - {list_row[1]}")
        else:
            print("fdas") #
            print(f"Message sending failed with status code {response.status_code}")
        '''
        
        # 
        list_start = list_row[2].split('T')
        starttime = list_start[0] + " " + list_start[1]
        
        list_finish = list_row[3].split('T')
        finishtime = list_finish[0] + " " + list_finish[1]
        
        message = f''
        message += f'[CTF Title]\t : \t[{list_row[1]}]\n '
        message += f'[StartTime]\t : \t{starttime[:-6]}\n '
        message += f'[FinishTime]\t : \t{finishtime[:-6]}\n '
        message += f'[Duration]\t : \t{list_row[4]}\n '
        message += f'[Url]\t : \t{list_row[5]}\n '
        
        # "Or_id", "Or_name", "Event_id", "Ctf_id"
        #print(list_row[7], list_row[8], list_row[9], list_row[10])
        
        # 미리보기를 생성할 URL
        event_url = "https://ctftime.org/event/" + str(list_row[9])
        image_url = collect_imgurl(event_url)

        # 메시지와 함께 전송될 미리보기 생성
        data = {
            "content": f"{message}",
            "embeds": [
                {
                    "title": str(list_row[1]),
                    "description": f"{starttime[:-6]} -> {finishtime[:-6]}",
                    "url": str(list_row[5]),
                    "color": 16711680,
                    "image": {"url": image_url}
                }
            ]
        }

        # POST 요청으로 메시지와 미리보기 전송
        headers = {"Content-Type": "application/json"}
        response = requests.post(discord_webhook, data=json.dumps(data), headers=discord_headers)

        '''
        # 응답 확인
        if response.status_code == 204:
            print(f"Alert - {list_row[1]}")
        else:
            print(f"Message sending failed with status code {response.status_code}")
        '''

        response = requests.post(discord_webhook,headers=discord_headers,data=data)
        
        # 3. update기능을 이용하여 alert 'o'로 변경
        update_spl = f'UPDATE CtfTime SET Alert="O" WHERE Title="{list_row[1]}"'
        #print(update_spl)
        cur.execute(update_spl)
        conn.commit()
        
        print(f"Alert - {list_row[1]}")
        
    conn.close()

def insert_ctftime(list_response): # list내부에 dict들
    add_count = 0
    recent_time = time.time()
    
    conn = sqlite3.connect('ctftime.db')
    cur = conn.cursor()
    
    # ctf_id와 event_id를 이용하여 내부에 중복 여부 확인
    for response in list_response:
        event_id = response['id']
        ctf_id = response['ctf_id']
        
        cur.execute(f"SELECT Event_id,Ctf_id FROM CtfTime WHERE Ctf_id = {ctf_id} and Event_id = {event_id}")
        if len(list(cur)) == 0:
            # 크롤링 데이터 넣기
            Or = response['organizers'][0]
            
            Alert = "X"
            Title = response['title']
            StartTime = response['start'][:-6]
            # 기간 한참 남은 ctf pass
            change_time = time.mktime(datetime.strptime(StartTime,'%Y-%m-%dT%H:%M:%S').timetuple())

            # 14 days
            if recent_time + 1209600 < change_time:
                continue
            
            FinishTime = response['finish']
            Duration = response['duration'] # 가공 필요
            Duration = f"{Duration['days']} days - {Duration['hours']} hours"
            Url = response['url']
            Desc = response['description']
            Or_id = Or['id']
            Or_name = Or['name']
            Event_id = response['id']
            Ctf_id = response['ctf_id']
            
            cur.execute("INSERT INTO CtfTime VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", \
                (Alert, Title, StartTime, FinishTime, Duration, Url, Desc, Or_id, Or_name, Event_id, Ctf_id))
            conn.commit() # 이것 해야지 데이터가 입력됨
            add_count += 1
    print(f"[+] Insert Data - {add_count}", end="\n\n")    
    conn.close()

def crawling_ctftime():
    timestamp = time.time()
    datetimes = str(datetime.fromtimestamp(timestamp))

    number = 100
    end_time = timestamp+1240000
    url = f"https://ctftime.org/api/v1/events/?limit={number}&start={timestamp}&finish={end_time}"

    responses = requests.get(url, headers=headers)
    response = responses.content.decode('utf-8')[1:-1]

    list_response = list()
    list_count = [0,0]
    dict_str = ""
    for s in response:
        if s == "{":
            list_count[0] += 1
        if s == "}":
            list_count[1] += 1
        
        dict_str += s
        
        if list_count[0] == list_count[1]:
            if dict_str == ",":
                dict_str = ""
                continue
            elif dict_str == " ":
                dict_str = ""
                continue
            
            list_response.append(dict_str)
            dict_str = ""
            
    # json변환 완료
    for i in range(len(list_response)):
        list_response[i] = json.loads(list_response[i])
    #print_dict(list_response[0])
    
    return list_response

def print_dict(dict_file):
    list_key = list(dict_file.keys())
    for key in list_key:
        print(f"[{key}]")
        print(dict_file[key])
        print()

def load_DBData(conn):
    cur = conn.cursor()
    # index(int), alert(text), title(text), start(text), Finish(text), duration(text), url(text), Description(text), organiers_id(int), organier_name(text), id(int), ctf_id(int)
    
    # 내부 데이터 load
    cur.execute('select * from CtfTime')
    for row in cur:
        ctftime = list(row)
        total_ctftime.append(ctftime)

def init_CTFData():
    conn = sqlite3.connect('ctftime.db')
    # 테이블 생성
    #cur.execute("CREATE TABLE CtfTime (\
    #        Alert text, Title text, StartTime text, FinishTime text, Duration text, \
    #        Url text, Desc text, Or_id INTEGER, Or_name text, Event_id INTEGER, Ctf_id INTEGER);")
    
    # 테이블 내에 데이터 가져와서 저장
    load_DBData(conn)
    conn.close()

# (1) DB의 유무확인
# (1-1) DB를 생성 / (1-2) DB내부에 데이터 로딩
base_path = os.getcwd()
list_dir = os.listdir(base_path)
if not "ctftime.db" in list_dir:
    open("ctftime.db","w") # db파일 생성

init_CTFData() # DB내에 ctftime데이터 로딩

# -----
list_response = crawling_ctftime()
insert_ctftime(list_response) # 중복이 없을 경우만 insert

# alert를 기준으로 Discord봇에 웹훅
alert_ctftime()

# Next : 일정시간마다 자동 실행하는 쉴스크립트 개발