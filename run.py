#!/usr/bin/env python3
"""
Запуск приложения СКУД Сервер
"""

import os
import sys
import threading
import time
import logging
from datetime import datetime

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Controller, Reader, Converter, Device
from flask_login import LoginManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Создание приложения
app = create_app()

# Настройка LoginManager
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def scan_devices():
    """Поток сканирования устройств"""
    while True:
        try:
            with app.app_context():
                logger.info("Сканирование устройств...")
                controllers = Controller.query.all()
                
                for controller in controllers:
                    # Здесь будет реальная проверка статуса контроллера
                    # Пока имитация
                    if controller.status == 'offline':
                        # Попытка подключения
                        logger.info(f"Проверка контроллера {controller.name}...")
                        # Если успешно:
                        # controller.status = 'online'
                        # controller.last_seen = datetime.utcnow()
                        # db.session.commit()
                
            time.sleep(10)  # Сканирование каждые 10 секунд
            
        except Exception as e:
            logger.error(f"Ошибка при сканировании устройств: {e}")
            time.sleep(30)

def init_database():
    """Инициализация базы данных"""
    with app.app_context():
        try:
            # Создание таблиц
            db.create_all()
            logger.info("Таблицы базы данных созданы")
            
            # Создание администратора
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    full_name='Администратор системы',
                    is_admin=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                logger.info("Создан администратор: admin/admin123")
            
            # Создание тестовых данных
            if Controller.query.count() == 0:
                # Тестовый контроллер
                controller = Controller(
                    name='Контроллер 1',
                    serial_number='CTRL001',
                    ip_address='192.168.1.100',
                    port=502,
                    status='offline'
                )
                db.session.add(controller)
                
                # Тестовый считыватель
                reader = Reader(
                    name='Считыватель 1',
                    reader_number=1,
                    reader_type='rfid',
                    controller=controller
                )
                db.session.add(reader)
                
                # Тестовое устройство
                device = Device(
                    name='Z-397 Конвертер',
                    device_type='converter',
                    serial_number='Z397001',
                    ip_address='192.168.1.101',
                    port=10001,
                    model='Z-397 Guard',
                    status='offline'
                )
                db.session.add(device)
                
                db.session.commit()
                logger.info("Созданы тестовые данные")
                
        except Exception as e:
            logger.error(f"Ошибка при инициализации базы данных: {e}")

if __name__ == '__main__':
    # Создание директории для логов
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Инициализация базы данных
    init_database()
    
    # Запуск потока сканирования
    scan_thread = threading.Thread(target=scan_devices, daemon=True)
    scan_thread.start()
    logger.info("Поток сканирования устройств запущен")
    
    # Запуск веб-сервера
    logger.info("Запуск СКУД Сервер на http://localhost:5000")
    logger.info("Логин: admin, Пароль: admin123")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
