
import logging
import os
import json
from datetime import datetime, date, time
from app import db
from app.models import Controller, Converter, Department, Personnel, AccessKey
from app.utils.firebird import fb_client

logger = logging.getLogger(__name__)

class SyncService:
    def _json_serializable(self, data):
        """Helper to make dict serializable for JSON"""
        if isinstance(data, dict):
            return {k: self._json_serializable(v) for k, v in data.items()}
        elif isinstance(data, (datetime, date, time)):
            return data.isoformat()
        return data

    def sync_equipment(self):
        """
        Синхронизация оборудования из базы Firebird
        """
        if not fb_client.connect():
            return {"success": False, "message": "Не удалось подключиться к базе данных Firebird"}
        
        conn = fb_client.get_connection()
        cursor = conn.cursor()
        
        stats = {"converters": 0, "controllers": 0, "departments": 0, "personnel": 0, "keys": 0, "updated": 0}
        
        try:
            # 1. Синхронизация конвертеров
            # Ищем таблицу конвертеров (обычно U_CONVERTERS или CONVERTERS)
            conv_table = self._find_table(cursor, ['CONV', 'U_CONVERTERS', 'CONVERTERS', 'CONVERTER'])
            
            # Словарь для маппинга ID конвертера из FB в ID локальной БД
            # Firebird ID -> Local ID
            conv_id_map = {}
            
            if conv_table:
                logger.info(f"Found converters table: {conv_table}")
                columns = self._get_columns(cursor, conv_table)
                cursor.execute(f"SELECT * FROM {conv_table}")
                rows = cursor.fetchall()
                
                for row in rows:
                    data = dict(zip(columns, row))
                    
                    # Определяем поля
                    # SN может быть SN, SERIAL, SERIAL_NUMBER, CVTNUM
                    sn = str(data.get('CVTNUM') or data.get('SN') or data.get('SERIAL') or data.get('SERIAL_NUMBER') or '')
                    if not sn: continue
                    
                    name = data.get('NAME', f'Converter {sn}')
                    
                    # IP and Port parsing from HOST field (e.g. "192.168.1.10:10001")
                    ip = '0.0.0.0'
                    port = 10001
                    
                    host = data.get('HOST') or data.get('IP') or data.get('IP_ADDRESS')
                    if host and ':' in str(host):
                        try:
                            parts = str(host).split(':')
                            ip = parts[0]
                            port = int(parts[1])
                        except:
                            pass
                    elif host:
                        ip = str(host)
                        port = int(data.get('PORT') or 10001)

                    fb_id = data.get('CONVID') or data.get('ID')
                    
                    # Ищем существующий или создаем новый
                    converter = Converter.query.filter_by(serial_number=sn).first()
                    if not converter:
                        converter = Converter(serial_number=sn)
                        db.session.add(converter)
                        stats['converters'] += 1
                    else:
                        stats['updated'] += 1
                        
                    converter.name = name
                    converter.ip_address = ip
                    converter.port = port
                    converter.status = 'online' # Предполагаем, что если он в базе, он существует
                    converter.extra_data = self._json_serializable(data)
                    
                    db.session.flush() # Чтобы получить ID
                    if fb_id:
                        conv_id_map[fb_id] = converter.id
            
            # 2. Синхронизация контроллеров
            cont_table = self._find_table(cursor, ['CONTR', 'U_CONTROLLERS', 'CONTROLLERS', 'CONTROLLER'])
            
            if cont_table:
                logger.info(f"Found controllers table: {cont_table}")
                columns = self._get_columns(cursor, cont_table)
                cursor.execute(f"SELECT * FROM {cont_table}")
                rows = cursor.fetchall()
                
                # Log columns for debugging
                # if rows:
                #     logger.info(f"Controllers table columns: {columns}")
                #     logger.info(f"First row data keys: {dict(zip(columns, rows[0])).keys()}")
                
                for row in rows:
                    data = dict(zip(columns, row))
                    
                    # SN: SERIALNUM, SN, SERIAL
                    sn = str(data.get('SERIALNUM') or data.get('SN') or data.get('SERIAL') or data.get('SERIAL_NUMBER') or '')
                    if not sn: continue
                    
                    name = data.get('NAME', f'Controller {sn}')
                    fb_conv_id = data.get('CONVID') or data.get('CONVERTER_ID') or data.get('CONVERTER')
                    
                    # Ищем существующий
                    controller = Controller.query.filter_by(serial_number=sn).first()
                    if not controller:
                        controller = Controller(serial_number=sn)
                        db.session.add(controller)
                        stats['controllers'] += 1
                    else:
                        stats['updated'] += 1
                        
                    controller.name = name
                    
                    # Адрес
                    addr = data.get('ADDR') or data.get('ADDRESS') or data.get('NETADDR') or data.get('NET_ADDR')
                    if addr:
                         try:
                             controller.addr = int(addr)
                         except:
                            pass
                    
                    controller.extra_data = self._json_serializable(data)
                    
                    # Привязка к конвертеру
                    if fb_conv_id and fb_conv_id in conv_id_map:
                        controller.converter_id = conv_id_map[fb_conv_id]

                    # Попытка найти время последней активности
                    last_session = data.get('LASTSESSION') or data.get('LAST_SESSION') or data.get('LASTTIME') or data.get('LAST_TIME') or data.get('LASTSEEN') or data.get('LAST_SEEN') or data.get('DT') or data.get('ACTIVITY_TIME') or data.get('LAST_ACCESS')
                    if last_session:
                        try:
                            # Firebird возвращает datetime, но на всякий случай проверим
                            controller.last_session = last_session
                        except:
                            pass
            
            
            # 3. Синхронизация отделов
            dep_table = self._find_table(cursor, ['DEPARTMENTS', 'GROUPS', 'U_DEPARTMENTS', 'U_GROUPS', 'ORG_UNITS'])
            dep_id_map = {} # FB ID -> Local ID
            
            if dep_table:
                logger.info(f"Found departments table: {dep_table}")
                columns = self._get_columns(cursor, dep_table)
                cursor.execute(f"SELECT * FROM {dep_table}")
                rows = cursor.fetchall()
                
                # Загружаем существующие отделы
                existing_depts = {d.external_id: d for d in Department.query.filter(Department.external_id.isnot(None)).all()}
                
                for row in rows:
                    data = dict(zip(columns, row))
                    fb_id = data.get('ID') or data.get('DEPTID') or data.get('GROUPID')
                    if not fb_id: continue
                    
                    name = data.get('NAME') or data.get('DEPTNAME') or data.get('GROUPNAME') or f'Department {fb_id}'
                    
                    dept = existing_depts.get(fb_id)
                    if not dept:
                        dept = Department(external_id=fb_id)
                        db.session.add(dept)
                        existing_depts[fb_id] = dept # Add to map for parent lookup
                        stats['departments'] += 1
                    else:
                        stats['updated'] += 1
                        
                    dept.name = name
                    dept.description = str(data.get('DESCRIPTION') or '')
                
                # Flush to generate IDs
                db.session.flush()
                
                # Re-build map with IDs and update parents
                dep_id_map = {d.external_id: d.id for d in existing_depts.values()}
                
                for row in rows:
                     data = dict(zip(columns, row))
                     fb_id = data.get('ID') or data.get('DEPTID') or data.get('GROUPID')
                     if not fb_id: continue
                     
                     parent_id_fb = data.get('PARENTID') or data.get('PARENT_ID') or data.get('PID')
                     if parent_id_fb and parent_id_fb in dep_id_map:
                         dept = existing_depts[fb_id]
                         dept.parent_id = dep_id_map[parent_id_fb]

            # 4. Синхронизация персонала
            pers_table = self._find_table(cursor, ['PEOPLE',])
            pers_map = {} # FB ID -> Personnel Object

            if pers_table:
                logger.info(f"Found personnel table: {pers_table}")
                columns = self._get_columns(cursor, pers_table)
                # logger.info(f"Personnel table columns: {columns}")
                
                cursor.execute(f"SELECT * FROM {pers_table}")
                rows = cursor.fetchall()
                
                # Загружаем существующий персонал
                # Используем external_id для маппинга
                all_personnel = Personnel.query.filter(Personnel.external_id.isnot(None)).all()
                pers_map = {p.external_id: p for p in all_personnel}
                
                for row in rows:
                    data = dict(zip(columns, row))
                    fb_id = data.get('PEOPLEID') or data.get('ID')
                    if not fb_id: 
                        # Если не нашли ID, пробуем искать первое поле с ID в названии
                        # Исключаем известные внешние ключи
                        excluded_ids = ['DEPTID', 'DEPARTMENTID', 'GROUPID', 'PARENTID', 'CONVID', 'CONVERTERID', 'CARDID', 'KEYID']
                        for key in data.keys():
                            if key.endswith('ID') and key not in excluded_ids and isinstance(data[key], int):
                                fb_id = data[key]
                                break
                    
                    if not fb_id: continue
                    
                    name = data.get('NAME') or data.get('FIO') or data.get('FULLNAME')
                    if not name:
                         # Пробуем собрать ФИО из частей
                         surname = data.get('SURNAME') or data.get('FAM') or data.get('LASTNAME') or ''
                         firstname = data.get('FIRSTNAME') or data.get('IM') or data.get('NAME') or ''
                         patronymic = data.get('PATRONYMIC') or data.get('OTCH') or data.get('MIDDLENAME') or ''
                         
                         parts = [p for p in [surname, firstname, patronymic] if p]
                         if parts:
                             name = ' '.join(parts)
                         else:
                             name = f'Person {fb_id}'

                    dept_id_fb = data.get('DEPTID') or data.get('DEPARTMENTID') or data.get('GROUPID') or data.get('DEPARTMENT_ID') or data.get('GROUP_ID')
                    
                    person = pers_map.get(fb_id)
                    if not person:
                        person = Personnel(external_id=fb_id)
                        db.session.add(person)
                        pers_map[fb_id] = person
                        stats['personnel'] += 1
                    else:
                        stats['updated'] += 1
                        
                    person.name = name
                    person.position = str(data.get('POST') or data.get('POSITION') or data.get('JOBTITLE') or '')
                    
                    if dept_id_fb and dept_id_fb in dep_id_map:
                        person.department_id = dep_id_map[dept_id_fb]
                        
                # Batch flush for personnel
                db.session.flush()

            # 5. Синхронизация карт
            keys_table = self._find_table(cursor, ['KEYS', 'CARDS', 'U_KEYS', 'U_CARDS', 'TOKENS'])
            
            if keys_table:
                logger.info(f"Found keys table: {keys_table}")
                columns = self._get_columns(cursor, keys_table)
                cursor.execute(f"SELECT * FROM {keys_table}")
                rows = cursor.fetchall()
                
                # Загружаем ключи
                existing_keys = {k.key_number: k for k in AccessKey.query.all()}
                
                for row in rows:
                    data = dict(zip(columns, row))
                    
                    key_num = str(data.get('KEYNUM') or data.get('CARDNUM') or data.get('CODE') or data.get('KEY_NUMBER') or '')
                    if not key_num: continue
                    
                    key = existing_keys.get(key_num)
                    if not key:
                        key = AccessKey(key_number=key_num)
                        db.session.add(key)
                        existing_keys[key_num] = key
                        stats['keys'] += 1
                    else:
                        stats['updated'] += 1
                        
                    holder_id_fb = data.get('PEOPLEID') or data.get('PEOPLE_ID') or data.get('USERID') or data.get('HOLDERID') or data.get('OWNERID')
                    
                    if holder_id_fb and holder_id_fb in pers_map:
                        person = pers_map[holder_id_fb]
                        if person:
                            key.holder_name = person.name
                            if not person.card_number:
                                person.card_number = key_num
                    
                    blocked = data.get('BLOCKED')
                    if blocked is not None:
                         key.is_active = (blocked == 0)

            db.session.commit()
            
            # Получаем путь к БД из настроек
            from app.models import Settings
            s = Settings.query.filter_by(key='FIREBIRD_DATABASE').first()
            db_path = s.value if s else os.environ.get('FIREBIRD_DATABASE', 'неизвестной базе')
            
            return {
                "success": True, 
                "message": f"Синхронизация успешна (База: {db_path}). Добавлено: Конвертеров - {stats['converters']}, Контроллеров - {stats['controllers']}, Отделов - {stats['departments']}, Персонала - {stats['personnel']}, Карт - {stats['keys']}. Обновлено: {stats['updated']}"
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Sync error: {e}")
            return {"success": False, "message": f"Ошибка при синхронизации: {str(e)}"}
        finally:
            # Не отключаемся, так как fb_client управляет соединением
            pass

    def _find_table(self, cursor, candidates):
        for table in candidates:
            try:
                cursor.execute(f"SELECT count(*) FROM {table}")
                return table
            except:
                continue
        return None

    def _get_columns(self, cursor, table):
        cursor.execute(f"SELECT * FROM {table}")
        return [d[0].upper() for d in cursor.description]

sync_service = SyncService()
