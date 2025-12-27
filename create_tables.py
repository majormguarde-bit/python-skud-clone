from app import create_app, db
from app.models import *

app = create_app()

with app.app_context():
    print("Creating missing tables...")
    db.create_all()
    print("Tables created successfully.")
