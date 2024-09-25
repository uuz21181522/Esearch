import subprocess
import signal
import time
import atexit

# 启动 Waitress 实例的命令
commands = [
    ["waitress-serve", "--port=5001", "Flask:app"],
    ["waitress-serve", "--port=5002", "Flask:app"],
    ["waitress-serve", "--port=5003", "Flask:app"],
    ["waitress-serve", "--port=5004", "Flask:app"],
    ["waitress-serve", "--port=5005", "Flask:app"],
    ["waitress-serve", "--port=5006", "Flask:app"],
    ["waitress-serve", "--port=5007", "Flask:app"],
    ["waitress-serve", "--port=5008", "Flask:app"],
]

# 存储子进程
processes = []

def start_processes():
    for command in commands:
        process = subprocess.Popen(command)
        processes.append(process)
        print(f"Started process {process.pid} with command: {' '.join(command)}")

def kill_processes():
    for process in processes:
        print(f"Terminating process {process.pid}")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print(f"Process {process.pid} did not terminate in time, killing it")
            process.kill()

# 注册退出时的清理函数
atexit.register(kill_processes)

if __name__ == "__main__":
    start_processes()
    try:
        # 保持主程序运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Received KeyboardInterrupt, exiting...")