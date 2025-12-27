from datetime import datetime
from app import db

class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    event_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    event_type_id = db.Column(db.Integer, db.ForeignKey('event_types.id'), nullable=False)
    controller_id = db.Column(db.Integer, db.ForeignKey('controllers.id'), nullable=True)
    reader_id = db.Column(db.Integer, db.ForeignKey('readers.id'), nullable=True)
    access_key_id = db.Column(db.Integer, db.ForeignKey('access_keys.id'), nullable=True)
    
    # Дополнительные данные
    card_number = db.Column(db.String(50), nullable=True)
    direction = db.Column(db.String(10), nullable=True)  # in, out
    access_granted = db.Column(db.Boolean, nullable=True)
    description = db.Column(db.Text, nullable=True)
    
    # Отношения
    event_type = db.relationship('EventType', backref='events')
    controller = db.relationship('Controller', backref='events')
    reader = db.relationship('Reader', backref='events')
    access_key = db.relationship('AccessKey', backref='events')
    
    def __repr__(self):
        return f'<Event {self.event_type.name} at {self.event_time}>'

class EventType(db.Model):
    __tablename__ = 'event_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_system = db.Column(db.Boolean, default=False)  # системные события
    color = db.Column(db.String(7), default='#000000')  # цвет для отображения
    
    def __repr__(self):
        return f'<EventType {self.name}>'
