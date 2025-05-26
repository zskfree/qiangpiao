import requests
import json
import time
import logging
from datetime import datetime
import urllib3
import ssl
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
import sys

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 导入配置
try:
    from config import CONFIG
except ImportError:
    print("❌ 配置文件导入失败，请确保config.py文件存在且配置正确")
    exit(1)

class SSLAdapter(HTTPAdapter):
    """自定义SSL适配器，支持更宽松的SSL配置"""
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        context.set_ciphers('DEFAULT@SECLEVEL=1')  # 降低安全级别
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('qiangpiao.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 创建全局session对象并配置SSL适配器
session = requests.Session()
session.mount('https://', SSLAdapter())


raw_cookie = """
EMAP_LANG=zh;
"""

# 解析Cookie字符串
cookies = {}
for item in raw_cookie.strip().split("; "):
    key, value = item.split("=", 1)
    cookies[key] = value

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Referer": "https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/index.do",
    "Origin": "https://ehall.szu.edu.cn",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "X-Requested-With": "XMLHttpRequest"
}

def get_time_priority(time_name):
    """根据时段名称获取优先级，数字越小优先级越高"""
    for i, preferred_time in enumerate(CONFIG["PREFERRED_TIMES"]):
        if preferred_time in time_name:
            return i
    return 999  # 未匹配的时段优先级最低

def is_time_slot_valid(time_slot, target_date):
    """检查时段是否有效（未过期）"""
    try:
        from datetime import datetime, timedelta
        
        # 如果是今天，检查时间是否已过
        today = datetime.now().strftime("%Y-%m-%d")
        if target_date == today:
            current_time = datetime.now().time()
            start_time_str = time_slot.split("-")[0]
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            
            # 如果当前时间已经超过开始时间，则该时段无效
            if current_time >= start_time and current_time > start_time + timedelta(hours=1):
                return False
        
        return True
    except Exception as e:
        logging.debug(f"时间验证错误: {e}")
        return True  # 出错时默认认为有效

def get_available_slots():
    """获取可用时段和场地"""
    try:
        # 遍历优先时段，查询每个时段的可用场地
        all_available = []
        
        for time_slot in CONFIG["PREFERRED_TIMES"]:
            # 检查时段是否还有效
            if not is_time_slot_valid(time_slot, CONFIG["TARGET_DATE"]):
                logging.info(f"跳过已过期时段: {time_slot}")
                continue
                
            start_time, end_time = time_slot.split("-")
            
            payload = {
                "XMDM": CONFIG["XMDM"],
                "YYRQ": CONFIG["TARGET_DATE"], 
                "YYLX": CONFIG["YYLX"],
                "KSSJ": start_time,
                "JSSJ": end_time,
                "XQDM": CONFIG["XQ"]
            }

            logging.info(f"正在查询 {CONFIG['TARGET_DATE']} {time_slot} 的可用场地...")
            
            resp = session.post(
                "https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/modules/sportVenue/getOpeningRoom.do",
                headers=headers,
                cookies=cookies,
                data=payload,
                verify=False,
                timeout=CONFIG["REQUEST_TIMEOUT"]
            )
            
            resp.raise_for_status()
            data = resp.json()
            
            # 解析响应数据
            if data.get("code") == "0" and "datas" in data:
                rooms = data["datas"].get("getOpeningRoom", {}).get("rows", [])
                
                available_count = 0
                for room in rooms:
                    # 只选择可预约的场地
                    if not room.get("disabled", True) and room.get("text") == "可预约":
                        slot_info = {
                            'name': f"{time_slot} - {room.get('CDMC', '未知场地')}",
                            'wid': room['WID'],
                            'time_slot': time_slot,
                            'start_time': start_time,
                            'end_time': end_time,
                            'venue_name': room.get('CDMC', ''),
                            'venue_code': room.get('CGBM', ''),
                            'priority': CONFIG["PREFERRED_TIMES"].index(time_slot)
                        }
                        all_available.append(slot_info)
                        available_count += 1
                        logging.info(f"可预约场地：{slot_info['name']}，WID：{slot_info['wid']}")
                
                if available_count == 0:
                    logging.info(f"时段 {time_slot} 暂无可预约场地")
            else:
                logging.warning(f"查询时段 {time_slot} 失败: {data}")
        
        # 按优先级排序
        all_available.sort(key=lambda x: x['priority'])
        return all_available
        
    except requests.exceptions.SSLError as e:
        logging.error(f"SSL错误: {e}")
        return []
    except requests.exceptions.Timeout as e:
        logging.error(f"请求超时: {e}")
        return []
    except requests.exceptions.RequestException as e:
        logging.error(f"请求错误: {e}")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"JSON解析错误: {e}")
        return []
    except Exception as e:
        logging.error(f"未知错误: {e}")
        return []


