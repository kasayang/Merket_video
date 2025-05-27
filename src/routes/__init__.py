from flask import Blueprint
from src.routes.api import api_bp
from src.routes.views import views_bp

def init_app(app):
    """初始化 Flask 應用程式
    
    註冊所有藍圖和路由。
    
    參數:
        app (Flask): Flask 應用程式實例
    """
    # 註冊藍圖
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(views_bp, url_prefix='')
    
    # 註冊全局錯誤處理
    register_error_handlers(app)
    
    # 註冊全局請求攔截器
    register_request_handlers(app)
    
    # 註冊全局視圖函數和上下文處理器
    register_context_processors(app)
    
    return app

def register_error_handlers(app):
    """註冊全局錯誤處理器
    
    參數:
        app (Flask): Flask 應用程式實例
    """
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('error.html', error_code=404, error_message='找不到頁面'), 404
        
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        return render_template('error.html', error_code=500, error_message='內部伺服器錯誤'), 500

def register_request_handlers(app):
    """註冊全局請求攔截器
    
    參數:
        app (Flask): Flask 應用程式實例
    """
    @app.before_request
    def before_request():
        # 可以在這裡添加請求前處理邏輯
        pass
        
    @app.after_request
    def after_request(response):
        # 可以在這裡添加請求後處理邏輯
        return response

def register_context_processors(app):
    """註冊全局視圖函數和上下文處理器
    
    參數:
        app (Flask): Flask 應用程式實例
    """
    @app.context_processor
    def inject_globals():
        """注入全局變數到模板"""
        from datetime import datetime
        return {
            'current_year': datetime.now().year,
            'app_name': '股票數據影片自動化製作系統'
        }