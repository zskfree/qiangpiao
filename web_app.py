from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import json
import os
import threading
import time
from datetime import datetime, timedelta
import logging
from qiangpiao import get_available_slots, book_slot, check_login_status, extract_cookies_from_text, test_cookie_validity, update_cookie_in_file
from config import CONFIG, SPORT_CODES, CAMPUS_CODES, TIME_SLOTS, get_campus_account, update_campus_account

app = Flask(__name__)
app.secret_key = 'qiangpiao_secret_key_2024'

def reset_booking_status():
    """重置抢票状态"""
    global booking_status
    booking_status = {
        'running': False,
        'thread': None,
        'results': [],
        'current_status': '未开始',
        'retry_count': 0,
        'start_time': None,
        'stop_event': None
    }

# 全局变量 - 初始化时重置
booking_status = {}
reset_booking_status()

@app.route('/')
def index():
    """主页"""
    return render_template('index.html', 
                         config=CONFIG, 
                         sport_codes=SPORT_CODES, 
                         campus_codes=CAMPUS_CODES,
                         time_slots=TIME_SLOTS)

@app.route('/config')
def config_page():
    """配置页面"""
    return render_template('config.html', 
                         config=CONFIG, 
                         sport_codes=SPORT_CODES, 
                         campus_codes=CAMPUS_CODES,
                         time_slots=TIME_SLOTS)

@app.route('/cookie')
def cookie_page():
    """Cookie管理页面"""
    return render_template('cookie.html')

@app.route('/booking')
def booking_page():
    """抢票页面"""
    return render_template('booking.html', status=booking_status)

@app.route('/api/config', methods=['POST'])
def update_config():
    """更新配置"""
    try:
        data = request.json
        
        # 更新CONFIG
        if 'XQ' in data:
            CONFIG['XQ'] = data['XQ']
        if 'XMDM' in data:
            CONFIG['XMDM'] = data['XMDM']
        if 'TARGET_DATE' in data:
            CONFIG['TARGET_DATE'] = data['TARGET_DATE']
        if 'PREFERRED_TIMES' in data:
            CONFIG['PREFERRED_TIMES'] = [t.strip() for t in data['PREFERRED_TIMES'] if t.strip()]
        if 'USER_INFO' in data:
            CONFIG['USER_INFO'].update(data['USER_INFO'])
        if 'MAX_RETRY_TIMES' in data:
            CONFIG['MAX_RETRY_TIMES'] = int(data['MAX_RETRY_TIMES'])
        if 'RETRY_INTERVAL' in data:
            CONFIG['RETRY_INTERVAL'] = int(data['RETRY_INTERVAL'])
        
        # 保存到文件
        save_config_to_file()
        
        return jsonify({'success': True, 'message': '配置更新成功！'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'配置更新失败: {str(e)}'})