def get_csrf_token():
    """获取CSRF Token"""
    try:
        # 先访问预约页面，获取必要的token
        resp = session.get(
            "https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/index.do",
            headers=headers,
            cookies=cookies,
            verify=False,
            timeout=CONFIG["REQUEST_TIMEOUT"]
        )
        
        # 尝试从页面中提取CSRF token
        import re
        csrf_pattern = r'csrfToken["\']?\s*[:=]\s*["\']([^"\']+)["\']'
        csrf_match = re.search(csrf_pattern, resp.text, re.IGNORECASE)
        
        if csrf_match:
            csrf_token = csrf_match.group(1)
            logging.debug(f"找到CSRF Token: {csrf_token}")
            return csrf_token
        else:
            logging.debug("未找到CSRF Token")
            return None
            
    except Exception as e:
        logging.error(f"获取CSRF Token失败: {e}")
        return None

def establish_session():
    """建立完整的会话状态"""
    try:
        logging.debug("正在建立会话状态...")
        
        # 1. 访问主页
        resp1 = session.get(
            "https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/index.do",
            headers=headers,
            cookies=cookies,
            verify=False,
            timeout=CONFIG["REQUEST_TIMEOUT"]
        )
        logging.debug(f"主页访问: {resp1.status_code}")
        
        # 2. 先查询一个时段来建立上下文
        if CONFIG["PREFERRED_TIMES"]:
            start_time, end_time = CONFIG["PREFERRED_TIMES"][0].split("-")
            query_payload = {
                "XMDM": CONFIG["XMDM"],
                "YYRQ": CONFIG["TARGET_DATE"],
                "YYLX": CONFIG["YYLX"],
                "KSSJ": start_time,
                "JSSJ": end_time,
                "XQDM": CONFIG["XQ"]
            }
            
            resp2 = session.post(
                "https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/modules/sportVenue/getOpeningRoom.do",
                headers=headers,
                cookies=cookies,
                data=query_payload,
                verify=False,
                timeout=CONFIG["REQUEST_TIMEOUT"]
            )
            logging.debug(f"场地查询: {resp2.status_code}")
        
        # 3. 获取CSRF Token
        csrf_token = get_csrf_token()
        
        return csrf_token
        
    except Exception as e:
        logging.error(f"建立会话状态失败: {e}")
        return None


