import polars as pl
import pandas as pd
import re
import locale
from datetime import datetime

# Eliminar columnas innecesarias
def get_relevant_columns(df, relevant_columns):
    return df[relevant_columns]

# Obtener las columnas que son periodos dinamicamente
def get_period_dates_columns(df):
    period_columns = [col for col in df.columns if re.match(r"FECHA_(INGRESO|CESE)_PERIODO_\d+", col)]
    return period_columns

# Filtrar ruido (obtener la tabla principal)
def filter_noise(df):
    df.columns = df.iloc[0].astype(str).str.strip()
    return df.iloc[1:].reset_index(drop=True)

# Procesar dataframe
def process_data(CONTRATOS):
    # Leer Excel con pandas
    df = pd.read_excel(
        CONTRATOS['file_name'],
        sheet_name=CONTRATOS['sheet_name'],
        header=None
    )

    # Limpiar datos
    df = filter_noise(df)

    period_columns = get_period_dates_columns(df)
    relevant_columns = CONTRATOS['relevant_columns'] + period_columns
    relevant_columns = list(dict.fromkeys(relevant_columns))

    df = get_relevant_columns(df, relevant_columns)

    # Asegurarse que todo es str (para que acepte el cambio de pandas a polars
    # ya que hay columnas que son fecha y a la vez str como SUBSIDIO)
    df = df.astype(str)

    # Convertir a polars
    df_pl = pl.from_pandas(df)    

    return df_pl

# Convertir columna str a fecha
def str_to_date(df, column_name):
    return df.with_columns(
        pl.col(column_name)
        .str.strptime(pl.Date, format="%Y-%m-%d %H:%M:%S", strict=False)
    )

# Expresión para limpiar y concatenar
def clean_and_concatenate():
    return (
        pl.col("NRODOCIDEN")
        .str.replace_all(r"[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]", "") # Mantener letras con tilde, ñ y espacios
        .str.strip_chars()
        .str.strip_chars(" ")
        .str.strip_chars(".")
        + pl.lit(" ") +
        pl.col("TRABAJADOR")
        .str.replace_all(r"[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]", "")
        .str.strip_chars()
        .str.strip_chars(" ")
        .str.strip_chars(".")
    ).str.strip_chars()

def formatear_fecha_es(fecha: datetime) -> str:
    try:
        locale.setlocale(locale.LC_TIME, "es_ES.utf8")
    except:
        try:
            locale.setlocale(locale.LC_TIME, "Spanish_Spain.1252")
        except:
            pass
    return fecha.strftime("%d %B %Y").lower()

def formatear_rango_periodo(ingreso, cese, TODAY) -> str:
    ingreso_txt = formatear_fecha_es(ingreso)
    cese_txt = formatear_fecha_es(cese)
    if cese == TODAY:
        cese_txt = f"(ACTIVO a la fecha {cese_txt})"
    elif TODAY <= cese:
        cese_txt = f"(CESE a la fecha {cese_txt})"
    return f"{ingreso_txt} a {cese_txt}"

# Expandir el dataframe con los datos necesarios
def expandir_contratos(df, PERIOD_COLUMNS, TODAY, DAYS_PER_YEAR, CONTRACT_TYPE):
    results = []

    # Agrupar pares ingreso/cese por número de periodo
    period_numbers = sorted(set(re.findall(r'PERIODO_(\d+)', ' '.join(PERIOD_COLUMNS))))

    for row in df.iter_rows(named=True):
        all_periods = 0
        valid_periods = []
        period_details = []
        previous_cese_period = None

        for period in period_numbers:
            ingreso_date = row.get(f'FECHA_INGRESO_PERIODO_{period}')
            cese_date = row.get(f'FECHA_CESE_PERIODO_{period}')

            # Si no hay fecha de ingreso verificar el siguiente periodo
            if ingreso_date is None:
                continue            

            # Si no hay fecha de salida, asumimos que sigue activo hoy
            if cese_date is None:
                cese_date = TODAY

            all_periods += 1
            period_details.append(formatear_rango_periodo(ingreso_date, cese_date, TODAY))

            # Verificamos si el periodo es válido
            if previous_cese_period:
                gap_days = (ingreso_date - previous_cese_period).days
                if gap_days > DAYS_PER_YEAR:
                    valid_periods = []  # reiniciar periodos válidos si el salto es muy grande

            valid_periods.append((ingreso_date, cese_date))
            previous_cese_period = cese_date

        # Calcular días de servicio usando solo los periodos válidos
        total_service_days = sum((cese - ingreso).days for ingreso, cese in valid_periods)

        # Tipo de contrato
        locacion = row['AREA'].strip().upper()
        threshold_years = 3 if 'PEDREGAL' in locacion else 5
        contrato = 0 if total_service_days >= threshold_years * DAYS_PER_YEAR else 1

        # Castear los periodos
        period_details_str = " / ".join(period_details)

        results.append({
            'Locacion': row['AREA'],
            'Nombre': row['NOMBRE'],
            'Dni': row['DNI'],
            'Cargo': row['CARGO'],
            'Periodos': all_periods,
            'Tiempo Servicio': total_service_days,
            'Contrato': CONTRACT_TYPE[contrato],
            'Periodos Detallados': period_details_str
        })

    return pl.DataFrame(results)

# Transformar dataframe
def transform_data(df, TODAY, DAYS_PER_YEAR, CONTRACT_TYPE):
    # Aplicar la transformación
    df = df.with_columns(
        clean_and_concatenate().alias("NOMBRE")
    )

    # Cambiar tipo de columna a fecha
    period_columns = get_period_dates_columns(df)
    for period in period_columns:
        df = str_to_date(df, period)

    # Calcular periodos, tiempo de servicio en dias, estado
    df = expandir_contratos(df, period_columns, TODAY, DAYS_PER_YEAR, CONTRACT_TYPE)

    return df