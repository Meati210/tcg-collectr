import streamlit as st
import pandas as pd
import pytesseract
from PIL import Image, ImageEnhance
from datetime import datetime, timedelta
import requests
import re

# --- FUNCIONES PRINCIPALES ---

def leer_carta_con_ocr(imagen):
    try:
        img_proc = imagen.convert('L')
        w, h = img_proc.size
        img_proc = img_proc.resize((w * 2, h * 2), Image.Resampling.LANCZOS)
        enhancer = ImageEnhance.Contrast(img_proc)
        img_proc = enhancer.enhance(2.0)
        
        texto = ""
        for lang in ['chi_sim+eng+jpn+spa', 'chi_sim+eng', 'eng']:
            try:
                texto = pytesseract.image_to_string(img_proc, lang=lang)
                if texto.strip(): break
            except: continue
                
        palabras = texto.split()
        nombre_estimado = "Charizard"
        for palabra in palabras:
            if len(palabra) > 3:
                nombre_estimado = palabra
                break
        return nombre_estimado
    except Exception:
        return "Charizard"

def leer_producto_sellado_ocr(imagen):
    texto_extraido = ""
    try:
        img_rgb = imagen.convert('RGB')
        w, h = img_rgb.size
        
        img_proc = img_rgb.resize((w * 2, h * 2), Image.Resampling.LANCZOS).convert('L')
        enhancer = ImageEnhance.Contrast(img_proc)
        img_proc = enhancer.enhance(1.5) 
        config_custom = r'--oem 3 --psm 11'
        
        for lang in ['spa+eng+chi_sim', 'spa', 'eng']:
            try:
                texto = pytesseract.image_to_string(img_proc, lang=lang, config=config_custom)
                if texto.strip():
                    texto_extraido += " " + texto
            except:
                continue
                
        if not texto_extraido.strip():
            return "", "El OCR no vio letras claras."
            
        texto_lower = texto_extraido.lower()
        texto_clean = re.sub(r'\s+', '', texto_lower)
        
        # Diccionario exhaustivo global (Megaevolución, Scarlet & Violet, Sword & Shield, Sun & Moon)
        sets_conocidos = {
            # Bloque Megaevolución & Novedades
            "fuegos": "Lote de Sobres - Fuegos Fantasmales", "fantasmal": "Lote de Sobres - Fuegos Fantasmales", "phantasmal": "Lote de Sobres - Fuegos Fantasmales",
            "ascended": "Ascended Heroes", "heroes": "Ascended Heroes",
            "perfect": "Perfect Order", "orden": "Perfect Order",
            "chaos": "Chaos Rising", "caos": "Chaos Rising",
            "pitch": "Pitch Black", "darkrai": "Pitch Black",
            "celebration": "30th Celebration", "30th": "30th Celebration",
            "delta": "Delta Reign", "rayquaza": "Delta Reign",
            
            # Scarlet & Violet / Escarlata y Púrpura
            "prismatic": "Prismatic Evolutions", "prismaticas": "Prismatic Evolutions", "pre": "Prismatic Evolutions",
            "surging": "Surging Sparks", "chispas": "Surging Sparks", "ssp": "Surging Sparks",
            "stellar": "Stellar Crown", "corona": "Stellar Crown", "scr": "Stellar Crown",
            "shrouded": "Shrouded Fable", "fabulas": "Shrouded Fable", "sfa": "Shrouded Fable",
            "twilight": "Twilight Masquerade", "mascarada": "Twilight Masquerade", "twm": "Twilight Masquerade",
            "temporal": "Temporal Forces", "fuerzas": "Temporal Forces", "tef": "Temporal Forces",
            "paradox": "Paradox Rift", "brechas": "Paradox Rift", "par": "Paradox Rift",
            "obsidian": "Obsidian Flames", "llamas": "Obsidian Flames", "obf": "Obsidian Flames",
            "paldea": "Paldea Evolved", "pal": "Paldea Evolved",
            "scarlet": "Scarlet & Violet Base", "svi": "Scarlet & Violet Base",
            "151": "Pokémon 151", "mew": "Pokémon 151", "sv2a": "Pokémon 151",
            
            # Set Chino específico
            "csv10": "CSV10C - 共逐荣光", "c5v10": "CSV10C - 共逐荣光", "共逐荣光": "CSV10C - 共逐荣光",
            
            # Sword & Shield / Espada y Escudo
            "evs": "Evolving Skies", "cielos": "Evolving Skies",
            "brs": "Brilliant Stars", "astros": "Brilliant Stars",
            "lor": "Lost Origin", "origen": "Lost Origin",
            "crz": "Crown Zenith", "cenit": "Crown Zenith",
            "cel": "Celebrations",
            "ssh": "Sword & Shield Base", "rcl": "Rebel Clash",
            "daa": "Darkness Ablaze", "viv": "Vivid Voltage",
            "bst": "Battle Styles", "cre": "Chilling Reign",
            "fst": "Fusion Strike", "asr": "Astral Radiance",
            "sit": "Silver Tempest",
            
            # Sun & Moon / Sol y Luna
            "sum": "Sun & Moon Base", "gri": "Guardians Rising",
            "bus": "Burning Shadows", "cin": "Crimson Invasion",
            "upr": "Ultra Prism", "fli": "Forbidden Light",
            "ces": "Celestial Storm", "lot": "Lost Thunder",
            "teu": "Team Up", "unb": "Unbroken Bonds",
            "unm": "Unified Minds", "cec": "Cosmic Eclipse"
        }
        
        for clave, nombre_set in sets_conocidos.items():
            if clave in texto_lower or clave in texto_clean:
                return nombre_set, texto_extraido

        match_sv = re.search(r'(sv\s*\d+[a-z]?)', texto_extraido, re.IGNORECASE)
        if match_sv:
            return match_sv.group(1).replace(" ", "").upper(), texto_extraido

        return "", texto_extraido
        
    except Exception as e:
        return "", f"Error crítico al procesar: {str(e)}"