def book_slot(wid, slot_name):
    """预约指定场地时段"""
    try:
        # 建立会话状态并获取CSRF token
        csrf_token = establish_session()
        
        # 从slot_name中提取时间信息
        time_slot = None
        venue_code = "111" # 默认场馆代码
        
        for preferred_time in CONFIG["PREFERRED_TIMES"]:
            if preferred_time in slot_name:
                time_slot = preferred_time
                break
        
        if not time_slot:
            logging.error(f"无法从 {slot_name} 中提取时间信息")
            return False
        
        # 从场地名称推断场馆代码
        if "至畅" in slot_name:
            venue_code = "104"  # 至畅体育馆
        elif "至快" in slot_name:
            venue_code = "111"  # 至快体育馆
        
        start_time, end_time = time_slot.split("-")
        
        # 构建预约请求的payload
        book_payload = {
            "DHID": "",  # 空的DHID
            "YYRGH": CONFIG["USER_INFO"]["YYRGH"],  # 从配置获取学号/工号
            "CYRS": "",  # 参与人数
            "YYRXM": CONFIG["USER_INFO"]["YYRXM"],  # 从配置获取姓名
            "CGDM": venue_code,  # 根据场地动态设置场馆代码
            "CDWID": wid,  # 场地WID
            "XMDM": CONFIG["XMDM"],  # 项目代码
            "XQWID": CONFIG["XQ"],  # 校区代码
            "KYYSJD": time_slot,  # 可用时间段
            "YYRQ": CONFIG["TARGET_DATE"],  # 预约日期
            "YYLX": CONFIG["YYLX"],  # 预约类型
            "YYKS": f"{CONFIG['TARGET_DATE']} {start_time}",  # 预约开始时间
            "YYJS": f"{CONFIG['TARGET_DATE']} {end_time}",   # 预约结束时间
            "PC_OR_PHONE": "pc"  # 平台标识
        }
        
        # 如果有CSRF token，添加到payload中
        if csrf_token:
            book_payload["csrfToken"] = csrf_token
            book_payload["_token"] = csrf_token
        
        # 创建增强的请求头
        enhanced_headers = headers.copy()
        enhanced_headers.update({
            "Accept": "*/*",  # 改为通配符
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors", 
            "Sec-Fetch-Site": "same-origin",
            "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"'
        })
        
        logging.info(f"正在预约场地：{slot_name} (WID: {wid}, 场馆: {venue_code})")
        logging.debug(f"预约参数: {book_payload}")
        
        # 添加短暂延迟，模拟人工操作
        time.sleep(0.5)
        
        # 使用正确的预约接口
        booking_url = "https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/sportVenue/insertVenueBookingInfo.do"
        
        resp = session.post(
            booking_url,
            headers=enhanced_headers,
            cookies=cookies,
            data=book_payload,
            verify=False,
            timeout=CONFIG["REQUEST_TIMEOUT"]
        )
        
        logging.debug(f"响应状态码: {resp.status_code}")
        logging.debug(f"响应头: {dict(resp.headers)}")
        
        # 如果是403错误，记录详细信息
        if resp.status_code == 403:
            logging.error(f"403 Forbidden错误:")
            logging.error(f"URL: {resp.url}")
            logging.error(f"响应内容: {resp.text[:500]}")
            return False
        
        resp.raise_for_status()
        
        # 解析JSON响应
        try:
            result = resp.json()
            logging.debug(f"预约响应: {result}")
            
            # 检查预约结果 - 根据真实API响应格式
            if result.get("code") == "0" and result.get("msg") == "成功":
                dhid = result.get("data", {}).get("DHID", "")
                logging.info(f"✅ 预约成功！场地：{slot_name}")
                logging.info(f"✅ 预约单号：{dhid}")
                print(f"🎉 预约详情:")
                print(f"   📅 日期: {CONFIG['TARGET_DATE']}")
                print(f"   ⏰ 时间: {time_slot}")
                print(f"   🏟️  场地: {slot_name}")
                print(f"   📋 单号: {dhid}")
                
                # 更新全局预约记录中的单号
                global successful_bookings
                if 'successful_bookings' in globals():
                    for booking in successful_bookings:
                        if booking.get('dhid') == 'Unknown' and booking['time_slot'] == time_slot:
                            booking['dhid'] = dhid
                            break
                
                return True
            else:
                error_msg = result.get("msg", "未知错误")
                error_code = result.get("code", "")
                logging.warning(f"❌ 预约失败：[{error_code}] {error_msg}")
                
                # 检查具体的失败原因并给出建议
                if "已过该预约时间" in error_msg:
                    logging.info("💡 建议：请将目标日期设置为明天或更晚的日期")
                elif "已被预约" in error_msg or "已满员" in error_msg:
                    logging.info("💡 该场地已被他人预约，尝试其他场地")
                elif "权限" in error_msg:
                    logging.info("💡 可能没有预约权限，请检查账号状态")
                elif "时间" in error_msg:
                    logging.info("💡 时间相关错误，建议检查预约时间设置")
                elif "只能预订2次" in error_msg or "超过限制" in error_msg:
                    logging.info("🎊 恭喜！您已达到预约上限")
                    print("🎊 检测到已达到当日预约上限！")
                
                return False
                
        except json.JSONDecodeError as e:
            logging.error(f"JSON解析错误: {e}")
            logging.error(f"响应内容: {resp.text[:500]}")
            
            # 检查是否有成功的HTML响应
            if ("成功" in resp.text or 
                "success" in resp.text.lower() or
                "预约完成" in resp.text):
                logging.info(f"✅ 预约成功！场地：{slot_name} (HTML响应)")
                return True
            
            return False
            
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP错误: {e}")
        if e.response:
            logging.error(f"响应状态码: {e.response.status_code}")
            logging.error(f"响应内容: {e.response.text[:500]}")
        return False
    except Exception as e:
        logging.error(f"预约时发生错误: {e}")
        return False


