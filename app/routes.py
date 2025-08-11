import os
from flask import send_file, Response
from .utils import procesar_excel
from . import cache

def register_routes(app):
    
    @app.route("/")
    def index():
        return send_file(os.path.join(app.static_folder, "index.html"))

    @app.route("/contrato.csv")
    def file_csv():
        cache.csv_cache = procesar_excel()

        return Response(
            cache.csv_cache,
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=contratos.csv"}
        )
