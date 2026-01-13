print("Starting check...")
from app import create_app, db
print("Imported app")
from app.models.settings import Settings
from sqlalchemy import inspect

app = create_app()

with app.app_context():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"Tables: {tables}")
    
    if 'settings' in tables:
        print("Settings table exists.")
        try:
            settings = Settings.query.all()
            print(f"Settings count: {len(settings)}")
            for s in settings:
                print(s)
        except Exception as e:
            print(f"Error querying settings: {e}")
    else:
        print("Settings table DOES NOT exist.")
