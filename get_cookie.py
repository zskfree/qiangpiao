import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from config import CAMPUS_ACCOUNT

def setup_chrome_driver(headless=False):
    """配置Chrome浏览器"""
    options = Options()
    if headless:
        options.add_argument('--headless')  # 无界面模式
    
    # 基础配置
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36')
    
    # SSL和网络优化配置
    options.add_argument('--ignore-ssl-errors-and-warnings')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-features=VizDisplayCompositor')
    options.add_argument('--disable-ipc-flooding-protection')
    
    # 网络和性能优化
    options.add_argument('--max_old_space_size=4096')
    options.add_argument('--disable-backgrounding-occluded-windows')
    options.add_argument('--disable-renderer-backgrounding')
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-background-networking')
    
    # 日志和错误抑制
    options.add_argument('--log-level=3')  # 只显示致命错误
    options.add_argument('--silent')
    options.add_argument('--disable-logging')
    options.add_argument('--disable-gpu-logging')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 设置日志过滤
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 无界面模式的额外配置
    if headless:
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # 设置超时时间
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)
        
        return driver
    except Exception as e:
        print(f"⚠️ Chrome浏览器启动警告: {e}")
        # 即使有警告也继续运行
        try:
            driver = webdriver.Chrome(options=options)
            return driver
        except Exception as fatal_error:
            print(f"❌ Chrome浏览器启动失败: {fatal_error}")
            raise

def wait_for_element(driver, by, value, timeout=10):
    """等待元素出现"""
    try:
        wait = WebDriverWait(driver, timeout)
        element = wait.until(EC.element_to_be_clickable((by, value)))
        return element
    except TimeoutException:
        return None

