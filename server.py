import socket
import threading
import pickle

SERVER_IP = "0.0.0.0" #테스트용 "127.0.0.1" 온라인 1ㄷ1 0.0.0.0<<< 좌표 수정
PORT = 5555

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    server.bind((SERVER_IP, PORT))
except socket.error as e:
    print(str(e))

server.listen(2)
print("서버가 시작되었습니다. 플레이어를 기다리는 중...")

clients = {}

def threaded_client(conn, player_id):
    global clients
    other_player = 2 if player_id == 1 else 1

    # 처음 접속 시 역할 부여
    conn.send(pickle.dumps({"player_id": player_id}))

    while True:
        try:
            # 클라이언트의 행동을 기다림
            data = pickle.loads(conn.recv(4096))
            if not data:
                break

            # 클라이언트가 어떤 행동(action)을 보냈다면
            if data.get("action"):
                if other_player in clients:
                    try:
                        clients[other_player].sendall(pickle.dumps({"messages": [data]}))
                    except Exception as e:
                        print(f"전송 에러: {e}")

        except Exception as e:
            break

    print(f"플레이어 {player_id} 연결 종료")
    if player_id in clients:
        del clients[player_id]
    conn.close()

current_player = 1
while True:
    conn, addr = server.accept()
    print(f"[{addr}] 연결됨 - Player {current_player}")
    clients[current_player] = conn
    threading.Thread(target=threaded_client, args=(conn, current_player)).start()
    current_player += 1