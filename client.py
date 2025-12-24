#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/12/21 15:47
# @Author  : Kevin Chang
# @File    : client.py
# @Software: PyCharm
import json
import os
import queue
import socket
import ssl
import threading
import time
import traceback
import uuid


class SecureClientSocket:
    def __init__(self, ca_cert_path=None):
        # 创建一个普通的 TCP 套接字
        self.tls_sock = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 包装套接字以使用 TLS
        if ca_cert_path and os.path.exists(ca_cert_path):
            # 只信任指定CA颁发的证书
            self.context = ssl.create_default_context(cafile=ca_cert_path)
        else:
            # 使用系统默认的证书存储
            self.context = ssl.create_default_context()
            if ca_cert_path:
                print(f"Warning: CA certificate file {ca_cert_path} not found, using system defaults")

    def connect(self, hostname: str, port: int):
        # 创建套接字
        self.tls_sock = self.context.wrap_socket(self.sock, server_hostname=hostname)
        # 连接
        self.tls_sock.connect((hostname, port))

    def close(self):
        # 关闭
        if self.tls_sock:
            self.tls_sock.close()

    def send(self, data: str):
        # 发送数据
        if self.tls_sock:
            self.tls_sock.sendall(len(data).to_bytes(4, 'big') + data.encode())

    def recv(self) -> str:
        # 接收数据
        if self.tls_sock:
            size = int.from_bytes(self.tls_sock.recv(4), 'big')
            return self.tls_sock.recv(size).decode()
        raise ConnectionResetError


class Client:
    def __init__(self, ca_cert_path: str = None):
        self.socket: SecureClientSocket = SecureClientSocket(ca_cert_path)
        self.message_send_queue: queue.Queue = queue.Queue()  # (message_id, message_content)
        self.pending_messages: dict = {}  # message_id -> (content, timestamp, callback, event, response)
        self.response_handlers: queue.Queue = queue.Queue()  # (message_id, response_content)
        self.running = True
        self.lock = threading.Lock()

    def send_message(self, message: str, callback=None, wait_for_reply=True, timeout=30.0):
        """发送消息并根据参数决定是否等待响应"""
        message_id = str(uuid.uuid4())[:8]  # 生成消息ID

        # 创建消息包
        message_packet = {
            'id': message_id,
            'content': message,
            'timestamp': time.time()
        }

        # 如果需要同步等待，创建事件对象
        event = threading.Event() if wait_for_reply else None

        with self.lock:
            self.pending_messages[message_id] = (message, time.time(), callback, event, None)

        # 发送到服务器
        self.socket.send(json.dumps(message_packet))

        # 如果需要同步等待回复
        if wait_for_reply and event:
            if event.wait(timeout):  # 等待回复或超时
                with self.lock:
                    _, _, _, _, response = self.pending_messages.pop(message_id, (None, None, None, None, None))
                    if response:
                        return message_id, response['content'], response
                    else:
                        return message_id, None, None
            else:
                # 超时处理
                with self.lock:
                    self.pending_messages.pop(message_id, None)
                raise TimeoutError(f"消息 {message_id} 等待回复超时")

        return message_id

    def handle_responses(self):
        """处理服务器响应的线程"""
        while self.running:
            try:
                response_data = self.socket.recv()
                if response_data:
                    response_packet = json.loads(response_data)
                    message_id = response_packet.get('id')
                    content = response_packet.get('content')

                    if message_id and message_id in self.pending_messages:
                        with self.lock:
                            original_message, timestamp, callback, event, _ = self.pending_messages[message_id]
                            # 保存响应到pending_messages以便同步获取
                            self.pending_messages[message_id] = (original_message, timestamp, callback, event,
                                                                 response_packet)

                        # print(f"收到回复 [ID:{message_id}]: {content}")
                        # print(f"原始消息: {original_message}")

                        if callback:
                            callback(message_id, content)
                        else:
                            self.response_handlers.put((message_id, content))

                        # 如果是同步等待模式，触发事件
                        if event:
                            event.set()
                    elif message_id == 'welcome':
                        pass
                    else:
                        print(f"收到未知或无匹配的消息 [ID:{message_id}]: {content}")

            except Exception as e:
                if self.running:
                    print(f"响应处理错误: {e}")
                break

    def run(self):
        try:
            self.socket.connect('192.168.10.30', 1443)
            # 启动响应处理线程
            response_thread = threading.Thread(target=self.handle_responses)
            response_thread.daemon = True
            response_thread.start()

            print("客户端已连接，请输入消息 (输入 'bye' 退出):")

            while self.running:
                # 从用户输入获取消息
                user_input = input("> ")
                if user_input.lower() == 'bye':
                    self.running = False
                    break

                if user_input.strip():
                    # 发送消息
                    # parse_command(user_input)
                    message_id, reply_content, full_response = self.send_message(user_input)
                    # print(f"发送消息 [ID:{message_id}]: {user_input} 回复: {reply_content}")
                    print(f"消息 [ID:{message_id}] 回复: {reply_content}")
        except ssl.SSLEOFError:
            print("服务器已关闭连接")
            self.running = False
            self.socket.close()

        except Exception as e:
            print(f"客户端错误: {e}")
            print(traceback.format_exc())
        finally:
            self.running = False
            self.socket.close()

    def reply_message(self, message):
        """直接向服务器发送消息（无ID，用于兼容原有逻辑）"""
        self.socket.send(json.dumps({'content': message}))


def run():
    # 使用指定CA证书路径初始化客户端
    client = Client('KevinCA.crt')  # 使用项目根目录下的KevinCA.crt
    client.run()


if __name__ == '__main__':
    run()
