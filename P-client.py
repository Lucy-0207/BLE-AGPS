import bluetooth
import hashlib
import json
import sys
import time
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

# 创建RSA密钥对
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()

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

# 保存MAC地址到文件
def save_mac_address_to_file(mac_address):
    try:
        with open("蓝牙地址表.txt", "a") as file:
            file.write(f"{mac_address}\n")
        print(f"MAC地址 {mac_address} 已保存到文件 '蓝牙地址表.txt'")
    except Exception as e:
        print(f"保存MAC地址失败: {e}")

# 蓝牙客户端
def bluetooth_client(server_mac_address):
    # 创建一个蓝牙套接字
    client_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

    try:
        print(f"连接到 {server_mac_address}")
        client_sock.connect((server_mac_address, 4))
        print("连接成功")

        # 等待服务端的等待信号
        data = client_sock.recv(1024).decode('utf-8')
        if data == "waiting":
            print("收到等待信号，准备发送公钥")

            # 发送公钥给服务端
            serialized_key = serialize_public_key(public_key)
            client_sock.send(json.dumps({"public_key": serialized_key}).encode('utf-8'))

            # 接收服务端处理后的公钥(SHA1)
            data = client_sock.recv(1024).decode('utf-8')
            received_data = json.loads(data)
            server_hashed_key = received_data["hashed_key"]
            print(f"收到服务端的SHA1公钥: {server_hashed_key}")

            # 客户端自己计算SHA1并进行验证
            client_hashed_key = process_public_key(serialized_key)
            if client_hashed_key == server_hashed_key:
                print("认证成功，公钥一致")

                # 保存服务器MAC地址到文件
                save_mac_address_to_file(server_mac_address)

                # 使用私钥加密简短消息 (认证成功)
                current_time = int(time.time())
                message = f"{current_time},ok"  # 添加时间戳
                encrypted_message = private_key.encrypt(
                    message.encode('utf-8'),
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )

                # 发送加密消息给服务端
                client_sock.send(encrypted_message)
                print("已发送加密消息给服务端")

        print("客户端任务完成，关闭连接")

    except bluetooth.BluetoothError as e:
        print(f"蓝牙连接失败: {e}")
    except OSError:
        print("连接已关闭或出错。")
    finally:
        client_sock.close()
        sys.exit(0)

if __name__ == '__main__':
    # 替换为服务器设备的MAC地址
    server_mac_address = "70:A8:D3:8F:43:B3"  # 修改为实际的MAC地址
    bluetooth_client(server_mac_address)
