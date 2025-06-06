# 深大体育场馆预约系统 🏸

一个功能完整的深圳大学体育场馆自动预约工具，支持Web界面操作和智能抢票功能。

## ✨ 主要功能

### 🎯 智能预约
- **自动监控** - 实时检测场地开放状态
- **智能重试** - 网络异常自动重试机制
- **多时段支持** - 可同时预约2个不同时间段
- **场馆优先级** - 智能优选至快体育馆 > 至畅体育馆

### 🌐 Web管理界面
- **配置管理** - 可视化设置预约参数
- **Cookie管理** - 自动/手动获取登录凭证
- **实时监控** - 查看预约进度和成功记录
- **一键操作** - 简单易用的Web界面

### 🏸 支持项目
羽毛球 🏸 | 篮球 🏀 | 网球 🎾 | 排球 🏐 | 游泳 🏊 | 乒乓球 🏓 | 桌球 🎱

### 🏫 校区支持
粤海校区 | 丽湖校区

## 🚀 快速开始

### 方法一：直接运行（推荐）
```bash
# 双击运行
start.bat

# 或命令行运行
python start_web.py
```

### 方法二：命令行模式

```bash
# 安装依赖
pip install -r requirements.txt

# 启动Web服务
python start_web.py

# 访问 http://localhost:5000
```

## 📖 使用说明

### 1. 🔧 配置设置

- 设置校区（粤海/丽湖）和运动项目
- 选择预约日期和优先时间段
- 填写学号姓名等个人信息

### 2. 🍪 Cookie管理

- **自动获取**：输入校园网账号密码，系统自动登录获取（需要有chromedriver.exe，放入 python 安装目录）
- **手动更新**：从浏览器复制Cookie字符串更新

### 3. 🎯 开始抢票

- 点击"开始预约"按钮启动系统
- 实时查看预约状态和成功记录
- 支持随时停止和重新开始

## 💡 使用技巧

- **最佳时机**：预约开放前5-10分钟启动系统
- **网络稳定**：确保网络连接稳定，避免频繁断线
- **及时更新**：定期更新Cookie以保持登录状态
- **合理设置**：重试间隔1-3秒效果最佳

## 📋 系统要求

- **Python 3.12+**（推荐）
- **Chrome浏览器** (用于Cookie获取)
- **Windows/Linux/macOS**

## 🛠️ 常见问题

### ❌ Cookie失效

**解决方案**：使用Web界面自动获取新Cookie或手动更新

### ❌ 网络连接错误

**解决方案**：检查网络连接，尝试更换网络环境

### ❌ 预约失败

**解决方案**：检查用户信息和目标日期设置，验证Cookie有效性

## 📁 项目结构

```
qiangpiao/
├── start_web.py          # Web版启动脚本
├── start.bat            # Windows启动脚本
├── qiangpiao.py         # 核心预约逻辑
├── web_app.py           # Web应用后端
├── config.py            # 配置文件
├── cookie_manager.py    # Cookie管理工具
├── get_cookie.py        # 自动获取Cookie
├── templates/           # Web界面模板
│   ├── index.html       # 主页
│   ├── config.html      # 配置页面
│   ├── cookie.html      # Cookie管理
│   └── booking.html     # 抢票页面
└── requirements.txt     # 依赖包列表
```

## 🔒 安全说明

- 所有账号信息仅存储在本地
- 不收集或上传任何个人数据
- Cookie信息本地加密存储

## ⚠️ 免责声明

本工具仅为方便学生预约体育场馆而开发，使用者应遵守学校相关规定。请合理使用，避免对服务器造成过大压力。

---

**🎉 祝您预约成功！享受运动的快乐！** 🏸🏀🎾
