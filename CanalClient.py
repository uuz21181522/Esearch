import time
from canal.client import Client
from canal.protocol import EntryProtocol_pb2
from canal.protocol import CanalProtocol_pb2

class CanalClient:
    def __init__(self, host, port, client_id, destination, username, password, filter='.*\\..*'):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.destination = destination
        self.username = username
        self.password = password
        self.filter = filter
        self.client = Client()
        self.process_func = None

    def connect(self):
        self.client.connect(host=self.host, port=self.port)
        self.client.check_valid(username=self.username.encode(), password=self.password.encode())
        self.client.subscribe(client_id=str(self.client_id).encode(), destination=self.destination.encode(), filter=self.filter.encode())

    def disconnect(self):
        self.client.disconnect()
        print("成功与数据库断开连接")

    def set_process_func(self, process_func):
        self.process_func = process_func

    def process_entries(self, entries):
        for entry in entries:
            entry_type = entry.entryType
            if entry_type in [EntryProtocol_pb2.EntryType.TRANSACTIONBEGIN, EntryProtocol_pb2.EntryType.TRANSACTIONEND]:
                continue
            row_change = EntryProtocol_pb2.RowChange()
            row_change.MergeFromString(entry.storeValue)
            event_type = row_change.eventType
            header = entry.header
            database = header.schemaName
            table = header.tableName
            for row in row_change.rowDatas:
                format_data = dict()
                if event_type == EntryProtocol_pb2.EventType.DELETE:
                    for column in row.beforeColumns:
                        format_data[column.name] = column.value
                elif event_type == EntryProtocol_pb2.EventType.INSERT:
                    for column in row.afterColumns:
                        format_data[column.name] = column.value
                else:
                    format_data['before'] = {column.name: column.value for column in row.beforeColumns}
                    format_data['after'] = {column.name: column.value for column in row.afterColumns}
                data = dict(
                    db=database,
                    table=table,
                    event_type=event_type,
                    data=format_data,
                )
                self.process_func(data)
                

    def start(self):
        try:
            while True:
                message = self.client.get(100)
                entries = message['entries']
                self.process_entries(entries)
                time.sleep(1)
        except KeyboardInterrupt:
            print("Interrupted by user")
        finally:
            self.disconnect()


# def run_canal_client():
#     canal_client = CanalClient(
#         host = '127.0.0.1',
#         port = 11111,
#         client_id = 1001,
#         destination = 'gmcommand',
#         username = 'root',
#         password = '123456',
#     )
#     def do_nothing(data):print(data)
#     canal_client.set_process_func(do_nothing)
#     canal_client.connect()
#     canal_client.start()


# if __name__ == "__main__":
#     run_canal_client()
    # 启动子线程运行Canal Client
    # canal_thread = threading.Thread(target=run_canal_client)
    # canal_thread.start()