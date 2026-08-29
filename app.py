import streamlit as st
import pandas as pd
import pytesseract
from PIL import Image
from datetime import datetime, timedelta
import requests

# --- FUNCIONES PRINCIPALES ---

def leer_carta_con_ocr(imagen):
    try:
        texto = pytesseract.image_to_string(imagen)
        palabras = texto.split()
        nombre_estimado = "Charizard"
        for palabra in palabras:
            if len(palabra) > 4 and palabra.isalpha():
                nombre_estimado = palabra
                break
        return nombre_estimado
    except Exception as e:
        return "Charizard"

def obtener_precio_real(nombre_carta):
    """Consulta la API oficial de Pokémon TCG para obtener el precio real de mercado automáticamente."""
    try:
        url = f"https://api.pokemontcg.io/v2/cards?q=name:{nombre_carta}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json().get("data", [])
            if data:
                precios = data[0].get("tcgplayer", {}).get("prices", {})
                for tipo in ["holofoil", "normal", "reverseHolofoil", "1stEditionHolofoil"]:
                    if tipo in precios:
                        market_price = precios[tipo].get("market")
                        if market_price:
                            return float(market_price)
        return None
    except Exception:
        return None

def guardar_en_portafolio(nombre, idioma, tipo, precio):
    nueva_fila = pd.DataFrame([{
        "Item": nombre, 
        "Tipo": tipo,
        "Idioma": idioma,
        "Precio Base (€)": float(precio),
        "Precio Actual (€)": float(precio)
    }])
    st.session_state.portfolio = pd.concat([st.session_state.portfolio, nueva_fila], ignore_index=True)
    total_actual = st.session_state.portfolio["Precio Actual (€)"].sum()
    st.session_state.historial.loc[st.session_state.historial.index[-1], "Valor Total (€)"] = total_actual


# --- INTERFAZ DE USUARIO ---

st.set_page_config(page_title="Mi TCG Collectr Pro", layout="wide")
st.title("🃏 Mi TCG Collectr (Precios Reales Automáticos)")

if 'portfolio' not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(columns=["Item", "Tipo", "Idioma", "Precio Base (€)", "Precio Actual (€)"])
if 'historial' not in st.session_state:
    fechas = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(4, -1, -1)]
    st.session_state.historial = pd.DataFrame({"Fecha": fechas, "Valor Total (€)": [0.0, 0.0, 0.0, 0.0, 0.0]})

col1, col2 = st.columns([1, 2])

with col1:
    st.header("Añadir a la Colección")
    modo_registro = st.radio("¿Qué quieres añadir?", ["Carta Individual (por Foto)", "Producto Sellado"])
    
    if modo_registro == "Carta Individual (por Foto)":
        idioma_carta = st.selectbox("Idioma de la carta", ["Inglés", "Español", "Japonés", "Chino"])
        archivo_foto = st.file_uploader("Sube la foto de tu carta", type=['jpg', 'png', 'jpeg'])
        
        if archivo_foto:
            img = Image.open(archivo_foto)
            st.image(img, caption="Imagen cargada", width=200)
            
            # Detección y consulta de precio real en la API
            nombre_detectado = leer_carta_con_ocr(img)
            st.info(f"🔍 Consultando precio real de mercado para: **{nombre_detectado}**...")
            
            precio_real = obtener_precio_real(nombre_detectado)
            
            if precio_real:
                st.success(f"✅ ¡Precio real encontrado en la API: **{precio_real} €**!")
                precio_sugerido = precio_real
            else:
                st.warning("⚠️ No se encontró precio automático exacto. Usando valor de referencia.")
                precio_sugerido = 25.50

            if idioma_carta == "Español":
                st.warning("⚠️ Aviso: El mercado internacional puede variar para versiones en español.")
            elif idioma_carta in ["Japonés", "Chino"]:
                st.warning("⚠️ Aviso: Versión asiática detectada.")

            precio_usuario = st.number_input("Precio inicial (€):", min_value=0.0, value=float(precio_sugerido), step=0.5)
            
            if st.button("Confirmar y Guardar en Portafolio"):
                guardar_en_portafolio(nombre_detectado, idioma_carta, "Carta", precio_usuario)
                st.success("¡Carta guardada con éxito!")
                st.rerun()

    else:
        st.subheader("Producto Sellado")
        tipo_sellado = st.selectbox("Tipo de producto", ["Booster Box", "Elite Trainer Box (ETB)", "Caja de Colección", "Blister"])
        idioma_sellado = st.selectbox("Idioma", ["Inglés", "Español", "Japonés", "Chino"])
        nombre_set = st.text_input("Nombre del Set (ej. 151, Evoluciones Paldea)")
        
        precio_base_sellado = 45.00
        if idioma_sellado == "Español":
            st.warning("⚠️ Aviso: Referencia de precio basada en versión en inglés.")
            
        precio_sellado_usuario = st.number_input("Precio inicial (€)", min_value=0.0, value=precio_base_sellado, step=1.0)
        
        if st.button("Añadir Producto Sellado"):
            if nombre_set.strip() != "":
                nombre_completo = f"{tipo_sellado} - {nombre_set}"
                guardar_en_portafolio(nombre_completo, idioma_sellado, "Sellado", precio_sellado_usuario)
                st.success("¡Producto sellado añadido correctamente!")
                st.rerun()
            else:
                st.error("Por favor, introduce el nombre del set.")

with col2:
    st.header("Tu Portafolio Dinámico")
    
    st.subheader("Inventario (Puedes editar el 'Precio Actual' haciendo clic)")
    
    if not st.session_state.portfolio.empty:
        edited_df = st.data_editor(
            st.session_state.portfolio, 
            num_rows="dynamic",
            key="portfolio_editor",
            use_container_width=True
        )
        st.session_state.portfolio = edited_df
        
        # Botón para restaurar si te equivocas editando
        if st.button("🔄 Restaurar Precios Base (Deshacer cambios manuales)"):
            st.session_state.portfolio["Precio Actual (€)"] = st.session_state.portfolio["Precio Base (€)"]
            st.success("¡Precios restablecidos a su valor base original!")
            st.rerun()
    else:
        st.info("Tu portafolio está vacío. Añade cartas o productos a la izquierda.")

    valor_total = st.session_state.portfolio["Precio Actual (€)"].sum() if not st.session_state.portfolio.empty else 0
    st.metric(label="Valor Total de la Colección", value=f"{round(valor_total, 2)} €")
    
    st.subheader("Gráfico de Valor (Evolución)")
    st.line_chart(st.session_state.historial.set_index("Fecha"))
