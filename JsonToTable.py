import json
import mysql.connector
import datetime

class JSONToMySQLTable:
    def __init__(self, connection_config):
        self.connection_config = connection_config

    def generate_create_table_query(self, table_name, json_array, sql_type=None):
        if not json_array:
            raise ValueError("JSON array is empty")

        # 使用第一个对象的键生成表结构
        first_object = json_array[0]
        columns = []
        for i, (key, value) in enumerate(first_object.items()):
            column_name = key
            column_type = self.detect_sql_type(value, column_name) if sql_type is None else sql_type[i]
            columns.append(f"{column_name} {column_type}")
        columns_definition = ", ".join(columns)
        create_table_query = f"CREATE TABLE {table_name} ({columns_definition});"
        return create_table_query

    def create_table(self, table_name, json_array, sql_type=None):
        create_table_query = self.generate_create_table_query(table_name, json_array, sql_type=sql_type)
        print(create_table_query)  # 打印生成的SQL语句

        try:
            conn = mysql.connector.connect(**self.connection_config)
            cursor = conn.cursor()
            drop_table_query = "DROP TABLE IF EXISTS {}".format(table_name)
            cursor.execute(drop_table_query)
            cursor.execute(create_table_query)
            conn.commit()
            print("Table created successfully.")
        except mysql.connector.Error as err:
            print(f"Error: {err}")
        finally:
            cursor.close()
            conn.close()
            
    def detect_sql_type(self, value, column_name):
        if column_name in ['commandid', 'body']:
            return "TEXT"
        if isinstance(value, int):
            return "INT"
        elif isinstance(value, float):
            return "FLOAT"
        elif isinstance(value, str):
            # 尝试解析日期时间字符串
            try:
                datetime.datetime.strptime(value, r'%Y-%m-%d %H:%M:%S')
                return "DATETIME"
            except ValueError:
                pass
            
            if len(value) > 255:
                return "TEXT"
            else:
                return "VARCHAR(255)"
        elif isinstance(value, bool):
            return "BOOLEAN"
        elif isinstance(value, bytes):
            return "BLOB"
        else:
            return "TEXT"  # 默认类型

    def insert_data(self, table_name, json_array):
        if not json_array:
            raise ValueError("JSON array is empty")

        # 使用第一个对象的键生成插入语句
        first_object = json_array[0]
        columns = ", ".join(first_object.keys())
        placeholders = ", ".join(["%s"] * len(first_object))
        insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        data = []
        for obj in json_array:
            data.append(tuple(obj.values()))

        try:
            conn = mysql.connector.connect(**self.connection_config)
            cursor = conn.cursor()
            for i in range(0, len(data), 1000):
                cursor.executemany(insert_query, data[i:i+1000])
            conn.commit()
            print("Data inserted successfully.")
        except mysql.connector.Error as err:
            print(f"Error: {err}")
        finally:
            cursor.close()
            conn.close()

if __name__ == '__main__':
    # 数据库连接配置
    connection_config = {
        'user': 'root',
        'password': '123456',
        'host': '127.0.0.1',
        'port': 3306,
        'database': 'gmcommand'
    }
    
    # 表名
    table_names = ['command', 'command_old', 'command_tree', 'custom_command', 'gameplay', 'public_command', 'user_config']
    for table_name in table_names:
        if table_name == 'custom_command':
            print(111111111)
        with open('data/{}.json'.format(table_name), encoding='utf-8') as json_file:
            json_array = json.load(json_file)
            
        # 创建JSONToMySQLTable实例并创建表和插入数据
        json_to_mysql = JSONToMySQLTable(connection_config)
        
        if table_name == 'user_config':
            sql_type = ['SMALLINT(5) UNSIGNED', 'MEDIUMINT(8) UNSIGNED', 'MEDIUMBLOB ', 'VARCHAR(255)']
        else:
            sql_type = None
            
        json_to_mysql.create_table(table_name, json_array, sql_type)
        print("***************************")
        json_to_mysql.insert_data(table_name, json_array)