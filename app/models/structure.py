from app import db
from datetime import datetime

class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    external_id = db.Column(db.Integer, nullable=True) # ID from Firebird
    parent_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    
    # Relations
    children = db.relationship('Department', backref=db.backref('parent', remote_side=[id]))
    personnel = db.relationship('Personnel', backref='department')
    
    def __repr__(self):
        return f'<Department {self.name}>'

class Personnel(db.Model):
    __tablename__ = 'personnel'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False) # Full name
    external_id = db.Column(db.Integer, nullable=True) # ID from Firebird
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    position = db.Column(db.String(200), nullable=True)
    card_number = db.Column(db.String(50), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Personnel {self.name}>'
