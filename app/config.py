import pandas as pd
import polars as pl
import os
from datetime import datetime

# Constantes
DAYS_PER_YEAR = 365
TODAY = datetime.today().date()
THIS_YEAR = TODAY.year
PROJECT_ADRESS = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
STATIC = os.path.join(PROJECT_ADRESS, 'static')
LOGO_AYA = 'logo.png'
PORT = 8002
INDETERMINADO = 'Indeterminado'
MAIL_TO = "rrhh@ayacda.com"
MAIL_CC = "contabilidad@ayacda.com;auxiliarrrhh@ayacda.com;gportocarrerob@unsa.edu.pe"
BECOMING_INDETERMINED_ALERT = 'index_indetermined.html'
BECOMING_INDETERMINED_SUBJECT = 'Cambio de contrato a indeterminado'
CONTRACT_FINALIZED_ALERT = 'index_finalized_contract.html'
CONTRACT_FINALIZED_SUBJECT = 'Personal a terminar contrato'

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
    "file_name": "Control Contratos - copia.xlsx",
    "sheet_name": "DATOS",
    "relevant_columns": [
        'TRABAJADOR',
        'NRODOCIDEN',
        'DNI',
        'CARGO',
        'AREA',
    ]
}