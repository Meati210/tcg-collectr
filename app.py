import streamlit as st
import pandas as pd
import pytesseract
from PIL import Image
from datetime import datetime, timedelta
import requests
import re

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
    """Busca en la API barriendo múltiples resultados (hasta 50) para encontrar una versión con precio real."""
    try:
        # Extraer números si los hay (ej: "109" de "Charizard 109")
        numeros = re.findall(r'\b\d+\b', nombre_carta)
        # Limpiar el nombre quitando los números para la consulta general
        nombre_limpio = re.sub(r'\b\d+\b', '', nombre_carta).strip()
        
        nombre_lower = nombre_limpio.lower()
        if "charizard" in nombre_lower:
            query_name = "Charizard"
        else:
            palabras = [p for p in nombre_limpio.replace('-', ' ').split() if len(p) > 2]
            query_name = palabras[0] if palabras else nombre_limpio
            
        query = f"name:{query_name}"
        if numeros:
            query += f" number:{numeros[0]}"
            
        # Solicitamos hasta 50 resultados para encontrar una carta con precio válido
        url = f"https://api.pokemontcg.io/v2/cards?q={query}&pageSize=50"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json().get("data", [])
            if not data and numeros:
                # Si con el número exacto no hay resultados, probamos solo con el nombre
                url = f"https://api.pokemontcg.io/v2/cards?q=name:{query_name}&pageSize=50"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json().get("data", [])
                    
            if data:
                # Recorremos todas las cartas encontradas hasta hallar una con precio de mercado
                for carta in data:
                    precios = carta.get("tcgplayer", {}).get("prices", {})
                    for tipo in ["holofoil", "normal", "reverseHolofoil", "1stEditionHolofoil"]:
                        if tipo in precios:
                            market_price = precios[tipo].get("market")
                            if market_price:
                                return float(market_price)
        return None
    except Exception:
        return None

def guardar_en_portafolio(nombre, idioma, tipo, precio_usuario, precio_ingles_ref):
    factor = (precio_usuario / precio_ingles_ref) if precio_ingles_ref > 0 else 1.0
    
    nueva_fila = pd.DataFrame([{
        "Item": nombre, 
        "Tipo": tipo,
        "Idioma": idioma,
        "Precio Inglés Ref (€)": float(precio_ingles_ref),
        "Precio Actual (€)": float(precio_usuario),
        "Factor Proporción": float(factor)
    }])
    st.session_state.portfolio = pd.concat([st.session_state.portfolio, nueva_fila], ignore_index=True)
    total_actual = st.session_state.portfolio["Precio Actual (€)"].sum()
    st.session_state.historial.loc[st.session_state.historial.index[-1], "Valor Total (€)"] = total_actual


# --- INTERFAZ DE USUARIO ---

st.set_page_config(page_title="Mi TCG Collectr Pro", layout="wide")
st.title("🃏 Mi TCG Collectr (Búsqueda Avanzada y Proporcional)")