def check_login_status():
    """检查登录状态"""
    try:
        resp = session.get(
            "https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/index.do",
            headers=headers,
            cookies=cookies,
            verify=False,
            timeout=CONFIG["REQUEST_TIMEOUT"]
        )
        
        logging.debug(f"登录检查 - 状态码: {resp.status_code}")
        logging.debug(f"响应长度: {len(resp.text)}")
        
        if resp.status_code == 403:
            logging.error("收到403错误，可能是Cookie已失效或IP被限制")
            logging.error(f"响应内容: {resp.text[:200]}")
            return False
            
        if "登录" in resp.text or resp.status_code == 401:
            logging.error("❌ 登录状态已失效，请重新获取cookie")
            return False
        
        # 检查是否包含预期的页面内容
        if "体育场馆" in resp.text or "sportVenue" in resp.text:
            logging.info("登录状态验证成功")
            return True
        else:
            logging.warning("页面内容异常，可能需要重新登录")
            logging.debug(f"页面内容片段: {resp.text[:200]}")
            return False
        
    except Exception as e:
        logging.error(f"检查登录状态时出错: {e}")
        return False

def auto_handle_cookie_expiry():
    """自动处理Cookie过期"""
    print("🔧 检测到Cookie可能已过期")
    print("\n自动解决方案:")
    print("1. 手动更新Cookie (推荐)")
    print("2. 跳过检查继续运行")
    print("3. 退出程序")
    
    choice = input("\n请选择 (1-3): ").strip()
    
    if choice == "1":
        try:
            import subprocess
            result = subprocess.run(["python", "cookie_manager.py", "update"], 
                                  capture_output=False, text=True)
            if result.returncode == 0:
                print("✅ Cookie更新完成，请重新启动脚本")
                return False
            else:
                print("❌ Cookie更新失败")
                return False
        except FileNotFoundError:
            print("❌ 找不到cookie_manager.py文件")
            print("💡 请手动运行: python cookie_manager.py update")
            return False
    elif choice == "2":
        print("⚠️  跳过检查，继续运行（可能会出现错误）")
        return True
    else:
        print("程序退出")
        return False

def print_statistics(retry_count, start_time):
    """打印统计信息"""
    elapsed = datetime.now() - start_time
    print(f"\n📊 运行统计:")
    print(f"   ⏱️  运行时间: {elapsed}")
    print(f"   🔄 查询次数: {retry_count}")
    print(f"   📅 目标日期: {CONFIG['TARGET_DATE']}")


def debug_request_info():
    """调试请求信息"""
    print("\n🔍 调试信息:")
    print(f"   目标URL: https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/sportVenue/bookVenue.do")
    print(f"   User-Agent: {headers.get('User-Agent', 'N/A')}")
    print(f"   Cookies数量: {len(cookies)}")
    print(f"   主要Cookie: {list(cookies.keys())[:3]}")
    
    # 测试基础连接
    try:
        resp = session.get("https://ehall.szu.edu.cn", timeout=5, verify=False)
        print(f"   基础连接: ✅ ({resp.status_code})")
    except Exception as e:
        print(f"   基础连接: ❌ ({e})")


