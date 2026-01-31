from app import create_app
from waitress import serve
import os

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    serve(app, host='0.0.0.0', port=port)
