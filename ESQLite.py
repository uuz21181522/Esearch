import sys
import torch

# 获取并打印 Python 版本
print("当前使用的 Python 版本是:", sys.version)

def check_gpu_pytorch():
    if torch.cuda.is_available():
        print(f"PyTorch detected {torch.cuda.device_count()} GPU(s):")
        for i in range(torch.cuda.device_count()):
            print(f"  - {torch.cuda.get_device_name(i)}")
    else:
        print("No GPU detected by PyTorch.")

check_gpu_pytorch()

import meilisearch
import json
import time
from tqdm import tqdm
import re
from FlagEmbedding import FlagModel

class ESQLite:
    def __init__(self, isNeedRecreate = False):
        print("初始化 ESQLite 类")
        self.client = meilisearch.Client('http://127.0.0.1:7700', 'aSampleMasterKey')
        
        self.model_zh = FlagModel('BAAI/bge-base-zh-v1.5', use_fp16=True)
        self.model_en = FlagModel('BAAI/bge-base-en-v1.5', use_fp16=True)
        self.EmbeedingMode = 'custom'
        #self.EmbeedingMode = 'huggingFace'
        
        if isNeedRecreate:
            self.create_table('command')
        self.public_id = self.get_public_id()

    def get_public_id(self):
        with open('data/{}.json'.format("public_command"), encoding='utf-8') as json_file:
            table = json.load(json_file)
        return [i['gameplayid'] for i in table]

    def listen(self, status, failedLog):
        BLUE = '\033[94m'
        RESET = '\033[0m'
        print("开始监听任务状态...")
        with tqdm(desc=f"{BLUE}任务用时{RESET}", unit="s") as pbar:
            while True:
                task = self.client.get_task(status.task_uid)
                if task.status != 'processing' and task.status != 'enqueued':
                    break
                time.sleep(2)
                print(task)
                pbar.update(2)  # 更新进度条

            print(task)
            if task.status == 'failed':
                print(task.error)
                ValueError(failedLog)

    def create_table(self, table_name):
        # 初始化客户端
        self.client.cancel_tasks({'statuses' : ['processing', 'enqueued']})
        self.client.index(table_name).delete_all_documents()
        self.client.index(table_name).reset_settings()

        # 读取 JSON 文件并添加文档到索引
        with open('data/{}.json'.format(table_name), encoding='utf-8') as json_file:
            table = json.load(json_file)
            table = [{'id': i['id'], 'name': i['name'], 'body': i['body'], 'gameplayid':i['gameplayid']} for i in table]
        
        # 设定主键
        self.client.create_index(table_name, {'primaryKey': 'id'})
        
        # 设定可搜索属性
        self.client.index(table_name).update_searchable_attributes([
            'name',
            'body',
            'gameplayid',
        ])
        
        # 设置可显示属性
        self.client.index(table_name).update_displayed_attributes([
            'name',
            'body',
            'gameplayid',
        ])
        
        # 设定不可重复属性
        self.client.index(table_name).update_distinct_attribute(
            'body'
        )
        
        # 添加filter
        self.client.index(table_name).update_filterable_attributes([
            'gameplayid',
        ])

        # 设定排序规则
        self.client.index(table_name).update_ranking_rules([
            "words", # 单词数
            "typo", # 错字数
            "proximity", # 分词距离
            "attribute", # 属性优先级
            "sort", # 数字属性
            "exactness" # 近义词
        ])

        # status = client.index(table_name).update_settings({
        #     'embedders': {
        #         'openai': {
        #             'source':  'openAi',
        #             'apiKey': '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',
        #             'model': 'text-embedding-3-small',
        #             'documentTemplate': r'A Lua command, titled {{doc.name}}, with code details {{doc.body|truncatewords: 20}}',
        #             'dimensions': 1536
        #         }
        #     }
        # })

        
        status = None
        # 设定向量编码器 API模式
        if self.EmbeedingMode == 'huggingFace':
            status = self.client.index(table_name).update_settings({
                'embedders': {
                    "TitleSearch": {
                        "source": "huggingFace",
                        "model": "BAAI/bge-base-zh-v1.5",
                        "documentTemplate": r'{{doc.name}}',
                        "distribution": {
                            "mean": 0.7,
                            "sigma": 0.3
                        }
                    },
                    "LuaSearch": {
                        "source": "huggingFace",
                        "model": "BAAI/bge-base-en-v1.5",
                        "documentTemplate": r'{{doc.body|truncatewords: 20}}',
                        "distribution": {
                            "mean": 0.7,
                            "sigma": 0.3
                        }
                    },
                }
            })
            #self.listen(status, 'Failed to update setting.')
            
        elif self.EmbeedingMode == 'custom':
            status = self.client.index(table_name).update_settings({
                'embedders': {
                    "TitleSearch": {
                        "source": "userProvided",
                        "dimensions": 768,
                        "distribution": {
                            "mean": 0.7,
                            "sigma": 0.3
                        }
                    },
                    "LuaSearch": {
                        "source": "userProvided",
                        "dimensions": 768,
                        "distribution": {
                            "mean": 0.7,
                            "sigma": 0.3
                        }
                    },
                }
            })
            self.add(table_name, table)

        print("\n\n", self.client.index(table_name).get_settings())
        
    def truncate_string_by_words(self, s):
        words = s.split()
        return ' '.join(words[:20]) + '...' if len(words) > 20 else s

    def add(self, table_name, table_old:json):
        table = table_old
        if self.EmbeedingMode == 'custom':
            if not isinstance(table, list):
                table = [table]
            name = [i['name'] for i in table]
            body = [self.truncate_string_by_words(i['body']) for i in table]
            embeedingsZH = self.generate_embedding(name, 'zh')
            embeedingsEN = self.generate_embedding(body, 'en')

            for i in range(len(table)):
                table[i]['_vectors'] = {
                    "TitleSearch": embeedingsZH[i],
                    "LuaSearch": embeedingsEN[i]
                }
                
        chunk_size = 2000
        for i in range(0, len(table), chunk_size):
            status = self.client.index(table_name).add_documents(table[i:i+chunk_size])
            #self.listen(status, 'Failed to add documents to index.')

    def delete(self, table_name, id):
        self.client.index(table_name).delete_document(id)

    def search(self, table_name, input_str, mode): 
        dict = None

        # 执行混合搜索
        if self.EmbeedingMode == 'huggingFace':
            if mode == 'TitleSearch':
                dict = self.client.index(table_name).search(input_str, {
                    'showRankingScoreDetails': True,
                    #'rankingScoreThreshold': 0.2,
                    'retrieveVectors': False,
                    'hybrid': {
                        'embedder': 'TitleSearch',
                        'semanticRatio': 0.7
                    },
                    'limit': 100,
                })
            elif mode == 'LuaSearch' or dict is None:
                dict = self.client.index(table_name).search(input_str, {
                    'showRankingScoreDetails': True,
                    'retrieveVectors': False,
                    'hybrid': {
                        'embedder': 'LuaSearch',
                        'semanticRatio': 0.3
                    },
                    'limit': 100,
                })
        elif self.EmbeedingMode == 'custom':
            if mode == 'TitleSearch':
                dict = self.client.index(table_name).search(input_str, {
                    'vector': self.generate_embedding(input_str, 'zh'),
                    'filter': 'gameplayid IN {}'. format(self.public_id),
                    'showRankingScoreDetails': True,
                    'retrieveVectors': False,
                    'hybrid': {
                        'embedder': 'TitleSearch',
                        'semanticRatio': 0.7
                    },
                    'limit': 50,
                })
            elif mode == 'LuaSearch' or dict is None:
                dict = self.client.index(table_name).search(input_str, {
                    'vector': self.generate_embedding(input_str, 'en'),
                    'filter': 'gameplayid IN {}'. format(self.public_id),
                    'showRankingScoreDetails': True,
                    'retrieveVectors': False,
                    'hybrid': {
                        'embedder': 'LuaSearch',
                        'semanticRatio': 0.3
                    },
                    'limit': 50,
                })
        #resDict = self.join(resDict, self.public_id, 'gameplayid', 'gameplayid')
        resDict = dict.get('hits')
        
        for res in resDict:
            res['body'] = repr(res['body'])
        
        return resDict
    
    def join(self, table1, table2, key1, key2):
        result = []
        for row1 in table1:
            for row2 in table2:
                if row1[key1] == row2[key2]:
                    combined_row = {**row1, **row2}
                    result.append(combined_row)
        return result
    
    def generate_embedding(self, sentences, mode):
        embeddings = None
        if mode == 'zh':
            embeddings = self.model_zh.encode(sentences)
        elif mode == 'en':
            embeddings = self.model_en.encode(sentences)

        return embeddings.tolist()
        
        
