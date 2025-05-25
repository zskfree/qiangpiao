from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import json
import os
import threading
import time
from datetime import datetime, timedelta
import logging
from qiangpiao import get_available_slots, book_slot, check_login_status, extract_cookies_from_text, test_cookie_validity, update_cookie_in_file
from config import CONFIG, SPORT_CODES, CAMPUS_CODES

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
    return render_template('index.html', config=CONFIG, sport_codes=SPORT_CODES, campus_codes=CAMPUS_CODES)

@app.route('/config')
def config_page():
    """配置页面"""
    return render_template('config.html', config=CONFIG, sport_codes=SPORT_CODES, campus_codes=CAMPUS_CODES)

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
        cookie_text = request.json.get('cookie', '')
        if not cookie_text:
            return jsonify({'success': False, 'message': 'Cookie不能为空'})
        
        cookies = extract_cookies_from_text(cookie_text)
        is_valid, message = test_cookie_validity(cookies)
        
        return jsonify({
            'success': is_valid,
            'message': message,
            'cookie_count': len(cookies)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'测试失败: {str(e)}'})

@app.route('/api/cookie/update', methods=['POST'])
def update_cookie():
    """更新Cookie"""
    try:
        cookie_text = request.json.get('cookie', '')
        if not cookie_text:
            return jsonify({'success': False, 'message': 'Cookie不能为空'})
        
        # 先测试Cookie有效性
        cookies = extract_cookies_from_text(cookie_text)
        is_valid, message = test_cookie_validity(cookies)
        
        if not is_valid:
            return jsonify({'success': False, 'message': f'Cookie无效: {message}'})
        
        # 更新到文件
        success = update_cookie_in_file(cookie_text)
        
        if success:
            return jsonify({'success': True, 'message': 'Cookie更新成功！'})
        else:
            return jsonify({'success': False, 'message': 'Cookie更新失败'})
    except Exception as e:
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
        # 读取qiangpiao.py文件中的Cookie
        with open('qiangpiao.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取当前Cookie
        start_marker = 'raw_cookie = """'
        end_marker = '"""'
        
        start_idx = content.find(start_marker)
        if start_idx == -1:
            return jsonify({
                'success': False, 
                'message': '未找到Cookie定义'
            })
        
        start_idx += len(start_marker)
        end_idx = content.find(end_marker, start_idx)
        
        if end_idx == -1:
            return jsonify({
                'success': False, 
                'message': 'Cookie格式错误'
            })
        
        current_cookie_text = content[start_idx:end_idx].strip()
        
        # 解析Cookie字段
        cookie_fields = extract_cookies_from_text(current_cookie_text)
        
        # 测试Cookie有效性
        is_valid, message = test_cookie_validity(cookie_fields)
        
        # 获取文件修改时间作为最后更新时间
        import os
        last_update = None
        try:
            stat = os.stat('qiangpiao.py')
            last_update = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
        
        return jsonify({
            'success': True,
            'valid': is_valid,
            'message': message,
            'cookie_count': len(cookie_fields),
            'cookie_text': current_cookie_text,
            'cookie_fields': cookie_fields,
            'last_update': last_update
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取Cookie失败: {str(e)}'
        })

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
        config_content = f'''# 配置文件
from datetime import datetime, timedelta

# 基础配置
CONFIG = {{
    # 查询参数
    "XQ": "{CONFIG['XQ']}",        # 校区：1=粤海, 2=丽湖
    "YYLX": "1.0",    # 预约类型
    "XMDM": "001",    # 项目代码：001=羽毛球
    
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
}}

# 校区代码映射
CAMPUS_CODES = {{
    "粤海": "1",
    "丽湖": "2"
}}

# Cookie配置 (占位符，实际Cookie在qiangpiao.py中定义)
COOKIE = ""
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
