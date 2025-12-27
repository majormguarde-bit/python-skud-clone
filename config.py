import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///skud.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Настройки Firebird
    FIREBIRD_HOST = os.environ.get('FIREBIRD_HOST', 'localhost')
    FIREBIRD_PORT = int(os.environ.get('FIREBIRD_PORT', 3050))
    FIREBIRD_DATABASE = os.environ.get('FIREBIRD_DATABASE', 'database.fdb')
    FIREBIRD_USER = os.environ.get('FIREBIRD_USER', 'sysdba')
    FIREBIRD_PASSWORD = os.environ.get('FIREBIRD_PASSWORD', 'masterkey')
    
    # Настройки сканирования
    SCAN_INTERVAL = int(os.environ.get('SCAN_INTERVAL', 5))  # секунд
    CONTROLLER_TIMEOUT = int(os.environ.get('CONTROLLER_TIMEOUT', 10))  # секунд
    
    # Настройки сессии
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
