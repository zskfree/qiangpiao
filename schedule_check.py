# 定时检查脚本 - 在指定时间启动抢票
import time
import subprocess
from datetime import datetime, timedelta

def wait_until_time(target_time_str):
    """等待到指定时间"""
    print(f"⏰ 等待到 {target_time_str} 启动抢票...")
    
    while True:
        now = datetime.now()
        current_time_str = now.strftime("%H:%M:%S")
        
        # 解析目标时间
        try:
            target_time = datetime.strptime(target_time_str, "%H:%M:%S").time()
            current_time = now.time()
            
            # 如果目标时间已过，设为明天
            if current_time > target_time:
                target_datetime = datetime.combine(now.date() + timedelta(days=1), target_time)
            else:
                target_datetime = datetime.combine(now.date(), target_time)
            
            time_diff = (target_datetime - now).total_seconds()
            
            if time_diff <= 0:
                print(f"\n🚀 时间到！启动抢票程序...")
                return True
            
            # 显示倒计时
            hours = int(time_diff // 3600)
            minutes = int((time_diff % 3600) // 60)
            seconds = int(time_diff % 60)
            
            print(f"\r⏳ 当前时间: {current_time_str} | 倒计时: {hours:02d}:{minutes:02d}:{seconds:02d}", end="", flush=True)
            time.sleep(1)
            
        except ValueError:
            print("❌ 时间格式错误，请使用 HH:MM:SS 格式")
            return False

def schedule_booking():
    """定时抢票主函数"""
    print("=" * 60)
    print("⏰ 定时抢票助手")
    print("=" * 60)
    print("💡 提示：建议在场地开放前几分钟启动")
    print("💡 例如：如果场地8:00开放，建议7:59:50启动")
    print()
    
    # 常见的开放时间
    common_times = [
        "07:59:50",  # 8点开放前10秒
        "11:59:50",  # 12点开放前10秒
        "21:11:50",  # 21点开放前10秒
    ]
    
    print("常见开放时间:")
    for i, time_str in enumerate(common_times, 1):
        print(f"  {i}. {time_str}")
    
    print("  4. 自定义时间")
    
    choice = input("\n请选择启动时间 (1-4): ").strip()
    
    target_time = None
    if choice in ["1", "2", "3"]:
        target_time = common_times[int(choice) - 1]
    elif choice == "4":
        target_time = input("请输入启动时间 (格式: HH:MM:SS): ").strip()
    else:
        print("❌ 无效选择")
        return
    
    if not target_time:
        print("❌ 时间不能为空")
        return
    
    print(f"\n✅ 已设置启动时间: {target_time}")
    print("💡 程序将在指定时间自动启动抢票脚本")
    print("💡 按 Ctrl+C 可随时取消")
    
    # 等待到指定时间
    if wait_until_time(target_time):
        try:
            # 启动抢票脚本
            subprocess.run(["python", "qiangpiao.py"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ 启动抢票脚本失败: {e}")
        except FileNotFoundError:
            print("❌ 找不到 qiangpiao.py 文件")

if __name__ == "__main__":
    try:
        schedule_booking()
    except KeyboardInterrupt:
        print(f"\n\n⛔ 定时任务已取消")
