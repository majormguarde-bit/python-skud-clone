from flask import Blueprint, jsonify, request
from flask_login import login_required
from app.models import Controller, Reader, Converter, Event, Device, AccessKey, EventType
from app import db
from datetime import datetime
import logging
import os
import platform

api = Blueprint('api', __name__)

@api.route('/files/list', methods=['GET'])
@login_required
def list_files():
    """Получить список файлов и директорий"""
    path = request.args.get('path', '')
    
    # Если путь не указан, показываем диски (для Windows) или корень (для *nix)
    if not path:
        if platform.system() == 'Windows':
            import string
            drives = []
            bitmask = os.popen('fsutil fsinfo drives').read()
            for drive in string.ascii_uppercase:
                if f'{drive}:' in bitmask:
                    drives.append({
                        'name': f'{drive}:\\',
                        'type': 'dir',
                        'path': f'{drive}:\\'
                    })
            # Fallback if fsutil fails or for simpler approach
            if not drives:
                drives = [{'name': f'{d}:\\', 'type': 'dir', 'path': f'{d}:\\'} for d in string.ascii_uppercase if os.path.exists(f'{d}:')]
            return jsonify(drives)
        else:
            path = '/'

    try:
        # Проверка безопасности: не позволяем выходить за пределы допустимых директорий, если нужно
        # В данном случае, так как это админский инструмент, разрешаем просмотр всей ФС
        
        items = []
        # Добавляем ссылку на уровень вверх
        parent = os.path.dirname(path)
        if parent and parent != path:
             items.append({
                'name': '..',
                'type': 'dir',
                'path': parent
            })
            
        with os.scandir(path) as it:
            for entry in it:
                try:
                    is_dir = entry.is_dir()
                    items.append({
                        'name': entry.name,
                        'type': 'dir' if is_dir else 'file',
                        'path': entry.path
                    })
                except PermissionError:
                    continue
                    
        # Сортировка: сначала директории, потом файлы
        items.sort(key=lambda x: (x['type'] != 'dir', x['name'].lower()))
        
        return jsonify(items)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@api.route('/controllers', methods=['GET'])
@login_required
def get_controllers():
    """Получить список контроллеров"""
    controllers = Controller.query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'serial_number': c.serial_number,
        'ip_address': c.ip_address,
        'port': c.port,
        'status': c.status,
        'last_seen': c.last_seen.isoformat() if c.last_seen else None,
        'readers_count': len(c.readers)
    } for c in controllers])

@api.route('/controllers/<int:id>', methods=['GET'])
@login_required
def get_controller(id):
    """Получить информацию о контроллере"""
    controller = Controller.query.get_or_404(id)
    return jsonify({
        'id': controller.id,
        'name': controller.name,
        'serial_number': controller.serial_number,
        'ip_address': controller.ip_address,
        'port': controller.port,
        'status': controller.status,
        'last_seen': controller.last_seen.isoformat() if controller.last_seen else None,
        'firmware_version': controller.firmware_version,
        'readers': [{
            'id': r.id,
            'name': r.name,
            'reader_number': r.reader_number,
            'reader_type': r.reader_type,
            'status': r.status
        } for r in controller.readers]
    })

@api.route('/controllers/<int:id>/status', methods=['POST'])
@login_required
def update_controller_status(id):
    """Обновить статус контроллера"""
    controller = Controller.query.get_or_404(id)
    data = request.get_json()
    
    if 'status' in data:
        controller.status = data['status']
        controller.last_seen = datetime.utcnow()
        
        if 'error' in data:
            logging.error(f"Controller {controller.name} error: {data['error']}")
    
    db.session.commit()
    return jsonify({'status': 'success'})

@api.route('/events', methods=['GET'])
@login_required
def get_events():
    """Получить события"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    events = Event.query.order_by(Event.event_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'events': [{
            'id': e.id,
            'event_time': e.event_time.isoformat(),
            'event_type': e.event_type.name,
            'controller': e.controller.name if e.controller else None,
            'reader': e.reader.name if e.reader else None,
            'access_key': e.access_key.key_number if e.access_key else e.card_number,
            'access_granted': e.access_granted,
            'description': e.description
        } for e in events.items],
        'total': events.total,
        'pages': events.pages,
        'current_page': events.page
    })

@api.route('/events', methods=['POST'])
@login_required
def create_event():
    """Создать новое событие"""
    data = request.get_json()
    
    event = Event(
        event_type_id=data.get('event_type_id'),
        controller_id=data.get('controller_id'),
        reader_id=data.get('reader_id'),
        access_key_id=data.get('access_key_id'),
        card_number=data.get('card_number'),
        direction=data.get('direction'),
        access_granted=data.get('access_granted'),
        description=data.get('description')
    )
    
    db.session.add(event)
    db.session.commit()
    
    return jsonify({'id': event.id, 'status': 'success'})

@api.route('/keys', methods=['GET'])
@login_required
def get_access_keys():
    """Получить список ключей доступа"""
    keys = AccessKey.query.all()
    return jsonify([{
        'id': k.id,
        'key_number': k.key_number,
        'key_type': k.key_type,
        'holder_name': k.holder_name,
        'is_active': k.is_active,
        'issue_date': k.issue_date.isoformat() if k.issue_date else None,
        'expiry_date': k.expiry_date.isoformat() if k.expiry_date else None
    } for k in keys])

@api.route('/keys/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_access_key(id):
    """Включить/выключить ключ доступа"""
    key = AccessKey.query.get_or_404(id)
    key.is_active = not key.is_active
    db.session.commit()
    
    return jsonify({
        'id': key.id,
        'is_active': key.is_active,
        'status': 'success'
    })

@api.route('/devices/scan', methods=['POST'])
@login_required
def scan_devices():
    """Запустить сканирование устройств"""
    # Здесь будет логика сканирования сети
    # Возвращаем статус запуска
    return jsonify({'status': 'scan_started', 'message': 'Сканирование устройств запущено'})

@api.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@api.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500
