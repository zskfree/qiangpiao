# -*- coding: utf-8 -*-
"""
深大体育场馆预约系统 - 智能打包脚本
自动检测Chrome版本并下载对应ChromeDriver
支持Chrome 110-136版本
"""

import os
import sys
import shutil
import subprocess
import urllib.request
import zipfile
import json
import re
import winreg
from pathlib import Path

def get_chrome_version():
    """获取本机Chrome浏览器版本"""
    try:
        # 方法1: 从注册表获取Chrome版本
        print("🔍 正在检测Chrome版本...")
        
        chrome_paths = [
            r"SOFTWARE\Google\Chrome\BLBeacon",
            r"SOFTWARE\Wow6432Node\Google\Chrome\BLBeacon",
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Google Chrome",
            r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Google Chrome"
        ]
        
        for path in chrome_paths:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                    version, _ = winreg.QueryValueEx(key, "version")
                    print(f"✅ 检测到Chrome版本: {version}")
                    return version
            except (FileNotFoundError, OSError):
                continue
        
        # 方法2: 通过Chrome可执行文件获取版本
        chrome_exe_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
        ]
        
        for chrome_path in chrome_exe_paths:
            if os.path.exists(chrome_path):
                try:
                    result = subprocess.run([chrome_path, "--version"], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        version_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', result.stdout)
                        if version_match:
                            version = version_match.group(1)
                            print(f"✅ 检测到Chrome版本: {version}")
                            return version
                except Exception:
                    continue
        
        print("⚠️ 无法检测Chrome版本，将下载通用版本")
        return None
        
    except Exception as e:
        print(f"⚠️ Chrome版本检测失败: {e}")
        return None

def get_compatible_chromedriver_version(chrome_version):
    """根据Chrome版本获取兼容的ChromeDriver版本"""
    if not chrome_version:
        return "119.0.6045.105"  # 默认稳定版本
    
    try:
        # 提取主版本号
        major_version = chrome_version.split('.')[0]
        print(f"Chrome主版本号: {major_version}")
        
        # ChromeDriver版本映射表（主要版本对应关系）- 更新到136版本
        version_mapping = {
            "136": "136.0.7103.113",  # 最新版本
            "135": "135.0.6790.75",
            "134": "134.0.6977.95", 
            "133": "133.0.6926.62",
            "132": "132.0.6834.83",
            "131": "131.0.6778.85",
            "130": "130.0.6723.92",
            "129": "129.0.6668.89",
            "128": "128.0.6613.84",
            "127": "127.0.6533.119",
            "126": "126.0.6478.182",
            "125": "125.0.6422.141",
            "124": "124.0.6367.201",
            "123": "123.0.6312.122",
            "122": "122.0.6261.128",
            "121": "121.0.6167.184",
            "120": "120.0.6099.109",
            "119": "119.0.6045.105",
            "118": "118.0.5993.70", 
            "117": "117.0.5938.92",
            "116": "116.0.5845.96",
            "115": "115.0.5790.102",
            "114": "114.0.5735.90",
            "113": "113.0.5672.63",
            "112": "112.0.5615.49",
            "111": "111.0.5563.64",
            "110": "110.0.5481.77"
        }
        
        if major_version in version_mapping:
            driver_version = version_mapping[major_version]
            print(f"✅ 匹配ChromeDriver版本: {driver_version}")
            return driver_version
        else:
            # 如果版本比136还新，使用最新的稳定版本
            if int(major_version) > 136:
                print(f"⚠️ Chrome版本{major_version}非常新，使用最新稳定版ChromeDriver")
                return "136.0.7103.113"  # 最新稳定版
            else:
                # 如果是未知的旧版本，使用通用版本
                print(f"⚠️ Chrome版本{major_version}未知，使用通用版本")
                return "119.0.6045.105"
            
    except Exception as e:
        print(f"⚠️ 版本匹配失败: {e}")
        return "119.0.6045.105"  # 默认版本

def download_chromedriver(version=None):
    """下载指定版本的ChromeDriver"""
    try:
        chrome_dir = Path('chrome_driver')
        chrome_dir.mkdir(exist_ok=True)
        
        # 检查是否已存在
        driver_path = chrome_dir / 'chromedriver.exe'
        if driver_path.exists():
            print("📁 发现已存在的ChromeDriver")
            
            # 检查现有版本是否匹配
            try:
                result = subprocess.run([str(driver_path), "--version"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    existing_version = re.search(r'(\d+\.\d+\.\d+\.\d+)', result.stdout)
                    if existing_version and version:
                        existing_ver = existing_version.group(1)
                        # 检查主版本号是否匹配
                        if existing_ver.split('.')[0] == version.split('.')[0]:
                            print(f"✅ 现有ChromeDriver版本{existing_ver}兼容，跳过下载")
                            return True
                        else:
                            print(f"⚠️ 现有版本{existing_ver}不兼容目标版本{version}，需要重新下载")
                            driver_path.unlink()
                    else:
                        print("✅ ChromeDriver已存在，跳过下载")
                        return True
            except Exception:
                print("⚠️ 无法检测现有ChromeDriver版本，重新下载")
                if driver_path.exists():
                    driver_path.unlink()
        
        # 如果没有指定版本，自动检测
        if not version:
            chrome_version = get_chrome_version()
            version = get_compatible_chromedriver_version(chrome_version)
        
        print(f"📥 正在下载ChromeDriver {version}...")
        
        # 构建下载URL - 使用新的Chrome for Testing下载地址
        major_version = version.split('.')[0]
        
        # Chrome 115+使用新的下载地址格式
        if int(major_version) >= 115:
            download_urls = [
                # 新的Chrome for Testing地址 (Chrome 115+)
                f"https://storage.googleapis.com/chrome-for-testing-public/{version}/win32/chromedriver-win32.zip",
                f"https://storage.googleapis.com/chrome-for-testing-public/{version}/win64/chromedriver-win64.zip",
                # 备用地址
                f"https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/{version}/win32/chromedriver-win32.zip",
                f"https://chromedriver.storage.googleapis.com/{version}/chromedriver_win32.zip"
            ]
        else:
            # 旧版本下载地址
            download_urls = [
                f"https://chromedriver.storage.googleapis.com/{version}/chromedriver_win32.zip"
            ]
        
        # 尝试下载
        success = False
        for url in download_urls:
            try:
                print(f"🌐 尝试下载: {url}")
                zip_path = chrome_dir / 'chromedriver.zip'
                
                # 添加请求头，模拟浏览器
                req = urllib.request.Request(url)
                req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36')
                
                with urllib.request.urlopen(req, timeout=30) as response:
                    if response.status == 200:
                        with open(zip_path, 'wb') as f:
                            shutil.copyfileobj(response, f)
                        print(f"✅ 下载成功，文件大小: {zip_path.stat().st_size / 1024 / 1024:.1f} MB")
                    else:
                        print(f"❌ 下载失败，状态码: {response.status}")
                        continue
                
                # 解压文件
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # 新版本可能在子目录中
                    extracted = False
                    for file_info in zip_ref.filelist:
                        if file_info.filename.endswith('chromedriver.exe'):
                            # 直接提取到目标位置
                            with zip_ref.open(file_info.filename) as source:
                                with open(driver_path, 'wb') as target:
                                    shutil.copyfileobj(source, target)
                            extracted = True
                            print(f"✅ 提取ChromeDriver: {file_info.filename}")
                            break
                    
                    if not extracted:
                        # 如果没找到，解压所有文件然后查找
                        print("🔍 在解压文件中查找ChromeDriver...")
                        zip_ref.extractall(chrome_dir)
                        for extracted_file in chrome_dir.rglob('chromedriver.exe'):
                            shutil.move(str(extracted_file), driver_path)
                            extracted = True
                            print(f"✅ 找到并移动ChromeDriver: {extracted_file}")
                            break
                
                zip_path.unlink()  # 删除zip文件
                
                # 清理多余的解压文件夹
                for item in chrome_dir.iterdir():
                    if item.is_dir():
                        shutil.rmtree(item)
                        print(f"🧹 清理临时目录: {item.name}")
                
                if driver_path.exists():
                    print(f"✅ ChromeDriver {version} 下载完成")
                    success = True
                    break
                else:
                    print("❌ ChromeDriver文件未找到")
                    
            except urllib.error.HTTPError as e:
                print(f"⚠️ HTTP错误 {e.code}: {e.reason}")
                continue
            except Exception as e:
                print(f"⚠️ 下载失败: {e}")
                continue
        
        if not success:
            print("❌ 所有下载地址都失败，尝试下载默认版本...")
            return download_fallback_chromedriver(chrome_dir)
        
        # 验证下载的文件
        try:
            result = subprocess.run([str(driver_path), "--version"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ ChromeDriver验证成功: {result.stdout.strip()}")
                return True
            else:
                print("⚠️ ChromeDriver验证失败")
                return False
        except Exception as e:
            print(f"⚠️ ChromeDriver验证出错: {e}")
            return False
        
    except Exception as e:
        print(f"❌ ChromeDriver下载失败: {e}")
        return False

def download_fallback_chromedriver(chrome_dir):
    """下载备用版本的ChromeDriver"""
    try:
        print("📥 正在下载备用ChromeDriver...")
        
        # 使用稳定的备用下载地址 - 更新到较新的稳定版本
        fallback_urls = [
            # 最新稳定版本
            "https://storage.googleapis.com/chrome-for-testing-public/119.0.6045.105/win32/chromedriver-win32.zip",
            # 备用镜像地址
            "https://npm.taobao.org/mirrors/chromedriver/119.0.6045.105/chromedriver_win32.zip",
            "https://registry.npmmirror.com/-/binary/chromedriver/119.0.6045.105/chromedriver_win32.zip",
            # 更早的稳定版本
            "https://storage.googleapis.com/chrome-for-testing-public/114.0.5735.90/win32/chromedriver-win32.zip"
        ]
        
        driver_path = chrome_dir / 'chromedriver.exe'
        
        for i, url in enumerate(fallback_urls):
            try:
                print(f"🔄 尝试备用地址 {i+1}/{len(fallback_urls)}: {url}")
                zip_path = chrome_dir / f'chromedriver_fallback_{i}.zip'
                
                req = urllib.request.Request(url)
                req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                
                with urllib.request.urlopen(req, timeout=30) as response:
                    with open(zip_path, 'wb') as f:
                        shutil.copyfileobj(response, f)
                
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # 查找ChromeDriver
                    for file_info in zip_ref.filelist:
                        if file_info.filename.endswith('chromedriver.exe'):
                            with zip_ref.open(file_info.filename) as source:
                                with open(driver_path, 'wb') as target:
                                    shutil.copyfileobj(source, target)
                            break
                    else:
                        # 解压所有文件并查找
                        zip_ref.extractall(chrome_dir)
                        for extracted_file in chrome_dir.rglob('chromedriver.exe'):
                            shutil.move(str(extracted_file), driver_path)
                            break
                
                zip_path.unlink()
                
                if driver_path.exists():
                    print("✅ 备用ChromeDriver下载成功")
                    # 清理临时文件夹
                    for item in chrome_dir.iterdir():
                        if item.is_dir():
                            shutil.rmtree(item)
                    return True
                    
            except Exception as e:
                print(f"⚠️ 备用地址{i+1}失败: {e}")
                continue
        
        print("❌ 所有备用地址都失败")
        return False
        
    except Exception as e:
        print(f"❌ 备用下载失败: {e}")
        return False

def check_chrome_installation():
    """检查Chrome浏览器是否安装"""
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"✅ 发现Chrome浏览器: {path}")
            return True
    
    print("⚠️ 未发现Chrome浏览器安装")
    print("💡 请先安装Google Chrome浏览器: https://www.google.com/chrome/")
    return False

def install_pyinstaller():
    """安装PyInstaller"""
    try:
        import PyInstaller
        print(f"✅ PyInstaller已安装: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("📦 正在安装PyInstaller...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
            print("✅ PyInstaller安装完成")
            return True
        except subprocess.CalledProcessError:
            print("❌ PyInstaller安装失败")
            return False

def check_core_files():
    """检查核心文件"""
    required_files = {
        'start_web.py': '主入口文件',
        'web_app.py': 'Web应用',
        'config.py': '配置文件',
        'qiangpiao.py': '核心逻辑',
        'templates': '模板目录'
    }
    
    missing = []
    for file, desc in required_files.items():
        if not os.path.exists(file):
            print(f"❌ 缺失: {file} ({desc})")
            missing.append(file)
        else:
            print(f"✅ {file}")
    
    return len(missing) == 0

def clean_build():
    """清理构建目录"""
    exe_dir = Path('exe')
    if exe_dir.exists():
        dirs_to_clean = ['build', 'dist', 'release']
        for dir_name in dirs_to_clean:
            dir_path = exe_dir / dir_name
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"🧹 清理: exe/{dir_name}")
    
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"🧹 清理: {dir_name}")
    
    for spec_file in Path('.').glob('*.spec'):
        spec_file.unlink()

def build_exe():
    """构建exe文件"""
    print("🔨 开始构建exe...")
    
    # 增强的PyInstaller命令
    cmd = [
        'pyinstaller',
        '--onefile',                      # 单文件
        '--console',                      # 显示控制台
        '--name=深大体育场馆预约系统',      # 程序名称
        '--add-data=templates;templates', # 包含模板
        '--add-data=chrome_driver;chrome_driver',  # 包含ChromeDriver
        '--hidden-import=flask',
        '--hidden-import=requests', 
        '--hidden-import=urllib3',
        '--hidden-import=selenium',
        '--hidden-import=selenium.webdriver',
        '--hidden-import=selenium.webdriver.chrome',
        '--hidden-import=selenium.webdriver.chrome.service',
        '--hidden-import=selenium.webdriver.chrome.options',
        '--hidden-import=selenium.webdriver.common.by',
        '--hidden-import=selenium.webdriver.support.ui',
        '--hidden-import=selenium.webdriver.support.expected_conditions',
        '--collect-all=flask',
        '--collect-all=jinja2',
        '--collect-all=selenium',
        'start_web.py'                    # 入口文件
    ]
    
    # 可选功能
    if os.path.exists('static'):
        cmd.insert(-1, '--add-data=static;static')
    
    if os.path.exists('icon.ico'):
        cmd.insert(-1, '--icon=icon.ico')
    
    print(f"🔧 执行PyInstaller...")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ 构建成功!")
        
        # 创建exe目录并移动构建文件
        exe_dir = Path('exe')
        exe_dir.mkdir(exist_ok=True)
        
        if os.path.exists('build'):
            if (exe_dir / 'build').exists():
                shutil.rmtree(exe_dir / 'build')
            shutil.move('build', exe_dir / 'build')
            print("📁 移动 build 目录到 exe/")
        
        if os.path.exists('dist'):
            if (exe_dir / 'dist').exists():
                shutil.rmtree(exe_dir / 'dist')
            shutil.move('dist', exe_dir / 'dist')
            print("📁 移动 dist 目录到 exe/")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 构建失败: {e}")
        if e.stderr:
            error_lines = e.stderr.split('\n')[-10:]
            for line in error_lines:
                if line.strip():
                    print(f"   {line}")
        return False

def create_release():
    """创建发布包"""
    exe_dir = Path('exe')
    exe_dir.mkdir(exist_ok=True)
    
    release_dir = exe_dir / 'release'
    
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir()
    
    # 复制exe文件
    exe_file = exe_dir / 'dist' / '深大体育场馆预约系统.exe'
    if not exe_file.exists():
        print("❌ 找不到生成的exe文件")
        return False
    
    shutil.copy2(exe_file, release_dir)
    exe_size = exe_file.stat().st_size / 1024 / 1024
    print(f"📦 复制exe文件 ({exe_size:.1f} MB)")
    
    # 复制必要的配置文件
    config_files = ['config.py', 'qiangpiao.py', 'web_app.py', 'cookie_manager.py', 'start_web.py', 'get_cookie.py', 'error_filter.py']
    for file in config_files:
        if os.path.exists(file):
            shutil.copy2(file, release_dir)
    
    # 复制模板目录
    if os.path.exists('templates'):
        shutil.copytree('templates', release_dir / 'templates')
    
    # 创建便携启动脚本
    start_script = """@echo off
title 深大体育场馆预约系统
echo ==========================================
echo    深大体育场馆预约系统 v
echo    智能版 - 支持Chrome 110-136版本
echo ==========================================
echo.
echo 正在启动系统...
echo 请稍候，浏览器将自动打开
echo.
echo 系统特性:
echo - 自动检测Chrome版本(支持110-136)
echo - 智能下载匹配的ChromeDriver
echo - 无需手动配置环境
echo - 支持最新Chrome 136版本
echo.
echo 如需停止程序，请直接关闭此窗口
echo ==========================================
echo.

"深大体育场馆预约系统.exe"

pause
"""
    
    with open(release_dir / '启动系统.bat', 'w', encoding='gbk') as f:
        f.write(start_script)
    
    # 创建详细使用说明
    readme = """# 深大体育场馆预约系统 v1.0 - 智能版

## 🚀 快速开始
1. 双击运行 "启动系统.bat" 或 "深大体育场馆预约系统.exe"
2. 系统将自动检测您的Chrome版本并下载匹配的ChromeDriver
3. 等待浏览器自动打开(首次启动需要10-30秒)
4. 在网页中配置个人信息和Cookie
5. 开始抢票

## ✨ v1.0版本特点
- ✅ 支持Chrome 110-136版本(包括最新版本)
- ✅ 自动检测Chrome浏览器版本
- ✅ 智能下载匹配的ChromeDriver
- ✅ 使用最新的Chrome for Testing下载源
- ✅ 多重备用下载地址
- ✅ 无需手动配置环境
- ✅ 完整的Web管理界面
- ✅ 支持自动获取Cookie

## 🌐 完整支持的Chrome版本
- Chrome 136.x - ChromeDriver 136.0.7103.113 (最新)
- Chrome 135.x - ChromeDriver 135.0.6790.75
- Chrome 134.x - ChromeDriver 134.0.6977.95
- Chrome 133.x - ChromeDriver 133.0.6926.62
- Chrome 132.x - ChromeDriver 132.0.6834.83
- Chrome 131.x - ChromeDriver 131.0.6778.85
- Chrome 130.x - ChromeDriver 130.0.6723.92
- Chrome 129.x - ChromeDriver 129.0.6668.89
- Chrome 128.x - ChromeDriver 128.0.6613.84
- Chrome 127.x - ChromeDriver 127.0.6533.119
- Chrome 126.x - ChromeDriver 126.0.6478.182
- Chrome 125.x - ChromeDriver 125.0.6422.141
- Chrome 124.x - ChromeDriver 124.0.6367.201
- Chrome 123.x - ChromeDriver 123.0.6312.122
- Chrome 122.x - ChromeDriver 122.0.6261.128
- Chrome 121.x - ChromeDriver 121.0.6167.184
- Chrome 120.x - ChromeDriver 120.0.6099.109
- Chrome 119.x - ChromeDriver 119.0.6045.105
- Chrome 118.x - ChromeDriver 118.0.5993.70
- Chrome 117.x - ChromeDriver 117.0.5938.92
- Chrome 116.x - ChromeDriver 116.0.5845.96
- Chrome 115.x - ChromeDriver 115.0.5790.102
- Chrome 114.x - ChromeDriver 114.0.5735.90
- Chrome 113.x - ChromeDriver 113.0.5672.63
- Chrome 112.x - ChromeDriver 112.0.5615.49
- Chrome 111.x - ChromeDriver 111.0.5563.64
- Chrome 110.x - ChromeDriver 110.0.5481.77

## 🔧 配置说明
- 修改 config.py 设置学号、姓名等基本信息
- 在网页界面更新Cookie(自动获取或手动输入)
- 所有配置都在网页界面完成，简单易用

## 📱 功能特色
- 🏠 主页：查看系统状态和快速操作
- 🔧 配置管理：设置个人信息和预约参数  
- 🍪 Cookie管理：自动/手动获取登录凭证
- 🎯 智能抢票：自动监控并预约场地

## ⚠️ 注意事项
- 需要安装Google Chrome浏览器(任意110-136版本)
- 首次运行会自动下载ChromeDriver（需要网络）
- 需要联网使用
- 防火墙提示请选择"允许访问"
- Cookie获取时会弹出浏览器窗口，这是正常现象
- 如遇企业微信验证码，请在浏览器中及时输入

## 🛠️ 故障排除
如果遇到问题：
1. 确保已安装Google Chrome浏览器
2. 检查网络连接（下载ChromeDriver需要）
3. 关闭杀毒软件的实时防护
4. 以管理员身份运行
5. 检查是否被防火墙阻止
6. 如果Chrome版本过新(>136)，系统会自动使用兼容版本

## 📊 系统要求
- Windows 7/8/10/11
- Google Chrome浏览器 (版本110-136)
- 4GB以上内存
- 稳定的网络连接

## 🔄 更新日志 v1.0
- ✅ 新增支持Chrome 120-136版本
- ✅ 更新ChromeDriver下载源为Chrome for Testing
- ✅ 增强版本检测和匹配算法
- ✅ 添加多重备用下载地址
- ✅ 优化错误处理和用户提示

版本: v1.0 智能版
更新日期: """ + str(__import__('datetime').datetime.now().strftime('%Y-%m-%d')) + """
开发者: GitHub Copilot Assistant
"""
    
    with open(release_dir / 'README.txt', 'w', encoding='utf-8') as f:
        f.write(readme)
    
    print(f"🎉 v1.0智能版发布包创建完成: {release_dir.absolute()}")
    
    # 显示文件列表
    print("\n📂 发布包内容:")
    for item in release_dir.iterdir():
        if item.is_file():
            size = item.stat().st_size
            if size > 1024 * 1024:
                size_str = f"{size / 1024 / 1024:.1f} MB"
            elif size > 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size} B"
            print(f"   📄 {item.name} ({size_str})")
    
    return True

def main():
    print("🚀 深大体育场馆预约系统 v1.0 - 智能打包工具")
    print("=" * 60)
    print("🆕 支持Chrome 110-136版本(包括最新版本)")
    print("=" * 60)
    
    try:
        # 1. 检查Chrome浏览器
        print("\n🌐 检查Chrome浏览器...")
        chrome_installed = check_chrome_installation()
        
        # 2. 检测Chrome版本并下载对应ChromeDriver
        print("\n📱 智能下载ChromeDriver...")
        chrome_version = get_chrome_version()
        if chrome_version:
            driver_version = get_compatible_chromedriver_version(chrome_version)
            print(f"🎯 目标ChromeDriver版本: {driver_version}")
        else:
            driver_version = None
            print("🎯 将下载通用版本ChromeDriver")
        
        if not download_chromedriver(driver_version):
            if chrome_installed:
                print("⚠️ ChromeDriver下载失败，但Chrome已安装，继续构建...")
            else:
                print("❌ Chrome和ChromeDriver都不可用，请先安装Chrome浏览器")
                return False
        
        # 3. 检查环境
        print("\n📦 检查构建环境...")
        if not install_pyinstaller():
            return False
        
        # 4. 检查文件
        print("\n📁 检查项目文件...")
        if not check_core_files():
            print("❌ 缺少必要文件，请检查项目完整性")
            return False
        
        # 5. 清理旧文件
        print("\n🧹 清理构建文件...")
        clean_build()
        
        # 6. 构建exe
        print("\n🔨 构建v1.0智能版exe文件...")
        if not build_exe():
            return False
        
        # 7. 创建发布包
        print("\n📦 创建v1.0智能版发布包...")
        if not create_release():
            return False
        
        print("\n" + "=" * 60)
        print("✅ v1.0智能版打包完成!")
        print("\n📋 使用步骤:")
        print("1. 进入 exe/release 目录")
        print("2. 双击运行 '启动系统.bat'")
        print("3. 系统自动检测Chrome并下载匹配驱动")
        print("4. 等待浏览器自动打开")
        print("5. 在网页中配置个人信息")
        print("6. 开始使用")
        print("\n🎁 v1.0版本特点:")
        print("   ✅ 支持Chrome 110-136版本")
        print("   ✅ 自动检测Chrome版本")
        print("   ✅ 智能下载匹配ChromeDriver")
        print("   ✅ 使用最新Chrome for Testing下载源")
        print("   ✅ 多重备用下载地址")
        print("   ✅ 无需手动配置环境")
        print("   ✅ 完整功能集成")
        
        return True
        
    except KeyboardInterrupt:
        print("\n⛔ 用户取消操作")
        return False
    except Exception as e:
        print(f"\n❌ 打包失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    input(f"\n{'✅ 成功' if success else '❌ 失败'}! 按回车键退出...")