#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/12/21 15:47
# @Author  : Kevin Chang
# @File    : server.py
# @Software: PyCharm
import json
import os
import socket
import ssl
import threading
from typing import Any

from command_parser import parse_command
from database_models import get_db_manager


class SecureServerSocket:
    def __init__(self, hostname: str, port: int, certfile: str, keyfile: str):
        # 创建一个普通的 TCP 套接字
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((hostname, port))
        self.sock.listen(1)

        # 检查证书和密钥文件是否存在
        if not os.path.exists(certfile):
            raise FileNotFoundError(f"Certificate file {certfile} not found")
        if not os.path.exists(keyfile):
            raise FileNotFoundError(f"Key file {keyfile} not found")

        # 创建 SSL 上下文并加载证书
        self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.context.load_cert_chain(certfile=certfile, keyfile=keyfile)

    def close(self):
        # 关闭
        self.sock.close()


class SecureReceivedSocket:
    def __init__(self, tls_socket: ssl.SSLSocket):
        self.tls_socket = tls_socket

    def recv(self) -> str:
        # 接收数据
        raw_size = self.tls_socket.recv(4)
        size = int.from_bytes(raw_size, 'big')
        # print(f"接收数据 : {raw_size} bytes")
        return self.tls_socket.recv(size).decode()

    def send(self, data: str):
        # 发送数据
        self.tls_socket.sendall(len(data).to_bytes(4, 'big') + data.encode())

    def close(self):
        # 关闭
        self.tls_socket.close()


