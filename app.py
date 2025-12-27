import os
from app import create_app, db
from app.models import User, Controller, Reader, Converter, AccessKey, AccessLevel, Event, EventType, Device
from flask_login import LoginManager

# Создание приложения
app = create_app()

# Настройка LoginManager
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Controller': Controller,
        'Reader': Reader,
        'Converter': Converter,
        'AccessKey': AccessKey,
        'AccessLevel': AccessLevel,
        'Event': Event,
        'EventType': EventType,
        'Device': Device
    }

if __name__ == '__main__':
    # Создание директории для логов
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Создание таблиц БД
    with app.app_context():
        db.create_all()
        
        # Создание администратора по умолчанию
        from app.models import User
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
            print("Создан администратор: admin/admin123")
        
        # Создание базовых типов событий
        from app.models import EventType
        event_types = [
            ('ACCESS_GRANTED', 'Доступ разрешен', '#28a745'),
            ('ACCESS_DENIED', 'Доступ запрещен', '#dc3545'),
            ('DOOR_OPEN', 'Дверь открыта', '#17a2b8'),
            ('DOOR_CLOSE', 'Дверь закрыта', '#6c757d'),
            ('ALARM', 'Тревога', '#ffc107'),
            ('CONTROLLER_ONLINE', 'Контроллер онлайн', '#28a745'),
            ('CONTROLLER_OFFLINE', 'Контроллер оффлайн', '#dc3545')
        ]
        
        for code, name, color in event_types:
            event_type = EventType.query.filter_by(code=code).first()
            if not event_type:
                event_type = EventType(code=code, name=name, color=color)
                db.session.add(event_type)
        
        db.session.commit()
        print("Базовые типы событий созданы")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
