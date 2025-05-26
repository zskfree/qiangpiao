# -*- coding: utf-8 -*-
"""
深大体育场馆预约系统 - 简化打包脚本
使用PyInstaller将项目打包为exe文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

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
    # 清理exe目录下的构建文件
    exe_dir = Path('exe')
    if exe_dir.exists():
        dirs_to_clean = ['build', 'dist', 'release']
        for dir_name in dirs_to_clean:
            dir_path = exe_dir / dir_name
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"🧹 清理: exe/{dir_name}")
    
    # 清理根目录的构建文件
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"🧹 清理: {dir_name}")
    
    # 删除spec文件
    for spec_file in Path('.').glob('*.spec'):
        spec_file.unlink()

def build_exe():
    """构建exe文件"""
    print("🔨 开始构建exe...")
    
    # 核心PyInstaller命令
    cmd = [
        'pyinstaller',
        '--onefile',                      # 单文件
        '--console',                      # 显示控制台
        '--name=深大体育场馆预约系统',      # 程序名称
        '--add-data=templates;templates', # 包含模板
        '--hidden-import=flask',
        '--hidden-import=requests', 
        '--hidden-import=urllib3',
        '--hidden-import=selenium',
        '--collect-all=flask',
        '--collect-all=jinja2',
        'start_web.py'                    # 入口文件
    ]
    
    # 可选功能
    if os.path.exists('static'):
        cmd.insert(-1, '--add-data=static;static')
    
    if os.path.exists('icon.ico'):
        cmd.insert(-1, '--icon=icon.ico')
    
    print(f"🔧 执行: {' '.join(cmd[:3])}...")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ 构建成功!")
        
        # 创建exe目录并移动构建文件
        exe_dir = Path('exe')
        exe_dir.mkdir(exist_ok=True)
        
        # 移动build和dist目录到exe文件夹
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
        # 显示关键错误信息
        if e.stderr:
            error_lines = e.stderr.split('\n')[-10:]  # 最后10行
            for line in error_lines:
                if line.strip():
                    print(f"   {line}")
        return False

def create_release():
    """创建发布包"""
    exe_dir = Path('exe')
    exe_dir.mkdir(exist_ok=True)
    
    release_dir = exe_dir / 'release'  # 在exe目录下创建release目录
    
    # 清理并创建发布目录
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
    config_files = ['config.py', 'qiangpiao.py', 'web_app.py']
    for file in config_files:
        if os.path.exists(file):
            shutil.copy2(file, release_dir)
    
    # 复制模板目录
    if os.path.exists('templates'):
        shutil.copytree('templates', release_dir / 'templates')
    
    # 复制静态文件目录（如果存在）
    if os.path.exists('static'):
        shutil.copytree('static', release_dir / 'static')
    
    # 创建简化的使用说明
    readme = """# 深大体育场馆预约系统

## 快速开始
1. 双击运行 "深大体育场馆预约系统.exe"
2. 等待浏览器自动打开(首次启动需要10-30秒)
3. 在网页中配置个人信息和Cookie
4. 开始抢票

## 配置说明
- 修改 config.py 设置学号、姓名等基本信息
- 在网页界面更新Cookie(登录ehall.szu.edu.cn获取)

## 注意事项
- 首次运行可能较慢，请耐心等待
- 需要联网使用
- 防火墙提示请选择"允许访问"

版本: v2.0
"""
    
    with open(release_dir / 'README.txt', 'w', encoding='utf-8') as f:
        f.write(readme)
    
    print(f"🎉 发布包创建完成: {release_dir.absolute()}")
    
    # 显示文件列表
    print("\n📂 exe 目录结构:")
    for item in exe_dir.iterdir():
        if item.is_dir():
            print(f"   📁 {item.name}/")
            if item.name == 'release':
                for file in item.rglob('*'):
                    if file.is_file():
                        size = file.stat().st_size
                        if size > 1024 * 1024:
                            size_str = f"{size / 1024 / 1024:.1f} MB"
                        else:
                            size_str = f"{size / 1024:.1f} KB"
                        rel_path = file.relative_to(exe_dir)
                        print(f"      📄 {rel_path} ({size_str})")
    
    return True

def main():
    print("🚀 深大体育场馆预约系统 - 打包工具")
    print("=" * 50)
    
    try:
        # 1. 检查环境
        if not install_pyinstaller():
            return False
        
        # 2. 检查文件
        print("\n📁 检查项目文件...")
        if not check_core_files():
            print("❌ 缺少必要文件，请检查项目完整性")
            return False
        
        # 3. 清理旧文件
        print("\n🧹 清理构建文件...")
        clean_build()
        
        # 4. 构建exe
        print("\n🔨 构建exe文件...")
        if not build_exe():
            return False
        
        # 5. 创建发布包
        print("\n📦 创建发布包...")
        if not create_release():
            return False
        
        print("\n" + "=" * 50)
        print("✅ 打包完成!")
        print("\n📋 后续步骤:")
        print("1. 进入 exe/release 目录")  # 修改提示信息
        print("2. 双击运行exe文件或启动脚本") 
        print("3. 在网页中配置个人信息")
        print("4. 开始使用")
        print("\n📁 所有构建文件都在 exe/ 目录下:")
        print("   - exe/build/     (构建临时文件)")
        print("   - exe/dist/      (生成的exe文件)")
        print("   - exe/release/   (最终发布包)")
        
        return True
        
    except KeyboardInterrupt:
        print("\n⛔ 用户取消操作")
        return False
    except Exception as e:
        print(f"\n❌ 打包失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    input(f"\n{'✅ 成功' if success else '❌ 失败'}! 按回车键退出...")
