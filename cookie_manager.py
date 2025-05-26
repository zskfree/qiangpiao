# Cookie管理工具 - 自动检测和更新Cookie
import re
import os
import time
from datetime import datetime
import requests
import urllib3
import logging

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 导入配置和session
try:
    from qiangpiao import session, headers, CONFIG
except ImportError:
    # 如果无法导入，创建基本的session
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }
    CONFIG = {"REQUEST_TIMEOUT": 10}

def extract_cookies_from_text(cookie_text):
    """从文本中提取并解析Cookie"""
    cookies = {}
    
    # 处理不同格式的Cookie字符串
    cookie_text = cookie_text.strip()
    
    print(f"Cookie管理器: 开始解析Cookie文本，长度: {len(cookie_text)}")
    
    try:
        # 如果是浏览器复制的格式（分号分隔）
        if ';' in cookie_text:
            print("Cookie管理器: 检测到分号分隔格式")
            for item in cookie_text.split(';'):
                item = item.strip()
                if '=' in item and item:
                    try:
                        key, value = item.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        if key and value:  # 确保键值都不为空
                            cookies[key] = value
                            print(f"Cookie管理器: 解析字段 {key} = {value[:20]}...")
                    except ValueError:
                        print(f"Cookie管理器: 跳过无效项 {item}")
                        continue
        
        # 如果是多行格式
        elif '\n' in cookie_text:
            print("Cookie管理器: 检测到多行格式")
            for line in cookie_text.split('\n'):
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    try:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        if key and value:
                            cookies[key] = value
                            print(f"Cookie管理器: 解析字段 {key} = {value[:20]}...")
                    except ValueError:
                        print(f"Cookie管理器: 跳过无效行 {line}")
                        continue
        
        # 如果是单行且没有分号，可能是键值对格式
        elif '=' in cookie_text:
            print("Cookie管理器: 检测到单个键值对格式")
            try:
                key, value = cookie_text.split('=', 1)
                key = key.strip()
                value = value.strip()
                if key and value:
                    cookies[key] = value
                    print(f"Cookie管理器: 解析字段 {key} = {value[:20]}...")
            except ValueError:
                print("Cookie管理器: 无法解析单个键值对")
        
        else:
            print("Cookie管理器: 未识别的Cookie格式")
    
    except Exception as e:
        print(f"Cookie管理器: 解析过程出错 {e}")
    
    print(f"Cookie管理器: 最终解析得到 {len(cookies)} 个字段")
    return cookies

def test_cookie_validity(cookies_dict):
    """测试Cookie是否有效"""
    if not cookies_dict:
        return False, "Cookie字典为空"
    
    print(f"Cookie管理器: 开始测试Cookie有效性，共 {len(cookies_dict)} 个字段")
    
    try:
        # 创建测试用的headers
        test_headers = headers.copy()
        test_headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        })
        
        print("Cookie管理器: 发送测试请求...")
        resp = session.get(
            "https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/index.do",
            headers=test_headers,
            cookies=cookies_dict,
            verify=False,
            timeout=15,
            allow_redirects=True
        )
        
        print(f"Cookie管理器: 测试响应状态码 {resp.status_code}")
        
        # 检查响应状态码
        if resp.status_code == 403:
            print("Cookie管理器: 收到403错误")
            return False, "访问被拒绝，Cookie可能已失效"
        elif resp.status_code == 302 or resp.status_code == 301:
            location = resp.headers.get('Location', '')
            print(f"Cookie管理器: 收到重定向 {location}")
            if "login" in location.lower():
                return False, "被重定向到登录页面，需要重新登录"
        elif resp.status_code != 200:
            print(f"Cookie管理器: 收到异常状态码 {resp.status_code}")
            return False, f"HTTP错误: {resp.status_code}"
        
        # 检查响应内容
        response_text = resp.text
        print(f"Cookie管理器: 响应内容长度 {len(response_text)}")
        
        # 检查是否需要登录
        login_indicators = ["登录", "login", "用户名", "密码", "验证码"]
        needs_login = any(indicator in response_text.lower() for indicator in login_indicators)
        
        if needs_login:
            print("Cookie管理器: 页面显示需要登录")
            return False, "需要重新登录"
        
        # 检查是否是正确的体育场馆页面
        success_indicators = ["体育场馆", "sportVenue", "预约", "场地"]
        is_sport_page = any(indicator in response_text for indicator in success_indicators)
        
        if is_sport_page:
            print("Cookie管理器: ✅ Cookie有效")
            return True, "Cookie有效，页面访问正常"
        
        # 检查页面是否有其他有效内容
        if len(response_text) > 1000:
            print("Cookie管理器: ⚠️ Cookie可能有效但页面异常")
            return True, "Cookie可能有效，但页面内容异常"
        else:
            print("Cookie管理器: ❌ 页面内容过少")
            return False, "页面内容异常，可能需要重新登录"
            
    except requests.exceptions.Timeout:
        print("Cookie管理器: 请求超时")
        return False, "请求超时，请检查网络连接"
    except requests.exceptions.SSLError:
        print("Cookie管理器: SSL错误")
        return False, "SSL连接错误"
    except requests.exceptions.ConnectionError:
        print("Cookie管理器: 连接错误")
        return False, "网络连接失败"
    except Exception as e:
        print(f"Cookie管理器: 未知错误 {e}")
        return False, f"测试失败: {str(e)}"