if 'portfolio' not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(columns=["Item", "Tipo", "Idioma", "Precio Inglés Ref (€)", "Precio Actual (€)", "Factor Proporción"])
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
            
            nombre_sugerido_ocr = leer_carta_con_ocr(img)
            st.info("💡 Consejo: Puedes escribir el nombre y su número (ej: 'Charizard 109') para afinar la búsqueda:")
            nombre_carta_input = st.text_input("Nombre de la carta:", value=nombre_sugerido_ocr)
            
            url_verificacion = f"https://www.google.com/search?q=pokemon+card+{nombre_carta_input.replace(' ' , '+')}"
            st.markdown(f"🔗 **[Verificar carta en Google]({url_verificacion})**", unsafe_allow_html=True)
            
            if st.button("Consultar Precio en la API"):
                st.info(f"🔍 Buscando entre las diferentes ediciones para: **{nombre_carta_input}**...")
                precio_ingles = obtener_precio_real(nombre_carta_input)
                
                if precio_ingles:
                    st.success(f"✅ Precio de referencia encontrado: **{precio_ingles} €**")
                else:
                    precio_ingles = 25.50
                    st.warning("⚠️ No se halló precio automático para esta variante. Usando referencia estándar de 25.50 €.")

                if idioma_carta == "Español":
                    st.warning("⚠️ Versión en español seleccionada. Puedes ajustar abajo el precio inicial a tu gusto.")

                st.session_state.temp_precio_ingles = precio_ingles
                st.session_state.temp_nombre = nombre_carta_input

            if 'temp_precio_ingles' in st.session_state:
                precio_usuario_inicial = st.number_input(
                    "Precio inicial (€) para tu inventario:", 
                    min_value=0.0, 
                    value=float(st.session_state.temp_precio_ingles), 
                    step=0.5
                )
                
                if st.button("Confirmar y Guardar en Portafolio"):
                    guardar_en_portafolio(
                        st.session_state.temp_nombre, 
                        idioma_carta, 
                        "Carta", 
                        precio_usuario_inicial, 
                        st.session_state.temp_precio_ingles
                    )
                    st.success("¡Carta guardada con éxito!")
                    del st.session_state.temp_precio_ingles
                    st.rerun()

    else:
        st.subheader("Producto Sellado")
        tipo_sellado = st.selectbox("Tipo de producto", ["Booster Box", "Elite Trainer Box (ETB)", "Caja de Colección", "Blister"])
        idioma_sellado = st.selectbox("Idioma", ["Inglés", "Español", "Japonés", "Chino"])
        nombre_set = st.text_input("Nombre del Set (ej. 151, Evoluciones Paldea)")
        
        precio_base_sellado = 45.00
        if idioma_sellado == "Español":
            st.warning("⚠️ Referencia de precio basada en versión en inglés.")
            
        precio_sellado_usuario = st.number_input("Precio inicial (€)", min_value=0.0, value=precio_base_sellado, step=1.0)
        
        if st.button("Añadir Producto Sellado"):
            if nombre_set.strip() != "":
                nombre_completo = f"{tipo_sellado} - {nombre_set}"
                guardar_en_portafolio(nombre_completo, idioma_sellado, "Sellado", precio_sellado_usuario, precio_base_sellado)
                st.success("¡Producto sellado añadido correctamente!")
                st.rerun()
            else:
                st.error("Por favor, introduce el nombre del set.")

with col2:
    st.header("Tu Portafolio Dinámico")
    
    st.subheader("Inventario (Edita el 'Precio Actual' cuando quieras)")
    
    if not st.session_state.portfolio.empty:
        edited_df = st.data_editor(
            st.session_state.portfolio, 
            num_rows="dynamic",
            key="portfolio_editor",
            use_container_width=True
        )
        
        for i in range(len(edited_df)):
            p_actual = edited_df.loc[i, "Precio Actual (€)"]
            p_ingles = edited_df.loc[i, "Precio Inglés Ref (€)"]
            if p_ingles > 0:
                edited_df.loc[i, "Factor Proporción"] = p_actual / p_ingles
                
        st.session_state.portfolio = edited_df
        
        if st.button("🔄 Actualizar Precios desde la API (Real y Proporcional)"):
            actualizados = 0
            for i, row in st.session_state.portfolio.iterrows():
                if row["Tipo"] == "Carta":
                    nuevo_ref = obtener_precio_real(row["Item"])
                    if nuevo_ref:
                        st.session_state.portfolio.loc[i, "Precio Inglés Ref (€)"] = float(nuevo_ref)
                        factor = row["Factor Proporción"]
                        st.session_state.portfolio.loc[i, "Precio Actual (€)"] = round(float(nuevo_ref) * factor, 2)
                        actualizados += 1
            
            st.success(f"¡Se actualizó el mercado para {actualizados} cartas de forma proporcional!")
            
            nuevo_dia = datetime.now().strftime("%Y-%m-%d %H:%M")
            nuevo_valor = st.session_state.portfolio["Precio Actual (€)"].sum()
            nueva_fila_hist = pd.DataFrame([{"Fecha": nuevo_dia, "Valor Total (€)": nuevo_valor}])
            st.session_state.historial = pd.concat([st.session_state.historial, nueva_fila_hist], ignore_index=True)
            st.rerun()
            
    else:
        st.info("Tu portafolio está vacío. Añade cartas o productos a la izquierda.")

    valor_total = st.session_state.portfolio["Precio Actual (€)"].sum() if not st.session_state.portfolio.empty else 0
    st.metric(label="Valor Total de la Colección", value=f"{round(valor_total, 2)} €")
    
    st.subheader("Gráfico de Valor (Evolución)")
    st.line_chart(st.session_state.historial.set_index("Fecha"))