if __name__ == '__main__':
    table_name = 'command'
    mode = 'TitleSearch' 
    ESQL = ESQLite(True)
    
    while True:
        BLUE = '\033[94m'
        RESET = '\033[0m'
        input_str = input(f'{BLUE}Enter a search query (or "exit" to quit): {RESET}')
        if input_str == 'exit':
            break
        mode = 'TitleSearch' if re.search('[\u4e00-\u9fff]', input_str) else 'LuaSearch'
        print(mode)
        resDict = ESQL.search(table_name, input_str, mode)
        for hit in resDict[:3]:
            print('-' * 50)
            #print(hit)
            print(f'{BLUE}【{{}}】{RESET}\n{{}}'.format(hit['name'], hit['body']))
    
    
# # 执行混合搜索
# results = client.multi_search([
#     {
#         'indexUid': 'movies',
#         'q': 'batman',
#         'hybrid': {
#             'embedder': 'default',
#             'semanticRatio': 0.5
#         }
#     }
# ])

# # 打印结果
# for hit in results['results'][0]['hits']:
#     print(f"ID: {hit['id']}, Title: {hit['title']}")


# curl ^
#   -X PATCH 'http://localhost:7700/indexes/movies/settings' ^
#   -H 'Content-Type: application/json' ^
#   --data-binary '{ ^
#     "embedders": { ^
#       "default": { ^
#         "source":  "openAi", ^
#         "apiKey": "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", ^
#         "model": "text-embedding-3-small", ^
#         "documentTemplate": "A movie titled {{doc.title}} whose description starts with {{doc.overview|truncatewords: 20}}", ^
#         "dimensions": 1536 ^
#       } ^
#     } ^
#   }' ^

