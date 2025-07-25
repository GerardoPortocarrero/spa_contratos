import pandas as pd
import polars as pl
import os
from datetime import datetime
import re
import locale

# Constantes
DAYS_PER_YEAR = 365
TODAY = datetime.today().date()
THIS_YEAR = TODAY.year
PROJECT_ADRESS = os.path.dirname(os.path.abspath(__file__))
LOGO_AYA = 'logo.png'
PORT = 8002
INDETERMINADO = 'Indeterminado'

# Diccionarios
MONTHS = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 
    11: 'Noviembre', 12: 'Diciembre'
}
CONTRACT_TYPE = {
    0: "INDETERMINADO",
    1: "NECESIDAD MERCADO"
}
CONTRATOS = {
    "name": "Control contratos",
    "file_name": "Control Contratos.xlsx",
    "sheet_name": "DATOS",
    "relevant_columns": [
        'TRABAJADOR',
        'NRODOCIDEN',
        'DNI',
        'CARGO',
        'AREA',
    ]
}