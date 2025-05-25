# 网络连接测试脚本
import requests
import urllib3
import ssl
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SSLAdapter(HTTPAdapter):
    """自定义SSL适配器，支持更宽松的SSL配置"""
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        context.set_ciphers('DEFAULT@SECLEVEL=1')  # 降低安全级别
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

def test_connection():
    """测试网络连接"""
    print("🔍 测试网络连接...")
    
    # 创建session并配置SSL适配器
    session = requests.Session()
    session.mount('https://', SSLAdapter())
    
    # 设置headers，模拟浏览器
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        # 测试基本网络连接
        resp = session.get("https://www.baidu.com", timeout=5, verify=False, headers=headers)
        print("✅ 基本网络连接正常")
        
        # 测试深大服务器连接 - 使用多种方法
        print("🔄 尝试连接深大服务器...")
        
        # 方法1：使用自定义SSL配置
        try:
            resp = session.get("https://ehall.szu.edu.cn", timeout=15, verify=False, headers=headers)
            print("✅ 深大服务器连接正常 (方法1)")
            print(f"   状态码: {resp.status_code}")
            return True
        except Exception as e1:
            print(f"⚠️  方法1失败: {e1}")
            
            # 方法2：尝试HTTP而不是HTTPS
            try:
                resp = session.get("http://ehall.szu.edu.cn", timeout=15, headers=headers)
                print("✅ 深大服务器连接正常 (HTTP)")
                print(f"   状态码: {resp.status_code}")
                return True
            except Exception as e2:
                print(f"⚠️  方法2失败: {e2}")
                
                # 方法3：尝试不同的TLS版本
                try:
                    # 创建新的session，强制使用TLS 1.0
                    new_session = requests.Session()
                    
                    class TLS10Adapter(HTTPAdapter):
                        def init_poolmanager(self, *args, **kwargs):
                            context = ssl.create_default_context()
                            context.minimum_version = ssl.TLSVersion.TLSv1
                            context.maximum_version = ssl.TLSVersion.TLSv1_2
                            context.set_ciphers('DEFAULT@SECLEVEL=1')
                            context.check_hostname = False
                            context.verify_mode = ssl.CERT_NONE
                            kwargs['ssl_context'] = context
                            return super().init_poolmanager(*args, **kwargs)
                    
                    new_session.mount('https://', TLS10Adapter())
                    resp = new_session.get("https://ehall.szu.edu.cn", timeout=15, verify=False, headers=headers)
                    print("✅ 深大服务器连接正常 (TLS 1.0)")
                    print(f"   状态码: {resp.status_code}")
                    return True
                except Exception as e3:
                    print(f"❌ 所有连接方法都失败了")
                    print(f"   方法1错误: {e1}")
                    print(f"   方法2错误: {e2}")
                    print(f"   方法3错误: {e3}")
                    return False
        
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL错误: {e}")
        return False
    except requests.exceptions.Timeout as e:
        print(f"❌ 连接超时: {e}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

if __name__ == "__main__":
    test_connection()