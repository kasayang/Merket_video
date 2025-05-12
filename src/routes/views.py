from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
import os
import json
from datetime import datetime

from src.core.main_controller import MainController

# 創建藍圖
views_bp = Blueprint('views', __name__)

# 初始化主控制器
main_controller = MainController()

@views_bp.route('/')
def index():
    """首頁"""
    return render_template('index.html')

@views_bp.route('/editor')
def editor():
    """編輯器頁面"""
    # 獲取 URL 參數
    ticker = request.args.get('ticker', '')
    article_id = request.args.get('article', '')
    project_id = request.args.get('project', '')
    
    # 獲取可用模板
    templates = get_available_templates()
    
    return render_template('editor.html', 
                           ticker=ticker, 
                           article_id=article_id, 
                           project_id=project_id, 
                           templates=templates)

@views_bp.route('/preview/<path:filename>')
def preview(filename):
    """預覽生成的視頻"""
    return render_template('preview.html', filename=filename)

@views_bp.route('/output/<path:filename>')
def serve_output(filename):
    """提供輸出視頻文件下載"""
    return send_from_directory('output', filename)

@views_bp.route('/cache/<path:filename>')
def serve_cache(filename):
    """提供暫存文件"""
    # 確定文件類型和目錄路徑
    file_parts = filename.split('/')
    if len(file_parts) > 1:
        cache_type = file_parts[0]
        file_name = '/'.join(file_parts[1:])
        cache_dir = os.path.join('cache', cache_type)
    else:
        cache_dir = 'cache'
        file_name = filename
    
    return send_from_directory(cache_dir, file_name)

@views_bp.route('/recent')
def recent_projects():
    """最近的項目頁面"""
    projects = main_controller.get_recent_projects(20)
    return render_template('recent.html', projects=projects)

@views_bp.route('/templates')
def templates():
    """模板頁面"""
    templates = get_available_templates()
    return render_template('templates.html', templates=templates)

@views_bp.route('/help')
def help_page():
    """幫助頁面"""
    return render_template('help.html')

@views_bp.route('/about')
def about():
    """關於頁面"""
    return render_template('about.html')

def get_available_templates():
    """獲取可用的模板
    
    返回:
        dict: 模板資訊字典
    """
    templates_dir = os.path.join(os.getcwd(), 'templates')
    
    result = {
        'layouts': [],
        'digital_humans': []
    }
    
    # 獲取佈局模板
    layouts_dir = os.path.join(templates_dir, 'layouts')
    if os.path.exists(layouts_dir):
        for file in os.listdir(layouts_dir):
            if file.endswith('.json'):
                template_path = os.path.join(layouts_dir, file)
                try:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                        result['layouts'].append({
                            'id': os.path.splitext(file)[0],
                            'name': template_data.get('name', os.path.splitext(file)[0]),
                            'description': template_data.get('description', ''),
                            'preview': template_data.get('preview', '')
                        })
                except:
                    # 如果讀取失敗，只添加基本資訊
                    result['layouts'].append({
                        'id': os.path.splitext(file)[0],
                        'name': os.path.splitext(file)[0],
                        'description': '',
                        'preview': ''
                    })
    
    # 獲取數位人模板
    dh_dir = os.path.join(templates_dir, 'digital_humans')
    if os.path.exists(dh_dir):
        for file in os.listdir(dh_dir):
            if file.endswith(('.mp4', '.avi', '.mov')):
                # 檢查是否有對應的元數據文件
                meta_file = os.path.join(dh_dir, os.path.splitext(file)[0] + '.json')
                if os.path.exists(meta_file):
                    try:
                        with open(meta_file, 'r', encoding='utf-8') as f:
                            meta_data = json.load(f)
                            result['digital_humans'].append({
                                'id': os.path.splitext(file)[0],
                                'name': meta_data.get('name', os.path.splitext(file)[0]),
                                'description': meta_data.get('description', ''),
                                'preview': meta_data.get('preview', ''),
                                'gender': meta_data.get('gender', 'neutral'),
                                'language': meta_data.get('language', 'zh-TW')
                            })
                    except:
                        # 如果讀取失敗，只添加基本資訊
                        result['digital_humans'].append({
                            'id': os.path.splitext(file)[0],
                            'name': os.path.splitext(file)[0],
                            'description': '',
                            'preview': '',
                            'gender': 'neutral',
                            'language': 'zh-TW'
                        })
                else:
                    # 沒有元數據文件時
                    result['digital_humans'].append({
                        'id': os.path.splitext(file)[0],
                        'name': os.path.splitext(file)[0],
                        'description': '',
                        'preview': '',
                        'gender': 'neutral',
                        'language': 'zh-TW'
                    })
    
    return result