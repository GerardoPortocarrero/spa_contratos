import locale
import time
import os
import webbrowser
from .config import DAYS_PER_YEAR, TODAY, THIS_YEAR, PROJECT_ADRESS, LOGO_AYA, PORT, MONTHS, CONTRACT_TYPE, CONTRATOS, BECOMING_INDETERMINED_ALERT, BECOMING_INDETERMINED_SUBJECT, CONTRACT_FINALIZED_ALERT, CONTRACT_FINALIZED_SUBJECT, MAIL_TO, MAIL_CC, STATIC
from . import data_management as dm
from . import cache

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
    if cache.csv_cache is None:
        dm.alerta_becoming_indetermined(df, os.path.join(PROJECT_ADRESS, BECOMING_INDETERMINED_ALERT))
        dm.alerta_contract_finalized(df, os.path.join(PROJECT_ADRESS, CONTRACT_FINALIZED_ALERT))
        dm.send_email_main(os.path.join(PROJECT_ADRESS, BECOMING_INDETERMINED_ALERT), MAIL_TO, MAIL_CC, BECOMING_INDETERMINED_SUBJECT, STATIC)
        dm.send_email_main(os.path.join(PROJECT_ADRESS, CONTRACT_FINALIZED_ALERT), MAIL_TO, MAIL_CC, CONTRACT_FINALIZED_SUBJECT, STATIC)

    # Convertir de Polars a Pandas
    df_pd = df.to_pandas()

    # Exportar como CSV separado por coma (encoding opcional)
    return df_pd.to_csv(index=False, sep=";", encoding="utf-8-sig")