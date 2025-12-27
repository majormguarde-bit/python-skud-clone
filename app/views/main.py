from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func
from app.models import Controller, Reader, Converter, Event, Device, AccessKey, Settings, Personnel
from app import db
from app.utils.firebird import fb_client
from app.services.sync_service import sync_service
from datetime import datetime, timedelta
import json
import os
from dotenv import set_key, load_dotenv

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    """Главная страница с дашбордом"""
    # Статистика
    now = datetime.utcnow()
    timeout = timedelta(minutes=3)
    
    total_converters = Converter.query.count()
    online_converters = Converter.query.filter(Converter.last_seen >= now - timeout).count()
    total_controllers = Controller.query.count()
    online_controllers = Controller.query.filter(Controller.last_session >= now - timeout).count()
    total_readers = Reader.query.count()
    online_readers = Reader.query.filter_by(status='online').count()
    total_keys = AccessKey.query.count()
    active_keys = AccessKey.query.filter_by(is_active=True).count()
    
    # Персонал (уникальные владельцы ключей)
    # Используем таблицу Personnel если есть данные, иначе фоллбек на владельцев ключей
    total_personnel = Personnel.query.count()
    if total_personnel == 0:
        total_personnel = db.session.query(func.count(func.distinct(AccessKey.holder_name))).filter(AccessKey.holder_name.isnot(None)).scalar()
    
    # Последние события
    recent_events = Event.query.order_by(Event.event_time.desc()).limit(10).all()
    
    # Статус устройств
    converters = Converter.query.all()
    
    return render_template('main/index.html',
                         total_converters=total_converters,
                         online_converters=online_converters,
                         total_controllers=total_controllers,
                         online_controllers=online_controllers,
                         total_readers=total_readers,
                         online_readers=online_readers,
                         total_keys=total_keys,
                         active_keys=active_keys,
                         total_personnel=total_personnel,
                         recent_events=recent_events,
                         converters=converters,
                         online_threshold=now - timeout)

@main.route('/equipment')
@login_required
def equipment():
    """Страница управления оборудованием"""
    converters = Converter.query.all()
    controllers = Controller.query.all()
    return render_template('main/equipment.html', converters=converters, controllers=controllers)

import threading

@main.route('/equipment/sync', methods=['POST'])
@login_required
def sync_equipment():
    """Синхронизация оборудования с Firebird"""
    # Запускаем в отдельном потоке
    app = current_app._get_current_object()
    
    def run_sync(app_instance):
        with app_instance.app_context():
            try:
                result = sync_service.sync_equipment()
                # Можно добавить логирование или сохранение результата в БД уведомлений
                print(f"Sync result: {result}")
            except Exception as e:
                print(f"Async sync error: {e}")

    thread = threading.Thread(target=run_sync, args=(app,))
    thread.start()
    
    flash('Синхронизация запущена в фоновом режиме. Обновите страницу через минуту.', 'info')
    
    # Redirect back to the referrer or default to index
    return redirect(request.referrer or url_for('main.index'))