class Server:
    def __init__(self):
        self.socket = SecureServerSocket('0.0.0.0', 1443, 'fullchain.crt', '192.168.10.30.pem')
        self.name = 'server'
        self.db_manager = get_db_manager()  # 初始化数据库管理器

    def service_thread(self):
        try:
            print(f"Server listening on {self.socket.sock.getsockname()[0]}:{self.socket.sock.getsockname()[1]}")
            while True:
                # 接受连接
                conn, addr = self.socket.sock.accept()
                print(f"Connection accepted from {addr}")
                # 使用预先配置好的SSL上下文
                tls_sock = self.socket.context.wrap_socket(conn, server_side=True)
                threading.Thread(target=self.handle_client, args=(SecureReceivedSocket(tls_sock),)).start()
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            # 关闭
            self.socket.close()

    def handle_client(self, client_socket: SecureReceivedSocket):
        message_id = ""
        try:
            # 发送欢迎消息（带ID）
            welcome_packet = {
                'id': 'welcome',
                'content': f'hello, this is {self.name}'
            }
            # client_socket.send(json.dumps(welcome_packet))

            while True:
                # 接收数据
                data = client_socket.recv()
                if not data:
                    break

                try:
                    # 解析JSON格式的消息
                    message_packet = json.loads(data)
                    # print(f"收到客户端消息 [ID:{message_packet.get('id', 'unknown')}]: {message_packet.get('content', '')}")

                    # 如果是bye消息（兼容旧格式）
                    if isinstance(message_packet, dict) and message_packet.get('content') == 'bye':
                        response_packet = {
                            'id': message_packet.get('id', 'unknown'),
                            'content': 'Goodbye!'
                        }
                        client_socket.send(json.dumps(response_packet))
                        client_socket.close()
                        break

                    # 处理带ID的消息
                    if isinstance(message_packet, dict) and 'content' in message_packet:
                        message_id = message_packet.get('id', 'unknown')
                        content = message_packet['content']

                        print(f"收到客户端消息 [ID:{message_id}]: {content}")

                        try:
                            # 构建回复消息（保持相同的ID以便客户端匹配）
                            response_packet: dict[str, Any] = self.get_response_message(message_id, content)
                        except Exception as e:
                            print(f"处理消息错误: {e}")
                            response_packet = {
                                'id': message_id,
                                'content': f'处理消息错误 {e}'
                            }
                        client_socket.send(json.dumps(response_packet))
                        print(f"发送回复 [ID:{message_id}]: {response_packet['content']}")

                    else:
                        # 兼容旧的无ID格式
                        if data == 'bye':
                            client_socket.close()
                            break
                        client_socket.send(data)

                except json.JSONDecodeError:
                    # 处理非JSON格式的消息（兼容旧格式）
                    if data == 'bye':
                        client_socket.close()
                        break
                    client_socket.send(data)
        except ssl.SSLError as e:
            print(f"SSL错误: {e}")
            client_socket.close()
            pass
        except Exception as e:
            print(f"客户端处理错误: {e}")
        finally:
            client_socket.close()

    def get_response_message(self, message_id, content) -> dict[str, Any]:
        """
        根据消息ID和内容生成回复消息
        :param message_id: 消息ID
        :param content: 消息内容
        :return: 回复消息
        """
        result_content = ""
        command, args = parse_command(content)

        match command:
            case 'add':
                if len(args) >= 2:
                    try:
                        result = int(args[0]) + int(args[1])
                        result_content = f"计算结果: {result}"
                    except ValueError:
                        result_content = "错误: 参数必须是数字"
                else:
                    result_content = "错误: add命令需要两个数字参数"

            case 'sub':
                if len(args) >= 2:
                    try:
                        result = int(args[0]) - int(args[1])
                        result_content = f"计算结果: {result}"
                    except ValueError:
                        result_content = "错误: 参数必须是数字"
                else:
                    result_content = "错误: sub命令需要两个数字参数"

            # ===== 数据库 CRUD 命令 =====
            case 'user_create':
                if len(args) >= 3:
                    # user_create username email password [full_name] [age] [description]
                    username, email, password = args[0], args[1], args[2]
                    full_name = args[3] if len(args) > 3 else None
                    age = int(args[4]) if len(args) > 4 and args[4].isdigit() else None
                    description = args[5] if len(args) > 5 else None

                    result = self.db_manager.create_user(username, email, password, full_name, age, description)
                    if result['success']:
                        user_data = result['data']
                        result_content = f"用户创建成功! ID: {user_data['id']}, 用户名: {user_data['username']}"
                    else:
                        result_content = f"用户创建失败: {result.get('message', '未知错误')}"
                else:
                    result_content = "错误: user_create 需要至少3个参数 (username email password)"

            case 'user_get':
                if len(args) >= 1:
                    # user_get [id/username] - 如果参数是数字则按ID查询，否则按用户名查询
                    search_term = args[0]
                    if search_term.isdigit():
                        result = self.db_manager.get_user(user_id=int(search_term))
                    else:
                        result = self.db_manager.get_user(username=search_term)

                    if result['success']:
                        if 'data' in result:
                            if isinstance(result['data'], list):
                                # 返回多个用户
                                users = result['data']
                                if users:
                                    result_content = "用户列表:\n"
                                    for user in users:
                                        result_content += f"  ID: {user['id']}, 用户名: {user['username']}, 邮箱: {user['email']}"
                                        if user['full_name']:
                                            result_content += f", 姓名: {user['full_name']}"
                                        if user['age']:
                                            result_content += f", 年龄: {user['age']}"
                                        result_content += "\n"
                                else:
                                    result_content = "没有找到任何用户"
                            else:
                                # 返回单个用户
                                user = result['data']
                                result_content = f"用户信息 - ID: {user['id']}\n"
                                result_content += f"  用户名: {user['username']}\n"
                                result_content += f"  邮箱: {user['email']}\n"
                                result_content += f"  姓名: {user.get('full_name', 'N/A')}\n"
                                result_content += f"  年龄: {user.get('age', 'N/A')}\n"
                                result_content += f"  创建时间: {user.get('created_at', 'N/A')}\n"
                                result_content += f"  更新时间: {user.get('updated_at', 'N/A')}\n"
                                if user.get('description'):
                                    result_content += f"  描述: {user['description']}"
                        else:
                            result_content = result.get('message', '未找到用户')
                    else:
                        result_content = f"查询失败: {result.get('message', '未知错误')}"
                else:
                    # 如果没有参数，查询所有用户
                    result = self.db_manager.get_user()
                    if result['success'] and 'data' in result:
                        users = result['data']
                        if users:
                            result_content = "所有用户:\n"
                            for user in users:
                                result_content += f"  ID: {user['id']}, 用户名: {user['username']}, 邮箱: {user['email']}"
                                if user['full_name']:
                                    result_content += f", 姓名: {user['full_name']}"
                                if user['age']:
                                    result_content += f", 年龄: {user['age']}"
                                result_content += "\n"
                        else:
                            result_content = "数据库中没有用户"
                    else:
                        result_content = "查询失败: " + result.get('message', '未知错误')

            case 'user_update':
                if len(args) >= 3:
                    # user_update id field1 value1 [field2 value2]...
                    user_id = int(args[0])
                    update_fields = {}

                    # 解析字段更新 (成对出现)
                    i = 1
                    while i + 1 < len(args):
                        field = args[i]
                        value = args[i + 1]

                        # 转换数据类型
                        if field == 'age':
                            value = int(value) if value.isdigit() else None
                        elif field in ['full_name', 'description', 'email', 'password']:
                            value = value if value != 'null' else None

                        update_fields[field] = value
                        i += 2

                    if update_fields:
                        result = self.db_manager.update_user(user_id, **update_fields)
                        if result['success']:
                            user_data = result['data']
                            result_content = f"用户更新成功! ID: {user_data['id']}, 用户名: {user_data['username']}"
                            if 'full_name' in update_fields:
                                result_content += f", 姓名: {user_data.get('full_name', 'N/A')}"
                            if 'age' in update_fields:
                                result_content += f", 年龄: {user_data.get('age', 'N/A')}"
                        else:
                            result_content = f"用户更新失败: {result.get('message', '未知错误')}"
                    else:
                        result_content = "错误: 没有提供要更新的字段"
                else:
                    result_content = "错误: user_update 需要至少3个参数 (id field value)"

            case 'user_delete':
                if len(args) >= 1:
                    # user_delete id
                    try:
                        user_id = int(args[0])
                        result = self.db_manager.delete_user(user_id)
                        if result['success']:
                            deleted_user = result['data']
                            result_content = f"用户删除成功! ID: {deleted_user['id']}, 用户名: {deleted_user['username']}"
                        else:
                            result_content = f"用户删除失败: {result.get('message', '未知错误')}"
                    except ValueError:
                        result_content = "错误: user_delete 的参数必须是数字ID"
                else:
                    result_content = "错误: user_delete 需要1个参数 (用户ID)"

            case 'help':
                # 显示帮助信息
                result_content = """可用命令列表:
=== 基础命令 ===
add num1 num2         - 加法运算
sub num1 num2         - 减法运算

=== 数据库操作命令 ===
user_create username email password [full_name] [age] [description] - 创建用户
user_get [id/username] - 查询用户（不带参数查询所有用户）
user_update id field1 value1 [field2 value2]... - 更新用户信息
user_delete id        - 删除用户

=== 其他命令 ===
bye                   - 断开连接
help                  - 显示此帮助信息"""

            case _:
                result_content = f"未知命令: {command}\n输入 'help' 查看可用命令列表"

        response_packet = {
            'id': message_id,
            'content': result_content
        }
        return response_packet


def run():
    try:
        server = Server()
        print("Starting server on 127.0.0.1:1443...")
        server.service_thread()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"Failed to start server: {e}")


if __name__ == '__main__':
    run()
