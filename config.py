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
    "XMDM": "001",    # 项目代码：001=羽毛球
    
    # 运行参数
    "MAX_RETRY_TIMES": 200,    # 最大重试次数
    "RETRY_INTERVAL": 1,       # 重试间隔（秒）
    "REQUEST_TIMEOUT": 10,     # 请求超时时间（秒）
    # 预约日期
    "TARGET_DATE": target_date,
    
    # 优先预约的时段关键词（按优先级排序）
    "PREFERRED_TIMES": ['20:00-21:00', '21:00-22:00'],
    
    # 用户信息配置
    "USER_INFO": {
        "YYRGH": "2300123009",  # 学号/工号
        "YYRXM": "朱尚昆"   # 姓名
    }
}

# 项目代码映射
SPORT_CODES = {
    "羽毛球": "001",
}

# 校区代码映射
CAMPUS_CODES = {
    "粤海": "1",
    "丽湖": "2"
}

# Cookie配置 (占位符，实际Cookie在qiangpiao.py中定义)
COOKIE = ""
