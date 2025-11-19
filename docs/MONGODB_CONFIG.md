# MongoDB配置指南

## 📋 概述

项目使用MongoDB存储Agent的会话数据、记忆和指标。所有MongoDB相关配置都可以通过环境变量进行设置。

## 🔧 配置方式

### 方式1: 环境变量（推荐）

在项目根目录的 `.env` 文件中配置：

```bash
# MongoDB连接URI
MONGODB_URI=mongodb://admin:password123@localhost:27017/

# 数据库名称
MONGODB_DATABASE=loan_advisor

# 集合名称（可选，使用默认值即可）
MONGODB_SESSION_COLLECTION=agno_sessions
MONGODB_MEMORY_COLLECTION=agno_memories
MONGODB_METRICS_COLLECTION=agno_metrics
```

### 方式2: 使用默认值（无需配置）

如果 `.env` 中没有设置MongoDB配置，系统将使用以下默认值：

```python
mongodb_uri: "mongodb://admin:password123@localhost:27017/"
database_name: "loan_advisor"
session_collection: "agno_sessions"
memory_collection: "agno_memories"
metrics_collection: "agno_metrics"
```

**默认配置适用于本地开发环境**。

## 💡 使用场景

### 场景1: 本地开发（使用默认值）

**不需要在.env中配置**，直接使用默认值：

```bash
# .env 中无需添加MongoDB配置
# 系统自动使用本地MongoDB: mongodb://admin:password123@localhost:27017/
```

**前提条件**:
- 本地运行 `docker-compose up -d` 启动MongoDB
- MongoDB使用默认配置（admin/password123）

### 场景2: 自定义本地配置

```bash
# .env 中配置自定义MongoDB
MONGODB_URI=mongodb://myuser:mypass@localhost:27017/
MONGODB_DATABASE=my_loan_db
```

### 场景3: 生产环境

```bash
# .env 中配置云MongoDB（如MongoDB Atlas）
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DATABASE=loan_advisor_prod
```

### 场景4: Docker环境

```bash
# .env 中配置Docker容器内的MongoDB
MONGODB_URI=mongodb://admin:password123@mongo:27017/
MONGODB_DATABASE=loan_advisor
```

## 🗄️ 数据结构

### 数据库: loan_advisor

MongoDB会自动创建以下集合：

#### 1. agno_sessions (会话集合)
存储Agent会话信息：
```json
{
  "session_id": "sess_xxx",
  "user_id": "user_123",
  "created_at": "2025-01-19T10:00:00Z",
  "updated_at": "2025-01-19T10:05:00Z",
  "messages": [...]
}
```

#### 2. agno_memories (记忆集合)
存储Agent长期记忆：
```json
{
  "session_id": "sess_xxx",
  "user_id": "user_123",
  "memory_type": "user_preference",
  "content": {...}
}
```

#### 3. agno_metrics (指标集合)
存储Agent性能指标：
```json
{
  "session_id": "sess_xxx",
  "timestamp": "2025-01-19T10:00:00Z",
  "response_time": 2.5,
  "tokens_used": 1500,
  "tool_calls": [...]
}
```

## 🚀 快速开始

### 1. 启动本地MongoDB

使用Docker Compose:

```bash
# 启动MongoDB
docker-compose up -d

# 验证MongoDB运行
docker-compose ps
```

### 2. 验证配置

```bash
# 运行配置检查
uv run python scripts/check_config.py
```

输出示例:
```
🗄️  MongoDB Config (src/utils/config.py):
  mongodb_uri: mongodb://admin:password123@localhost:27017/
  database_name: loan_advisor
  session_collection: agno_sessions
  memory_collection: agno_memories
  metrics_collection: agno_metrics
```

### 3. 运行Agent

```bash
uv run python src/agent/loan_advisor_agent.py
```

Agent会自动连接到配置的MongoDB并开始存储数据。

## 🔍 验证MongoDB连接

### 方法1: Python代码验证

```python
from src.utils.config import config

print(f"MongoDB URI: {config.mongodb.mongodb_uri}")
print(f"Database: {config.mongodb.database_name}")

# 导入Agent验证连接
from src.agent.loan_advisor_agent import loan_advisor_agent
print(f"✅ Agent MongoDB配置: {loan_advisor_agent.db.db_url}")
```

### 方法2: MongoDB客户端连接

```bash
# 使用mongosh连接
mongosh "mongodb://admin:password123@localhost:27017/"

# 查看数据库
show dbs

# 切换到loan_advisor数据库
use loan_advisor

# 查看集合
show collections
```

### 方法3: Docker日志

```bash
# 查看MongoDB容器日志
docker-compose logs mongo

# 实时查看日志
docker-compose logs -f mongo
```

