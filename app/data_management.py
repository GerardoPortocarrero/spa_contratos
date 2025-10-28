import polars as pl
import pandas as pd
import re
import os
import locale
from datetime import datetime
import win32com.client
from bs4 import BeautifulSoup

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
    if TODAY <= cese:
        cese_txt = f"(Fecha Cese {cese_txt}) ACTIVO"
    elif TODAY > cese:
        cese_txt = f"(Fecha Cese {cese_txt}) INACTIVO"
    return f"{ingreso_txt} a {cese_txt}"

# Expandir el dataframe con los datos necesarios
def expandir_contratos(df, PERIOD_COLUMNS, TODAY, DAYS_PER_YEAR, CONTRACT_TYPE):
    results = []

    # Agrupar pares ingreso/cese por número de periodo
    period_numbers = sorted(set(re.findall(r'PERIODO_(\d+)', ' '.join(PERIOD_COLUMNS))))

    for row in df.iter_rows(named=True):
        all_periods = 0
        period_details = []
        
        continuous_periods = []
        last_continuous_cese = None

        # 1. Recopilar todos los periodos continuos
        for period in period_numbers:
            ingreso_date = row.get(f'FECHA_INGRESO_PERIODO_{period}')
            cese_date = row.get(f'FECHA_CESE_PERIODO_{period}')

            if ingreso_date is None:
                continue

            # Si hay una interrupción grande, reiniciar la cadena de continuidad
            if last_continuous_cese and (ingreso_date - last_continuous_cese).days > DAYS_PER_YEAR:
                continuous_periods = []

            continuous_periods.append((ingreso_date, cese_date))
            last_continuous_cese = cese_date
            all_periods += 1
            
            # Para el detalle visual, usamos la fecha de cese real o asumimos hoy si no existe
            display_cese_date = cese_date if cese_date is not None else TODAY
            period_details.append(formatear_rango_periodo(ingreso_date, display_cese_date, TODAY))

        # 2. Determinar el estado (activo/inactivo) y la fecha final real
        is_active = False
        last_real_cese_date = None
        if continuous_periods:
            # La última fecha de cese real de la cadena continua
            last_real_cese_date = continuous_periods[-1][1]
            # Si la última fecha de cese es nula o futura, el empleado está activo
            if last_real_cese_date is None or TODAY <= last_real_cese_date:
                is_active = True

        # 3. Calcular el tiempo de servicio total hasta el día de HOY
        total_service_days = 0
        if continuous_periods:
            first_ingreso_date = continuous_periods[0][0]
            # Si está activo, contamos hasta hoy. Si no, hasta su última fecha de cese.
            end_date_for_calc = TODAY if is_active else last_real_cese_date
            if end_date_for_calc:
                total_service_days = (end_date_for_calc - first_ingreso_date).days

        # 4. Determinar el tipo de contrato basado en la nueva lógica
        locacion = row['AREA'].strip().upper()
        threshold_years = 3 if 'PEDREGAL' in locacion else 5
        is_eligible_for_indeterminado = (total_service_days >= threshold_years * DAYS_PER_YEAR)
        
        contrato = 1 # Por defecto 'NECESIDAD MERCADO'
        if is_active and is_eligible_for_indeterminado:
            contrato = 0 # 'INDETERMINADO'

        # 5. Calcular alertas
        # Alerta para ser indeterminado (solo si está activo y aún no lo es)
        becoming_indetermined = False
        days_to_become_indetermined = 0
        if is_active and not is_eligible_for_indeterminado:
            days_remaining = (threshold_years * DAYS_PER_YEAR) - total_service_days
            if 0 <= days_remaining <= 30:
                becoming_indetermined = True
                days_to_become_indetermined = days_remaining

        # Alerta para finalización de contrato (solo si está activo y tiene fecha de fin)
        contract_finalized = False
        days_to_finalized_contract = 0
        if is_active and last_real_cese_date:
            days_remaining = (last_real_cese_date - TODAY).days
            if 0 < days_remaining <= 14:
                contract_finalized = True
                days_to_finalized_contract = days_remaining

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
            'Periodos Detallados': period_details_str,
            'Indeterminacion de contrato': becoming_indetermined,
            'Dias para ser indeterminado': days_to_become_indetermined,
            'Finalizacion de contrato': contract_finalized,
            'Dias para terminar contrato': days_to_finalized_contract,
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

# Adjust table to admit css on outlook and gmail
def dataframe_to_table_html(df: pl.DataFrame) -> str:
    df_pd = df.to_pandas()
    headers = df_pd.columns.tolist()

    # Estilos para Outlook
    table_style = "width: 100%; border-collapse: collapse; font-size: 14px; color: #2c3e50;"
    th_style = "padding: 8px; background-color: #c4161c; color: #fff; text-align: left; border: 1px solid #ddd;"
    td_style = "padding: 8px; border: 1px solid #ddd; text-align: left;"

    html = f'<table style="{table_style}">'
    html += "<thead><tr>" + "".join([f"<th style='{th_style}'>{col}</th>" for col in headers]) + "</tr></thead><tbody>"

    for _, row in df_pd.iterrows():
        html += "<tr>" + "".join([f"<td style='{td_style}'>{val}</td>" for val in row]) + "</tr>"

    html += "</tbody></table>"
    return html

