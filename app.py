import streamlit as st
from functions import process_html_table, update_csv_in_drive

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
            # Procesar la tabla HTML y convertirla a CSV
            csv_data = process_html_table(html_input)
            
            # Actualizar el archivo en Google Drive
            folder_id = '1B8gnCmbBaGMBT77ba4ntjpZj_NkJcvuI'
            file_name = 'Consulta_de_servicios.csv'
            update_csv_in_drive(csv_data, folder_id, file_name)
            
            st.success("¡Archivo CSV actualizado en Google Drive con éxito!")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.warning("Por favor, pega una tabla HTML antes de actualizar.")