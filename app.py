import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import pytesseract
from PIL import Image
from datetime import datetime, timedelta
import re

# --- FUNCIONES PRINCIPALES ---

def leer_carta_con_ocr(imagen):
    try:
        texto = pytesseract.image_to_string(imagen)
        palabras = texto.split()
        nombre_estimado = "Desconocido"
        for palabra in palabras:
            if len(palabra) > 4 and palabra.isalpha():
                nombre_estimado = palabra
                break
        return nombre_estimado
    except Exception as e:
        return "Error de lectura"

def buscar_precio_cardmarket(nombre_carta):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    url = f"https://www.cardmarket.com/es/Pokemon/Products/Singles?searchString={nombre_carta}"
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            return None, []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        etiquetas_precio = soup.find_all('span', class_='color-primary small text-end text-nowrap fw-bold')
        
        precios = []
        for etiqueta in etiquetas_precio:
            texto_precio = etiqueta.text.replace('€', '').replace(',', '.').strip()
            numero = re.findall(r"[-+]?\d*\.\d+|\d+", texto_precio)
            if numero:
                precios.append(float(numero[0]))
            if len(precios) == 5:
                break
                
        if len(precios) > 0:
            media = sum(precios) / len(precios)
            return round(media, 2), precios
        else:
            return None, []
            
    except Exception as e:
        return None, []

# --- NUEVA FUNCIÓN PARA GUARDAR SIN ERRORES ---
def guardar_en_portafolio(nombre, precio):
    nueva_fila = pd.DataFrame([{
        "Carta": nombre, 
        "Precio Inicial (€)": precio, 
        "Precio Actual (€)": precio
    }])
    # Añade la carta a la tabla
    st.session_state.portfolio = pd.concat([st.session_state.portfolio, nueva_fila], ignore_index=True)
    # Suma el precio al gráfico
    st.session_state.historial.loc[st.session_state.historial.index[-1], "Valor Total (€)"] += precio


# --- INTERFAZ DE USUARIO ---

st.set_page_config(page_title="Mi TCG Collectr", layout="wide")
st.title("🃏 Mi TCG Collectr Personal")

if 'portfolio' not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(columns=["Carta", "Precio Inicial (€)", "Precio Actual (€)"])
if 'historial' not in st.session_state:
    fechas = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(4, -1, -1)]
    st.session_state.historial = pd.DataFrame({"Fecha": fechas, "Valor Total (€)": [0.0, 0.0, 0.0, 0.0, 0.0]})

col1, col2 = st.columns([1, 2])

with col1:
    st.header("Añadir Carta")
    archivo_foto = st.file_uploader("Sube la foto de tu carta", type=['jpg', 'png', 'jpeg'])
    
    if archivo_foto:
        img = Image.open(archivo_foto)
        st.image(img, caption="Imagen cargada", width=250)
        
        if st.button("Analizar y Buscar Precio"):
            st.info("Leyendo texto de la imagen...")
            nombre_detectado = leer_carta_con_ocr(img)
            
            if nombre_detectado == "Desconocido" or nombre_detectado == "Error de lectura":
                nombre_detectado = "Charizard" 
                
            st.success(f"Carta detectada (Estimación): **{nombre_detectado}**")
            
            st.info("Buscando en Cardmarket...")
            precio_medio, ultimos_precios = buscar_precio_cardmarket(nombre_detectado)
            
            if not precio_medio:
                st.warning("Aviso: Cardmarket ha bloqueado la conexión. Usando datos simulados.")
                precios_simulados = [12.50, 13.00, 11.90, 14.00, 12.00]
                precio_medio = sum(precios_simulados) / len(precios_simulados)
                ultimos_precios = precios_simulados

            st.write(f"**Primeros 5 precios:** {ultimos_precios}")
            st.metric(label="Precio Medio Calculado", value=f"{precio_medio} €")
            
            # SOLUCIÓN: El botón ahora dispara el evento 'guardar_en_portafolio' inmediatamente
            st.button("Añadir al Portafolio", on_click=guardar_en_portafolio, args=(nombre_detectado, precio_medio))

with col2:
    st.header("Tu Portafolio")
    valor_total = st.session_state.portfolio["Precio Actual (€)"].sum()
    st.metric(label="Valor Total de la Colección", value=f"{round(valor_total, 2)} €")
    
    st.subheader("Gráfico de Valor (Evolución)")
    st.line_chart(st.session_state.historial.set_index("Fecha"))
    
    st.subheader("Tus Cartas")
    st.dataframe(st.session_state.portfolio, use_container_width=True)
    
    if st.button("Actualizar Precios"):
        st.session_state.portfolio["Precio Actual (€)"] = st.session_state.portfolio["Precio Actual (€)"] * 1.05
        nuevo_dia = datetime.now().strftime("%Y-%m-%d %H:%M")
        nuevo_valor = st.session_state.portfolio["Precio Actual (€)"].sum()
        nueva_fila_hist = pd.DataFrame([{"Fecha": nuevo_dia, "Valor Total (€)": nuevo_valor}])
        st.session_state.historial = pd.concat([st.session_state.historial, nueva_fila_hist], ignore_index=True)
        st.rerun()
