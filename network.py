# network.py
import socket
import pickle
import threading
import queue


class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = "25.1.148.132" #테스트용 "127.0.0.1" my ip 25.1.148.132
        self.port = 5555
        self.addr = (self.server, self.port)

        self.recv_queue = queue.Queue()

        # 접속 시 첫 번째 데이터를 받아와서 저장합니다.
        self.initial_data = self.connect()

        self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receive_thread.start()

    def connect(self):
        try:
            self.client.connect(self.addr)
            data = pickle.loads(self.client.recv(4096))
            print(f"서버 연결 성공! 내 정보: {data}")
            return data
        except Exception as e:
            print(f"서버 연결 실패. 서버가 켜져 있는지 확인하세요: {e}")
            return {}

    def _receive_loop(self):
        while True:
            try:
                data = pickle.loads(self.client.recv(4096))
                if data:
                    self.recv_queue.put(data)
            except Exception as e:
                print(f"서버 연결 끊김: {e}")
                break

    def send(self, data):
        try:
            if data.get("action") is not None:
                self.client.send(pickle.dumps(data))

            # 2. 수신 우체통에 도착한 메시지가 있는지 확인하고 모두 꺼내옵니다.
            messages = []
            while not self.recv_queue.empty():
                msg_pack = self.recv_queue.get_nowait()
                if "messages" in msg_pack:
                    messages.extend(msg_pack["messages"])

            return {"messages": messages}

        except socket.error as e:
            print(f"통신 에러: {e}")
            return {"messages": []}