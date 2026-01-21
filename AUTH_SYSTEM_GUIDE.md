# 用户认证系统使用指南

## 概述

本项目已成功集成了完整的用户认证系统，支持用户注册、登录、会话管理和数据隔离。系统采用Flask + SQLite架构，提供RESTful API接口，并通过Gradio桥接器与现有Web界面集成。

## 系统架构

### 核心组件

1. **存储适配器** (`storage/`)
   - `base.py`: 存储接口抽象基类
   - `sqlite_adapter.py`: SQLite数据库适配器实现

2. **认证模块** (`auth/`)
   - `auth_utils.py`: 密码加密、JWT令牌管理工具
   - `user_manager.py`: 用户管理核心逻辑
   - `auth_handler.py`: Flask认证中间件和装饰器
   - `auth_routes.py`: 认证API路由

3. **集成模块** (`integration/`)
   - `gradio_bridge.py`: Gradio与Flask通信桥接器

4. **Flask应用** (`deploy/`)
   - `flask_app.py`: Flask API服务入口

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动系统

#### 方法一：使用集成启动脚本（推荐）

```bash
python start_with_auth.py
```

这将同时启动：
- Flask API服务 (http://localhost:5000)
- Gradio Web界面 (http://localhost:7860)

#### 方法二：分别启动

```bash
# 启动Flask API服务
python deploy/flask_app.py

# 在另一个终端启动Gradio界面
python deploy/app.py
```

### 3. 测试认证系统

```bash
python test_auth_system.py
```

## API接口文档

### 认证相关接口

#### 用户注册
- **URL**: `POST /api/auth/register`
- **请求体**:
  ```json
  {
    "username": "testuser",
    "email": "test@example.com",
    "password": "Password123!"
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "message": "注册成功",
    "user_id": "uuid",
    "username": "testuser"
  }
  ```

#### 用户登录
- **URL**: `POST /api/auth/login`
- **请求体**:
  ```json
  {
    "username_or_email": "testuser",
    "password": "Password123!"
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "message": "登录成功",
    "token": "jwt_token",
    "user_id": "uuid",
    "username": "testuser",
    "session_id": "session_uuid"
  }
  ```

#### 用户登出
- **URL**: `POST /api/auth/logout`
- **头部**: `Authorization: Bearer <token>`
- **响应**:
  ```json
  {
    "success": true,
    "message": "登出成功"
  }
  ```

#### 获取用户资料
- **URL**: `GET /api/auth/profile`
- **头部**: `Authorization: Bearer <token>`
- **响应**:
  ```json
  {
    "success": true,
    "user": {
      "user_id": "uuid",
      "username": "testuser",
      "email": "test@example.com",
      "created_at": "2023-01-01T00:00:00",
      "is_active": true,
      "metadata": {}
    },
    "stats": {
      "video_count": 0,
      "session_count": 1,
      "conversation_count": 0
    }
  }
  ```

#### 更新用户资料
- **URL**: `PUT /api/auth/profile`
- **头部**: `Authorization: Bearer <token>`
- **请求体**:
  ```json
  {
    "username": "newusername",
    "email": "new@example.com"
  }
  ```

#### 验证令牌
- **URL**: `POST /api/auth/verify`
- **请求体**:
  ```json
  {
    "token": "jwt_token"
  }
  ```

#### 刷新令牌
- **URL**: `POST /api/auth/refresh`
- **请求体**:
  ```json
  {
    "token": "jwt_token"
  }
  ```

### 系统接口

#### 健康检查
- **URL**: `GET /api/health`
- **响应**:
  ```json
  {
    "status": "healthy",
    "message": "Flask应用运行正常",
    "timestamp": "2023-01-01T00:00:00"
  }
  ```

#### 获取当前用户
- **URL**: `GET /api/user`
- **头部**: `Authorization: Bearer <token>`
- **响应**:
  ```json
  {
    "success": true,
    "user": {
      "user_id": "uuid",
      "username": "testuser"
    }
  }
  ```

## 数据隔离机制

### 用户数据目录结构

```
data/users/
├── {user_id}/
│   ├── videos/          # 用户视频文件
│   ├── transcripts/     # 转录结果
│   ├── conversations/   # 对话历史
│   └── sessions/        # 会话数据
```

### 隔离策略

1. **文件系统隔离**：每个用户拥有独立的数据目录
2. **数据库隔离**：所有数据通过user_id关联
3. **会话隔离**：每个用户拥有独立的会话空间
4. **API隔离**：所有API需要认证令牌

## 安全特性

### 密码安全
- 使用bcrypt进行密码哈希加密
- 支持密码强度验证
- 备选SHA-256加密方案

### 令牌安全
- JWT令牌签名验证
- 令牌过期机制（默认24小时）
- 令牌刷新功能

### API安全
- 速率限制保护
- 请求参数验证
- CORS跨域保护
- 错误信息脱敏

## 配置说明

### 环境变量

```bash
# JWT密钥（生产环境必须更改）
export JWT_SECRET_KEY="your-jwt-secret-key"

# Flask密钥（生产环境必须更改）
export SECRET_KEY="your-secret-key"

# 数据库路径
export DATABASE_URL="data/app.db"
```

### 认证配置

```python
# JWT配置
JWT_SECRET_KEY = "your-jwt-secret-key"
JWT_EXPIRE_HOURS = 24

# 密码策略
PASSWORD_MIN_LENGTH = 6
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGITS = True
PASSWORD_REQUIRE_SPECIAL = True
```

## 开发指南

### 添加新的认证路由

1. 在`auth/auth_routes.py`中添加路由函数
2. 使用`@auth_handler.require_auth`装饰器保护路由
3. 使用`@validate_json`验证输入参数
4. 使用`@rate_limit`限制请求频率

### 扩展用户模型

1. 修改`storage/base.py`中的User类
2. 更新数据库表结构（SQLiteAdapter）
3. 修改API接口以支持新字段
4. 更新前端界面

### 添加新的存储后端

1. 继承`storage/base.StorageAdapter`类
2. 实现所有抽象方法
3. 在Flask应用中注册新的适配器
4. 更新配置文件

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库文件路径
   - 确保目录权限正确
   - 查看日志输出

2. **令牌验证失败**
   - 检查JWT密钥配置
   - 确认令牌未过期
   - 验证令牌格式

3. **跨域请求失败**
   - 检查CORS配置
   - 确认请求头部正确
   - 验证API端点

### 日志查看

```bash
# 查看Flask日志
tail -f logs/flask.log

# 查看系统日志
tail -f logs/app.log
```

## 部署建议

### 生产环境配置

1. **安全配置**
   - 更改所有默认密钥
   - 启用HTTPS
   - 配置防火墙

2. **性能优化**
   - 使用PostgreSQL/MySQL替代SQLite
   - 配置Redis缓存
   - 启用负载均衡

3. **监控告警**
   - 配置日志收集
   - 设置性能监控
   - 配置错误告警

### 扩展部署

1. **微服务架构**
   - 拆分认证服务
   - 使用API网关
   - 配置服务发现

2. **容器化部署**
   - 创建Docker镜像
   - 使用Kubernetes编排
   - 配置持久化存储

## 下一步计划

1. **功能增强**
   - 添加角色权限系统
   - 支持OAuth2登录
   - 添加邮件验证

2. **性能优化**
   - 实现数据库连接池
   - 添加缓存层
   - 优化查询性能

3. **安全加固**
   - 添加多因素认证
   - 实现审计日志
   - 加强输入验证

## 联系方式

如有问题或建议，请提交Issue或联系开发团队。