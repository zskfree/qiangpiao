# 场地监控脚本 - 实时监控场地状态变化
import time
import json
from datetime import datetime
from qiangpiao import get_available_slots, CONFIG

def monitor_venues():
    """监控场地状态变化"""
    print("=" * 60)
    print("👁️  场地状态监控器")
    print("=" * 60)
    print(f"📅 监控日期: {CONFIG['TARGET_DATE']}")
    print(f"🏫 校区: {'丽湖' if CONFIG['XQ'] == '2' else '粤海'}")
    print(f"🏸 项目: 羽毛球")
    print(f"⏱️  检查间隔: {CONFIG['RETRY_INTERVAL']} 秒")
    print("=" * 60)
    
    previous_status = {}
    check_count = 0
    
    try:
        while True:
            check_count += 1
            current_time = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{current_time}] 🔍 第 {check_count} 次检查...")
            
            available_slots = get_available_slots()
            
            # 按时段分组
            current_status = {}
            for slot in available_slots:
                time_slot = slot['time_slot']
                if time_slot not in current_status:
                    current_status[time_slot] = []
                current_status[time_slot].append(slot['venue_name'])
            
            # 检查变化
            changes_detected = False
            
            for time_slot in CONFIG["PREFERRED_TIMES"]:
                current_venues = set(current_status.get(time_slot, []))
                previous_venues = set(previous_status.get(time_slot, []))
                
                # 新增的场地
                new_venues = current_venues - previous_venues
                # 消失的场地
                lost_venues = previous_venues - current_venues
                
                if new_venues:
                    changes_detected = True
                    print(f"🆕 {time_slot} 新增可预约场地:")
                    for venue in new_venues:
                        print(f"   ✅ {venue}")
                
                if lost_venues:
                    changes_detected = True
                    print(f"🚫 {time_slot} 场地已被预约:")
                    for venue in lost_venues:
                        print(f"   ❌ {venue}")
                
                if current_venues and not (new_venues or lost_venues):
                    print(f"📍 {time_slot}: {len(current_venues)} 个场地可预约")
                elif not current_venues and not lost_venues:
                    print(f"📍 {time_slot}: 暂无可预约场地")
            
            if not changes_detected and available_slots:
                print(f"📊 状态无变化，当前共 {len(available_slots)} 个可预约场地")
            elif not available_slots:
                print("📭 暂无可预约场地")
            
            # 更新状态
            previous_status = current_status.copy()
            
            # 等待下次检查
            print(f"⏱️  等待 {CONFIG['RETRY_INTERVAL']} 秒...")
            for i in range(CONFIG['RETRY_INTERVAL'], 0, -1):
                print(f"\r⏳ 倒计时: {i} 秒", end="", flush=True)
                time.sleep(1)
            print("\r" + " " * 20 + "\r", end="")
            
    except KeyboardInterrupt:
        print(f"\n\n⛔ 监控已停止")
        print(f"📊 总检查次数: {check_count}")

if __name__ == "__main__":
    monitor_venues()