@main.route('/equipment/converter/delete', methods=['POST'])
@login_required
def delete_converter():
    """Удаление конвертера и связанных контроллеров"""
    converter_id = request.form.get('converter_id')
    if not converter_id:
        flash('Не указан ID конвертера', 'danger')
        return redirect(url_for('main.equipment'))
        
    try:
        converter = Converter.query.get(converter_id)
        if converter:
            # Контроллеры удалятся каскадно или вручную
            controllers = Controller.query.filter_by(converter_id=converter.id).all()
            for c in controllers:
                db.session.delete(c)
            db.session.delete(converter)
            db.session.commit()
            flash(f'Конвертер {converter.name} и связанные контроллеры удалены', 'success')
        else:
            flash('Конвертер не найден', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении конвертера: {e}', 'danger')
        
    return redirect(url_for('main.equipment'))

@main.route('/equipment/controller/delete', methods=['POST'])
@login_required
def delete_single_controller():
    """Удаление одного контроллера"""
    controller_id = request.form.get('controller_id')
    if not controller_id:
        flash('Не указан ID контроллера', 'danger')
        return redirect(url_for('main.equipment'))
        
    try:
        controller = Controller.query.get(controller_id)
        if controller:
            db.session.delete(controller)
            db.session.commit()
            flash(f'Контроллер {controller.name} удален', 'success')
        else:
            flash('Контроллер не найден', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении контроллера: {e}', 'danger')
        
    return redirect(url_for('main.equipment'))

@main.route('/controllers/<int:id>')
@login_required
def controller_detail(id):
    """Детальная информация о контроллере"""
    controller = Controller.query.get_or_404(id)
    return render_template('main/controller_detail.html', controller=controller)

@main.route('/events')
@login_required
def events():
    """Страница событий"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    events = Event.query.order_by(Event.event_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    
    return render_template('main/events.html', events=events)

@main.route('/keys')
@login_required
def access_keys():
    """Страница управления ключами доступа"""
    keys = AccessKey.query.all()
    return render_template('main/keys.html', keys=keys)

@main.route('/devices')
@login_required
def devices():
    """Страница устройств"""
    devices = Device.query.all()
    return render_template('main/devices.html', devices=devices)

@main.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Страница настроек"""
    
    if request.method == 'POST':
        # Сохранение настроек
        settings_map = {
            'FIREBIRD_HOST': request.form.get('firebird_host'),
            'FIREBIRD_PORT': request.form.get('firebird_port'),
            'FIREBIRD_DATABASE': request.form.get('firebird_database'),
            'FIREBIRD_USER': request.form.get('firebird_user'),
            'FIREBIRD_PASSWORD': request.form.get('firebird_password'),
            'SCAN_INTERVAL': request.form.get('scan_interval')
        }
        
        try:
            # Обновляем или создаем настройки в БД
            for key, value in settings_map.items():
                if value is not None:
                    setting = Settings.query.filter_by(key=key).first()
                    if setting:
                        setting.value = value
                    else:
                        setting = Settings(key=key, value=value)
                        db.session.add(setting)
            
            db.session.commit()
            
            # Обновляем переменные окружения (для совместимости, если нужно)
            # Но основной источник теперь БД
            for key, value in settings_map.items():
                if value:
                    os.environ[key] = value

            # Переподключение к базе данных Firebird
            firebird_database = settings_map.get('FIREBIRD_DATABASE')
            if fb_client.reconnect():
                flash(f'Настройки сохранены, подключение к БД Firebird успешно установлено (База: {firebird_database}).', 'success')
            else:
                flash(f'Настройки сохранены, но не удалось подключиться к БД Firebird (База: {firebird_database}). Проверьте параметры.', 'warning')
            
            return redirect(url_for('main.settings'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при сохранении настроек: {e}', 'danger')
    
    # Загружаем текущие настройки для отображения
    # Сначала пробуем загрузить из БД, если нет - берем дефолтные
    def get_conf(key, default):
        s = Settings.query.filter_by(key=key).first()
        return s.value if s else os.environ.get(key, default)

    config = {
        'FIREBIRD_HOST': get_conf('FIREBIRD_HOST', 'localhost'),
        'FIREBIRD_PORT': get_conf('FIREBIRD_PORT', '3050'),
        'FIREBIRD_DATABASE': get_conf('FIREBIRD_DATABASE', 'database.fdb'),
        'FIREBIRD_USER': get_conf('FIREBIRD_USER', 'sysdba'),
        'FIREBIRD_PASSWORD': get_conf('FIREBIRD_PASSWORD', 'masterkey'),
        'SCAN_INTERVAL': get_conf('SCAN_INTERVAL', '5')
    }
    
    return render_template('main/settings.html', config=config)

@main.route('/api/dashboard/stats')
@login_required
def dashboard_stats():
    """API для получения статистики дашборда"""
    # Статистика за последние 24 часа
    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)
    
    events_today = Event.query.filter(Event.event_time >= day_ago).count()
    
    # График событий за последние 7 дней
    events_7_days = []
    for i in range(7):
        date = now - timedelta(days=i)
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        count = Event.query.filter(
            Event.event_time >= day_start,
            Event.event_time < day_end
        ).count()
        
        events_7_days.append({
            'date': day_start.strftime('%Y-%m-%d'),
            'count': count
        })
    
    return jsonify({
        'events_today': events_today,
        'events_7_days': list(reversed(events_7_days))
    })

@main.route('/api/equipment/status')
@login_required
def equipment_status():
    """API для получения текущих статусов оборудования"""
    converters = Converter.query.all()
    controllers = Controller.query.all()
    
    converters_data = {}
    for c in converters:
        converters_data[c.id] = {
            'id': c.id,
            'last_seen_ts': c.last_seen.timestamp() if c.last_seen else 0,
            'last_seen_str': c.last_seen.strftime('%Y.%m.%d - %H:%M:%S') if c.last_seen else 'Никогда',
            'extra_data': c.extra_data or {}
        }
        
    controllers_data = {}
    for c in controllers:
        controllers_data[c.id] = {
            'id': c.id,
            'last_session_ts': c.last_session.timestamp() if c.last_session else 0,
            'last_session_str': c.last_session.strftime('%d.%m.%Y %H:%M') if c.last_session else 'Никогда',
            'extra_data': c.extra_data or {}
        }
        
    return jsonify({
        'converters': converters_data,
        'controllers': controllers_data
    })
