'''
mi_app/
│
├── app/
│   ├── __init__.py            # Crea y configura la app Flask
│   ├── routes.py              # Rutas y controladores
│   ├── utils.py               # Funciones auxiliares (leer Excel, limpiar, etc.)
│   ├── config.py              # Configuración general (archivo, contraseña, puertos)
│
├── static/
│   └── index.html             # Tu HTML actual con JS y estilo
│
├── requirements.txt           # Lista de paquetes necesarios
├── run.py                     # Punto de entrada para ejecutar la app
'''

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=8002)