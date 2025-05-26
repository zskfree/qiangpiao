# 配置文件
from datetime import datetime, timedelta

current_date = datetime.now()
# 计算目标日期（当前日期 + 1 天）
target_date = current_date + timedelta(days=1)
# 格式化目标日期为字符串
target_date = target_date.strftime('%Y-%m-%d')

# 基础配置
CONFIG = {
    # 查询参数
    "XQ": "2",        # 校区：1=粤海, 2=丽湖
    "YYLX": "1.0",    # 预约类型
    "XMDM": "001",    # 项目代码：001=羽毛球  003=排球 004=网球 005=篮球 009=游泳 013=乒乓球 016=桌球
    
    # 运行参数
    "MAX_RETRY_TIMES": 200,    # 最大重试次数
    "RETRY_INTERVAL": 1,       # 重试间隔（秒）
    "REQUEST_TIMEOUT": 10,     # 请求超时时间（秒）
    # 预约日期
    "TARGET_DATE": "2025-05-27",

    # 优先预约的时段关键词（按优先级排序）
    "PREFERRED_TIMES": ['20:00-21:00', '21:00-22:00'],
    
    # 用户信息配置
    "USER_INFO": {
        "YYRGH": "2300123999",  # 学号/工号
        "YYRXM": "张三"   # 姓名
    }
}

# 项目代码映射
SPORT_CODES = {
    "羽毛球": "001",
    "排球": "003",
    "网球": "004",
    "篮球": "005",
    "游泳": "009",
    "乒乓球": "013",
    "桌球": "016"
}

# 校区代码映射
CAMPUS_CODES = {
    "粤海": "1",
    "丽湖": "2"
}

# 可选时间段（每小时一个时段）
TIME_SLOTS = [
    "08:00-09:00", "09:00-10:00", "10:00-11:00", "11:00-12:00",
    "12:00-13:00", "13:00-14:00", "14:00-15:00", "15:00-16:00",
    "16:00-17:00", "17:00-18:00", "18:00-19:00", "19:00-20:00",
    "20:00-21:00", "21:00-22:00"
]

# 校园网账户
CAMPUS_ACCOUNT = {
    "username": "2300123999",  # 学号或工号
    "password": ""
}

# 导出配置供其他模块使用
def get_campus_account():
    """获取校园网账户信息"""
    return CAMPUS_ACCOUNT.copy()

def update_campus_account(username, password):
    """更新校园网账户信息"""
    global CAMPUS_ACCOUNT
    CAMPUS_ACCOUNT["username"] = username
    CAMPUS_ACCOUNT["password"] = password
    return True
