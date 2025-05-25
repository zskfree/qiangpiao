# Cookie管理工具 - 自动检测和更新Cookie
import re
import os
import time
from datetime import datetime
import requests
import urllib3
from qiangpiao import session, headers, CONFIG

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

def backup_current_cookie():
    """备份当前Cookie"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"cookie_backup_{timestamp}.txt"
    
    try:
        with open('qiangpiao.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取当前Cookie
        start_marker = 'raw_cookie = """'
        end_marker = '"""'
        
        start_idx = content.find(start_marker)
        if start_idx != -1:
            start_idx += len(start_marker)
            end_idx = content.find(end_marker, start_idx)
            if end_idx != -1:
                current_cookie = content[start_idx:end_idx].strip()
                
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(f"# Cookie备份 - {datetime.now()}\n")
                    f.write(current_cookie)
                
                print(f"✅ 当前Cookie已备份到: {backup_file}")
                return backup_file
    
    except Exception as e:
        print(f"⚠️  备份失败: {e}")
    
    return None

def update_cookie_in_file(new_cookie_text):
    """更新文件中的Cookie"""
    try:
        # 先备份当前Cookie
        backup_current_cookie()
        
        # 读取原文件
        with open('qiangpiao.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换cookie
        start_marker = 'raw_cookie = """'
        end_marker = '"""'
        
        start_idx = content.find(start_marker)
        if start_idx == -1:
            print("❌ 未找到cookie位置！")
            return False
        
        start_idx += len(start_marker)
        end_idx = content.find(end_marker, start_idx)
        
        if end_idx == -1:
            print("❌ 未找到cookie结束位置！")
            return False
        
        new_content = content[:start_idx] + '\n' + new_cookie_text + '\n' + content[end_idx:]
        
        # 写入文件
        with open('qiangpiao.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Cookie更新成功！")
        return True
        
    except Exception as e:
        print(f"❌ 更新失败: {e}")
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
