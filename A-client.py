import bluetooth
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, padding, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from secrets import token_bytes

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

def bluetooth_client(server_mac_address):
    client_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

    try:
        print(f"连接到 {server_mac_address}")
        client_sock.connect((server_mac_address, 4))
        print("连接成功")

        # 发送请求信息
        client_sock.send("请求开始认证".encode('utf-8'))

        # 接受服务端状态
        server_status = client_sock.recv(1024)
        print(f"服务端状态: {server_status.decode('utf-8')}")
        if server_status.decode('utf-8') != "认证开始":
            print("服务端拒绝认证")
            return

        # 开始 ECDH 密钥交换
        alice = DiffieHellman()

        # 发送 Alice 的公钥给服务器
        client_sock.send(alice.get_public_key_bytes())
        print("已发送客户端公钥")

        # 接收服务器的公钥
        server_public_key_bytes = client_sock.recv(1024)
        print("已接收服务器公钥")

        # 生成共享密钥
        shared_key = alice.derive_shared_key(server_public_key_bytes)
        print("共享密钥已生成")

        # 使用AES-CBC生成密文A
        message_a = "认证成功"
        encrypted_message_a = alice.encrypt(shared_key, message_a.encode('utf-8'))
        client_sock.send(encrypted_message_a)
        print(f"发送加密消息A: {encrypted_message_a}")

        # 接受服务器的token G
        encrypted_token_g = client_sock.recv(1024)
        token_g = alice.decrypt(shared_key, encrypted_token_g).decode('utf-8')
        print(f"收到服务器token G: {token_g}")

        # 获取自己的AGPS数据
        agps_data = (34.0500, -118.2425)  # 示例：客户端的AGPS坐标

        # 使用 token G 和计数器生成并发送消息B，agps数据也包含在内
        message_b = f"{token_g}; count=2 ; agps_data={agps_data}"
        encrypted_message_b = alice.encrypt(shared_key, message_b.encode('utf-8'))
        client_sock.send(encrypted_message_b)
        print(f"发送加密消息B: {encrypted_message_b}")

        # 接收最终确认
        encrypted_confirmation = client_sock.recv(1024)
        final_confirmation = alice.decrypt(shared_key, encrypted_confirmation).decode('utf-8')
        print(f"最终确认: {final_confirmation}")

    except bluetooth.BluetoothError as e:
        print(f"蓝牙连接失败: {e}")
    finally:
        client_sock.close()

if __name__ == '__main__':
    server_mac_address = "70:A8:D3:8F:43:B3"  # 修改为服务器的 MAC 地址
    bluetooth_client(server_mac_address)