## 📊 配置参数说明

| 环境变量 | 默认值 | 说明 | 是否必需 |
|----------|--------|------|----------|
| `MONGODB_URI` | `mongodb://admin:password123@localhost:27017/` | MongoDB连接URI | ❌ |
| `MONGODB_DATABASE` | `loan_advisor` | 数据库名称 | ❌ |
| `MONGODB_SESSION_COLLECTION` | `agno_sessions` | 会话集合名 | ❌ |
| `MONGODB_MEMORY_COLLECTION` | `agno_memories` | 记忆集合名 | ❌ |
| `MONGODB_METRICS_COLLECTION` | `agno_metrics` | 指标集合名 | ❌ |

**注意**: 所有参数都有默认值，适用于本地开发环境。

## ⚠️ 注意事项

### 1. 连接字符串格式

```bash
# 本地MongoDB
MONGODB_URI=mongodb://username:password@localhost:27017/

# MongoDB Atlas (云服务)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/

# 副本集
MONGODB_URI=mongodb://user:pass@host1:27017,host2:27017,host3:27017/?replicaSet=myReplicaSet
```

### 2. 用户名密码包含特殊字符

需要进行URL编码：

```python
from urllib.parse import quote_plus

username = "my@user"
password = "p@ss#word!"

encoded_username = quote_plus(username)  # my%40user
encoded_password = quote_plus(password)  # p%40ss%23word%21

mongodb_uri = f"mongodb://{encoded_username}:{encoded_password}@localhost:27017/"
```

### 3. Docker环境主机名

在Docker Compose中，MongoDB容器的主机名是服务名（默认为 `mongo`）：

```bash
# 在容器内访问MongoDB
MONGODB_URI=mongodb://admin:password123@mongo:27017/
```

### 4. 连接池配置

如需自定义连接池，可以在URI中添加参数：

```bash
MONGODB_URI=mongodb://admin:password123@localhost:27017/?maxPoolSize=50&minPoolSize=10
```

## 🔧 故障排查

### 问题1: 连接失败

**症状**: `pymongo.errors.ServerSelectionTimeoutError`

**检查步骤**:

1. 确认MongoDB正在运行:
   ```bash
   docker-compose ps
   # 或
   systemctl status mongod
   ```

2. 检查连接URI是否正确:
   ```bash
   uv run python scripts/check_config.py
   ```

3. 测试连接:
   ```bash
   mongosh "mongodb://admin:password123@localhost:27017/"
   ```

**解决方案**:
- 确保MongoDB已启动
- 检查端口是否被占用（默认27017）
- 验证用户名密码是否正确

### 问题2: 认证失败

**症状**: `pymongo.errors.OperationFailure: Authentication failed`

**检查步骤**:

1. 验证用户名密码:
   ```bash
   echo $MONGODB_URI
   ```

2. 在MongoDB中检查用户:
   ```javascript
   use admin
   db.getUsers()
   ```

**解决方案**:
- 更新 `.env` 中的正确用户名密码
- 在MongoDB中创建用户（如果不存在）

### 问题3: 数据库/集合不存在

**症状**: Agent运行但看不到数据

**检查步骤**:

1. 确认数据库名称:
   ```bash
   uv run python -c "from src.utils.config import config; print(config.mongodb.database_name)"
   ```

2. 在MongoDB中查看:
   ```javascript
   show dbs
   use loan_advisor
   show collections
   ```

**解决方案**:
- MongoDB会在首次写入时自动创建数据库和集合
- 运行Agent进行一次对话即可创建

## 📚 相关文档

- [MongoDB官方文档](https://docs.mongodb.com/)
- [PyMongo文档](https://pymongo.readthedocs.io/)
- [Agno MongoDB集成](https://docs.agno.ai/storage/mongodb)
- [Docker Compose配置](../docker-compose.yml)

## 💡 最佳实践

### 开发环境
```bash
# 使用本地MongoDB，无需配置
# 直接运行 docker-compose up -d
```

### 测试环境
```bash
# 使用独立的测试数据库
MONGODB_URI=mongodb://admin:password123@localhost:27017/
MONGODB_DATABASE=loan_advisor_test
```

### 生产环境
```bash
# 使用云MongoDB服务（如MongoDB Atlas）
MONGODB_URI=mongodb+srv://prod_user:secure_pass@cluster.mongodb.net/
MONGODB_DATABASE=loan_advisor_prod

# 添加连接池和超时配置
MONGODB_URI=mongodb+srv://.../?maxPoolSize=100&connectTimeoutMS=10000
```

---

**更新日期**: 2025-01-19
**版本**: 1.0
