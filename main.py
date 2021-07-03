import streamlit as st
from PIL import Image
import src.manage_data as dat
import plotly.express as px
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import base64

st.set_page_config(page_title="mpx", page_icon="🎸", layout='centered', initial_sidebar_state='auto')

imagen = Image.open("musicopolix.jpg")
st.image(imagen)

m = pd.read_csv("Marcas.csv")
recordatorio = st.button('RECORDATORIO!')
if recordatorio:
    st.write("Para pasar un CSV a Excel: 1. Abrir con excel 2. Seleccionar la primera columna 3. Datos 4. Texto en columnas 5. Delimitados ")
    st.write("Antes de subir los CSVs de PRODUCTOS (columna H) y MOVIMIENTOS (columna L) tienes que borrar la primera columna en blanco del excel")
    st.write("El CSV de MARCAS tiene que tener el siguiente formato: ")
    st.write(m)
productos = st.file_uploader("Sube el CSV de PRODUCTOS")

if productos: 
    df_p = dat.limpiar_productos(productos)
    st.success("CSV subido correctamente")
    movimientos = st.file_uploader("Sube el CSV de MOVIMIENTOS")
    if movimientos: 
        df_m = dat.limpiar_movimientos(movimientos)
        st.success("CSV subido correctamente")
        marca = st.file_uploader("Sube el CSV de MARCAS")
        if marca:
            marcas = pd.read_csv(marca)
            st.success("CSV subido correctamente")
            fecha = st.date_input("¿Desde que fecha quieres el análisis?")
            boton_1 = st.button('Da clic para descargarte el excel')
            if boton_1:
                df_final = dat.devuelve_excel(df_m,df_p,fecha,marcas)
                csv = df_final.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()  # some strings
                linko= f'<a href="data:file/csv;base64,{b64}" download="myfilename.csv">Descárgate aquí el excel</a>'
                st.markdown(linko, unsafe_allow_html=True)
                st.write(df_final)
            boton_2 = st.button('Da clic para ver algunos gráficos')
            if boton_2:
                df_final = dat.devuelve_excel(df_m,df_p,fecha,marcas)
                df_final_marcas_frecuentes = dat.marcas_freq(df_final)
                fig, ax = plt.subplots(figsize=(15, 8))
                marcas = sns.countplot(data=df_final_marcas_frecuentes, x = "MARCA", palette = "pastel")
                ax.set_title("Marcas más frecuentemente vendidas")
                plt.xticks(rotation=90)
                plt.grid()
                st.pyplot(fig)
                df_final_marcas_no_frecuentes = dat.marcas_freq(df_final)
                df_final_marcas_no_frecuentes = dat.marcas_no_freq(df_final)
                fig, ax = plt.subplots(figsize=(15, 8))
                marcas = sns.countplot(data=df_final_marcas_no_frecuentes, x = "MARCA", palette = "pastel")
                ax.set_title("Marcas menos frecuentemente vendidas")
                plt.xticks(rotation=90)  
                plt.grid()   
                st.pyplot(fig)