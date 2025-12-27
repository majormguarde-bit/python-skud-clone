from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bootstrap import Bootstrap5
import threading
import time
import logging
import os
from datetime import datetime

# Инициализация расширений
db = SQLAlchemy()
login_manager = LoginManager()
bootstrap = Bootstrap5()

def create_app(config_name='default'):
    # Определяем путь к папке templates
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    template_dir = os.path.join(base_dir, 'templates')
    
    app = Flask(__name__, template_folder=template_dir)
    
    # Конфигурация
    app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///skud.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Инициализация расширений
    db.init_app(app)
    login_manager.init_app(app)
    bootstrap.init_app(app)
    
    # Настройка LoginManager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
    
    # Регистрация blueprints
    from app.views.main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from app.views.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    
    from app.views.api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler()
        ]
    )
    
    # Создание таблиц БД
    with app.app_context():
        db.create_all()
    
    return app
