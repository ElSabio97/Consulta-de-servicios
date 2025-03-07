import streamlit as st
from functions import process_html_table, update_csv_in_drive, download_csv_from_drive, generate_pdf, update_cdu_csv, get_drive_service
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Actualizar CSV en Drive", page_icon="📊")

# Título y descripción
st.title("¿Qué está haciendo Pedrito?")
st.write("Descarga la progra que quieras seleccionando el mes")

# Área de texto para pegar la tabla HTML
html_input = st.text_area("Pega aquí la tabla HTML", height=300)

# Botón para procesar y actualizar
if st.button("Actualizar CSV"):
    if html_input:
        try:
            csv_data = process_html_table(html_input)
            folder_id = '1B8gnCmbBaGMBT77ba4ntjpZj_NkJcvuI'
            file_name = 'Consulta_de_servicios.csv'
            update_csv_in_drive(csv_data, folder_id, file_name)
            st.success("¡Archivo CSV actualizado en Google Drive con éxito!")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.warning("Por favor, pega una tabla HTML antes de actualizar.")

# Selector de mes y generación de PDF
st.subheader("Generar PDF por mes")
meses = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]
mes_seleccionado = st.selectbox("Selecciona un mes", meses)
anio_seleccionado = st.number_input("Selecciona un año", min_value=2020, max_value=2030, value=datetime.now().year)

if st.button("Generar PDF"):
    try:
        folder_id = '1B8gnCmbBaGMBT77ba4ntjpZj_NkJcvuI'
        file_name = 'Consulta_de_servicios.csv'
        service = get_drive_service()
        df = download_csv_from_drive(service, folder_id, file_name)
        
        if df is None:
            st.error("No se encontró el archivo CSV en Google Drive.")
        else:
            mes_num = meses.index(mes_seleccionado) + 1
            pdf_buffer = generate_pdf(df, mes_num, anio_seleccionado)
            st.download_button(
                label="Descargar PDF",
                data=pdf_buffer,
                file_name=f"Programa_{mes_seleccionado}_{anio_seleccionado}.pdf",
                mime="application/pdf"
            )
    except Exception as e:
        st.error(f"Error al generar el PDF: {str(e)}")

# Botón para abrir el formulario de CDU
st.subheader("Añadir datos a CDU.csv")
with st.expander("Añadir entrada a CDU", expanded=False):
    with st.form(key='cdu_form'):
        st.write("Ingrese los datos para CDU.csv")
        date = st.text_input("DATE", value=datetime.now().strftime("%d/%m/%Y %H:%M"))
        flt_num = st.text_input("FLT NUM")
        out = st.text_input("OUT")
        off = st.text_input("OFF")
        on_ = st.text_input("ON")
        in_ = st.text_input("IN")
        submit_button = st.form_submit_button(label="Guardar en CDU.csv")
        
        if submit_button:
            try:
                folder_id = '1B8gnCmbBaGMBT77ba4ntjpZj_NkJcvuI'
                file_name = 'CDU.csv'
                data = {
                    "DATE": date,
                    "FLT NUM": flt_num,
                    "OUT": out,
                    "OFF": off,
                    "ON": on_,
                    "IN": in_
                }
                # Debugging: Mostrar los datos antes de enviarlos
                st.write("Datos enviados:", data)
                update_cdu_csv(data, folder_id, file_name)
                st.success("¡Datos guardados en CDU.csv con éxito!")
            except Exception as e:
                st.error(f"Error al guardar en CDU.csv: {str(e)}")
