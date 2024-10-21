import bluetooth
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, padding, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from secrets import token_bytes
import math

class DiffieHellman:
    def __init__(self):
        # 生成私钥和公钥
        self.diffieHellman = ec.generate_private_key(ec.SECP384R1(), default_backend())
        self.public_key = self.diffieHellman.public_key()

    def get_public_key_bytes(self):
        # 将公钥序列化为字节
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )

    def derive_shared_key(self, peer_public_key_bytes):
        # 从字节恢复公钥
        peer_public_key = ec.EllipticCurvePublicKey.from_encoded_point(
            ec.SECP384R1(), peer_public_key_bytes
        )
        # 生成共享密钥
        shared_key = self.diffieHellman.exchange(ec.ECDH(), peer_public_key)
        # 使用 HKDF 派生出对称加密密钥
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=None,
            backend=default_backend()
        ).derive(shared_key)
        return derived_key

    def encrypt(self, key, plaintext):
        # 生成随机初始化向量
        iv = token_bytes(16)
        # AES-CBC 加密
        aes = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = aes.encryptor()
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(plaintext) + padder.finalize()
        return iv + encryptor.update(padded_data) + encryptor.finalize()  # 发送 IV 和密文

    def decrypt(self, key, ciphertext):
        # 从密文中提取 IV
        iv = ciphertext[:16]  # 提取前 16 字节作为 IV
        encrypted_data = ciphertext[16:]  # 剩余部分为密文
        # AES-CBC 解密
        aes = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = aes.decryptor()
        decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        return unpadder.update(decrypted_data) + unpadder.finalize()

def haversine(lon1, lat1, lon2, lat2):
    R = 6371  # 地球半径，单位：公里
    dlon = math.radians(lon2 - lon1)
    dlat = math.radians(lat2 - lat1)

    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance


def bluetooth_server():
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    server_sock.bind(("", 4))
    server_sock.listen(1)
    print("等待客户端连接...")

    try:
        client_sock, address = server_sock.accept()
        print(f"已连接客户端: {address}")

        # 接收客户端请求
        request = client_sock.recv(1024)
        print(f"客户端请求: {request.decode('utf-8')}")

        # 发送确认状态
        client_sock.send("认证开始".encode('utf-8'))

        # 开始 ECDH 密钥交换
        bob = DiffieHellman()

        # 接收客户端公钥
        client_public_key_bytes = client_sock.recv(1024)
        print("已接收客户端公钥")

        # 发送服务器公钥
        client_sock.send(bob.get_public_key_bytes())
        print("已发送服务器公钥")

        # 生成共享密钥
        shared_key = bob.derive_shared_key(client_public_key_bytes)
        print("共享密钥已生成")

        # 接收并解密客户端的消息A
        encrypted_message_a = client_sock.recv(1024)
        decrypted_message_a = bob.decrypt(shared_key, encrypted_message_a)
        print(f"收到客户端消息A: {decrypted_message_a.decode('utf-8')}")

        # 生成 token G 并发送
        token_g = "tokenG"
        encrypted_token_g = bob.encrypt(shared_key, token_g.encode('utf-8'))
        client_sock.send(encrypted_token_g)
        print(f"发送token G: {encrypted_token_g}")

        # 获取自己的agps数据
        own_agps_data = (34.0522, -118.2437)  # 示例：此为服务器的AGPS坐标

        # 接收并解密客户端的消息B
        encrypted_message_b = client_sock.recv(1024)
        decrypted_message_b = bob.decrypt(shared_key, encrypted_message_b)
        decrypted_message_str = decrypted_message_b.decode('utf-8')
        print(f"收到客户端消息B: {decrypted_message_str}")

        # 确保消息格式正确再进行解析
        try:
            # 提取 token G 和 AGPS 数据
            parts = decrypted_message_str.split(";")
            token_g_received = parts[0]  # 提取 token G
            # 输出tokenG
            print(f"收到token G: {token_g_received}")
            count = int(parts[1].split('=')[1])  # 提取计数器
            # 输出计数器
            print(f"收到计数器: {count}")
            agps_data_str = parts[2].split('=')[1]  # 提取 AGPS 数据部分
            # 输出AGPS数据
            print(f"收到AGPS数据: {agps_data_str}")

            # 将 AGPS 数据字符串转换为元组
            client_agps_data = tuple(map(float, agps_data_str.strip("()").split(",")))
            print(f"客户端AGPS数据: {client_agps_data}")

            # 计算距离
            distance = haversine(own_agps_data[1], own_agps_data[0], client_agps_data[1], client_agps_data[0])
            print(f"车辆与钥匙扣之间的距离: {distance:.2f} 千米")

            # 验证客户端的 tokenG 和距离
            if token_g_received == "tokenG" and distance <= 0.03:  # 假设有效距离为30米
                print("客户端消息验证成功，认证完成")
                final_confirmation = "认证完成"
            else:
                print("客户端消息验证失败或距离超出范围")
                final_confirmation = "认证失败"

        except (IndexError, ValueError) as e:
            print("消息格式不正确，无法解析AGPS数据。", e)
            final_confirmation = "认证失败"

        # 发送最终确认消息
        encrypted_final_confirmation = bob.encrypt(shared_key, final_confirmation.encode('utf-8'))
        client_sock.send(encrypted_final_confirmation)
        print(f"发送最终确认: {encrypted_final_confirmation}")



    except bluetooth.BluetoothError as e:
        print(f"蓝牙连接失败: {e}")
    finally:
        client_sock.close()
        server_sock.close()

if __name__ == '__main__':
    bluetooth_server()
