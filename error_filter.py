"""
错误过滤器 - 用于抑制常见的非关键错误输出
"""

import sys
import os
import warnings
import logging

def suppress_ssl_warnings():
    """抑制SSL相关警告"""
    try:
        import urllib3
        urllib3.disable_warnings()
    except:
        pass
    
    # 过滤Python警告
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", message=".*SSL.*")
    warnings.filterwarnings("ignore", message=".*certificate.*")
    warnings.filterwarnings("ignore", message=".*handshake.*")

def setup_chrome_logging():
    """设置Chrome日志过滤"""
    # 设置环境变量来抑制Chrome日志
    os.environ['CHROME_LOG_FILE'] = os.devnull
    os.environ['PYTHONWARNINGS'] = 'ignore'
    
    # 抑制Selenium日志
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

def filter_console_output():
    """过滤控制台输出中的错误信息"""
    class ErrorFilter:
        def __init__(self, original_stderr):
            self.original_stderr = original_stderr
            
        def write(self, text):
            # 过滤掉Chrome的SSL错误
            if any(pattern in text for pattern in [
                'handshake failed',
                'SSL error code',
                'net_error -101',
                'ERR_CONNECTION_RESET',
                'DevTools listening'
            ]):
                return  # 不输出这些错误
            
            # 其他错误正常输出
            self.original_stderr.write(text)
            
        def flush(self):
            self.original_stderr.flush()
    
    # 只在非调试模式下过滤
    if '--debug' not in sys.argv:
        sys.stderr = ErrorFilter(sys.stderr)

def initialize_error_suppression():
    """初始化所有错误抑制机制"""
    suppress_ssl_warnings()
    setup_chrome_logging()
    filter_console_output()
