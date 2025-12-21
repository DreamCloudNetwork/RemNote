# 数据库CRUD功能使用手册

## 功能概述

服务器已集成SQLAlchemy数据库支持，提供用户表的增删改查功能。客户端可以通过命令与MariaDB/SQLite数据库进行交互。

## 依赖配置

### MariaDB配置
默认连接配置：
```python
mysql+pymysql://root@localhost:3306/mydb
```

修改`/home/kevinchang/PycharmProjects/RemNote/database_models.py`中的连接字符串：
```python
connection_string = "mysql+pymysql://username:password@host:port/database"
```

### SQLite备选方案
如果MariaDB连接失败，系统会自动回退到SQLite：
```
sqlite:///./myapp.db
```

## 数据库命令

### 1. 创建用户
```
user_create username email password [full_name] [age] [description]
```

**示例:**
```
user_create alice alice@example.com alice123 "Alice Smith" 25 "这是一个测试用户"
```

### 2. 查询用户
```
# 按ID查询
user_get 1

# 按用户名查询
user_get alice

# 查询所有用户
user_get
```

### 3. 更新用户
```
user_update id field1 value1 [field2 value2]...
```

**可更新字段:** `username`, `email`, `password`, `full_name`, `age`, `description`

**示例:**
```
# 更新姓名和年龄
user_update 1 full_name "Alice Wonderland" age 26

# 更新邮箱
user_update 1 email alice.updated@example.com

# 清除年龄字段
user_update 1 age null
```

### 4. 删除用户
```
user_delete id
```

**示例:**
```
user_delete 1
```

### 5. 获取帮助
```
help
```

## 使用示例

### 基本操作流程

1. **启动服务器**
```bash
python server.py
```

2. **运行测试客户端**
```bash
# 完整测试
python database_test_client.py

# 简单演示
python simple_db_demo.py
```

3. **交互式使用**
```bash
python client.py

# 在客户端输入命令
> user_create testuser test@example.com pass123 "Test User" 30 "测试描述"
> user_get testuser
> user_update testuser full_name "Updated Name" age 31
> user_get
> user_delete testuser
```

### 命令解析器的引号规则

- 单引号 `'...'` 或双引号 `"..."` 可以包含空格
- 反斜杠 `\` 用于转义引号

**示例:**
```
user_create 'John Doe' john@example.com pass123 "John \"JD\" Doe" 28 "This is a test user"
```

## 数据模型

### User表结构

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | Integer | 主键，自增 |
| username | String(50) | 用户名，唯一，必填 |
| email | String(100) | 邮箱，唯一，必填 |
| password | String(255) | 密码，必填 |
| full_name | String(100) | 全名，可选 |
| age | Integer | 年龄，可选 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |
| description | Text | 描述，可选 |

## 错误处理

系统会返回具体的错误信息：

- 参数不足：显示正确的参数格式
- 数据类型错误：显示正确的数据类型要求
- 数据库错误：显示具体的数据库错误原因
- 用户不存在：显示具体的查询条件

## 安全提示

⚠️ **注意：** 当前实现为演示用途，生产环境中请注意：

1. 使用环境变量存储数据库连接信息
2. 对密码进行加密存储
3. 实施适当的访问控制和权限验证
4. 使用连接池和适当的超时设置
5. 对SQL注入进行防护

## 故障排除

### 数据库连接失败
- 检查MariaDB服务是否运行
- 验证用户名密码是否正确
- 确认数据库存在且可访问
- 系统将自动回退到SQLite

### 命令执行失败
- 使用`help`命令查看可用命令
- 检查参数数量和格式
- 注意引号的使用规则
- 查看服务器控制台输出的详细错误信息