# Rainbow Register Backend - 启动指南

## 第一次启动（完整步骤）

### 步骤1：确认环境
```powershell
# 检查Python版本（需要3.9+）
python --version

# 检查虚拟环境
.\rainbowEnv\Scripts\Activate.ps1
```

### 步骤2：初始化数据库
```powershell
# 运行数据库初始化脚本
python scripts/init_db.py
```

你会看到：
```
==============================================================
开始初始化数据库...
==============================================================

1. 创建数据库表...
✅ 数据库表创建成功

2. 创建默认管理员账号...
✅ 管理员账号创建成功
   用户名: admin
   密码: change_this_password
   ⚠️  请及时修改默认密码！

==============================================================
数据库初始化完成！
==============================================================
```

### 步骤3：生成初始邀请码
```powershell
# 生成10个邀请码
python scripts/generate_invitations.py -c 10 -n "初始邀请码"
```

### 步骤4：启动应用
```powershell
# 启动服务
.\run.ps1
```

或者
```powershell
python run.py
```

### 步骤5：访问API文档

打开浏览器，访问：
```
http://localhost:8000/docs
```

---

## 常用操作

### 管理员登录测试

1. 打开 http://localhost:8000/docs
2. 找到 `POST /api/v1/admin/login`
3. 点击 "Try it out"
4. 输入：
```json
{
  "username": "admin",
  "password": "change_this_password"
}
```
5. 点击 "Execute"
6. 复制返回的 `token`

### 生成邀请码

1. 使用上面获得的token
2. 找到 `POST /api/v1/admin/invitation/generate`
3. 点击右上角 🔒 "Authorize"
4. 输入：`Bearer {你的token}`
5. 执行API，生成邀请码

### 测试完整流程
```powershell
# 运行自动化测试
python test_api.py
```

---

## 常见问题

### 问题1：端口被占用
```
ERROR: [Errno 10048] error while attempting to bind on address
```

**解决：** 修改 `.env` 中的 `PORT=8001`

### 问题2：数据库文件被锁定
```
OperationalError: database is locked
```

**解决：** 关闭所有数据库连接，重启应用

### 问题3：虚拟环境未激活

**解决：**
```powershell
.\rainbowEnv\Scripts\Activate.ps1
```

---

## 开发模式 vs 生产模式

### 开发模式（当前）
- DEBUG=True
- 自动重载代码
- 详细错误信息
- 使用SQLite
- 模拟微信登录

### 生产模式（部署时）
- DEBUG=False
- 使用PostgreSQL
- 真实微信API
- HTTPS必须
- 配置域名白名单

---

## 下一步

1. ✅ 测试所有API
2. ✅ 创建测试数据
3. ⏳ 开发小程序前端
4. ⏳ 部署到VPS

---

## 获取帮助

- API文档：http://localhost:8000/docs
- 项目文档：docs/
- 问题反馈：提交Issue