from datetime import datetime
from app import db

class Device(db.Model):
    __tablename__ = 'devices'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    device_type = db.Column(db.String(50), nullable=False)  # controller, converter, reader
    serial_number = db.Column(db.String(50), unique=True, nullable=False)
    ip_address = db.Column(db.String(15), nullable=True)
    port = db.Column(db.Integer, nullable=True)
    model = db.Column(db.String(100), nullable=True)
    firmware_version = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(200), nullable=True)
    
    # Статус устройства
    status = db.Column(db.String(20), default='offline')  # online, offline, error, maintenance
    last_seen = db.Column(db.DateTime, nullable=True)
    last_error = db.Column(db.Text, nullable=True)
    error_count = db.Column(db.Integer, default=0)
    
    # Метаданные
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def update_status(self, status, error=None):
        self.status = status
        self.last_seen = datetime.utcnow()
        if error:
            self.last_error = error
            self.error_count += 1
        else:
            self.error_count = 0
            self.last_error = None
        db.session.commit()
    
    def __repr__(self):
        return f'<Device {self.name} ({self.serial_number})>'

class DeviceStatus(db.Model):
    __tablename__ = 'device_status'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    device = db.relationship('Device', backref='status_history')
    
    def __repr__(self):
        return f'<DeviceStatus {self.device.name}: {self.status}>'
