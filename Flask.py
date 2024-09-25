from flask import Flask, request, jsonify
from waitress import serve
import sys

from ESQLite import ESQLite
import re
import json
from downloadData import DatabaseDownloader
import time
from CanalClient import CanalClient
import threading
from canal.protocol import EntryProtocol_pb2
import concurrent.futures


app = Flask(__name__)
ESQL = None

BLUE = '\033[34m'
END = '\033[0m'

@app.route('/search', methods=['POST'])
def search():
    global ESQL
    data = request.json
    
    table_name = data.get('table_name', '')
    input_str = data.get('input_str', '')
    
    mode = 'TitleSearch' if re.search('[\u4e00-\u9fff]', input_str) else 'LuaSearch'
    
    # print(f'{BLUE}Searching {table_name} for "{input_str}"...{END}')
    
    # start_time = time.time()
    resDict = ESQL.search(table_name, input_str, mode)
    # end_time = time.time()
    # elapsed_time = end_time - start_time
    # print(f'{BLUE}Searching {table_name} for "{input_str}" took {elapsed_time:.2f} seconds.{END}')
    
    response = []
    for hit in resDict[:50]:
        response.append({'name': hit['name'], 'body': hit['body']})
    
    return jsonify(response)


def meilisearch_process(data):
    if data['db']!='gmcommand' or data['table'] != 'command':
        return
    global ESQL
    
    if data['event_type'] == EntryProtocol_pb2.EventType.DELETE:
        ESQL.delete(data['table'], data['data']['id'])
        print(f"{BLUE}DELETE:{END}{data['data']}\n")
        
    elif data['event_type'] == EntryProtocol_pb2.EventType.INSERT:
        print(f"{BLUE}INSERT:{END}{data['data']}\n")
        ESQL.add(data['table'], data['data'])
        
    elif data['event_type'] == EntryProtocol_pb2.EventType.UPDATE:
        print(f"{BLUE}UPDATE:{END}{data['data']}\n")
        ESQL.add(data['table'], data['data']['after'])

def run_canal_client():
    canal_client = CanalClient(
        host = '127.0.0.1',
        port = 11111,
        client_id = 1001,
        destination = 'gmcommand',
        username = 'gmt',
        password = '123456',
    )
    canal_client.set_process_func(meilisearch_process)
    canal_client.connect()
    canal_client.start()


def initialize():
    # 同步Mysql数据到ESQLite
    downloader = DatabaseDownloader(
        host='cloud.leihuo.netease.com',
        port=40135,
        user='gmt',
        password='gmt1234',
        database='gmcommand'
    )
    downloader.download_table('command', 'data/command.json')
    downloader.download_table('gameplay', 'data/gameplay.json')
    downloader.download_table('public_command', 'data/public_command.json')
    
    global ESQL 
    ESQL = ESQLite(isNeedRecreate=False)
    
    # run_canal_client()
    # 启动子线程运行Canal Client
    canal_thread = threading.Thread(target=run_canal_client)
    canal_thread.daemon = True
    canal_thread.start()

def get_port():
    if len(sys.argv) > 1:
        return int(sys.argv[1].split('=')[1])
    return 5000

# if __name__ == '__main__':
initialize()
print("judge:**************************", ESQL==None)
try:
    #app.run(host='0.0.0.0', port=5000, threaded=True, debug=True)
    serve(app,
            host='0.0.0.0',
            port=get_port(),
        #   threads=4,
        #   connection_limit=1000,  # 增加连接限制
        #   backlog=2048  # 增加等待队列长度
            )
except KeyboardInterrupt:
    print("Interrupted by user")

# CREATE USER 'gmt'@'%' IDENTIFIED BY '123456';
# GRANT ALL PRIVILEGES ON gmcommand.* TO 'gmt'@'%';
# FLUSH PRIVILEGES;