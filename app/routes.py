import os
from flask import send_file, Response
from .utils import procesar_excel

def register_routes(app):
    
    @app.route("/")
    def index():
        return send_file(os.path.join(app.static_folder, "index.html"))

    @app.route("/contrato.csv")
    def file_csv():
        csv_data = procesar_excel()
        return Response(
            csv_data,
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=contratos.csv"}
        )
