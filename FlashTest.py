import requests
import ast

url = 'http://127.0.0.1:5000//search'

while True:
    BLUE = '\033[94m'
    RESET = '\033[0m'
    input_str = input(f'{BLUE}Enter a search query (or "exit" to quit): {RESET}')
    if input_str == 'exit':
        break
    resDict = requests.post(url, json={'table_name': 'command', 'input_str': input_str}).json()
    for hit in resDict[:3]:
        print('-' * 50)
        print(f'{BLUE}【{{}}】{RESET}\n{{}}'.format(hit['name'], ast.literal_eval(hit['body'])))

