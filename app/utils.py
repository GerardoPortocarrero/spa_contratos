import locale
import time
import webbrowser
import pandas as pd
from .config import DAYS_PER_YEAR, TODAY, THIS_YEAR, PROJECT_ADRESS, LOGO_AYA, PORT, MONTHS, CONTRACT_TYPE, CONTRATOS
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
    df = dm.process_data(CONTRATOS)
    df = dm.transform_data(df, TODAY, DAYS_PER_YEAR, CONTRACT_TYPE)

    # Convertir de Polars a Pandas
    df_pd = df.to_pandas()

    # Exportar como CSV separado por coma (encoding opcional)
    return df_pd.to_csv(index=False, sep=";", encoding="utf-8-sig")