if __name__ == "__main__":
    print("=" * 60)
    print("🎾 深圳大学体育场馆预约脚本 v1.0")
    print("=" * 60)
    print(f"📅 目标日期: {CONFIG['TARGET_DATE']}")
    print(f"🏫 校区: {'丽湖' if CONFIG['XQ'] == '2' else '粤海'}")
    print(f"🏸 项目: 羽毛球" if CONFIG['XMDM'] == '001' else f"🏓 项目: 其他")
    print(f"👤 预约人: {CONFIG['USER_INFO']['YYRXM']} ({CONFIG['USER_INFO']['YYRGH']})")
    print(f"⏱️  重试间隔: {CONFIG['RETRY_INTERVAL']}秒")
    print(f"🔄 最大重试: {CONFIG['MAX_RETRY_TIMES']}次")
    print(f"🎯 预约目标: 最多2个不同时间段")
    print("=" * 60)
    
    # 检查目标日期
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    if CONFIG["TARGET_DATE"] <= today:
        print("⚠️  建议：目标日期应设置为明天或更晚，以避免时间冲突")
    
    # 检查用户信息
    if (CONFIG["USER_INFO"]["YYRGH"] == "" or 
        CONFIG["USER_INFO"]["YYRXM"] == ""):
        print("⚠️  警告：请在config.py中修改为您的真实学号和姓名！")
        confirm = input("是否继续测试？(y/N): ")
        if confirm.lower() != 'y':
            print("程序退出。")
            exit(0)
    
    # 启用调试日志（可选）
    if "--debug" in sys.argv:
        logging.getLogger().setLevel(logging.DEBUG)
        print("🐛 调试模式已启用")
    
    logging.info("🚀 深圳大学体育场馆抢票脚本启动")
    
    # 显示调试信息
    debug_request_info()
    
    # 检查登录状态
    print("\n🔐 检查登录状态...")
    if not check_login_status():
        print("❌ 登录状态失效")
        
        # 自动处理Cookie过期
        if not auto_handle_cookie_expiry():
            print("\n💡 其他解决方案:")
            print("   1. 运行: python cookie_manager.py update")
            print("   2. 检查网络连接")
            print("   3. 确认账号未被限制")
            input("\n按回车键退出...")
            exit(1)
    else:
        print("✅ 登录状态正常")
    
    print("\n🔍 开始监控可用时段...")
    print("💡 按 Ctrl+C 可随时停止程序")
    print("💡 如需调试信息，请使用: python qiangpiao.py --debug")
    print("-" * 60)
    
    # 配置参数
    MAX_RETRY_TIMES = CONFIG["MAX_RETRY_TIMES"]
    RETRY_INTERVAL = CONFIG["RETRY_INTERVAL"]
    
    retry_count = 0
    start_time = datetime.now()
    
    # 预约成功记录
    successful_bookings = []
    max_bookings = 2  # 最多预约2个时间段
    
    try:
        while retry_count < MAX_RETRY_TIMES:
            try:
                current_time = datetime.now().strftime("%H:%M:%S")
                print(f"\n[{current_time}] 📡 第 {retry_count + 1} 次查询... (已预约: {len(successful_bookings)}/{max_bookings})")
                
                # 如果已经预约满了，显示成功信息并退出
                if len(successful_bookings) >= max_bookings:
                    print(f"\n🎊 恭喜！已成功预约 {max_bookings} 个时间段！")
                    print("\n📋 预约详情:")
                    for i, booking in enumerate(successful_bookings, 1):
                        print(f"   {i}. {booking['time_slot']} - {booking['venue_name']}")
                        print(f"      📋 预约单号: {booking['dhid']}")
                    print_statistics(retry_count, start_time)
                    input("\n按回车键退出...")
                    exit(0)
                
                available_slots = get_available_slots()
                
                if available_slots:
                    print(f"🎉 找到 {len(available_slots)} 个可预约时段!")
                    
                    # 过滤掉已经预约过的时间段
                    booked_time_slots = [booking['time_slot'] for booking in successful_bookings]
                    remaining_slots = [slot for slot in available_slots 
                                     if slot['time_slot'] not in booked_time_slots]
                    
                    if not remaining_slots:
                        print("📭 当前可用时段都已预约过，继续监控新时段...")
                    else:
                        print(f"🔍 过滤后剩余 {len(remaining_slots)} 个新时段可预约:")
                        
                        # 按时间段分组，每个时间段只显示第一个场地
                        time_slot_groups = {}
                        for slot in remaining_slots:
                            if slot['time_slot'] not in time_slot_groups:
                                time_slot_groups[slot['time_slot']] = []
                            time_slot_groups[slot['time_slot']].append(slot)
                        
                        # 显示每个时间段的第一个场地
                        display_slots = []
                        for time_slot in CONFIG["PREFERRED_TIMES"]:
                            if time_slot in time_slot_groups:
                                display_slots.append(time_slot_groups[time_slot][0])
                        
                        for i, slot in enumerate(display_slots, 1):
                            venue_count = len(time_slot_groups[slot['time_slot']])
                            print(f"   {i}. {slot['time_slot']} ({venue_count}个场地可选) - 优先级: {slot['priority']}")
                        
                        # 按时间段优先级尝试预约
                        for time_slot in CONFIG["PREFERRED_TIMES"]:
                            # 如果已经预约满了，跳出循环
                            if len(successful_bookings) >= max_bookings:
                                break
                            
                            # 如果该时间段已经预约过，跳过
                            if time_slot in booked_time_slots:
                                continue
                            
                            # 如果该时间段有可用场地，尝试预约第一个
                            if time_slot in time_slot_groups:
                                slots_in_time = time_slot_groups[time_slot]
                                first_slot = slots_in_time[0]  # 选择第一个可用场地
                                
                                print(f"\n🎯 尝试预约时间段 {time_slot}:")
                                print(f"   选择场地: {first_slot['venue_name']} (共{len(slots_in_time)}个可选)")
                                
                                success = book_slot(first_slot['wid'], first_slot['name'])
                                
                                if success:
                                    # 记录成功的预约
                                    booking_record = {
                                        'time_slot': first_slot['time_slot'],
                                        'venue_name': first_slot['venue_name'],
                                        'dhid': 'Unknown',  # 在book_slot函数中会更新
                                        'slot_name': first_slot['name']
                                    }
                                    successful_bookings.append(booking_record)
                                    
                                    print(f"🎉 预约成功！当前已预约 {len(successful_bookings)}/{max_bookings} 个时间段")
                                    
                                    # 如果还没预约满，继续下一个时间段
                                    if len(successful_bookings) < max_bookings:
                                        print(f"💡 继续尝试预约下一个时间段...")
                                        time.sleep(1)  # 短暂延迟
                                    else:
                                        # 预约满了，显示成功信息并退出
                                        print(f"\n🎊 太棒了！已成功预约满 {max_bookings} 个时间段！")
                                        print("\n📋 最终预约详情:")
                                        for i, booking in enumerate(successful_bookings, 1):
                                            print(f"   {i}. {booking['slot_name']}")
                                        print_statistics(retry_count + 1, start_time)
                                        input("\n按回车键退出...")
                                        exit(0)
                                else:
                                    print(f"❌ 时间段 {time_slot} 预约失败，尝试下一个时间段...")
                                    
                                    # 检查是否是预约上限错误
                                    if "只能预订2次" in str(logging.getLogger().handlers):
                                        print("🎊 检测到已达到预约上限，停止尝试")
                                        break
                                    
                                    time.sleep(1)  # 短暂延迟
                        
                        # 如果所有时间段都尝试过了但还没预约满
                        if len(successful_bookings) < max_bookings:
                            print("⚠️  所有可用时间段都尝试过了，继续监控...")
                
                else:
                    print("📭 暂无可预约时段")
                
                retry_count += 1
                
                # 如果还没预约满且没有达到最大重试次数，继续监控
                if len(successful_bookings) < max_bookings and retry_count < MAX_RETRY_TIMES:
                    print(f"⏳ 等待 {RETRY_INTERVAL} 秒后重试...")
                    for i in range(RETRY_INTERVAL, 0, -1):
                        print(f"\r⏱️  倒计时: {i} 秒 | 已预约: {len(successful_bookings)}/{max_bookings}", end="", flush=True)
                        time.sleep(1)
                    print("\r" + " " * 50 + "\r", end="")  # 清除倒计时
                
            except KeyboardInterrupt:
                print("\n\n⛔ 用户手动停止程序")
                break
            except Exception as e:
                print(f"\n❌ 程序执行错误: {e}")
                logging.error(f"程序执行错误: {e}")
                retry_count += 1
                if retry_count < MAX_RETRY_TIMES:
                    time.sleep(RETRY_INTERVAL)
        
        print("\n⏹️  程序结束")
        
        # 显示最终统计
        if successful_bookings:
            print(f"\n🎉 预约成功统计: {len(successful_bookings)}/{max_bookings} 个时间段")
            print("📋 成功预约的时段:")
            for i, booking in enumerate(successful_bookings, 1):
                print(f"   {i}. {booking['slot_name']}")
        else:
            print("\n😢 很遗憾，没有成功预约到任何时段")
        
        print_statistics(retry_count, start_time)
        
        if retry_count >= MAX_RETRY_TIMES and len(successful_bookings) < max_bookings:
            print(f"⏰ 已达到最大重试次数，当前预约 {len(successful_bookings)}/{max_bookings} 个时间段")
        
    except KeyboardInterrupt:
        print("\n\n⛔ 程序被用户中断")
        if successful_bookings:
            print(f"\n📊 中断前已预约: {len(successful_bookings)}/{max_bookings} 个时间段")
            for i, booking in enumerate(successful_bookings, 1):
                print(f"   {i}. {booking['slot_name']}")
        print_statistics(retry_count, start_time)
    
    input("\n按回车键退出...")

    
