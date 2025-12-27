from datetime import datetime
from app import db

class Controller(db.Model):
    __tablename__ = 'controllers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    serial_number = db.Column(db.String(50), unique=True, nullable=False)
    addr = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), default='offline')  # online, offline, error
    last_session = db.Column(db.DateTime, nullable=True)
    firmware_version = db.Column(db.String(50), nullable=True)
    extra_data = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Отношения
    converter_id = db.Column(db.Integer, db.ForeignKey('converters.id'), nullable=True)
    converter = db.relationship('Converter', backref='controllers')
    readers = db.relationship('Reader', backref='controller', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Controller {self.name} ({self.serial_number})>'

class Reader(db.Model):
    __tablename__ = 'readers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    reader_number = db.Column(db.Integer, nullable=False)  # номер на контроллере
    reader_type = db.Column(db.String(20), default='rfid')  # rfid, fingerprint, etc.
    status = db.Column(db.String(20), default='offline')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Отношения
    controller_id = db.Column(db.Integer, db.ForeignKey('controllers.id'), nullable=False)
    
    def __repr__(self):
        return f'<Reader {self.name} on {self.controller.name}>'

class Converter(db.Model):
    __tablename__ = 'converters'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    serial_number = db.Column(db.String(50), unique=True, nullable=False)
    ip_address = db.Column(db.String(15), nullable=False)
    port = db.Column(db.Integer, default=10001)
    converter_type = db.Column(db.String(20), default='Z397')  # Z397, etc.
    status = db.Column(db.String(20), default='offline')
    last_seen = db.Column(db.DateTime, nullable=True)
    extra_data = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Converter {self.name} ({self.serial_number})>'
