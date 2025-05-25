#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深大羽球预约 Web版启动脚本
"""

import os
import sys
import webbrowser
import time
import logging
import signal
import atexit
import threading
from threading import Timer

# 全局变量记录所有运行的线程
active_threads = []
app_instance = None

def cleanup_on_exit():
    """程序退出时的清理函数"""
    try:
        # 停止所有活跃线程
        for thread in active_threads:
            if thread.is_alive():
                # 强制停止线程（通过标记）
                if hasattr(thread, '_stop_event'):
                    thread._stop_event.set()
        
        # 如果有web_app实例，停止抢票
        if app_instance:
            try:
                from web_app import booking_status
                booking_status['running'] = False
            except:
                pass
        
        # 清理临时文件
        cleanup_temp_files()
        
    except Exception:
        pass

def cleanup_temp_files():
    """清理临时文件"""
    try:
        temp_files = [f for f in os.listdir('.') if f.endswith(('.tmp', '.temp', '.lock'))]
        for temp_file in temp_files:
            os.remove(temp_file)
    except Exception:
        pass

def signal_handler(signum, frame):
    """信号处理函数"""
    cleanup_on_exit()
    sys.exit(0)

def open_browser():
    """延迟打开浏览器"""
    try:
        webbrowser.open('http://localhost:5000')
        print("🌐 浏览器已打开")
    except Exception as e:
        print(f"⚠️ 自动打开浏览器失败: {e}")
        print("请手动访问: http://localhost:5000")

def setup_logging():
    """设置日志配置，减少输出"""
    # 设置Flask和Werkzeug的日志级别为WARNING，保留基本信息
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('flask').setLevel(logging.WARNING)
    logging.getLogger().setLevel(logging.WARNING)

def cleanup_files():
    """清理历史记录和日志文件"""
    try:
        # 清理日志文件
        log_files = ['qiangpiao.log']
        for log_file in log_files:
            if os.path.exists(log_file):
                os.remove(log_file)
        
        # 清理Cookie备份文件（保留最近3个）
        backup_files = [f for f in os.listdir('.') if f.startswith('cookie_backup_') and f.endswith('.txt')]
        if len(backup_files) > 3:
            # 按修改时间排序，删除较旧的备份
            backup_files.sort(key=lambda x: os.path.getmtime(x))
            for old_backup in backup_files[:-3]:
                os.remove(old_backup)
        
        # 清理临时文件
        temp_files = [f for f in os.listdir('.') if f.endswith('.tmp') or f.endswith('.temp')]
        for temp_file in temp_files:
            os.remove(temp_file)
        
        # 清理Python缓存文件
        cache_dirs = ['__pycache__']
        for cache_dir in cache_dirs:
            if os.path.exists(cache_dir):
                import shutil
                shutil.rmtree(cache_dir, ignore_errors=True)
        
        # 清理.pyc文件
        pyc_files = [f for f in os.listdir('.') if f.endswith('.pyc')]
        for pyc_file in pyc_files:
            os.remove(pyc_file)
        
        # 清理状态缓存文件（如果存在）
        state_files = ['booking_state.json', 'app_state.json', 'session_state.json']
        for state_file in state_files:
            if os.path.exists(state_file):
                os.remove(state_file)
            
    except Exception:
        pass  # 静默处理清理错误

def reset_global_state():
    """重置全局状态变量"""
    try:
        # 强制删除可能缓存的模块
        modules_to_clear = []
        for module_name in list(sys.modules.keys()):
            if any(module_name.startswith(prefix) for prefix in ['qiangpiao', 'web_app', 'config']):
                modules_to_clear.append(module_name)
        
        for module in modules_to_clear:
            if module in sys.modules:
                del sys.modules[module]
        
        # 清理importlib缓存
        import importlib
        if hasattr(importlib, 'invalidate_caches'):
            importlib.invalidate_caches()
            
    except Exception:
        pass

def force_reset_booking_status():
    """强制重置抢票状态"""
    try:
        # 在导入前先清理
        if 'web_app' in sys.modules:
            web_app_module = sys.modules['web_app']
            if hasattr(web_app_module, 'booking_status'):
                web_app_module.booking_status = {
                    'running': False,
                    'thread': None,
                    'results': [],
                    'current_status': '未开始',
                    'retry_count': 0,
                    'start_time': None,
                    'stop_event': None
                }
    except Exception:
        pass

def main():
    global app_instance
    
    print("🚀 正在启动深大羽球预约...")
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # 终止信号
    
    # 注册退出处理器
    atexit.register(cleanup_on_exit)
    
    # 清理历史文件
    print("🧹 清理历史文件...")
    cleanup_files()
    
    # 重置全局状态
    print("🔄 重置模块状态...")
    reset_global_state()
    
    # 检查必要文件
    print("📁 检查必要文件...")
    required_files = ['web_app.py', 'config.py', 'qiangpiao.py']
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"❌ 缺少必要文件: {', '.join(missing_files)}")
        input("按回车键退出...")
        sys.exit(1)
    
    # 检查模板目录
    if not os.path.exists('templates'):
        print("❌ 缺少templates目录")
        print("💡 请确保templates文件夹及其中的HTML文件存在")
        input("按回车键退出...")
        sys.exit(1)
    
    # 创建静态文件目录
    if not os.path.exists('static'):
        os.makedirs('static')
        print("📁 已创建static目录")
    
    try:
        # 设置日志级别，减少输出
        setup_logging()
        
        print("📡 启动Web服务器...")
        print("🌐 服务地址: http://localhost:5000")
        print("💡 按 Ctrl+C 可停止服务")
        print("-" * 50)

        # 延迟3秒后打开浏览器
        browser_timer = Timer(3.0, open_browser)
        browser_timer.daemon = True  # 设置为守护线程
        browser_timer.start()
        active_threads.append(browser_timer)
        
        # 强制重置状态
        force_reset_booking_status()
        
        # 启动Flask应用
        print("📦 导入Web应用模块...")
        from web_app import app
        app_instance = app
        
        # 再次确保状态重置
        print("✨ 初始化应用状态...")
        from web_app import reset_booking_status
        reset_booking_status()
        
        print("🌐 Web服务器启动成功！")
        # 启动Flask（保留基本输出）
        app.run(debug=False, host='127.0.0.1', port=5000, use_reloader=False, threaded=True)
        
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        print("💡 可能的解决方案:")
        print("   1. 检查所有Python文件语法是否正确")
        print("   2. 确保Flask已安装: pip install flask")
        print("   3. 检查qiangpiao.py文件是否存在且无语法错误")
        input("按回车键退出...")
    except OSError as e:
        if "Address already in use" in str(e):
            print("❌ 端口5000已被占用")
            print("💡 解决方案:")
            print("   1. 关闭其他使用5000端口的程序")
            print("   2. 或等待几秒后重试")
        else:
            print(f"❌ 网络错误: {e}")
        input("按回车键退出...")
    except KeyboardInterrupt:
        print("\n⛔ 用户手动停止服务")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print(f"📝 详细错误信息: {type(e).__name__}")
        import traceback
        print("🐛 错误详情:")
        traceback.print_exc()
        input("按回车键退出...")
    finally:
        # 确保清理
        cleanup_on_exit()
        print("🏁 服务已停止")

if __name__ == "__main__":
    main()
