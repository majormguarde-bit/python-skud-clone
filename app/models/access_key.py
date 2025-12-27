from datetime import datetime
from app import db

class AccessKey(db.Model):
    __tablename__ = 'access_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    key_number = db.Column(db.String(50), unique=True, nullable=False)
    key_type = db.Column(db.String(20), default='rfid')  # rfid, fingerprint, etc.
    holder_name = db.Column(db.String(200), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    issue_date = db.Column(db.Date, nullable=True)
    expiry_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Отношения
    access_levels = db.relationship('AccessLevel', secondary='key_access_levels', backref='access_keys')
    
    def __repr__(self):
        return f'<AccessKey {self.key_number}>'

class AccessLevel(db.Model):
    __tablename__ = 'access_levels'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    level = db.Column(db.Integer, nullable=False)  # уровень доступа (число)
    time_restrictions = db.Column(db.Text, nullable=True)  # JSON с ограничениями по времени
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AccessLevel {self.name}>'

# Таблица связи ключей и уровней доступа
key_access_levels = db.Table('key_access_levels',
    db.Column('access_key_id', db.Integer, db.ForeignKey('access_keys.id'), primary_key=True),
    db.Column('access_level_id', db.Integer, db.ForeignKey('access_levels.id'), primary_key=True)
)