def obtener_precio_real(nombre_carta):
    try:
        numeros = re.findall(r'\b\d+\b', nombre_carta)
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
            
        url = f"https://api.pokemontcg.io/v2/cards?q={query}&pageSize=50"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json().get("data", [])
            if not data and numeros:
                url = f"https://api.pokemontcg.io/v2/cards?q=name:{query_name}&pageSize=50"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json().get("data", [])
                    
            if data:
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
        "Item": nombre, "Tipo": tipo, "Idioma": idioma,
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
if 'last_sealed_file' not in st.session_state:
    st.session_state.last_sealed_file = None
if 'auto_set_name' not in st.session_state:
    st.session_state.auto_set_name = ""

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
            
            url_cardmarket = f"https://www.cardmarket.com/en/Pokemon/Products/Search?searchString={nombre_carta_input.replace(' ' , '+')}"
            st.markdown(f"🔗 **[Entra en Cardmarket y selecciona el idioma para precio concreto en otros idiomas]({url_cardmarket})**", unsafe_allow_html=True)
            
            if st.button("Consultar Precio en la API"):
                st.info(f"🔍 Buscando entre las diferentes ediciones para: **{nombre_carta_input}**...")
                precio_ingles = obtener_precio_real(nombre_carta_input)
                
                if precio_ingles:
                    st.success(f"✅ Precio de referencia encontrado: **{precio_ingles} €**")
                else:
                    precio_ingles = 25.50
                    st.warning("⚠️ No se halló precio automático para esta variante. Usando referencia estándar de 25.50 €.")

                st.session_state.temp_precio_ingles = precio_ingles
                st.session_state.temp_nombre = nombre_carta_input

            if 'temp_precio_ingles' in st.session_state:
                precio_usuario_inicial = st.number_input(
                    "Precio inicial (€) para tu inventario:", 
                    min_value=0.0, value=float(st.session_state.temp_precio_ingles), step=0.5
                )
                
                if st.button("Confirmar y Guardar en Portafolio"):
                    guardar_en_portafolio(
                        st.session_state.temp_nombre, idioma_carta, "Carta", 
                        precio_usuario_inicial, st.session_state.temp_precio_ingles
                    )
                    st.success("¡Carta guardada con éxito!")
                    del st.session_state.temp_precio_ingles
                    st.rerun()

    else:
        st.subheader("Producto Sellado")
        
        archivo_foto_sellado = st.file_uploader("📷 Sube la foto del producto sellado", type=['jpg', 'png', 'jpeg'], key="foto_sellado")
        
        if archivo_foto_sellado is not None:
            if st.session_state.last_sealed_file != archivo_foto_sellado.name:
                st.session_state.last_sealed_file = archivo_foto_sellado.name
                img_sellado = Image.open(archivo_foto_sellado)
                
                with st.spinner("🤖 Leyendo imagen minuciosamente..."):
                    detectado, debug_text = leer_producto_sellado_ocr(img_sellado)
                    
                    if detectado:
                        st.session_state.auto_set_name = detectado
                        st.success(f"✨ ¡Detectado y autorellenado: **{detectado}**!")
                        with st.expander("🛠️ Ver qué leyó el robot (Diagnóstico)"):
                            st.text(debug_text)
                    else:
                        st.session_state.auto_set_name = ""
                        st.warning("⚠️ No se pudo leer automáticamente. Escribe el set manualmente abajo.")
                        with st.expander("🛠️ ¿Por qué falló? (Despliega para ver el diagnóstico)"):
                            if "not found" in debug_text.lower() or "is not installed" in debug_text.lower() or "tesseract is not" in debug_text.lower():
                                st.error("🚨 ¡FALTA TESSERACT! El servidor no tiene el lector instalado.")
                            else:
                                st.write("El bot extrajo esta información de la imagen:")
                                st.text(debug_text)
        else:
            st.session_state.last_sealed_file = None

        tipo_sellado = st.selectbox("Categoría", ["Booster Box", "Elite Trainer Box (ETB)", "Caja de Colección", "Blister", "Lote de Sobres", "Otros"])
        custom_producto = st.text_input("Especifica el producto:", value=st.session_state.auto_set_name) if tipo_sellado == "Otros" else ""
        idioma_sellado = st.selectbox("Idioma", ["Inglés", "Español", "Japonés", "Chino"])
        nombre_set = st.text_input("Nombre del Set o Colección", value=st.session_state.auto_set_name if tipo_sellado != "Otros" else "")
        
        precio_base_sellado = 45.00
        precio_sellado_usuario = st.number_input("Precio inicial / estimado (€):", min_value=0.0, value=precio_base_sellado, step=1.0)
        
        if st.button("Añadir Producto Sellado"):
            nombre_completo = f"{custom_producto} - {nombre_set}" if tipo_sellado == "Otros" else f"{tipo_sellado} - {nombre_set}"
            if nombre_set.strip() != "" or (tipo_sellado == "Otros" and custom_producto.strip() != ""):
                guardar_en_portafolio(nombre_completo, idioma_sellado, "Sellado", precio_sellado_usuario, precio_base_sellado)
                st.success("¡Producto sellado añadido correctamente!")
                st.rerun()
            else:
                st.error("Por favor, rellena los campos necesarios del producto.")

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
