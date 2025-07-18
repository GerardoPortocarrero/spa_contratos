import locale
import time
import webbrowser
import pandas as pd
import msoffcrypto
from io import BytesIO
from .config import START_YEAR, TODAY, THIS_YEAR, PORT, MONTHS, VACATION_PERIODS, VACACIONES
from . import data_management as dm

def setup_locale():
    try:
        locale.setlocale(locale.LC_TIME, "es_ES.utf8")
    except:
        try:
            locale.setlocale(locale.LC_TIME, "Spanish_Spain.1252")
        except:
            pass

def open_browser():
    time.sleep(2)
    webbrowser.open(f"http://localhost:{PORT}")

def procesar_excel():
    df = None # Entregar dataframe con polars

    # Convertir de Polars a Pandas
    df_pd = df.to_pandas()

    # Exportar como CSV separado por coma (encoding opcional)
    return df_pd.to_csv(index=False, sep=";", encoding="utf-8-sig")