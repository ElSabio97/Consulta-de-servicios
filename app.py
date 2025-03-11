import streamlit as st
from functions import process_html_table, update_csv_in_drive, download_csv_from_drive, generate_pdf, generate_filtered_pdf, update_cdu_csv, get_drive_service
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Progra Pedrito", page_icon="✈️")

# Título y descripción
st.title("¿Qué está haciendo Pedrito?")
st.write("Descarga la progra que quieras seleccionando el mes")

# Selector de mes y generación de PDFs
st.subheader("Descargar programación")
meses = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]
mes_actual = meses[datetime.now().month - 1]  # Mes actual (0-based index)
mes_seleccionado = st.selectbox("Selecciona un mes", meses, index=meses.index(mes_actual))
anio_seleccionado = st.number_input("Selecciona un año", min_value=2020, max_value=2030, value=datetime.now().year)

# Botón para el PDF detallado
if st.button("Generar progra detallada"):
    try:
        folder_id = '1B8gnCmbBaGMBT77ba4ntjpZj_NkJcvuI'
        file_name = 'Consulta_de_servicios.csv'
        service = get_drive_service()
        df = download_csv_from_drive(service, folder_id, file_name)
        
        if df is None:
            st.error("No se encontró el archivo CSV en Google Drive.")
        else:
            mes_num = meses.index(mes_seleccionado) + 1
            pdf_buffer = generate_pdf(df, mes_num, anio_seleccionado, mes_seleccionado)
            st.download_button(
                label="Descargar progra",
                data=pdf_buffer,
                file_name=f"Programa_{mes_seleccionado}_{anio_seleccionado}.pdf",
                mime="application/pdf"
            )
    except Exception as e:
        st.error(f"Error al generar el PDF: {str(e)}")

# Botón para el PDF sencillo (CO) y preparación para cálculo de horas
if st.button("Generar progra sencilla"):
    try:
        folder_id = '1B8gnCmbBaGMBT77ba4ntjpZj_NkJcvuI'
        file_name = 'Consulta_de_servicios.csv'
        service = get_drive_service()
        df = download_csv_from_drive(service, folder_id, file_name)
        
        if df is None:
            st.error("No se encontró el archivo CSV en Google Drive.")
        else:
            mes_num = meses.index(mes_seleccionado) + 1
            pdf_buffer = generate_filtered_pdf(df, mes_num, anio_seleccionado, mes_seleccionado)
            st.download_button(
                label="Descargar progra",
                data=pdf_buffer,
                file_name=f"Programa_CO_{mes_seleccionado}_{anio_seleccionado}.pdf",
                mime="application/pdf"
            )
            # Filtrar el DataFrame y guardarlo en session_state
            df['parsed_date'] = df['Inicio'].apply(lambda x: datetime.strptime(str(x).replace(" (LT)", "").strip(), "%d/%m/%Y %H:%M"))
            df_filtered = df[
                (df['parsed_date'].dt.month == mes_num) & 
                (df['parsed_date'].dt.year == anio_seleccionado) & 
                (df['Servicio'].str.contains("CO", case=False, na=False))
            ]
            st.session_state['df_filtered'] = df_filtered
            st.session_state['progra_sencilla_generada'] = True  # Bandera para mostrar el botón
            st.success("Programa sencilla generada. Ahora puedes calcular las horas de vuelo.")
            st.write(f"Filas en df_filtered: {len(df_filtered)}")  # Depuración
    except Exception as e:
        st.error(f"Error al generar el PDF filtrado: {str(e)}")
        st.session_state['progra_sencilla_generada'] = False  # Asegurar que no se muestre el botón si hay error

# Botón para calcular las horas de vuelo
if st.session_state.get('progra_sencilla_generada', False):
    if st.button("Calcular horas de vuelo"):
        try:
            df_filtered = st.session_state['df_filtered']
            st.write(f"Datos cargados para cálculo: {len(df_filtered)} filas")  # Depuración
            
            # Asegurarse de que las columnas 'Inicio' y 'Fin' estén en formato datetime
            df_filtered['inicio_dt'] = df_filtered['Inicio'].apply(lambda x: datetime.strptime(str(x).replace(" (LT)", "").strip(), "%d/%m/%Y %H:%M"))
            df_filtered['fin_dt'] = df_filtered['Fin'].apply(lambda x: datetime.strptime(str(x).replace(" (LT)", "").strip(), "%d/%m/%Y %H:%M"))
            
            # Calcular la diferencia de tiempo en horas para cada vuelo
            df_filtered['horas_vuelo'] = (df_filtered['fin_dt'] - df_filtered['inicio_dt']).dt.total_seconds() / 3600
            
            # Sumar todas las horas de vuelo
            total_horas = df_filtered['horas_vuelo'].sum()
            
            # Mostrar el resultado
            st.write(f"Total de horas de vuelo para {mes_seleccionado} {anio_seleccionado}: **{total_horas:.2f} horas**")
        except Exception as e:
            st.error(f"Error al calcular las horas de vuelo: {str(e)}")
else:
    st.write("Primero genera la progra sencilla para calcular las horas de vuelo.")  # Mensaje aclaratorio

# Botón para abrir el formulario de CDU
st.subheader("Cosas mías")
with st.expander("Añadir entrada desde CDU", expanded=False):
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
                st.write("Datos enviados:", data)
                update_cdu_csv(data, folder_id, file_name)
                st.success("¡Datos guardados en CDU.csv con éxito!")
            except Exception as e:
                st.error(f"Error al guardar en CDU.csv: {str(e)}")

# Sección de actualizar CSV (apartada y colapsada)
with st.expander("Actualizar CSV (Admin)", expanded=False):
    st.write("Copia la tabla HTML al portapapeles y haz clic en 'Actualizar CSV'.")
    if st.button("Actualizar CSV"):
        html_input = st.text_input("Pega aquí (Ctrl+V)", value="", key="clipboard_input", label_visibility="collapsed")
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
            st.warning("Por favor, pega la tabla HTML (Ctrl+V) después de hacer clic en el botón.")