def update_cookie_in_file(new_cookie_text):
    """更新文件中的Cookie"""
    try:
        print(f"Cookie管理器: 开始更新Cookie到文件，长度: {len(new_cookie_text)}")
        
        # 读取原文件
        try:
            with open('qiangpiao.py', 'r', encoding='utf-8') as f:
                content = f.read()
            print("Cookie管理器: 成功读取qiangpiao.py")
        except Exception as e:
            print(f"Cookie管理器: 读取文件失败 {e}")
            return False
        
        # 查找并替换cookie
        start_marker = 'raw_cookie = """'
        end_marker = '"""'
        
        start_idx = content.find(start_marker)
        if start_idx == -1:
            print("Cookie管理器: ❌ 未找到cookie起始位置")
            return False
        
        start_idx += len(start_marker)
        end_idx = content.find(end_marker, start_idx)
        
        if end_idx == -1:
            print("Cookie管理器: ❌ 未找到cookie结束位置")
            return False
        
        print(f"Cookie管理器: 找到Cookie位置 {start_idx}-{end_idx}")
        
        # 构造新内容
        new_content = content[:start_idx] + '\n' + new_cookie_text + '\n' + content[end_idx:]
        
        # 写入新文件
        try:
            with open('qiangpiao.py', 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("Cookie管理器: ✅ Cookie写入成功")
        except Exception as e:
            print(f"Cookie管理器: 写入失败 {e}")
            return False
        
        # 验证写入结果
        try:
            with open('qiangpiao.py', 'r', encoding='utf-8') as f:
                verify_content = f.read()
            if new_cookie_text.strip() in verify_content:
                print("Cookie管理器: ✅ Cookie更新验证成功")
            else:
                print("Cookie管理器: ⚠️ Cookie更新验证失败")
        except Exception as e:
            print(f"Cookie管理器: 验证失败 {e}")
        
        print("Cookie管理器: ✅ 更新完成")
        return True
        
    except Exception as e:
        print(f"Cookie管理器: ❌ 更新失败 {e}")
        return False

def clear_cookie_in_file():
    """清空文件中的Cookie"""
    try:
        print("Cookie管理器: 开始清空Cookie")
        
        # 使用空Cookie更新
        return update_cookie_in_file("")
        
    except Exception as e:
        print(f"Cookie管理器: 清空失败 {e}")
        return False

def check_and_suggest_update():
    """检查Cookie状态并建议更新"""
    print("=" * 60)
    print("🔍 Cookie状态检查")
    print("=" * 60)
    
    # 从当前文件读取Cookie
    try:
        with open('qiangpiao.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        start_marker = 'raw_cookie = """'
        end_marker = '"""'
        
        start_idx = content.find(start_marker)
        if start_idx != -1:
            start_idx += len(start_marker)
            end_idx = content.find(end_marker, start_idx)
            if end_idx != -1:
                current_cookie_text = content[start_idx:end_idx].strip()
                current_cookies = extract_cookies_from_text(current_cookie_text)
                
                print(f"当前Cookie包含 {len(current_cookies)} 个字段")
                
                # 测试有效性
                print("🧪 测试Cookie有效性...")
                is_valid, message = test_cookie_validity(current_cookies)
                
                if is_valid:
                    print(f"✅ {message}")
                    print("💡 Cookie状态良好，无需更新")
                    return True
                else:
                    print(f"❌ {message}")
                    print("\n💡 建议操作:")
                    print("1. 重新登录获取新Cookie")
                    print("2. 运行 python cookie_manager.py update")
                    return False
    
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def interactive_update():
    """交互式Cookie更新"""
    print("=" * 60)
    print("🔧 Cookie更新向导")
    print("=" * 60)
    
    print("📝 获取Cookie的详细步骤:")
    print("1. 打开浏览器（Chrome/Edge/Firefox）")
    print("2. 访问: https://ehall.szu.edu.cn")
    print("3. 登录你的学号和密码")
    print("4. 进入体育场馆预约系统")
    print("5. 按F12打开开发者工具")
    print("6. 切换到Network/网络标签页")
    print("7. 刷新页面（F5）")
    print("8. 在请求列表中找到任意请求，点击")
    print("9. 在Request Headers中找到Cookie字段")
    print("10. 复制完整的Cookie值")
    print()
    
    # 选择输入方式
    print("选择输入方式:")
    print("1. 粘贴完整Cookie字符串")
    print("2. 从文件读取")
    print("3. 取消操作")
    
    choice = input("\n请选择 (1-3): ").strip()
    
    if choice == "1":
        print("\n请粘贴Cookie字符串:")
        print("(可以分多行粘贴，输入空行结束)")
        
        cookie_lines = []
        while True:
            line = input()
            if not line.strip():
                break
            cookie_lines.append(line)
        
        new_cookie_text = ' '.join(cookie_lines).strip()
        
        if not new_cookie_text:
            print("❌ Cookie不能为空！")
            return False
        
        # 验证新Cookie
        print("\n🧪 验证新Cookie...")
        new_cookies = extract_cookies_from_text(new_cookie_text)
        is_valid, message = test_cookie_validity(new_cookies)
        
        if is_valid:
            print(f"✅ {message}")
            confirm = input("确认更新Cookie? (y/N): ").lower()
            if confirm == 'y':
                return update_cookie_in_file(new_cookie_text)
        else:
            print(f"❌ 新Cookie无效: {message}")
            return False
    
    elif choice == "2":
        file_path = input("请输入Cookie文件路径: ").strip()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                new_cookie_text = f.read().strip()
            
            new_cookies = extract_cookies_from_text(new_cookie_text)
            is_valid, message = test_cookie_validity(new_cookies)
            
            if is_valid:
                print(f"✅ {message}")
                return update_cookie_in_file(new_cookie_text)
            else:
                print(f"❌ 文件中的Cookie无效: {message}")
                return False
                
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            return False
    
    else:
        print("取消操作")
        return False

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Cookie管理工具使用方法:")
        print("  python cookie_manager.py check    # 检查Cookie状态")
        print("  python cookie_manager.py update   # 更新Cookie")
        print("  python cookie_manager.py test     # 测试当前Cookie")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'check':
        check_and_suggest_update()
    elif command == 'update':
        interactive_update()
    elif command == 'test':
        check_and_suggest_update()
    else:
        print("❌ 未知命令！")

if __name__ == "__main__":
    main()
