# Railway HTTPS Deployment Guide
# Railway HTTPS 部署指南

## Overview | 概述

This application is configured to run on Railway with automatic HTTPS support and CORS enabled for AgentUI access.

本应用配置为在Railway上运行，自动支持HTTPS，并启用CORS以供AgentUI访问。

---

## Features | 功能特性

✅ **Automatic HTTPS** - Railway provides free SSL/TLS certificates
✅ **CORS Enabled** - AgentUI can connect from any origin
✅ **Bearer Token Authentication** - Secure API access via OS_SECURITY_KEY
✅ **MongoDB Persistence** - Session and conversation storage
✅ **Production Ready** - Configured for production deployment

✅ **自动HTTPS** - Railway提供免费SSL/TLS证书
✅ **CORS已启用** - AgentUI可以从任何来源连接
✅ **Bearer Token认证** - 通过OS_SECURITY_KEY进行安全API访问
✅ **MongoDB持久化** - 会话和对话存储
✅ **生产就绪** - 配置用于生产部署

---

## Railway Deployment URL | Railway部署URL

Once deployed on Railway, your app will be accessible at:
```
https://your-app-name.up.railway.app
```

Railway automatically provisions an HTTPS certificate and handles SSL/TLS termination.

Railway部署后，您的应用将可通过以下地址访问：
```
https://your-app-name.up.railway.app
```

Railway自动提供HTTPS证书并处理SSL/TLS终止。

---

## Environment Variables | 环境变量

### Required | 必需

```bash
OPENAI_API_KEY=your_openai_api_key
MONGODB_URI=your_mongodb_connection_string
```

### Optional | 可选

```bash
# API Authentication (recommended for production)
OS_SECURITY_KEY=your_secret_key

# CORS Configuration
# Default: * (allow all origins)
# Production: specify your AgentUI domain
ALLOWED_ORIGINS=https://your-agentui-domain.com,https://localhost:3000

# Model Configuration
AGENT_MODEL=gpt-4o-mini
TEMPERATURE=0.7
```

---

## CORS Configuration | CORS配置

### Development | 开发环境

By default, CORS allows all origins (`*`):
```bash
ALLOWED_ORIGINS=*
```

### Production | 生产环境

Restrict to specific AgentUI domains:
```bash
ALLOWED_ORIGINS=https://your-agentui.com,https://app.yourdomain.com
```

Multiple origins are separated by commas.

默认情况下，CORS允许所有来源（`*`）：
```bash
ALLOWED_ORIGINS=*
```

生产环境中，限制为特定的AgentUI域名：
```bash
ALLOWED_ORIGINS=https://your-agentui.com,https://app.yourdomain.com
```

多个来源用逗号分隔。

---

## AgentUI Integration | AgentUI集成

### Step 1: Deploy Backend on Railway

1. Push this branch to GitHub
2. Railway will automatically deploy with HTTPS
3. Note your deployment URL: `https://your-app.up.railway.app`

### Step 2: Configure AgentUI

In your AgentUI configuration, set the backend URL:

```javascript
// AgentUI config
const config = {
  apiUrl: "https://your-app.up.railway.app",
  agentId: "personal-loan-advisor"
}
```

### Step 3: Authentication (if OS_SECURITY_KEY is set)

If you've set `OS_SECURITY_KEY`, include the bearer token:

```javascript
// AgentUI API call
fetch("https://your-app.up.railway.app/v1/chat", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_OS_SECURITY_KEY"
  },
  body: JSON.stringify({
    message: "I want to apply for a loan",
    agent_id: "personal-loan-advisor"
  })
})
```

---

## API Endpoints | API端点

### Base URL
```
https://your-app.up.railway.app
```

### Available Endpoints | 可用端点

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/docs` | GET | Interactive API documentation |
| `/v1/chat` | POST | Chat with agent |
| `/health` | GET | Health check (if configured) |

---

## Testing HTTPS Locally | 本地HTTPS测试

While Railway provides HTTPS automatically, you can test CORS locally:

```bash
# Start the API server
uv run python src/agent/loan_advisor_agent.py --api

