#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库CRUD功能测试客户端
演示如何使用客户端命令来操作数据库
"""

import threading
import time
from client import Client

def test_database_operations():
    """测试数据库CRUD操作"""
    # 创建客户端实例
    client = Client('KevinCA.crt')

    try:
        print("正在连接服务器...")
        client.socket.connect('127.0.0.1', 1443)
        print("已连接到服务器")

        # 启动响应处理线程
        response_thread = threading.Thread(target=client.handle_responses)
        response_thread.daemon = True
        response_thread.start()

        # 等待欢迎消息
        time.sleep(1)

        print("\n" + "="*60)
        print("开始测试数据库CRUD功能")
        print("="*60)

        # 1. 测试创建用户
        print("\n[测试1] 创建用户")
        test_users = [
            ("alice", "alice@example.com", "alice123", "Alice Smith", "25", "这是一个测试用户Alice"),
            ("bob", "bob@example.com", "bob123", "Bob Johnson", "30", "这是一个测试用户Bob"),
            ("charlie", "charlie@example.com", "charlie123", "Charlie Brown", "28", "这是一个测试用户Charlie")
        ]

        created_user_ids = []
        for i, user_data in enumerate(test_users, 1):
            print(f"\n创建用户 {i}: {user_data[0]}")
            message = f"user_create {' '.join(user_data)}"

            try:
                msg_id, reply, _ = client.send_message(message, wait_for_reply=True, timeout=10.0)
                print(f"回复: {reply}")

                # 从回复中提取用户ID (如果创建成功)
                if "用户创建成功! ID:" in reply:
                    import re
                    match = re.search(r'ID: (\d+)', reply)
                    if match:
                        created_user_ids.append(int(match.group(1)))

            except TimeoutError:
                print(f"创建用户超时")
            except Exception as e:
                print(f"创建用户错误: {e}")

            time.sleep(1)

        # 2. 测试查询所有用户
        print("\n\n[测试2] 查询所有用户")
        try:
            msg_id, reply, _ = client.send_message("user_get", wait_for_reply=True, timeout=10.0)
            print(f"所有用户信息:\n{reply}")
        except TimeoutError:
            print(f"查询所有用户超时")

        time.sleep(1)

        # 3. 测试查询特定用户
        if created_user_ids:
            print(f"\n\n[测试3] 查询特定用户 (ID: {created_user_ids[0]})")
            try:
                msg_id, reply, _ = client.send_message(f"user_get {created_user_ids[0]}", wait_for_reply=True, timeout=10.0)
                print(f"查询结果:\n{reply}")
            except TimeoutError:
                print(f"查询特定用户超时")

            time.sleep(1)

            print(f"\n\n[测试4] 按用户名查询用户 (alice)")
            try:
                msg_id, reply, _ = client.send_message("user_get alice", wait_for_reply=True, timeout=10.0)
                print(f"查询结果:\n{reply}")
            except TimeoutError:
                print(f"按用户名查询超时")

            time.sleep(1)

        # 4. 测试更新用户
        if created_user_ids:
            print(f"\n\n[测试5] 更新用户 (ID: {created_user_ids[0]})")
            try:
                # 更新姓名和年龄
                msg_id, reply, _ = client.send_message(
                    f"user_update {created_user_ids[0]} full_name 'Alice Wonderland' age 26 email alice.updated@example.com",
                    wait_for_reply=True,
                    timeout=10.0
                )
                print(f"更新结果:\n{reply}")
            except TimeoutError:
                print(f"更新用户超时")
            except Exception as e:
                print(f"更新用户错误: {e}")

            time.sleep(1)

        # 5. 测试删除用户（删除最后一个创建的用户）
        if created_user_ids:
            print(f"\n\n[测试6] 删除用户 (ID: {created_user_ids[-1]})")
            try:
                msg_id, reply, _ = client.send_message(f"user_delete {created_user_ids[-1]}", wait_for_reply=True, timeout=10.0)
                print(f"删除结果:\n{reply}")
            except TimeoutError:
                print(f"删除用户超时")

            time.sleep(1)

        # 6. 再次查询所有用户，确认删除成功
        print("\n\n[测试7] 再次查询所有用户（确认删除成功）")
        try:
            msg_id, reply, _ = client.send_message("user_get", wait_for_reply=True, timeout=10.0)
            print(f"剩余用户:\n{reply}")
        except TimeoutError:
            print(f"查询所有用户超时")

        # 7. 显示帮助信息
        print("\n\n[测试8] 显示帮助信息")
        try:
            msg_id, reply, _ = client.send_message("help", wait_for_reply=True, timeout=10.0)
            print(f"帮助信息:\n{reply}")
        except TimeoutError:
            print(f"获取帮助超时")

        print("\n" + "="*60)
        print("数据库CRUD功能测试完成!")
        print("="*60)

        # 保持连接一段时间，让用户查看结果
        print("\n按 Ctrl+C 退出...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n测试结束")

    except KeyboardInterrupt:
        print("\n测试被中断")
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.running = False
        client.socket.close()
        print("客户端已关闭")

def simple_demo():
    """简单的数据库演示"""
    client = Client('KevinCA.crt')

    try:
        client.socket.connect('127.0.0.1', 1443)
        response_thread = threading.Thread(target=client.handle_responses)
        response_thread.daemon = True
        response_thread.start()

        # 简单演示
        print("简化的数据库操作演示")
        print("-" * 40)

        # 创建用户
        print("1. 创建用户...")
        try:
            msg_id, reply, _ = client.send_message('user_create testuser test@example.com pass123 "Test User" 25 "测试用户"', wait_for_reply=True, timeout=5.0)
            print(f"创建结果: {reply}")
        except:
            print("创建用户命令失败")

        time.sleep(1)

        # 查询用户
        print("\n2. 查询用户...")
        try:
            msg_id, reply, _ = client.send_message('user_get testuser', wait_for_reply=True, timeout=5.0)
            print(f"查询结果: {reply}")
        except:
            print("查询用户命令失败")

        print("\n演示结束")

    except Exception as e:
        print(f"连接失败: {e}")
    finally:
        client.running = False
        client.socket.close()

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'simple':
        simple_demo()
    else:
        test_database_operations()