@app.route('/api/cookie/test', methods=['POST'])
def test_cookie():
    """测试Cookie有效性"""
    try:
        data = request.json
        cookie_text = data.get('cookie', '').strip()
        
        if not cookie_text:
            return jsonify({'success': False, 'message': 'Cookie不能为空'})
        
        print(f"测试Cookie文本长度: {len(cookie_text)}")
        
        # 解析Cookie
        try:
            cookies = extract_cookies_from_text(cookie_text)
            print(f"解析得到Cookie字段数量: {len(cookies)}")
            
            if not cookies:
                return jsonify({'success': False, 'message': 'Cookie格式无效，无法解析出任何字段'})
            
            # 显示解析的关键Cookie字段
            key_cookies = ['route', 'JSESSIONID', 'MOD_AUTH_CAS']
            found_keys = [key for key in key_cookies if key in cookies]
            print(f"找到关键Cookie字段: {found_keys}")
            
        except Exception as e:
            print(f"Cookie解析失败: {e}")
            return jsonify({'success': False, 'message': f'Cookie解析失败: {str(e)}'})
        
        # 测试Cookie有效性
        print("开始测试Cookie有效性...")
        try:
            is_valid, message = test_cookie_validity(cookies)
            print(f"Cookie测试结果: {is_valid}, 消息: {message}")
            
            # 返回详细的测试结果
            return jsonify({
                'success': is_valid,
                'message': message,
                'cookie_count': len(cookies),
                'found_keys': found_keys,
                'details': {
                    'total_fields': len(cookies),
                    'key_fields_found': len(found_keys),
                    'cookie_sample': {k: v[:20] + '...' if len(v) > 20 else v 
                                    for k, v in list(cookies.items())[:3]}
                }
            })
            
        except Exception as e:
            print(f"Cookie测试过程出错: {e}")
            return jsonify({
                'success': False, 
                'message': f'测试过程出错: {str(e)}',
                'cookie_count': len(cookies),
                'found_keys': found_keys
            })
        
    except Exception as e:
        print(f"Cookie测试接口错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'接口错误: {str(e)}'})

@app.route('/api/cookie/update', methods=['POST'])
def update_cookie():
    """更新Cookie"""
    try:
        data = request.json
        cookie_text = data.get('cookie', '').strip()
        
        if not cookie_text:
            return jsonify({'success': False, 'message': 'Cookie不能为空'})
        
        print(f"开始更新Cookie，文本长度: {len(cookie_text)}")
        
        # 先解析Cookie
        try:
            cookies = extract_cookies_from_text(cookie_text)
            print(f"解析得到Cookie字段: {len(cookies)} 个")
            
            if not cookies:
                return jsonify({'success': False, 'message': 'Cookie格式无效，无法解析'})
            
        except Exception as e:
            print(f"Cookie解析失败: {e}")
            return jsonify({'success': False, 'message': f'Cookie解析失败: {str(e)}'})
        
        # 先测试新Cookie的有效性
        print("验证新Cookie有效性...")
        try:
            is_valid, test_message = test_cookie_validity(cookies)
            print(f"Cookie验证结果: {is_valid}, 消息: {test_message}")
            
            if not is_valid:
                return jsonify({
                    'success': False, 
                    'message': f'Cookie无效，无法更新: {test_message}',
                    'test_result': test_message
                })
            
        except Exception as e:
            print(f"Cookie验证过程出错: {e}")
            # 验证出错时也允许更新，但给出警告
            pass
        
        # 更新到文件
        print("开始更新Cookie到文件...")
        try:
            success = update_cookie_in_file(cookie_text)
            
            if success:
                print("✅ Cookie更新成功")
                return jsonify({
                    'success': True, 
                    'message': 'Cookie更新成功！请刷新页面查看最新状态',
                    'cookie_count': len(cookies)
                })
            else:
                print("❌ Cookie文件更新失败")
                return jsonify({'success': False, 'message': 'Cookie文件更新失败'})
                
        except Exception as e:
            print(f"文件更新过程出错: {e}")
            return jsonify({'success': False, 'message': f'文件更新失败: {str(e)}'})
        
    except Exception as e:
        print(f"Cookie更新接口错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'})

@app.route('/api/booking/start', methods=['POST'])
def start_booking():
    """开始抢票"""
    try:
        if booking_status['running']:
            return jsonify({'success': False, 'message': '抢票已在运行中'})
        
        # 检查登录状态
        if not check_login_status():
            return jsonify({'success': False, 'message': 'Cookie已失效，请更新Cookie'})
        
        # 创建停止事件
        stop_event = threading.Event()
        booking_status['stop_event'] = stop_event
        
        # 启动抢票线程
        booking_status['running'] = True
        booking_status['results'] = []
        booking_status['current_status'] = '正在启动...'
        booking_status['retry_count'] = 0
        booking_status['start_time'] = datetime.now()
        
        thread = threading.Thread(target=booking_worker, args=(stop_event,))
        thread.daemon = True  # 设置为守护线程，主程序退出时会自动结束
        booking_status['thread'] = thread
        thread.start()
        
        return jsonify({'success': True, 'message': '抢票已启动！'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'启动失败: {str(e)}'})

@app.route('/api/booking/stop', methods=['POST'])
def stop_booking():
    """停止抢票"""
    try:
        booking_status['running'] = False
        if booking_status['stop_event']:
            booking_status['stop_event'].set()  # 设置停止信号
        booking_status['current_status'] = '正在停止...'
        
        return jsonify({'success': True, 'message': '正在停止抢票...'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'停止失败: {str(e)}'})

@app.route('/api/booking/status')
def booking_status_api():
    """获取抢票状态"""
    # 创建状态副本，排除不可序列化的对象
    status = {
        'running': booking_status['running'],
        'results': booking_status['results'],
        'current_status': booking_status['current_status'],
        'retry_count': booking_status['retry_count']
    }
    
    if booking_status['start_time']:
        elapsed = datetime.now() - booking_status['start_time']
        status['elapsed_time'] = str(elapsed).split('.')[0]  # 去掉微秒
    else:
        status['elapsed_time'] = '00:00:00'
    
    return jsonify(status)

@app.route('/api/cookie/current', methods=['GET'])
def get_current_cookie():
    """获取当前Cookie状态"""
    try:
        print("获取当前Cookie状态...")
        
        # 读取qiangpiao.py文件中的Cookie
        try:
            with open('qiangpiao.py', 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"读取文件失败: {e}")
            return jsonify({
                'success': False, 
                'message': f'读取qiangpiao.py文件失败: {str(e)}'
            })
        
        # 提取当前Cookie
        start_marker = 'raw_cookie = """'
        end_marker = '"""'
        
        start_idx = content.find(start_marker)
        if start_idx == -1:
            return jsonify({
                'success': False, 
                'message': '未找到Cookie定义，请检查qiangpiao.py文件格式'
            })
        
        start_idx += len(start_marker)
        end_idx = content.find(end_marker, start_idx)
        
        if end_idx == -1:
            return jsonify({
                'success': False, 
                'message': 'Cookie格式错误，缺少结束标记'
            })
        
        current_cookie_text = content[start_idx:end_idx].strip()
        print(f"提取到Cookie文本长度: {len(current_cookie_text)}")
        
        # 解析Cookie字段
        try:
            cookie_fields = extract_cookies_from_text(current_cookie_text)
            print(f"解析到Cookie字段: {len(cookie_fields)} 个")
        except Exception as e:
            print(f"Cookie解析失败: {e}")
            return jsonify({
                'success': False,
                'message': f'Cookie解析失败: {str(e)}',
                'cookie_text': current_cookie_text
            })
        
        # 测试Cookie有效性
        print("测试当前Cookie有效性...")
        try:
            is_valid, message = test_cookie_validity(cookie_fields)
            print(f"当前Cookie测试结果: {is_valid}, 消息: {message}")
        except Exception as e:
            print(f"Cookie测试失败: {e}")
            is_valid = False
            message = f"测试失败: {str(e)}"
        
        # 获取文件修改时间
        last_update = None
        try:
            import os
            stat = os.stat('qiangpiao.py')
            last_update = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            print(f"获取文件修改时间失败: {e}")
        
        # 检查关键Cookie字段
        key_cookies = ['route', 'JSESSIONID', 'MOD_AUTH_CAS']
        found_keys = [key for key in key_cookies if key in cookie_fields]
        missing_keys = [key for key in key_cookies if key not in cookie_fields]
        
        return jsonify({
            'success': True,
            'valid': is_valid,
            'message': message,
            'cookie_count': len(cookie_fields),
            'cookie_text': current_cookie_text,
            'cookie_fields': {k: v[:50] + '...' if len(v) > 50 else v 
                            for k, v in cookie_fields.items()},
            'last_update': last_update,
            'analysis': {
                'total_fields': len(cookie_fields),
                'key_fields_found': found_keys,
                'key_fields_missing': missing_keys,
                'status': 'good' if len(found_keys) >= 1 else 'warning'
            }
        })
        
    except Exception as e:
        print(f"获取Cookie状态失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取Cookie失败: {str(e)}'
        })

@app.route('/api/cookie/auto_get', methods=['POST'])
def auto_get_cookie():
    """自动获取Cookie - 使用有界面浏览器"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username:
            return jsonify({'success': False, 'message': '用户名不能为空'})
        
        # 如果密码是***，表示使用已保存的密码
        if password == '***':
            current_account = get_campus_account()
            saved_password = current_account.get('password', '')
            if not saved_password:
                return jsonify({'success': False, 'message': '未找到已保存的密码，请重新输入'})
            password = saved_password
            print(f"使用已保存的密码进行Cookie获取，用户: {username}")
        elif not password:
            return jsonify({'success': False, 'message': '密码不能为空'})
        else:
            # 如果提供了新密码，更新保存的账户信息
            update_campus_account(username, password)
            print(f"使用新密码并保存，用户: {username}")
        
        # 导入并调用获取cookie的函数
        try:
            from get_cookie import auto_login_and_get_cookies
            
            print(f"启动浏览器获取Cookie... 用户: {username}")
            
            # 创建一个回调函数来更新状态
            status_messages = []
            def status_callback(message):
                status_messages.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
                print(f"Cookie获取状态: {message}")
            
            # 使用线程来避免阻塞web请求
            import threading
            result = {'success': False, 'message': '', 'cookie': '', 'status_log': []}
            
            def get_cookie_worker():
                try:
                    print("开始Cookie获取工作线程...")
                    cookie_str = auto_login_and_get_cookies(username, password, status_callback)
                    print(f"Cookie获取结果: {'成功' if cookie_str else '失败'}")
                    
                    if cookie_str:
                        # 尝试更新到文件
                        print("尝试更新Cookie到文件...")
                        success = update_cookie_in_file(cookie_str)
                        if success:
                            result.update({
                                'success': True, 
                                'cookie': cookie_str,
                                'message': 'Cookie获取并更新成功！',
                                'status_log': status_messages
                            })
                            print("✅ Cookie获取和更新都成功")
                        else:
                            result.update({
                                'success': False, 
                                'message': 'Cookie获取成功但更新到文件失败',
                                'cookie': cookie_str,
                                'status_log': status_messages
                            })
                            print("⚠️ Cookie获取成功但文件更新失败")
                    else:
                        result.update({
                            'success': False, 
                            'message': 'Cookie获取失败，请检查账号密码或网络连接',
                            'status_log': status_messages
                        })
                        print("❌ Cookie获取失败")
                except Exception as e:
                    error_msg = f'获取过程出错: {str(e)}'
                    result.update({
                        'success': False,
                        'message': error_msg,
                        'status_log': status_messages
                    })
                    print(f"❌ Cookie获取线程异常: {e}")
                    import traceback
                    traceback.print_exc()
            
            # 启动获取线程并等待完成
            thread = threading.Thread(target=get_cookie_worker)
            thread.daemon = True
            thread.start()
            
            print("等待Cookie获取线程完成...")
            thread.join(timeout=180)  # 减少到3分钟
            
            if thread.is_alive():
                result.update({
                    'success': False,
                    'message': '获取超时，请检查是否在浏览器中完成了登录。如遇验证码请及时输入。',
                    'status_log': status_messages
                })
                print("⚠️ Cookie获取超时")
            
            print(f"返回结果: success={result['success']}, message_length={len(result.get('message', ''))}")
            return jsonify(result)
            
        except ImportError as e:
            error_msg = f'获取Cookie模块导入失败: {str(e)}'
            print(f"❌ 导入错误: {error_msg}")
            return jsonify({'success': False, 'message': error_msg})
        except Exception as e:
            error_msg = f'模块加载出错: {str(e)}'
            print(f"❌ 模块错误: {error_msg}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'message': error_msg})
            
    except Exception as e:
        error_msg = f'操作失败: {str(e)}'
        print(f"❌ API错误: {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': error_msg})

@app.route('/api/config/campus_account', methods=['GET'])
def get_campus_account_api():
    """获取校园网账户配置"""
    try:
        account = get_campus_account()
        # 返回用户名和密码状态（不返回实际密码）
        return jsonify({
            'success': True, 
            'account': {
                'username': account.get('username', ''),
                'password': '***' if account.get('password', '') else ''
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'})

@app.route('/api/config/campus_account', methods=['POST'])
def update_campus_account_api():
    """更新校园网账户配置"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username:
            return jsonify({'success': False, 'message': '用户名不能为空'})
        
        # 如果密码是***，保持原密码不变
        if password == '***':
            current_account = get_campus_account()
            password = current_account.get('password', '')
        
        # 更新内存中的账户信息
        update_campus_account(username, password)
        
        # 保存到配置文件
        save_success = save_config_to_file()
        
        if save_success:
            return jsonify({'success': True, 'message': '账户信息更新成功'})
        else:
            return jsonify({'success': False, 'message': '账户信息更新失败，无法保存到文件'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'})

@app.route('/api/cookie/clear', methods=['POST'])
def clear_cookie():
    """清空Cookie"""
    try:
        print("开始清空Cookie...")
        
        # 导入cookie管理器的清空函数
        try:
            from cookie_manager import clear_cookie_in_file
            success = clear_cookie_in_file()
            
            if success:
                print("✅ Cookie清空成功")
                return jsonify({
                    'success': True, 
                    'message': 'Cookie已清空！请重新获取Cookie'
                })
            else:
                print("❌ Cookie清空失败")
                return jsonify({'success': False, 'message': 'Cookie清空失败'})
                
        except ImportError as e:
            print(f"导入cookie_manager失败: {e}")
            # 如果导入失败，直接更新为空Cookie
            success = update_cookie_in_file("")
            if success:
                return jsonify({
                    'success': True, 
                    'message': 'Cookie已清空！'
                })
            else:
                return jsonify({'success': False, 'message': 'Cookie清空失败'})
        
    except Exception as e:
        print(f"Cookie清空接口错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'清空失败: {str(e)}'})

def booking_worker(stop_event):
    """抢票工作线程"""
    try:
        max_bookings = 2
        successful_bookings = []
        
        while (booking_status['running'] and 
               booking_status['retry_count'] < CONFIG['MAX_RETRY_TIMES'] and
               not stop_event.is_set()):  # 检查停止信号
            try:
                booking_status['retry_count'] += 1
                booking_status['current_status'] = f'第{booking_status["retry_count"]}次查询中...'
                
                # 如果已经预约满了
                if len(successful_bookings) >= max_bookings:
                    booking_status['current_status'] = f'已成功预约{max_bookings}个时间段'
                    booking_status['running'] = False
                    break
                
                # 检查停止信号
                if stop_event.is_set():
                    break
                
                available_slots = get_available_slots()
                
                if available_slots:
                    booking_status['current_status'] = f'发现{len(available_slots)}个可用时段，开始预约...'
                    
                    # 过滤已预约的时间段
                    booked_time_slots = [b['time_slot'] for b in successful_bookings]
                    remaining_slots = [s for s in available_slots if s['time_slot'] not in booked_time_slots]
                    
                    if remaining_slots:
                        # 按时间段分组
                        time_slot_groups = {}
                        for slot in remaining_slots:
                            if slot['time_slot'] not in time_slot_groups:
                                time_slot_groups[slot['time_slot']] = []
                            time_slot_groups[slot['time_slot']].append(slot)
                        
                        # 尝试预约
                        for time_slot in CONFIG["PREFERRED_TIMES"]:
                            if not booking_status['running'] or stop_event.is_set():
                                break
                            
                            if len(successful_bookings) >= max_bookings:
                                break
                            
                            if time_slot in booked_time_slots:
                                continue
                            
                            if time_slot in time_slot_groups:
                                slots_in_time = time_slot_groups[time_slot]
                                first_slot = slots_in_time[0]
                                
                                booking_status['current_status'] = f'尝试预约: {time_slot} - {first_slot["venue_name"]}'
                                
                                success = book_slot(first_slot['wid'], first_slot['name'])
                                
                                if success:
                                    booking_record = {
                                        'time_slot': first_slot['time_slot'],
                                        'venue_name': first_slot['venue_name'],
                                        'slot_name': first_slot['name'],
                                        'timestamp': datetime.now().strftime('%H:%M:%S')
                                    }
                                    successful_bookings.append(booking_record)
                                    booking_status['results'] = successful_bookings
                                    
                                    booking_status['current_status'] = f'预约成功！已预约{len(successful_bookings)}/{max_bookings}个时间段'
                                    
                                    if len(successful_bookings) >= max_bookings:
                                        booking_status['running'] = False
                                        break
                                    
                                    # 可中断的延迟
                                    if stop_event.wait(1):  # 等待1秒或收到停止信号
                                        break
                                else:
                                    # 检查是否是预约上限错误
                                    booking_status['current_status'] = f'时间段{time_slot}预约失败，继续尝试下一个...'
                                    
                                    # 如果检测到预约上限，停止尝试
                                    if "只能预订2次" in booking_status['current_status'] or "已预订2次" in str(booking_status.get('last_error', '')):
                                        booking_status['current_status'] = '🎊 已达到当日预约上限！'
                                        booking_status['running'] = False
                                        break
                                    
                                    # 可中断的延迟
                                    if stop_event.wait(1):
                                        break
                
                else:
                    booking_status['current_status'] = '暂无可预约时段，继续监控...'
                
                # 可中断的等待
                if booking_status['running'] and len(successful_bookings) < max_bookings:
                    for i in range(CONFIG['RETRY_INTERVAL']):
                        if not booking_status['running'] or stop_event.is_set():
                            break
                        booking_status['current_status'] = f'等待中... {CONFIG["RETRY_INTERVAL"]-i}秒后重试'
                        if stop_event.wait(1):  # 等待1秒或收到停止信号
                            break
                
            except Exception as e:
                booking_status['current_status'] = f'执行错误: {str(e)}'
                booking_status['last_error'] = str(e)
                # 可中断的延迟
                if stop_event.wait(CONFIG['RETRY_INTERVAL']):
                    break
        
        # 设置最终状态
        if stop_event.is_set():
            booking_status['current_status'] = '⛔ 用户手动停止'
        elif len(successful_bookings) >= max_bookings:
            booking_status['current_status'] = f'✅ 抢票完成！成功预约{len(successful_bookings)}个时间段'
        else:
            booking_status['current_status'] = f'⏰ 达到最大重试次数，当前预约{len(successful_bookings)}个时间段'
        
        booking_status['running'] = False
        
    except Exception as e:
        booking_status['current_status'] = f'❌ 程序错误: {str(e)}'
        booking_status['running'] = False

def save_config_to_file():
    """保存配置到文件"""
    try:
        # 获取项目名称（通过代码查找）
        sport_name = "未知项目"
        for name, code in SPORT_CODES.items():
            if code == CONFIG['XMDM']:
                sport_name = name
                break
        
        # 获取校园网账户信息
        campus_account = get_campus_account()
        
        config_content = f'''# 配置文件
from datetime import datetime, timedelta

current_date = datetime.now()
# 计算目标日期（当前日期 + 1 天）
target_date = current_date + timedelta(days=1)
# 格式化目标日期为字符串
target_date = target_date.strftime('%Y-%m-%d')

# 基础配置
CONFIG = {{
    # 查询参数
    "XQ": "{CONFIG['XQ']}",        # 校区：1=粤海, 2=丽湖
    "YYLX": "1.0",    # 预约类型
    "XMDM": "{CONFIG['XMDM']}",    # 项目代码：001=羽毛球  003=排球 004=网球 005=篮球 009=游泳 013=乒乓球 016=桌球
    
    # 运行参数
    "MAX_RETRY_TIMES": {CONFIG['MAX_RETRY_TIMES']},    # 最大重试次数
    "RETRY_INTERVAL": {CONFIG['RETRY_INTERVAL']},       # 重试间隔（秒）
    "REQUEST_TIMEOUT": 10,     # 请求超时时间（秒）
    # 预约日期
    "TARGET_DATE": "{CONFIG['TARGET_DATE']}",

    # 优先预约的时段关键词（按优先级排序）
    "PREFERRED_TIMES": {CONFIG['PREFERRED_TIMES']},
    
    # 用户信息配置
    "USER_INFO": {{
        "YYRGH": "{CONFIG['USER_INFO']['YYRGH']}",  # 学号/工号
        "YYRXM": "{CONFIG['USER_INFO']['YYRXM']}"   # 姓名
    }}
}}

# 项目代码映射
SPORT_CODES = {{
    "羽毛球": "001",
    "排球": "003",
    "网球": "004",
    "篮球": "005",
    "游泳": "009",
    "乒乓球": "013",
    "桌球": "016"
}}

# 校区代码映射
CAMPUS_CODES = {{
    "粤海": "1",
    "丽湖": "2"
}}

# 可选时间段（每小时一个时段）
TIME_SLOTS = [
    "08:00-09:00", "09:00-10:00", "10:00-11:00", "11:00-12:00",
    "12:00-13:00", "13:00-14:00", "14:00-15:00", "15:00-16:00",
    "16:00-17:00", "17:00-18:00", "18:00-19:00", "19:00-20:00",
    "20:00-21:00", "21:00-22:00"
]

# 校园网账户
CAMPUS_ACCOUNT = {{
    "username": "{campus_account['username']}",  # 学号或工号
    "password": "{campus_account['password']}"
}}

# 导出配置供其他模块使用
def get_campus_account():
    """获取校园网账户信息"""
    return CAMPUS_ACCOUNT.copy()

def update_campus_account(username, password):
    """更新校园网账户信息"""
    global CAMPUS_ACCOUNT
    CAMPUS_ACCOUNT["username"] = username
    CAMPUS_ACCOUNT["password"] = password
    return True
'''
        
        with open('config.py', 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        return True
    except Exception as e:
        logging.error(f"保存配置失败: {e}")
        return False

if __name__ == '__main__':
    # 启动前重置状态
    reset_booking_status()
    app.run(debug=False, host='0.0.0.0', port=5000)
