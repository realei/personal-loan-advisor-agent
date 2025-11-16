# Personal Loan Advisor Agent - Demo 使用指南

## 🎯 三种使用方式

### 1. ⚡ 最简单 Demo（推荐新手）

**simple_demo.py** - 零配置，纯对话

```bash
# 确保 .env 中有 OPENAI_API_KEY
uv run python simple_demo.py
```

**特点：**
- ✅ 无需 MongoDB
- ✅ 无需额外配置
- ✅ 纯命令行对话
- ❌ 不保存历史记录

---

### 2. 🔧 完整 CLI Demo

**main.py** - 完整功能

```bash
# 需要 MongoDB（可选）
docker-compose up -d

uv run python main.py
```

**特点：**
- ✅ MongoDB 会话管理
- ✅ 对话历史保存
- ✅ 会话恢复功能
- ✅ 评估系统（可选）
- ✅ 用户管理

---

### 3. 🎨 Web UI

#### Streamlit（简单前端）

```bash
git checkout feature/streamlit-frontend
./start_streamlit.sh
# 访问 http://localhost:8501
```

**特点：**
- ✅ 网页界面
- ✅ 聊天历史显示
- ✅ 示例查询按钮
- ✅ 一条命令启动

#### AG-UI（生产级前端）

```bash
git checkout feature/agui-frontend
./scripts/start_agui.sh enhanced
# 后端: http://localhost:7777
# 前端需要单独设置
```

**特点：**
- ✅ 标准协议
- ✅ 自定义事件
- ✅ 适合生产环境
- ⚠️ 需要前端构建

---

## 🚀 快速开始（新用户）

### 1 分钟启动

```bash
# 1. 确保有 .env 文件
cp .env.example .env
# 编辑 .env，添加 OPENAI_API_KEY

# 2. 运行最简单的 demo
uv run python simple_demo.py

# 3. 输入查询
# You: I'm 35, earn $10k/month, credit score 720, want $50k for 36 months
```

---

## 📊 功能对比

| 功能 | simple_demo.py | main.py | Streamlit | AG-UI |
|------|----------------|---------|-----------|-------|
| 启动速度 | ⚡ 极快 | ⚡ 快 | 🔧 中等 | 🐌 慢 |
| 安装复杂度 | ⭐ 简单 | ⭐⭐ 中等 | ⭐⭐ 中等 | ⭐⭐⭐⭐⭐ 复杂 |
| 对话历史 | ❌ 无 | ✅ 有 | ✅ 有 | ✅ 有 |
| 会话管理 | ❌ 无 | ✅ 有 | ✅ 有 | ✅ 有 |
| 用户界面 | 命令行 | 命令行 | 网页 | 网页 |
| 适合场景 | 快速测试 | 完整测试 | 演示/内部工具 | 生产部署 |

---

## 💡 推荐使用

| 场景 | 推荐 |
|------|------|
| 第一次使用 | `simple_demo.py` |
| 开发调试 | `main.py` |
| 演示给客户 | `Streamlit` |
| 生产部署 | `AG-UI` |
| 快速测试 | `simple_demo.py` |
| 完整功能测试 | `main.py` |

---

## 🔧 环境要求

### 必需
- Python 3.11+
- OpenAI API Key

### 可选
- MongoDB（main.py 完整功能）
- Docker（运行 MongoDB）

---

## 📝 示例查询

```
# 1. 资格检查
I'm 35, earn $10k/month, credit score 720, want $50k for 36 months

# 2. 月供计算
Calculate payment for $50000 at 5% for 36 months

# 3. 负担能力
Is $50k affordable with $8000 income and $500 existing debt?

# 4. 对比方案
Compare loan terms for $30000 at 4.5%

# 5. 最大可贷
What's the maximum loan I can afford with $12000 income?
```

---

## 📁 分支说明

- **dev** - 基础 demo（当前分支）
  - `simple_demo.py` - 最简单版本
  - `main.py` - 完整 CLI 版本

- **feature/streamlit-frontend** - Streamlit 网页界面
  - `streamlit_app/` - Streamlit 应用
  - `start_streamlit.sh` - 启动脚本

- **feature/agui-frontend** - AG-UI 生产级前端
  - `src/app_agui_enhanced.py` - AG-UI 后端
  - `scripts/start_agui.sh` - 启动脚本
  - AG-UI 完整文档

---

开始使用最简单的方式：`uv run python simple_demo.py` 🚀