def extract_cookies_from_text(cookie_text):
    """从文本中提取并解析Cookie"""
    cookies = {}
    
    # 处理不同格式的Cookie字符串
    cookie_text = cookie_text.strip()
    
    # 如果是浏览器复制的格式（分号分隔）
    if ';' in cookie_text:
        for item in cookie_text.split(';'):
            item = item.strip()
            if '=' in item:
                key, value = item.split('=', 1)
                cookies[key.strip()] = value.strip()
    
    # 如果是多行格式
    elif '\n' in cookie_text:
        for line in cookie_text.split('\n'):
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                cookies[key.strip()] = value.strip()
    
    return cookies

def test_cookie_validity(cookies_dict):
    """测试Cookie是否有效"""
    try:
        resp = session.get(
            "https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/index.do",
            headers=headers,
            cookies=cookies_dict,
            verify=False,
            timeout=10
        )
        
        # 检查响应
        if resp.status_code == 200:
            if "登录" in resp.text or "login" in resp.text.lower():
                return False, "需要重新登录"
            elif "体育场馆" in resp.text or "sportVenue" in resp.text:
                return True, "Cookie有效"
            else:
                return False, "页面内容异常"
        elif resp.status_code == 403:
            return False, "访问被拒绝"
        else:
            return False, f"HTTP错误: {resp.status_code}"
            
    except Exception as e:
        return False, f"测试失败: {e}"

def update_cookie_in_file(new_cookie_text):
    """更新文件中的Cookie"""
    try:
        # 读取原文件
        with open('qiangpiao.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换cookie
        start_marker = 'raw_cookie = """'
        end_marker = '"""'
        
        start_idx = content.find(start_marker)
        if start_idx == -1:
            logging.error("未找到cookie位置！")
            return False
        
        start_idx += len(start_marker)
        end_idx = content.find(end_marker, start_idx)
        
        if end_idx == -1:
            logging.error("未找到cookie结束位置！")
            return False
        
        new_content = content[:start_idx] + '\n' + new_cookie_text + '\n' + content[end_idx:]
        
        # 写入文件
        with open('qiangpiao.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        logging.info("Cookie更新成功！")
        
        # 重新加载cookies到全局变量
        global cookies
        cookies = extract_cookies_from_text(new_cookie_text)
        
        return True
        
    except Exception as e:
        logging.error(f"更新失败: {e}")
        return False
