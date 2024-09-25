import pymysql
import json
import datetime
import base64

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime(r"%Y-%m-%d %H:%M:%S")
        elif isinstance(obj, bytes):
            return base64.b64encode(obj).decode('utf-8')
        return super(DateTimeEncoder, self).default(obj)

class DatabaseDownloader:
    def __init__(self, host, port, user, password, database):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def connect(self):
        self.connection = pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            charset='utf8'
        )

    def download_table(self, table_name, output_file):
        try:
            self.connect()
            with self.connection.cursor() as cursor:
                # 执行查询
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                
                # 获取列名和列类型
                columns = [desc[0] for desc in cursor.description]
                column_types = [desc[1] for desc in cursor.description]
                
                # 将数据转换为 JSON 格式
                data = []
                for row in rows:
                    row_dict = {}
                    for col, col_type, value in zip(columns, column_types, row):
                        if isinstance(value, bytes):
                            row_dict[col] = value.decode('utf-8')
                        else:
                            row_dict[col] = value
                    data.append(row_dict)
                    
                with open(output_file, 'w', encoding='utf-8') as jsonfile:
                    json.dump(data, jsonfile, ensure_ascii=False, indent=4, cls=DateTimeEncoder)
        finally:
            if self.connection:
                self.connection.close()


if __name__ == '__main__':
    # downloader = DatabaseDownloader(
    #     host='cloud.leihuo.netease.com',
    #     port=40135,
    #     user='gmt',
    #     password='gmt1234',
    #     database='gmcommand'
    # )
    downloader = DatabaseDownloader(
        host='127.0.0.1',
        port=3306,
        user='root',
        password='123456',
        database='gmcommand'
    )
    # 表名
    table_names = ['command', 'command_old', 'command_tree', 'custom_command', 'gameplay', 'public_command', 'user_config']
    for table_name in table_names:
        print("downloading table {}...".format(table_name))
        downloader.download_table(table_name, 'data/{}.json'.format(table_name))