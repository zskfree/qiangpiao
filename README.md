# 深圳大学体育场馆抢票系统 Web版

## 🎯 项目概述

这是一个功能完善的深圳大学体育场馆自动抢票系统，支持Web界面操作和命令行两种使用方式，具有智能预约、实时监控、Cookie管理等特性。

## ✨ 主要特性

### 🌐 Web界面特性

- **响应式设计**: 支持桌面和移动端访问
- **实时监控**: 抢票进度实时更新，无需刷新页面
- **可视化配置**: 所有参数通过Web界面修改，无需编辑代码
- **Cookie管理**: 内置Cookie测试、更新和状态检查功能
- **状态持久化**: 每次启动自动重置，确保干净状态

### 🤖 智能化特性

- **SSL连接优化**: 完美解决SSL握手失败问题
- **多时段预约**: 最多同时预约2个不同时间段
- **优先级策略**: 按配置的时段优先级智能选择
- **异常自动处理**: 网络超时、Cookie失效等自动重试
- **进程生命周期管理**: 优雅启动停止，自动清理历史状态

### 🛡️ 稳定性特性

- **完善异常处理**: 网络错误、SSL错误、JSON解析错误全覆盖
- **智能重试机制**: 可配置重试次数和间隔
- **登录状态检查**: 实时检测Cookie和登录状态
- **详细日志系统**: 文件和控制台双重日志记录

## 🚀 快速开始

### 方式一：Web界面（推荐）

1. **一键启动**

   ```bash
   # Windows用户
   双击 start.bat
   
   # 命令行启动
   python start_web.py
   ```

2. **访问Web界面**
   - 浏览器会自动打开 <http://localhost:5000>
   - 或手动访问该地址

3. **完成配置**
   - 进入"配置管理"页面设置基本参数
   - 进入"Cookie管理"页面更新Cookie
   - 进入"抢票监控"页面开始抢票

### 方式二：命令行工具

```bash
# 检查Cookie状态
python cookie_manager.py check

# 更新Cookie
python cookie_manager.py update

# 开始抢票
python qiangpiao.py

# 调试模式
python qiangpiao.py --debug
```

## ⚙️ 详细配置

### 基础配置

| 参数 | 说明 | 可选值 |
|------|------|--------|
| XQ | 校区选择 | "1"=粤海校区, "2"=丽湖校区 |
| XMDM | 运动项目 | "001"=羽毛球 |
| TARGET_DATE | 预约日期 | 格式："YYYY-MM-DD" |
| PREFERRED_TIMES | 优先时段 | ["20:00-21:00", "21:00-22:00"] |
| USER_INFO | 用户信息 | 学号和姓名（必须真实） |

### 运行参数

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| MAX_RETRY_TIMES | 最大重试次数 | 200 |
| RETRY_INTERVAL | 重试间隔(秒) | 1-2 |
| REQUEST_TIMEOUT | 请求超时(秒) | 10 |

### 用户信息配置（重要！）

```python
"USER_INFO": {
    "YYRGH": "你的学号",    # 必须是真实学号
    "YYRXM": "你的姓名"     # 必须是真实姓名
}
```

## 🔑 Cookie管理

### Web界面管理（推荐）

1. 访问"Cookie管理"页面
2. 查看当前Cookie状态
3. 点击"测试Cookie"验证有效性
4. 需要更新时点击"更新Cookie"

### 命令行管理

```bash
# 检查Cookie状态
python cookie_manager.py check

# 交互式更新
python cookie_manager.py update
```

### 获取Cookie步骤

1. 浏览器登录 <https://ehall.szu.edu.cn>
2. 进入体育场馆预约系统
3. 按F12开发者工具 → Network标签
4. 刷新页面，点击任意请求
5. Request Headers中复制Cookie值
6. 粘贴到Web界面或命令行工具

## 📊 Web界面功能

### 主页Dashboard

- 系统状态总览
- 快速导航菜单
- 关键信息展示

### 配置管理

- 校区和项目选择
- 目标日期设置
- 优先时段配置
- 用户信息修改
- 运行参数调整

### Cookie管理

