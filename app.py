#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
股票數據影片自動化製作系統 - Flask版入口
"""

from flask import Flask
import sys
import os
import logging

# 添加當前目錄到Python路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.logging_utils import setup_logging
from src.utils.config_manager import ConfigManager
from src.routes import init_app

# 設置日誌
setup_logging(log_dir='logs')
logger = logging.getLogger(__name__)

# 載入配置
config_manager = ConfigManager('config.yaml')
server_config = config_manager.get_server_settings()

# 創建Flask應用
app = Flask(__name__, 
            static_folder='src/static',
            template_folder='src/templates')

# 註冊藍圖
init_app(app)

# 配置密鑰
app.config['SECRET_KEY'] = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB上傳限制

# 主函數
if __name__ == '__main__':
    host = server_config.get('host', '0.0.0.0')
    port = server_config.get('port', 5555)
    debug = server_config.get('debug', True)
    
    logger.info(f"啟動股票數據影片自動化製作系統 - Flask版 (http://{host}:{port})")
    app.run(debug=debug, host=host, port=port)