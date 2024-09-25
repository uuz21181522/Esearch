import mysql.connector

class DatabaseCopier:
    def __init__(self, source_config, target_config):
        self.source_conn = mysql.connector.connect(**source_config)
        self.target_conn = mysql.connector.connect(**target_config)
        self.source_cursor = self.source_conn.cursor()
        self.target_cursor = self.target_conn.cursor()

    def get_table_names(self, cursor):
        cursor.execute("SHOW TABLES")
        return [table[0] for table in cursor.fetchall()]

    def get_create_table_statement(self, table_name):
        self.source_cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
        return self.source_cursor.fetchone()[1]

    def add_missing_indexes(self, table_name):
        try:
            # 手动构建 SHOW CREATE TABLE 语句
            self.source_cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
            create_table_stmt = self.source_cursor.fetchone()[1]
            lines = create_table_stmt.split('\n')
            for line in lines:
                if 'FOREIGN KEY' in line:
                    referenced_table = line.split('REFERENCES')[1].split('(')[0].strip()
                    referenced_column = line.split('REFERENCES')[1].split('(')[1].split(')')[0].strip()
                    # 手动构建 SHOW INDEX 语句
                    self.target_cursor.execute(f"SHOW INDEX FROM `{referenced_table}` WHERE Column_name = '{referenced_column}'")
                    indexes = self.target_cursor.fetchall()
                    if not indexes:
                        index_name = f"idx_{referenced_table}_{referenced_column}"
                        # 手动构建 CREATE INDEX 语句
                        self.target_cursor.execute(f"CREATE INDEX `{index_name}` ON `{referenced_table}` (`{referenced_column}`)")
        except mysql.connector.Error as err:
            print(f"Error: {err}")

    def copy_table(self, table_name):
        self.add_missing_indexes(table_name)
        create_table_stmt = self.get_create_table_statement(table_name)
        self.target_cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
        self.target_cursor.execute(create_table_stmt)
        self.source_cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
        columns = [column[0] for column in self.source_cursor.fetchall()]
        placeholders = ', '.join(['%s'] * len(columns))
        columns_str = ', '.join([f"`{col}`" for col in columns])
        insert_query = f"INSERT INTO `{table_name}` ({columns_str}) VALUES ({placeholders})"
        self.source_cursor.execute(f"SELECT * FROM `{table_name}`")
        while True:
            rows = self.source_cursor.fetchmany(size=1000)
            if not rows:
                break
            self.target_cursor.executemany(insert_query, rows)
            self.target_conn.commit()

    def copy_database(self):
        # 按照特定顺序定义表名
        # table_order = ['gameplay', 'custom_command', 'command_tree', 'public_command', 'user_config',
        #                'command_old', 'command']  # 替换为实际的表名
        table_order = ['command']
        for table in table_order:
            self.copy_table(table)
            print(f"复制表 {table} 完成")

    def close_connections(self):
        self.source_cursor.close()
        self.source_conn.close()
        self.target_cursor.close()
        self.target_conn.close()

# 配置源数据库和目标数据库的连接信息
source_config = {
    'user': 'gmt',
    'password': 'gmt1234',
    'host': 'cloud.leihuo.netease.com',
    'port': 40135,
    'database': 'gmcommand'
}

target_config = {
    'user': 'root',
    'password': '123456',
    'host': '127.0.0.1',
    'port': 3306,
    'database': 'gmcommand'
}

# 创建 DatabaseCopier 实例并复制数据库
copier = DatabaseCopier(source_config, target_config)
copier.copy_database()
copier.close_connections()