import bluetooth
import threading
import hashlib
import json
import sys
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# 创建RSA密钥对
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()

running = True  # 全局标志，控制程序运行状态

# 将公钥转换为可传输的字符串
def serialize_public_key(pub_key):
    return pub_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

# 处理公钥并返回SHA1
def process_public_key(pub_key):
    sha1_hash = hashlib.sha1(pub_key.encode('utf-8')).hexdigest()
    return sha1_hash

# 接收客户端数据
def receive_data(client_sock):
    global running
    try:
        # 发送等待信号
        client_sock.send("waiting".encode('utf-8'))

        # 接收客户端公钥
        data = client_sock.recv(1024).decode('utf-8')
        if data:
            print(f"接收到的公钥: {data}")
            client_data = json.loads(data)
            client_pub_key = client_data["public_key"]

            # 处理客户端的公钥
            client_hashed_key = process_public_key(client_pub_key)
            print(f"客户端公钥SHA1: {client_hashed_key}")

            # 保存到白名单
            with open("whitelist.txt", "a") as f:
                f.write(f"{client_pub_key}\n{client_hashed_key}\n")

            # 返回处理过的公钥
            response = json.dumps({"hashed_key": client_hashed_key})
            client_sock.send(response.encode('utf-8'))

        else:
            print("客户端已断开连接。")
    except OSError:
        pass

# 发送数据到客户端
def send_data(client_sock):
    global running
    try:
        while running:
            message = input("服务端输入消息: ")
            if message.lower() == 'exit':  # 输入 exit 可以安全关闭
                running = False
                break
            client_sock.send(message.encode('utf-8'))  # 确保发送的是字节类型
    except EOFError:
        print("输入流已关闭，停止发送数据。")
    except OSError:
        pass
    finally:
        print("关闭连接")
        client_sock.close()
        sys.exit(0)  # 退出程序

# 蓝牙服务端
def bluetooth_server():
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    server_sock.bind(("", 4))
    server_sock.listen(1)

    print("等待连接，服务在端口 4 上...")

    bluetooth.advertise_service(server_sock, "BluetoothServer",
                                service_classes=[bluetooth.SERIAL_PORT_CLASS],
                                profiles=[bluetooth.SERIAL_PORT_PROFILE])

    client_sock, client_info = server_sock.accept()
    print(f"连接自 {client_info}")

    # 线程处理接收与发送
    receive_thread = threading.Thread(target=receive_data, args=(client_sock,))
    send_thread = threading.Thread(target=send_data, args=(client_sock,))

    receive_thread.start()
    #send_thread.start()

    receive_thread.join()
    #send_thread.join()

    print("关闭连接")
    client_sock.close()
    server_sock.close()

if __name__ == '__main__':
    bluetooth_server()