def generar_html_alerta(titulo: str, tabla_html: str, mensaje_html: str) -> str:
    return f"""
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <title>{titulo}</title>
  <style>
    table.data {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
    }}
    table.data th, table.data td {{
      padding: 10px;
      border: 1px solid #ccc;
      text-align: left;
      font-size: 14px;
    }}
    table.data th {{
      background-color: #ecf0f1;
      color: #2c3e50;
      font-weight: bold;
    }}
  </style>
</head>
<body style="margin:0; padding:0; background-color:#f4f6f8; font-family: Arial, sans-serif;">

  <table align="center" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#f4f6f8">
    <tr>
      <td align="center" style="padding: 30px;">

        <table width="680" cellpadding="0" cellspacing="0" border="0" bgcolor="#ffffff" style="border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.05); border: 1px solid #ddd;">
          <tr>
            <td style="padding: 30px;">

              <table width="100%" cellpadding="0" cellspacing="0" style="border-bottom: 1px solid #f0f0f0; margin-bottom: 20px;">
                <tr>
                  <td valign="middle" style="width: 80px;">
                    <img src="cid:logo.png" alt="Logo AYA" width="60" style="display: block;">
                  </td>
                  <td align="left" valign="middle" style="padding-left: 16px;">
                    <h1 style="font-size: 22px; color: #c4161c; margin: 0;">{titulo}</h1>
                    <span style="font-size: 13px; color: #7f8c8d;">A Y A DISTRIBUCIONES E.I.R.L</span>
                  </td>
                </tr>
              </table>

              {"<table width='100%' cellpadding='12' cellspacing='0' style='background-color:#f9f9f9; border:1px solid #ddd; border-radius:6px; margin-bottom:20px;'><tr><td style='font-size:15px; color:#333;'>" + mensaje_html + "</td></tr></table>" if mensaje_html else ""}

              {tabla_html}

            </td>
          </tr>
        </table>

      </td>
    </tr>
  </table>

</body>
</html>
"""

def alerta_becoming_indetermined(df: pl.DataFrame, output_path: str):
    alert_df = df.filter(pl.col("Indeterminacion de contrato") == True)

    if alert_df.is_empty():
        mensaje = "<strong>✅ No hay trabajadores próximos a quedar indeterminados.</strong>"
        html = generar_html_alerta("Alerta - Indeterminación de Contrato", "", mensaje)
    else:
        table = dataframe_to_table_html(
            alert_df.select(["Nombre", "Contrato", "Dias para ser indeterminado"]).sort("Dias para ser indeterminado")
        )
        html = generar_html_alerta("Alerta - Indeterminación de Contrato", table, "")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

def alerta_contract_finalized(df: pl.DataFrame, output_path: str):
    alert_df = df.filter(pl.col("Finalizacion de contrato") == True)

    if alert_df.is_empty():
        mensaje = "<strong>✅ No hay contratos próximos a finalizar.</strong>"
        html = generar_html_alerta("Alerta - Contratos por Finalizar", "", mensaje)
    else:
        table = dataframe_to_table_html(
            alert_df.select(["Nombre", "Contrato", "Dias para terminar contrato"]).sort("Dias para terminar contrato")
        )
        html = generar_html_alerta("Alerta - Contratos por Finalizar", table, "")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

# Embeber imagenes para que se visualice por correo con "cid"
def embedir_imagenes_en_html(soup, mail, ruta_base_imagenes):
    """
    Inserta imágenes embebidas en el HTML de un correo de Outlook (usando cid),
    reemplazando espacios por guiones bajos en los nombres de archivo.

    Args:
        soup (BeautifulSoup): Contenido HTML del correo como objeto BeautifulSoup.
        mail: Objeto mail de Outlook (MailItem).
        ruta_base_imagenes (str): Ruta donde están almacenadas las imágenes referenciadas con cid.
    """
    img_tags = soup.find_all("img", src=True)
    
    for img_tag in img_tags:
        src = img_tag["src"]
        if src.startswith("cid:"):
            raw_cid = src[4:]
            full_path = os.path.join(ruta_base_imagenes, raw_cid)

            if not os.path.isfile(full_path):
                print(f"[!] Imagen no encontrada: {full_path}")
                continue

            # Agrega la imagen como attachment embebido
            attachment = mail.Attachments.Add(full_path)
            attachment.PropertyAccessor.SetProperty(
                "http://schemas.microsoft.com/mapi/proptag/0x3712001F", raw_cid
            )

            # Actualiza el src en el HTML
            img_tag["src"] = f"cid:{raw_cid}"

# Enviar correo atravéz de outlook
def send_email_main(index_html, MAIL_TO, MAIL_CC, subject, STATIC):
    # Crear instancia de Outlook
    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0) # 0 = MailItem

    # Leer el archivo HTML
    with open(index_html, "r", encoding="utf-8") as f:
        html_body = f.read()

    soup = BeautifulSoup(html_body, "html.parser")

    # Embebe todas las imágenes antes de guardar o enviar
    embedir_imagenes_en_html(soup, mail, ruta_base_imagenes=STATIC)

    # Guardar o usar el HTML final
    html_body = str(soup)

    # Asunto
    mail.Subject = subject
    
    # Destinatarios principales
    mail.To = MAIL_TO

    # Con copia (CC)
    mail.CC = MAIL_CC

    # Cuerpo en HTML
    mail.HTMLBody = html_body

    # (Opcional) Agregar archivo adjunto
    # mail.Attachments.Add("C:\\ruta\\al\\archivo.pdf")

    # Enviar el correo
    mail.Send()