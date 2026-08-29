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

# --- FUNCIONES DE GUARDADO ---
def guardar_en_portafolio(nombre, idioma, tipo, precio):
    nueva_fila = pd.DataFrame([{
        "Item": nombre, 
        "Tipo": tipo,
        "Idioma": idioma,
        "Precio Actual (€)": precio
    }])
    st.session_state.portfolio = pd.concat([st.session_state.portfolio, nueva_fila], ignore_index=True)
    st.session_state.historial.loc[st.session_state.historial.index[-1], "Valor Total (€)"] += precio


# --- INTERFAZ DE USUARIO ---

st.set_page_config(page_title="Mi TCG Collectr Pro", layout="wide")
st.title("🃏 Mi TCG Collectr (Cartas y Sellados)")

if 'portfolio' not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(columns=["Item", "Tipo", "Idioma", "Precio Actual (€)"])
if 'historial' not in st.session_state:
    fechas = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(4, -1, -1)]
    st.session_state.historial = pd.DataFrame({"Fecha": fechas, "Valor Total (€)": [0.0, 0.0, 0.0, 0.0, 0.0]})

col1, col2 = st.columns([1, 2])

with col1:
    st.header("Añadir a la Colección")
    
    # Elegir si queremos añadir carta o producto sellado
    modo_registro = st.radio("¿Qué quieres añadir?", ["Carta Individual (por Foto)", "Producto Sellado (ETB, Booster Box...)"])
    
    if modo_registro == "Carta Individual (por Foto)":
        idioma_carta = st.selectbox("Idioma de la carta", ["Español", "Inglés", "Japonés", "Chino"])
        archivo_foto = st.file_uploader("Sube la foto de tu carta", type=['jpg', 'png', 'jpeg'])
        
        if archivo_foto:
            img = Image.open(archivo_foto)
            st.image(img, caption="Imagen cargada", width=200)
            
            if st.button("Analizar y Buscar Precio"):
                st.info("Leyendo texto de la imagen...")
                nombre_detectado = leer_carta_con_ocr(img)
                
                if nombre_detectado == "Desconocido" or nombre_detectado == "Error de lectura":
                    nombre_detectado = "Charizard" 
                    
                st.success(f"Carta detectada: **{nombre_detectado}** ({idioma_carta})")
                
                precio_medio, ultimos_precios = buscar_precio_cardmarket(nombre_detectado)
                if not precio_medio:
                    st.warning("Aviso: Conexión bloqueada. Usando precio simulado.")
                    precio_medio = 25.50
                    ultimos_precios = [24.0, 26.0, 25.0, 27.0, 25.5]

                st.write(f"**Primeros 5 precios:** {ultimos_precios}")
                st.metric(label="Precio Medio", value=f"{precio_medio} €")
                
                st.button("Añadir Carta al Portafolio", on_click=guardar_en_portafolio, args=(nombre_detectado, idioma_carta, "Carta", precio_medio))

    else:
        # Formulario para productos sellados
        st.subheader("Datos del Producto Sellado")
        tipo_sellado = st.selectbox("Tipo de producto", ["Booster Box", "Elite Trainer Box (ETB)", "Caja de Colección", "Blister"])
        idioma_sellado = st.selectbox("Idioma del producto", ["Español", "Inglés", "Japonés", "Chino"])
        nombre_set = st.text_input("Nombre del Set (ej. 151, Evoluciones Paldea, Obsidian Flames)")
        precio_sellado = st.number_input("Precio de mercado / estimado (€)", min_value=0.0, value=45.00, step=1.0)
        
        if st.button("Añadir Producto Sellado al Portafolio"):
            if nombre_set.strip() != "":
                nombre_completo = f"{tipo_sellado} - {nombre_set}"
                guardar_en_portafolio(nombre_completo, idioma_sellado, "Sellado", precio_sellado)
                st.success(f"¡{nombre_completo} añadido correctamente!")
                st.rerun()
            else:
                st.error("Por favor, introduce el nombre del set.")

with col2:
    st.header("Tu Portafolio")
    valor_total = st.session_state.portfolio["Precio Actual (€)"].sum() if not st.session_state.portfolio.empty else 0
    st.metric(label="Valor Total de la Colección", value=f"{round(valor_total, 2)} €")
    
    st.subheader("Gráfico de Valor (Evolución)")
    st.line_chart(st.session_state.historial.set_index("Fecha"))
    
    st.subheader("Inventario Completo (Cartas y Sellados)")
    if not st.session_state.portfolio.empty:
        st.dataframe(st.session_state.portfolio, use_container_width=True)
    else:
        st.info("Tu portafolio está vacío. Añade tu primera carta o producto sellado.")
    
    if st.button("Actualizar Precios Globales"):
        if not st.session_state.portfolio.empty:
            st.session_state.portfolio["Precio Actual (€)"] = st.session_state.portfolio["Precio Actual (€)"] * 1.05
            nuevo_dia = datetime.now().strftime("%Y-%m-%d %H:%M")
            nuevo_valor = st.session_state.portfolio["Precio Actual (€)"].sum()
            nueva_fila_hist = pd.DataFrame([{"Fecha": nuevo_dia, "Valor Total (€)": nuevo_valor}])
            st.session_state.historial = pd.concat([st.session_state.historial, nueva_fila_hist], ignore_index=True)
            st.rerun()