# Test CORS headers
curl -X GET http://localhost:8000/ \
  -H "Origin: http://localhost:3000" \
  -i | grep -i "access-control"

# Expected output:
# access-control-allow-credentials: true
# access-control-allow-origin: *
# access-control-expose-headers: *
```

---

## Security Best Practices | 安全最佳实践

### 1. Use Bearer Token Authentication

Always set `OS_SECURITY_KEY` in production:

```bash
OS_SECURITY_KEY=$(openssl rand -hex 32)
```

### 2. Restrict CORS Origins

Don't use `ALLOWED_ORIGINS=*` in production. Specify your AgentUI domain:

```bash
ALLOWED_ORIGINS=https://your-agentui.production.com
```

### 3. Use Environment-Specific MongoDB

- **Development**: Local MongoDB or MongoDB Atlas free tier
- **Production**: MongoDB Atlas with authentication

### 4. Keep Dependencies Updated

```bash
uv sync --upgrade
```

---

## Troubleshooting | 故障排除

### CORS Errors | CORS错误

**Problem**: AgentUI shows "CORS error" or "Access blocked"

**Solution**:
1. Check `ALLOWED_ORIGINS` includes your AgentUI domain
2. Verify Railway deployment is running
3. Check browser console for exact error

### Authentication Errors | 认证错误

**Problem**: "401 Unauthorized" or "Invalid bearer token"

**Solution**:
1. Verify `OS_SECURITY_KEY` matches in Railway and AgentUI
2. Check Authorization header format: `Bearer <token>`
3. Ensure no extra spaces in the token

### Connection Errors | 连接错误

**Problem**: "Failed to connect" or "Network error"

**Solution**:
1. Verify Railway app is running (check Railway dashboard)
2. Check deployment URL is correct (https not http)
3. Test endpoint directly: `curl https://your-app.up.railway.app/`

---

## Monitoring | 监控

### Railway Dashboard

Monitor your deployment:
- **Metrics**: CPU, Memory, Network usage
- **Logs**: Real-time application logs
- **Deployments**: Build and deployment history

### Application Logs

View logs in Railway dashboard or via CLI:
```bash
railway logs
```

Look for:
```
✅ CORS configured with allowed origins: ['*']
✅ Starting Personal Loan Advisor API Server
✅ API will be available at http://0.0.0.0:8000
```

---

## Updates and Redeployment | 更新和重新部署

### Automatic Deployment

Railway automatically redeploys when you push to your main branch.

### Manual Deployment

1. Make changes locally
2. Commit and push:
   ```bash
   git add .
   git commit -m "Update configuration"
   git push origin main
   ```
3. Railway will automatically rebuild and redeploy

---

## Cost Estimates | 成本估算

### Railway

- **Starter Plan**: $5/month (includes 500 hours)
- **Includes**: HTTPS, automatic deployments, monitoring
- **Bandwidth**: 100GB/month

### MongoDB Atlas

- **Free Tier**: 512MB storage (sufficient for development)
- **Shared Cluster**: ~$9/month (recommended for production)

### OpenAI API

- **GPT-4o-mini**: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
- Estimate: $10-50/month depending on usage

---

## Support | 支持

### Documentation

- [Railway Docs](https://docs.railway.app/)
- [AgentOS Docs](https://docs.agno.com/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)

### Issues

Report issues on GitHub or check application logs in Railway dashboard.

---

## Next Steps | 下一步

1. ✅ Deploy on Railway
2. ✅ Configure environment variables
3. ✅ Test HTTPS endpoint
4. ⬜ Deploy AgentUI
5. ⬜ Configure AgentUI to connect to backend
6. ⬜ Test end-to-end integration

---

**Status**: Ready for production deployment 🚀

**状态**: 准备好生产部署 🚀