# curl ^
#   -X PATCH 'http://localhost:7700/indexes/movies/settings' ^
#   -H 'Content-Type: application/json' ^
#   --data-binary '{ "embedders": { "default": { "source":  "openAi", "apiKey": "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", "model": "text-embedding-3-small", "documentTemplate": "A movie titled {{doc.title}} whose description starts with {{doc.overview|truncatewords: 20}}", "dimensions": 1536 }}}'



# curl -X PATCH "http://localhost:7700/indexes/movies/settings" -H "Content-Type: application/json" --data-binary "{\"embedders\": {\"default\": {\"source\": \"openAi\",\"apiKey\": \"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\",\"model\": \"text-embedding-3-small\",\"documentTemplate\": \"A movie titled {{doc.title}} whose description starts with {{doc.overview|truncatewords: 20}}\",\"dimensions\": 1536}}}"

# client.index('movies').update_settings({
#   'rankingRules': [
#     'words',
#     'typo',
#     'proximity',
#     'attribute',
#     'sort',
#     'exactness',
#     'release_date:desc',
#     'rank:desc'
#   ],
#   'distinctAttribute': 'movie_id',
#   'searchableAttributes': [
#     'title',
#     'overview',
#     'genres'
#   ],
#   'displayedAttributes': [
#     'title',
#     'overview',
#     'genres',
#     'release_date'
#   ],
#   'sortableAttributes': [
#     'title',
#     'release_date'
#   ],
#   'stopWords': [
#     'the',
#     'a',
#     'an'
#   ],
#   'synonyms': {
#     'wolverine': ['xmen', 'logan'],
#     'logan': ['wolverine']
#   },
#   'typoTolerance': {
#     'minWordSizeForTypos': {
#         'oneTypo': 8,
#         'twoTypos': 10
#     },
#     'disableOnAttributes': ['title']
#   },
#   'pagination': {
#     'maxTotalHits': 5000
#   },
#   'faceting': {
#     'maxValuesPerFacet': 200
#   },
#   'searchCutoffMs': 150
# })