#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单的数据库操作演示
"""

import threading
from client import Client

def simple_demo():
    """最简单的数据库演示"""
    client = Client('KevinCA.crt')

    try:
        print("连接服务器...")
        client.socket.connect('127.0.0.1', 1443)

        # 启动响应处理
        response_thread = threading.Thread(target=client.handle_responses)
        response_thread.daemon = True
        response_thread.start()

        time.sleep(1)  # 等待连接稳定

        print("\n=== 数据库操作演示 ===")

        # 1. 创建用户
        print("\n1. 创建用户...")
        try:
            msg_id, reply, _ = client.send_message(
                'user_create alice alice@example.com alice123 "Alice Smith" 25 "测试用户"',
                wait_for_reply=True,
                timeout=5.0
            )
            print(f"结果: {reply}")
        except Exception as e:
            print(f"创建失败: {e}")

        # 2. 查询用户
        time.sleep(1)
        print("\n2. 查询用户...")
        try:
            msg_id, reply, _ = client.send_message('user_get alice', wait_for_reply=True, timeout=5.0)
            print(f"结果: {reply}")
        except Exception as e:
            print(f"查询失败: {e}")

        print("\n=== 演示完成 ===")

    except Exception as e:
        print(f"演示失败: {e}")
    finally:
        client.running = False
        client.socket.close()

if __name__ == '__main__':
    import time
    simple_demo()