# 辅助工具脚本
import sys
from datetime import datetime, timedelta

def update_cookie():
    """更新cookie的交互式工具"""
    print("=" * 50)
    print("🔧 Cookie更新工具")
    print("=" * 50)
    print()
    print("请按照以下步骤获取最新的Cookie：")
    print("1. 打开浏览器，访问深圳大学体育场馆预约系统")
    print("2. 登录你的账号")
    print("3. 按F12打开开发者工具")
    print("4. 在Network标签页中刷新页面")
    print("5. 找到任意请求，复制Cookie值")
    print()
    
    new_cookie = input("请粘贴新的Cookie值: ").strip()
    
    if not new_cookie:
        print("❌ Cookie不能为空！")
        return False
    
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
    
    new_content = content[:start_idx] + '\n' + new_cookie + '\n' + content[end_idx:]
    
    # 写入文件
    with open('qiangpiao.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Cookie更新成功！")
    return True

def show_config():
    """显示当前配置"""
    try:
        from config import CONFIG, SPORT_CODES, CAMPUS_CODES
        
        print("=" * 50)
        print("⚙️  当前配置信息")
        print("=" * 50)
        print(f"目标日期: {CONFIG['TARGET_DATE']}")
        print(f"校区: {CONFIG['XQ']} ({'粤海' if CONFIG['XQ'] == '1' else '丽湖'})")
        print(f"运动项目: {CONFIG['XMDM']}")
        print(f"最大重试次数: {CONFIG['MAX_RETRY_TIMES']}")
        print(f"重试间隔: {CONFIG['RETRY_INTERVAL']}秒")
        print("\n优先时段:")
        for i, time_slot in enumerate(CONFIG['PREFERRED_TIMES'], 1):
            print(f"  {i}. {time_slot}")
        print()
        
    except ImportError:
        print("❌ 配置文件读取失败！")

def main():
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python utils.py cookie    # 更新Cookie")
        print("  python utils.py config    # 查看配置")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'cookie':
        update_cookie()
    elif command == 'config':
        show_config()
    else:
        print("❌ 未知命令！")

if __name__ == "__main__":
    main()