- 当前Cookie状态显示
- Cookie有效性实时检查
- 一键更新Cookie功能
- Cookie详情查看
- 获取Cookie指导

### 抢票监控

- 实时状态显示
- 运行进度条
- 预约结果展示
- 开始/停止控制
- 运行统计信息

## 🎯 使用策略

### 最佳时机

- 预约开放前2-3分钟启动
- 网络环境稳定时段
- 避开网络高峰期

### 配置建议

- 重试间隔设为1-2秒
- 配置3-5个候选时段
- 保持Cookie最新状态
- 目标日期设为明天或更晚

### 监控要点

- Web界面实时查看状态
- 关注Cookie有效性提示
- 监控预约成功通知
- 注意系统异常警告

## 🔧 故障排除

### 常见问题

**Q: Web服务启动失败**

```bash
# 检查Python和Flask
pip install flask
python start_web.py
```

**Q: Cookie失效怎么办？**

- Web界面：Cookie管理 → 重新检查
- 命令行：`python cookie_manager.py update`

**Q: 端口被占用**

- 关闭其他占用5000端口的程序
- 或等待几秒后重试

**Q: 抢票长时间无结果**

- 检查目标日期是否正确
- 确认时段是否已开放预约
- 验证Cookie是否有效
- 检查网络连接稳定性

### 调试技巧

```bash
# 启用调试模式
python qiangpiao.py --debug

# 查看详细日志
type qiangpiao.log
```

## 📁 项目结构

```
d:\projects\qiangpiao\
├── 核心文件
│   ├── qiangpiao.py        # 主抢票逻辑
│   ├── config.py           # 配置文件
│   ├── web_app.py          # Flask Web应用
│   ├── start_web.py        # Web服务启动脚本
│   └── cookie_manager.py   # Cookie管理工具
├── 启动文件
│   └── start.bat           # Windows一键启动
├── Web模板
│   └── templates/          # HTML模板文件
├── 静态资源
│   └── static/             # CSS/JS资源
├── 文档
│   ├── README.md           # 本文档
│   └── 使用指南.md         # 详细使用指南
└── 运行时文件
    ├── qiangpiao.log       # 运行日志
    └── cookie_backup_*.txt # Cookie备份
```

## 📈 运行示例

### Web启动界面

```
🚀 正在启动深圳大学体育场馆抢票系统...
🧹 清理历史文件...
🔄 重置模块状态...
📁 检查必要文件...
📡 启动Web服务器...
🌐 服务地址: http://localhost:5000
🌐 浏览器已打开
```

### 抢票成功示例

```
✅ 预约成功！场地：20:00-21:00 - 至快体育馆A1
📋 预约单号：YY202501010001
🎉 预约详情:
   📅 日期: 2025-01-02
   ⏰ 时间: 20:00-21:00
   🏟️ 场地: 至快体育馆羽毛球场A1
```

## ⚠️ 重要提醒

### 必须配置

1. **用户信息**: 必须设置真实学号和姓名
2. **Cookie更新**: 定期更新保持有效性
3. **目标日期**: 设置为有效的预约日期

### 使用规范

1. **合规使用**: 遵守学校相关规定
2. **适度频率**: 合理设置重试间隔
3. **隐私保护**: 妥善保管Cookie信息
4. **单实例运行**: 避免同时运行多个实例

### 技术要求

- Python 3.6+
- Flask框架
- 稳定的网络连接
- 现代浏览器支持

## 🆘 获取帮助

### 自助诊断

- Web界面：Cookie管理页面 → 重新检查
- 命令行：`python cookie_manager.py check`
- 调试模式：`python qiangpiao.py --debug`
- 日志分析：查看 `qiangpiao.log` 文件

### 快速命令

```bash
# 启动Web界面
python start_web.py

# Cookie管理
python cookie_manager.py check
python cookie_manager.py update

# 命令行抢票
python qiangpiao.py
```

## 📄 许可证

本项目仅供学习交流使用，请遵守深圳大学相关规定，合理合规使用。

---

🎊 **祝您抢票成功！** 这个Web版抢票系统将为您提供最佳的预约体验！🏸
