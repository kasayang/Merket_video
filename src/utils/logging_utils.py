#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
股票數據影片自動化製作系統 - 日誌工具
"""

import os
import logging
import logging.handlers
from datetime import datetime

def setup_logging(log_dir='logs', log_level=logging.INFO, console_level=logging.INFO):
    """設置日誌系統
    
    參數:
        log_dir (str): 日誌目錄
        log_level (int): 文件日誌級別
        console_level (int): 控制台日誌級別
    """
    # 確保日誌目錄存在
    os.makedirs(log_dir, exist_ok=True)
    
    # 獲取根日誌器
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # 設置最低級別以捕獲所有消息
    
    # 清除現有處理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 創建格式器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 創建控制台處理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 創建文件處理器
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = os.path.join(log_dir, f'app_{today}.log')
    
    file_handler = logging.handlers.TimedRotatingFileHandler(
        log_file, when='midnight', interval=1, backupCount=30, encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    logging.info("日誌系統已設置")
    return logger