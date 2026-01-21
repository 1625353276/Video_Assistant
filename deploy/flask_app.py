#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask应用入口

提供API服务和Web界面，集成用户认证系统
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, g
from flask_cors import CORS

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))  # 使用insert而不是append，确保优先级

# 导入认证相关模块
from storage.sqlite_adapter import SQLiteAdapter
from auth.user_manager import UserManager
from auth.auth_handler import AuthHandler
from auth.auth_routes import create_auth_routes

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 应用配置
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    app.config['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'data/app.db')
    
    # 配置CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:7860", "http://127.0.0.1:7860"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # 初始化存储
    storage = SQLiteAdapter(app.config['DATABASE_URL'])
    if not storage.connect():
        logger.error("数据库连接失败")
        raise RuntimeError("数据库连接失败")
    
    if not storage.initialize_schema():
        logger.error("数据库初始化失败")
        raise RuntimeError("数据库初始化失败")
    
    # 初始化认证组件
    user_manager = UserManager(storage, app.config['JWT_SECRET_KEY'])
    auth_handler = AuthHandler(user_manager)
    
    # 注册认证路由
    auth_routes = create_auth_routes(user_manager, auth_handler)
    app.register_blueprint(auth_routes)
    
    # 存储组件到应用上下文
    app.storage = storage
    app.user_manager = user_manager
    app.auth_handler = auth_handler
    
    # 基础路由
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """健康检查"""
        return jsonify({
            'status': 'healthy',
            'message': 'Flask应用运行正常',
            'timestamp': datetime.now().isoformat()
        })
    
    @app.route('/api/test', methods=['GET'])
    def test():
        """测试路由"""
        return jsonify({
            'message': 'Flask API测试成功',
            'timestamp': datetime.now().isoformat()
        })
    
    @app.route('/api/user', methods=['GET'])
    @auth_handler.require_auth
    def get_current_user():
        """获取当前用户信息"""
        current_user = auth_handler.get_current_user()
        return jsonify({
            'success': True,
            'user': current_user
        })
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'message': '资源未找到'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"内部服务器错误: {error}")
        return jsonify({
            'success': False,
            'message': '内部服务器错误'
        }), 500
    
    # 请求前处理
    @app.before_request
    def before_request():
        """请求前处理"""
        g.start_time = datetime.utcnow()
    
    # 请求后处理
    @app.after_request
    def after_request(response):
        """请求后处理"""
        # 记录请求时间
        if hasattr(g, 'start_time'):
            duration = (datetime.utcnow() - g.start_time).total_seconds()
            logger.info(f"请求处理时间: {duration:.3f}s - {request.method} {request.path}")
        
        return response
    
    # 应用关闭时清理
    @app.teardown_appcontext
    def teardown_db(error):
        """应用上下文清理"""
        if error:
            logger.error(f"应用上下文错误: {error}")
    
    logger.info("Flask应用创建完成")
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5001, debug=True)