import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
from io import StringIO, BytesIO
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

# Definir los scopes necesarios
SCOPES = ['https://www.googleapis.com/auth/drive']

# Función para obtener el servicio de Google Drive
def get_drive_service():
    try:
        credentials_json = st.secrets["google_drive"]["credentials"]
        credentials_info = json.loads(credentials_json)
        credentials = Credentials.from_service_account_info(credentials_info, scopes=SCOPES)
        return build('drive', 'v3', credentials=credentials)
    except KeyError:
        st.error("Google Drive credentials not found.")
        raise
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON in credentials: {str(e)}")
        raise

# Función para procesar la tabla HTML y convertirla a CSV
def process_html_table(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table')
    if not table:
        raise ValueError("No se encontró una tabla válida en el HTML proporcionado.")
    df = pd.read_html(str(table))[0]
    if df.empty:
        raise ValueError("La tabla HTML no contiene datos válidos.")
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8')
    return csv_buffer.getvalue()

# Función para descargar el CSV de Google Drive
def download_csv_from_drive(service, folder_id, file_name):
    query = f"'{folder_id}' in parents and name = '{file_name}' and trashed = false"
    response = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = response.get('files', [])
    if not files:
        return None
    file_id = files[0]['id']
    request = service.files().get_media(fileId=file_id)
    file_buffer = BytesIO()
    downloader = request.execute()
    file_buffer.write(downloader)
    file_buffer.seek(0)
    try:
        return pd.read_csv(file_buffer, encoding='utf-8')
    except UnicodeDecodeError:
        file_buffer.seek(0)
        return pd.read_csv(file_buffer, encoding='latin1')

# Función para parsear fechas con múltiples formatos
def parse_date(date_str):
    date_str = str(date_str).replace(" (LT)", "").strip()
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"No se pudo parsear la fecha: {date_str}")

# Función para actualizar el archivo CSV en Google Drive
def update_csv_in_drive(csv_data, folder_id, file_name):
    service = get_drive_service()
    try:
        new_df = pd.read_csv(StringIO(csv_data), encoding='utf-8')
    except UnicodeDecodeError:
        new_df = pd.read_csv(StringIO(csv_data), encoding='latin1')
    ref_date_str = new_df.iloc[0, 1]
    ref_date = parse_date(ref_date_str)
    existing_df = download_csv_from_drive(service, folder_id, file_name)
    if existing_df is not None:
        existing_df['parsed_date'] = existing_df.iloc[:, 1].apply(parse_date)
        filtered_df = existing_df[existing_df['parsed_date'] < ref_date].drop(columns=['parsed_date'])
        final_df = pd.concat([filtered_df, new_df], ignore_index=True)
    else:
        final_df = new_df
    csv_buffer = StringIO()
    final_df.to_csv(csv_buffer, index=False, encoding='utf-8')
    csv_data_final = csv_buffer.getvalue()
    query = f"'{folder_id}' in parents and name = '{file_name}' and trashed = false"
    response = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = response.get('files', [])
    media = MediaIoBaseUpload(StringIO(csv_data_final), mimetype='text/csv')
    if files:
        file_id = files[0]['id']
        service.files().update(fileId=file_id, media_body=media).execute()
    else:
        file_metadata = {'name': file_name, 'parents': [folder_id]}
        service.files().create(body=file_metadata, media_body=media).execute()

# Función para generar el PDF
def generate_pdf(df, mes, anio):
    """
    Genera un PDF con los datos del CSV filtrados por mes y año, excluyendo 'Función' y 'Flota'.
    """
    # Parsear las fechas y filtrar por mes y año
    df['parsed_date'] = df['Inicio'].apply(parse_date)
    df_filtered = df[(df['parsed_date'].dt.month == mes) & (df['parsed_date'].dt.year == anio)]
    
    # Eliminar columnas no deseadas y la columna temporal
    columns_to_keep = [col for col in df.columns if col not in ['Función', 'Flota', 'parsed_date']]
    df_filtered = df_filtered[columns_to_keep]
    
    # Crear el buffer para el PDF
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    
    # Preparar los datos para la tabla
    data = [df_filtered.columns.tolist()] + df_filtered.values.tolist()
    
    # Crear la tabla con ReportLab
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    # Construir el PDF
    elements = [table]
    doc.build(elements)
    pdf_buffer.seek(0)
    
    return pdf_buffer
