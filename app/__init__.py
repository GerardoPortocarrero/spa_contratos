import os
from flask import Flask
from .routes import register_routes
from .utils import setup_locale, open_browser
import threading

def create_app():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    static_dir = os.path.join(base_dir, "static")

    app = Flask(__name__, static_folder=static_dir)
    
    # Locale en español
    setup_locale()

    # Rutas
    register_routes(app)

    # Abrir navegador automáticamente
    threading.Thread(target=open_browser).start()

    return app