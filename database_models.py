#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库模型定义
使用SQLAlchemy ORM定义用户表和基本CRUD操作
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import json

Base = declarative_base()

class User(Base):
    """用户表模型"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    age = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    description = Column(Text, nullable=True)

    def to_dict(self):
        """将模型转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'age': self.age,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'description': self.description
        }

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

class DatabaseManager:
    """数据库管理器，提供CRUD操作"""

    def __init__(self, connection_string):
        """
        初始化数据库连接
        默认连接到本地的MariaDB数据库
        """
        try:
            if connection_string is None:
                connection_string = "mysql+pymysql://root:0d0c3cdcda2fe68a@127.0.0.1:3306/remnote"
            self.engine = create_engine(
                connection_string,
                echo=False,  # 设置为True可查看SQL语句
                pool_pre_ping=True,  # 连接池心跳检测
                pool_recycle=3600   # 连接回收时间
            )

            # 创建表
            Base.metadata.create_all(self.engine)

            # 创建会话工厂
            self.SessionLocal = sessionmaker(bind=self.engine)

            print(f"数据库连接成功: {connection_string}")

        except Exception as e:
            print(f"数据库连接失败: {e}")
            # 使用SQLite作为备选
            """
            try:
                print("尝试连接到SQLite数据库...")
                self.engine = create_engine("sqlite:///./myapp.db", echo=False)
                Base.metadata.create_all(self.engine)
                self.SessionLocal = sessionmaker(bind=self.engine)
                print("已连接到SQLite数据库: sqlite:///./myapp.db")
            except Exception as sqlite_error:
                raise Exception(f"数据库连接失败: MariaDB({e}), SQLite({sqlite_error})")
            """

    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()

    # === CRUD 操作 ===

    def create_user(self, username: str, email: str, password: str, full_name: str = None, age: int = None, description: str = None):
        """创建用户"""
        session = self.get_session()
        try:
            user = User(
                username=username,
                email=email,
                password=password,
                full_name=full_name,
                age=age,
                description=description
            )
            session.add(user)
            session.commit()
            return {"success": True, "data": user.to_dict(), "message": "用户创建成功"}
        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e), "message": "用户创建失败"}
        finally:
            session.close()

    def get_user(self, user_id: int = None, username: str = None):
        """查询用户"""
        session = self.get_session()
        try:
            if user_id:
                user = session.query(User).filter_by(id=user_id).first()
                if user:
                    return {"success": True, "data": user.to_dict(), "message": "用户查询成功"}
                else:
                    return {"success": False, "message": f"未找到ID为 {user_id} 的用户"}
            elif username:
                user = session.query(User).filter_by(username=username).first()
                if user:
                    return {"success": True, "data": user.to_dict(), "message": "用户查询成功"}
                else:
                    return {"success": False, "message": f"未找到用户名为 {username} 的用户"}
            else:
                users = session.query(User).all()
                return {"success": True, "data": [user.to_dict() for user in users], "message": f"查询到 {len(users)} 个用户"}
        except Exception as e:
            return {"success": False, "error": str(e), "message": "用户查询失败"}
        finally:
            session.close()

    def update_user(self, user_id: int, **kwargs):
        """更新用户信息"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                return {"success": False, "message": f"未找到ID为 {user_id} 的用户"}

            # 更新字段
            for key, value in kwargs.items():
                if hasattr(user, key) and key != 'id':  # 不允许更新id
                    setattr(user, key, value)

            user.updated_at = datetime.now()
            session.commit()

            return {"success": True, "data": user.to_dict(), "message": "用户更新成功"}
        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e), "message": "用户更新失败"}
        finally:
            session.close()

    def delete_user(self, user_id: int):
        """删除用户"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                return {"success": False, "message": f"未找到ID为 {user_id} 的用户"}

            user_data = user.to_dict()  # 先保存数据用于返回
            session.delete(user)
            session.commit()

            return {"success": True, "data": user_data, "message": "用户删除成功"}
        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e), "message": "用户删除失败"}
        finally:
            session.close()

# 全局数据库管理器实例
_db_manager = None

def get_db_manager(connection_string=None):
    """获取全局数据库管理器实例"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(connection_string)
    return _db_manager

if __name__ == "__main__":
    # 测试数据库连接和基本功能
    print("测试数据库连接...")
    db = get_db_manager()

    print("\n测试创建用户:")
    result = db.create_user("testuser", "test@example.com", "password123", "Test User", 25, "这是一个测试用户")
    print(result)

    print("\n测试查询所有用户:")
    result = db.get_user()
    print(result)

    print("\n测试更新用户:")
    if result.get("data") and len(result["data"]) > 0:
        user_id = result["data"][0]["id"]
        result = db.update_user(user_id, full_name="Updated Name", age=30)
        print(result)

    print("\n测试删除用户:")
    result = db.get_user(username="testuser")
    if result.get("data"):
        user_id = result["data"]["id"]
        result = db.delete_user(user_id)
        print(result)