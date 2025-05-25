# 查询测试脚本 - 用于测试场地查询功能
import requests
import json
import logging
from datetime import datetime, timedelta
import urllib3
from qiangpiao import session, headers, cookies, CONFIG

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_query_detailed(date, time_slot):
    """详细测试单个时段的查询结果"""
    start_time, end_time = time_slot.split("-")
    
    payload = {
        "XMDM": CONFIG["XMDM"],
        "YYRQ": date, 
        "YYLX": CONFIG["YYLX"],
        "KSSJ": start_time,
        "JSSJ": end_time,
        "XQDM": CONFIG["XQ"]
    }

    print(f"\n🔍 查询 {date} {time_slot}")
    print(f"   请求参数: {payload}")
    
    try:
        resp = session.post(
            "https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/modules/sportVenue/getOpeningRoom.do",
            headers=headers,
            cookies=cookies,
            data=payload,
            verify=False,
            timeout=10
        )
        
        print(f"   响应状态: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"   响应代码: {data.get('code', 'N/A')}")
            
            if data.get("code") == "0" and "datas" in data:
                rooms = data["datas"].get("getOpeningRoom", {}).get("rows", [])
                print(f"   总场地数: {len(rooms)}")
                
                available_count = 0
                occupied_count = 0
                
                for room in rooms:
                    status = room.get("text", "未知")
                    disabled = room.get("disabled", True)
                    venue_name = room.get("CDMC", "未知场地")
                    
                    if not disabled and status == "可预约":
                        available_count += 1
                        print(f"   ✅ {venue_name} - {status}")
                    else:
                        occupied_count += 1
                        print(f"   ❌ {venue_name} - {status}")
                
                print(f"   📊 统计: 可预约 {available_count} 个, 已占用 {occupied_count} 个")
            else:
                print(f"   ⚠️  查询失败: {data}")
        else:
            print(f"   ❌ HTTP错误: {resp.status_code}")
            print(f"   响应内容: {resp.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ 查询异常: {e}")

def test_multiple_dates():
    """测试多个日期的场地情况"""
    print("=" * 60)
    print("📅 多日期场地查询测试")
    print("=" * 60)
    
    # 测试今天、明天的场地情况
    base_date = datetime.now()
    dates_to_test = []
    
    for i in range(2):
        test_date = base_date + timedelta(days=i)
        dates_to_test.append(test_date.strftime("%Y-%m-%d"))
    
    print(f"测试日期: {', '.join(dates_to_test)}")
    print(f"测试时段: {', '.join(CONFIG['PREFERRED_TIMES'])}")
    print()
    
    for date in dates_to_test:
        print(f"\n{'='*20} {date} {'='*20}")
        
        for time_slot in CONFIG["PREFERRED_TIMES"]:
            test_query_detailed(date, time_slot)
        
        print()

def test_all_time_slots():
    """测试所有可能的时段"""
    print("=" * 60)
    print("⏰ 全时段查询测试")
    print("=" * 60)
    
    # 常见的体育馆开放时段
    all_time_slots = [
        "08:00-09:00", "09:00-10:00", "10:00-11:00", "11:00-12:00",
        "14:00-15:00", "15:00-16:00", "16:00-17:00", "17:00-18:00",
        "18:00-19:00", "19:00-20:00", "20:00-21:00", "21:00-22:00"
    ]
    
    target_date = CONFIG["TARGET_DATE"]
    print(f"目标日期: {target_date}")
    print()
    
    available_summary = []
    
    for time_slot in all_time_slots:
        start_time, end_time = time_slot.split("-")
        
        payload = {
            "XMDM": CONFIG["XMDM"],
            "YYRQ": target_date, 
            "YYLX": CONFIG["YYLX"],
            "KSSJ": start_time,
            "JSSJ": end_time,
            "XQDM": CONFIG["XQ"]
        }
        
        try:
            resp = session.post(
                "https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/modules/sportVenue/getOpeningRoom.do",
                headers=headers,
                cookies=cookies,
                data=payload,
                verify=False,
                timeout=10
            )
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == "0" and "datas" in data:
                    rooms = data["datas"].get("getOpeningRoom", {}).get("rows", [])
                    available_count = sum(1 for room in rooms 
                                        if not room.get("disabled", True) and room.get("text") == "可预约")
                    total_count = len(rooms)
                    
                    status = f"{available_count}/{total_count}" if total_count > 0 else "无数据"
                    print(f"{time_slot}: {status} 可预约")
                    
                    if available_count > 0:
                        available_summary.append((time_slot, available_count))
                else:
                    print(f"{time_slot}: 查询失败")
            else:
                print(f"{time_slot}: HTTP {resp.status_code}")
                
        except Exception as e:
            print(f"{time_slot}: 异常 - {e}")
    
    print(f"\n📊 可预约时段汇总:")
    if available_summary:
        for time_slot, count in available_summary:
            print(f"   {time_slot}: {count} 个场地可预约")
    else:
        print("   暂无可预约时段")

if __name__ == "__main__":
    print("🧪 场地查询测试工具")
    print("1. 多日期测试")
    print("2. 全时段测试") 
    print("3. 单个时段详细测试")
    
    choice = input("\n请选择测试类型 (1/2/3): ").strip()
    
    if choice == "1":
        test_multiple_dates()
    elif choice == "2":
        test_all_time_slots()
    elif choice == "3":
        date = input("请输入日期 (格式: 2025-05-26): ").strip()
        time_slot = input("请输入时段 (格式: 19:00-20:00): ").strip()
        test_query_detailed(date, time_slot)
    else:
        print("❌ 无效选择")
