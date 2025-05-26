# -*- coding: utf-8 -*-
"""
深大体育场馆预约-zsk Web版启动脚本
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

# 处理PyInstaller打包后的资源路径
def resource_path(relative_path):
    """获取资源文件的绝对路径，支持PyInstaller打包"""
    try:
        # PyInstaller创建临时文件夹并将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# 设置工作目录
if getattr(sys, 'frozen', False):
    # 如果是exe运行，设置工作目录为exe所在目录
    application_path = os.path.dirname(sys.executable)
    os.chdir(application_path)
else:
    # 如果是Python脚本运行，设置工作目录为脚本所在目录
    application_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(application_path)

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
    
    # 过滤Chrome和Selenium的SSL错误日志
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", message=".*SSL.*")
    warnings.filterwarnings("ignore", message=".*certificate.*")
    
    # 设置urllib3日志级别，减少SSL警告
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        urllib3.disable_warnings(urllib3.exceptions.SubjectAltNameWarning)
    except:
        pass

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
        
        # 清理其他临时文件
        temp_extensions = ['.tmp', '.temp', '.pyc']
        for ext in temp_extensions:
            temp_files = [f for f in os.listdir('.') if f.endswith(ext)]
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                except:
                    pass
        
        # 清理Python缓存文件
        cache_dirs = ['__pycache__']
        for cache_dir in cache_dirs:
            if os.path.exists(cache_dir):
                import shutil
                shutil.rmtree(cache_dir, ignore_errors=True)
            
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

def check_files():
    """检查必要文件"""
    print("� 检查必要文件...")
    
    # 检查Python文件
    required_files = ['web_app.py', 'config.py', 'qiangpiao.py']
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ 缺少必要文件: {', '.join(missing_files)}")
        return False
    
    # 检查模板目录
    templates_dir = resource_path('templates')
    if not os.path.exists(templates_dir) and not os.path.exists('templates'):
        print("❌ 缺少templates目录")
        print("💡 请确保templates文件夹及其中的HTML文件存在")
        return False
    
    return True

def main():
    global app_instance
    
    print("🚀 深大体育场馆预约系统 v1.0")
    print("=" * 50)
    
    # 初始化错误抑制（在其他导入之前）
    try:
        from error_filter import initialize_error_suppression
        initialize_error_suppression()
    except ImportError:
        pass  # 如果没有错误过滤器模块，继续正常运行
    
    # 显示运行环境信息
    if getattr(sys, 'frozen', False):
        print("📦 运行模式: EXE独立版本")
        print(f"📁 工作目录: {os.getcwd()}")
    else:
        print("🐍 运行模式: Python脚本")
    
    # 注册信号处理器（仅在非Windows系统或支持的情况下）
    try:
        signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # 终止信号
    except:
        pass  # 在Windows的exe中可能不支持某些信号
    
    # 注册退出处理器
    atexit.register(cleanup_on_exit)
    
    # 清理历史文件
    print("🧹 清理历史文件...")
    cleanup_files()
    
    # 重置全局状态
    print("🔄 重置模块状态...")
    reset_global_state()
    
    # 检查必要文件
    if not check_files():
        input("按回车键退出...")
        sys.exit(1)
    
    try:
        # 设置日志级别，减少输出（包括SSL错误过滤）
        setup_logging()
        
        print("📡 启动Web服务器...")
        print("🌐 服务地址: http://localhost:5000")
        print("💡 按 Ctrl+C 可停止服务")
        print("💡 浏览器SSL错误提示可以忽略，不影响功能")
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
        print("💡 首次启动可能需要几秒钟...")
        
        # 启动Flask（生产模式）
        app.run(debug=False, host='127.0.0.1', port=5000, use_reloader=False, threaded=True)
        
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        print("💡 可能的解决方案:")
        print("   1. 检查所有Python文件是否存在")
        print("   2. 重新下载完整的程序包")
        print("   3. 确保程序没有被杀毒软件误删")
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