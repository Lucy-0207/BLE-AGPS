# 基于定位系统的无钥匙安全进入方案
## 目录
### `P-client.py` 配对客户端代码(y已更新扫描功能)
### `P-sercer.py` 配对服务端代码
### `A-client.py` 认证客户端代码(添加AGPS)
### `A-sercer.py` 认证服务端代码(添加AGPS)
### `A-client-noGPS.py` 认证客户端代码
### `A-sercer-noGPS.py` 认证服务端代码
### `blue_scan.cpp` 客户端扫描蓝牙设备

## 实现情况

### 配对：
* 服务端：白名单存储成txt形式在本地
![服务端](img/f96a513616ad42ea6838814569893ea.png)
* 客户端：将认证成功的服务器mac地址存入txt中
![客户端](img/07a6d6ac27527a8058392bbdbf9dd85.png)

### 认证：加密算法更改为AES-CBC
* 服务端：
![服务端](img/image.png)
* 客户端：
![客户端](img/26ed2c20fb6e3e5e5188d765fb03487.png)

### 加上AGPS：
#### 车钥匙key与车距离在连接范围内，认证通过
* 服务端
  ![alt text](img/8228b88137f077f2ba95b5fd47153edf_.png)
* 客户端
  ![alt text](img/bdf779273582795b86b6db64484aeed7_.png)

#### 车钥匙key与车距离超出连接范围，认证失败
* 服务端：
  ![alt text](img/96273c694c4656ce7252fb78b184c983_.png)
* 客户端：
![alt text](img/7f5cb0f1b66824ef79993f0aacd89652_.png)