def auto_login_and_get_cookies(username, password, callback=None):
    """自动登录并获取cookies - 始终使用有界面模式"""
    driver = None
    try:
        # 始终使用有界面模式，因为可能需要用户输入验证码
        if callback:
            callback("正在初始化浏览器...")
        print("正在初始化浏览器...")
        driver = setup_chrome_driver(headless=False)
        
        if callback:
            callback("正在访问登录页面...")
        print("正在访问登录页面...")
        
        # 添加重试机制来处理SSL错误
        max_retries = 3
        for attempt in range(max_retries):
            try:
                driver.get("https://ehall.szu.edu.cn/login")
                time.sleep(2)  # 给页面加载一些时间
                break
            except Exception as e:
                print(f"尝试 {attempt + 1}/{max_retries} 访问登录页面失败: {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2)
        
        # 更宽松的页面检查 - 只要能访问到页面就继续
        page_title = driver.title if driver.title else ""
        print(f"当前页面: {page_title}")
        
        # 检查页面是否正确加载 - 更宽松的条件
        if driver.current_url and "ehall.szu.edu.cn" in driver.current_url:
            print("✅ 页面加载成功")
            if callback:
                callback("页面加载成功，准备登录...")
        else:
            error_msg = f"页面加载异常，当前URL: {driver.current_url}"
            print(error_msg)
            if callback:
                callback(error_msg)
            # 不立即返回，继续尝试
        
        # 输入用户名
        if callback:
            callback("正在输入用户名...")
        print("正在输入用户名...")
        
        # 增加更多的等待时间和重试机制
        username_input = None
        for attempt in range(3):  # 最多重试3次
            username_input = wait_for_element(driver, By.ID, "username", 10)
            if username_input:
                break
            print(f"第{attempt + 1}次查找用户名输入框失败，重试中...")
            time.sleep(2)
        
        if not username_input:
            error_msg = "❌ 无法找到用户名输入框，可能页面结构发生变化"
            print(error_msg)
            if callback:
                callback(error_msg)
            # 尝试备用方案
            try:
                # 尝试其他可能的用户名输入框选择器
                alternative_selectors = [
                    (By.NAME, "username"),
                    (By.XPATH, "//input[@type='text']"),
                    (By.XPATH, "//input[contains(@placeholder, '用户名') or contains(@placeholder, '学号')]")
                ]
                
                for by, selector in alternative_selectors:
                    username_input = wait_for_element(driver, by, selector, 5)
                    if username_input:
                        print(f"✅ 找到备用用户名输入框: {by}={selector}")
                        break
                
                if not username_input:
                    return None
            except Exception as e:
                print(f"备用方案也失败: {e}")
                return None
        
        username_input.clear()
        time.sleep(0.5)
        username_input.send_keys(username)
        print(f"✅ 用户名输入完成: {username}")
        
        # 输入密码
        if callback:
            callback("正在输入密码...")
        print("正在输入密码...")
        
        password_input = None
        for attempt in range(3):
            password_input = wait_for_element(driver, By.ID, "password", 10)
            if password_input:
                break
            print(f"第{attempt + 1}次查找密码输入框失败，重试中...")
            time.sleep(2)
        
        if not password_input:
            error_msg = "❌ 无法找到密码输入框"
            print(error_msg)
            if callback:
                callback(error_msg)
            # 尝试备用方案
            try:
                alternative_selectors = [
                    (By.NAME, "password"),
                    (By.XPATH, "//input[@type='password']")
                ]
                
                for by, selector in alternative_selectors:
                    password_input = wait_for_element(driver, by, selector, 5)
                    if password_input:
                        print(f"✅ 找到备用密码输入框: {by}={selector}")
                        break
                
                if not password_input:
                    return None
            except Exception as e:
                print(f"备用密码输入框查找失败: {e}")
                return None
        
        password_input.clear()
        time.sleep(0.5)
        password_input.send_keys(password)
        print("✅ 密码输入完成")
        
        # 点击登录按钮
        if callback:
            callback("正在提交登录...")
        print("正在点击登录...")
        
        login_button = wait_for_element(driver, By.ID, "login_submit", 10)
        if login_button:
            login_button.click()
            print("✅ 登录按钮点击成功")
        else:
            # 尝试备用登录按钮
            alternative_login_selectors = [
                (By.XPATH, "//button[contains(text(), '登录') or contains(text(), '登陆')]"),
                (By.XPATH, "//input[@type='submit']"),
                (By.CLASS_NAME, "login-btn"),
                (By.NAME, "submit")
            ]
            
            login_clicked = False
            for by, selector in alternative_login_selectors:
                try:
                    alt_button = wait_for_element(driver, by, selector, 3)
                    if alt_button:
                        alt_button.click()
                        print(f"✅ 备用登录按钮点击成功: {by}={selector}")
                        login_clicked = True
                        break
                except Exception as e:
                    continue
            
            if not login_clicked:
                # 最后尝试按回车键
                print("尝试按回车键提交...")
                password_input.send_keys(Keys.RETURN)
        
        # 等待页面跳转 - 减少等待时间
        time.sleep(3)
        
        # 快速检查登录状态
        current_url = driver.current_url
        print(f"登录后URL: {current_url}")
        
        # 优化的验证码检查逻辑
        if callback:
            callback("快速检查登录状态...")
        print("快速检查登录状态...")
        
        # 如果URL已经跳转到主页面，说明登录成功
        if ("login" not in current_url.lower() and 
            "ehall.szu.edu.cn" in current_url and 
            ("index" in current_url or "main" in current_url or "new" in current_url)):
            print("✅ 检测到已成功登录（无需验证码）")
            if callback:
                callback("✅ 登录成功（无需验证码）")
        else:
            # 只有在还在登录页面时才检查验证码
            if "login" in current_url.lower():
                if callback:
                    callback("检查是否需要验证码...")
                print("检查是否需要验证码...")
                
                # 快速检查验证码按钮（减少等待时间）
                verification_selectors = [
                    (By.ID, "getDynamicCode"),
                    (By.CLASS_NAME, "dynamicCode_btn"),
                    (By.XPATH, "//button[contains(text(), '获取验证码')]"),
                    (By.XPATH, "//button[@onclick='sendDynamicCodeByPhone(this)']")
                ]
                
                verification_button = None
                for by, value in verification_selectors:
                    try:
                        verification_button = wait_for_element(driver, by, value, 2)  # 减少等待时间到2秒
                        if verification_button:
                            print(f"✅ 找到验证码按钮: {by}={value}")
                            break
                    except:
                        continue
                
                if verification_button:
                    if callback:
                        callback("检测到需要短信验证码，请在浏览器中完成...")
                    print("正在点击获取验证码...")
                    try:
                        verification_button.click()
                        print("✅ 验证码按钮点击成功")
                    except Exception as e:
                        print(f"点击验证码按钮失败: {e}")
                    
                    # 弹出浏览器窗口并提示用户
                    driver.maximize_window()
                    
                    print("🔍 请在打开的浏览器窗口中:")
                    print("   1. 输入收到的短信验证码")
                    print("   2. 点击登录按钮完成登录")
                    if callback:
                        callback("请在浏览器中输入短信验证码并完成登录...")
                    
                    # 等待用户完成验证码输入和登录 - 减少总等待时间
                    print("等待登录完成（最多等待90秒）...")
                    login_success = False
                    for i in range(90):  # 减少到90秒
                        try:
                            current_url = driver.current_url
                            if "login" not in current_url.lower() and "ehall.szu.edu.cn" in current_url:
                                login_success = True
                                break
                            # 每15秒提醒一次（减少提醒频率）
                            if i > 0 and i % 15 == 0:
                                if callback:
                                    callback(f"等待登录中...({i}秒)，请在浏览器中完成验证码输入")
                                print(f"等待登录...({i}秒)")
                            time.sleep(1)
                        except Exception as e:
                            continue
                    
                    if not login_success:
                        error_msg = "❌ 登录超时，请确保在浏览器中完成了验证码输入和登录"
                        print(error_msg)
                        if callback:
                            callback(error_msg)
                        return None
                else:
                    # 快速检查其他验证方式
                    try:
                        page_content = driver.page_source.lower()
                        if any(keyword in page_content for keyword in ["验证码", "captcha"]):
                            if callback:
                                callback("检测到其他验证码，请在浏览器中完成...")
                            print("🔍 检测到其他验证码，请在浏览器中手动完成...")
                            driver.maximize_window()
                            
                            # 等待用户完成登录 - 减少等待时间
                            login_success = False
                            for i in range(60):  # 减少到60秒
                                try:
                                    current_url = driver.current_url
                                    if "login" not in current_url.lower() and "ehall.szu.edu.cn" in current_url:
                                        login_success = True
                                        break
                                    if i > 0 and i % 15 == 0:
                                        if callback:
                                            callback(f"等待登录中...({i}秒)")
                                    time.sleep(1)
                                except:
                                    continue
                            
                            if not login_success:
                                error_msg = "❌ 登录超时"
                                print(error_msg)
                                if callback:
                                    callback(error_msg)
                                return None
                        else:
                            # 可能是账号密码错误
                            if any(error_keyword in page_content for error_keyword in ["用户名或密码错误", "登录失败", "error"]):
                                error_msg = "❌ 登录失败，请检查用户名密码是否正确"
                            else:
                                error_msg = "❌ 登录状态异常，可能需要手动处理"
                            print(error_msg)
                            if callback:
                                callback(error_msg)
                            
                            # 给用户30秒时间手动处理
                            print("🔍 请在浏览器中检查登录状态并手动完成登录（30秒超时）")
                            driver.maximize_window()
                            
                            login_success = False
                            for i in range(30):  # 减少到30秒
                                try:
                                    current_url = driver.current_url
                                    if "login" not in current_url.lower() and "ehall.szu.edu.cn" in current_url:
                                        login_success = True
                                        break
                                    time.sleep(1)
                                except:
                                    continue
                            
                            if not login_success:
                                return None
                    except Exception as e:
                        print(f"验证码检查异常: {e}")
                        # 继续执行，可能不需要验证码
            else:
                print("✅ 检测到已跳转到其他页面，登录可能成功")
                if callback:
                    callback("✅ 登录状态检查通过")
        
        # 最终验证登录状态 - 减少等待时间
        if callback:
            callback("最终验证登录状态...")
        print("最终验证登录状态...")
        for i in range(5):  # 减少到5次检查，共10秒
            try:
                current_url = driver.current_url
                if "login" not in current_url.lower() and "ehall.szu.edu.cn" in current_url:
                    print("✅ 登录成功!")
                    if callback:
                        callback("✅ 登录验证成功!")
                    break
                time.sleep(2)
            except:
                continue
        else:
            error_msg = "❌ 登录验证失败，可能未成功登录"
            print(error_msg)
            if callback:
                callback(error_msg)
            return None
        
        # 访问体育预约页面
        if callback:
            callback("正在访问体育预约页面...")
        print("正在访问体育预约页面...")
        driver.get("https://ehall.szu.edu.cn/qljfwapp/sys/lwSzuCgyy/index.do")
        time.sleep(3)  # 减少等待时间
        
        # 更宽松的页面验证
        page_source = driver.page_source
        if ("体育" in page_source or 
            "sport" in page_source.lower() or 
            "venue" in page_source.lower() or
            "场馆" in page_source or
            "预约" in page_source):
            print("✅ 成功进入体育预约页面")
            if callback:
                callback("✅ 成功进入体育预约页面")
        else:
            # 不完全阻止，给出警告但继续
            warning_msg = "⚠️ 页面内容可能不完整，但继续获取Cookie"
            print(warning_msg)
            if callback:
                callback(warning_msg)
        
        # 获取cookies
        if callback:
            callback("正在获取Cookie...")
        cookies = driver.get_cookies()
        if not cookies:
            error_msg = "❌ 未获取到Cookie"
            print(error_msg)
            if callback:
                callback(error_msg)
            return None
        
        success_msg = f"✅ 成功获取 {len(cookies)} 个Cookie"
        print(success_msg)
        if callback:
            callback(success_msg)
        
        cookie_str = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
        
        # 验证Cookie的基本完整性
        essential_cookies = ['JSESSIONID', 'MOD_AUTH_CAS']
        missing_cookies = [name for name in essential_cookies if name not in cookie_str]
        if missing_cookies:
            warning_msg = f"⚠️ 缺少部分关键Cookie: {missing_cookies}，但仍可尝试使用"
            print(warning_msg)
            if callback:
                callback(warning_msg)
        else:
            if callback:
                callback("✅ Cookie完整性验证通过")
        
        print(f"Cookie示例: {cookie_str[:100]}...")
        return cookie_str
        
    except Exception as e:
        error_msg = f"❌ 获取Cookie失败: {e}"
        print(error_msg)
        if callback:
            callback(error_msg)
        import traceback
        print("详细错误信息:")
        traceback.print_exc()
        return None
    finally:
        if driver:
            # 减少关闭浏览器的等待时间
            if callback:
                callback("正在关闭浏览器...")
            time.sleep(1)  # 减少到1秒
            try:
                driver.quit()
            except:
                pass

def update_cookie_in_file(cookie_str):
    """更新qiangpiao.py文件中的cookie"""
    try:
        # 备份原文件
        import shutil
        backup_file = f"qiangpiao_backup_{int(time.time())}.py"
        shutil.copy2('qiangpiao.py', backup_file)
        
        with open('qiangpiao.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        start_marker = 'raw_cookie = """'
        end_marker = '"""'
        
        start_idx = content.find(start_marker)
        if start_idx == -1:
            print("❌ 未找到cookie配置")
            return False
        
        start_idx += len(start_marker)
        end_idx = content.find(end_marker, start_idx)
        if end_idx == -1:
            print("❌ cookie配置格式错误")
            return False
        
        new_content = content[:start_idx] + '\n' + cookie_str + '\n' + content[end_idx:]
        
        with open('qiangpiao.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Cookie更新成功!")
        
        # 清理旧备份文件（保留最近3个）
        import glob
        backup_files = glob.glob('qiangpiao_backup_*.py')
        if len(backup_files) > 3:
            backup_files.sort()
            for old_backup in backup_files[:-3]:
                try:
                    import os
                    os.remove(old_backup)
                except:
                    pass
        
        return True
        
    except FileNotFoundError:
        print("❌ 未找到qiangpiao.py文件")
        return False
    except Exception as e:
        print(f"❌ 更新失败: {e}")
        # 如果更新失败，尝试恢复备份
        try:
            if 'backup_file' in locals():
                shutil.copy2(backup_file, 'qiangpiao.py')
                print("✅ 已恢复原文件")
        except:
            pass
        return False