# 测试脚本初始化
from qiangpiao import check_login_status, CONFIG
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print("=" * 50)
print("🧪 抢票脚本测试")
print("=" * 50)

print(f"📅 目标日期: {CONFIG['TARGET_DATE']}")
print(f"🏫 校区: {'丽湖' if CONFIG['XQ'] == '2' else '粤海'}")
print(f"🏸 运动项目: {CONFIG['XMDM']}")

print("\n🔐 测试登录状态...")
try:
    status = check_login_status()
    if status:
        print("✅ 登录状态检查通过")
    else:
        print("❌ 登录状态失效")
except Exception as e:
    print(f"❌ 登录检查失败: {e}")

print("\n✅ 初始化测试完成")
