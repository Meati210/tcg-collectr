import streamlit as st
import pandas as pd
import pytesseract
from PIL import Image, ImageEnhance
from datetime import datetime, timedelta
import requests
import re
import difflib

# --- DICCIONARIO MAESTRO AMPLIADO (ESPAÑOL, INGLÉS, JAPONÉS Y CHINO) ---
TRADUCCION_SETS_COMPLETO = {
    # --- BLOQUE MEGA EVOLUTION / RECIENTES ---
    "30th celebration": "30th Celebration",
    "30th celebration premium deck set": "30th Celebration Premium Deck Set: Espeon & Umbreon",
    "eevee ex starter set": "Eevee ex Starter Set ex",
    "sprigatito & meowscarada": "Sprigatito & Meowscarada ex Starter Set ex",
    "storm emeralda": "Storm Emeralda",
    "zorua & zoroark": "Zorua & Zoroark ex Starter Set ex",
    "m6a": "30th Celebration",
    "mf": "30th Celebration Premium Deck Set: Espeon & Umbreon",
    "mee": "Eevee ex Starter Set ex",
    "mem": "Sprigatito & Meowscarada ex Starter Set ex",
    "m6": "Storm Emeralda",
    "mez": "Zorua & Zoroark ex Starter Set ex",

    # --- BLOQUE SCARLET & VIOLET / ESCARLATA Y PÚRPURA ---
    "fuegos fantasmales": "Phantasmal Flames",
    "prismáticas": "Prismatic Evolutions",
    "chispas vertiginosas": "Surging Sparks",
    "corona estelar": "Stellar Crown",
    "fábulas sombrías": "Shrouded Fable",
    "mascarada crepuscular": "Twilight Masquerade",
    "fuerzas temporales": "Temporal Forces",
    "brechas paradox": "Paradox Rift",
    "llamas obsidianas": "Obsidian Flames",
    "evoluciones en paldea": "Paldea Evolved",
    "escarlata y púrpura": "Scarlet & Violet",
    "151": "Pokémon 151",
    # Códigos Japón / Asia SV
    "sv1s": "Scarlet ex",
    "sv1v": "Violet ex",
    "sv2a": "Pokémon 151",
    "sv2p": "Snow Hazard",
    "sv2d": "Clay Burst",
    "sv3": "Ruler of the Black Flame",
    "sv3a": "Raging Surf",
    "sv4k": "Ancient Roar",
    "sv4m": "Future Flash",
    "sv4a": "Shiny Treasure ex",
    "sv5k": "Wild Force",
    "sv5m": "Cyber Judge",
    "sv5a": "Crimson Haze",
    "sv6": "Mask of Change",
    "sv6a": "Night Wanderer",
    "sv7": "Stellar Miracle",
    "sv8": "Super Electric Breaker",

    # --- BLOQUE SWORD & SHIELD / ESPADA Y ESCUDO ---
    "tempestad plateada": "Silver Tempest",
    "origen perdido": "Lost Origin",
    "resplandor astral": "Astral Radiance",
    "astros brillantes": "Brilliant Stars",
    "golpe furioso": "Fusion Strike",
    "cielos evolutivos": "Evolving Skies",
    "reino escalofriante": "Chilling Reign",
    "estilos de combate": "Battle Styles",
    "voltaje vívido": "Vivid Voltage",
    "oscuridad incandescente": "Darkness Ablaze",
    "choque rebelde": "Rebel Clash",
    "espada y escudo": "Sword & Shield",
    "zenit supremo": "Crown Zenith",
    "celebraciones": "Celebrations",
    # Códigos Japón SWSH
    "s1w": "Sword",
    "s1h": "Shield",
    "s2": "Rebellion Crash",
    "s3": "Infinity Zone",
    "s4": "Amazing Volt Tackle",
    "s5i": "Single Strike Master",
    "s5r": "Rapid Strike Master",
    "s6": "Jet-Black Spirit",
    "s6h": "Silver Lance",
    "s7r": "Skyscraping Perfection",
    "s7d": "Blue Sky Stream",
    "s8": "Fusion Arts",
    "s8b": "VMAX Climax",
    "s9": "Star Birth",
    "s9a": "Battle Region",
    "s10p": "Space Juggler",
    "s10d": "Time Gazer",
    "s10a": "Dark Phantasma",
    "s11": "Lost Abyss",
    "s11a": "Incandescent Arcana",
    "s12": "Paradigm Trigger",
    "s12a": "VSTAR Universe",

    # --- BLOQUE SUN & MOON / SOL Y LUNA ---
    "eclipse cósmico": "Cosmic Eclipse",
    "mentes unificadas": "Unified Minds",
    "vínculos indelebles": "Unbroken Bonds",
    "unión de amigos": "Team Up",
    "trueno perdido": "Lost Thunder",
    "tormenta celestial": "Celestial Storm",
    "luz prohibida": "Forbidden Light",
    "ultraprisma": "Ultra Prism",
    "sombras ardientes": "Burning Shadows",
    "guardianes nacientes": "Guardians Rising",
    "sol y luna": "Sun & Moon"
}

def normalizar_set_para_cm(nombre_set):
    """Traduce y busca coincidencias exactas y parciales para Cardmarket"""
    set_lower = nombre_set.lower().strip()
    if set_lower in TRADUCCION_SETS_COMPLETO:
        return TRADUCCION_SETS_COMPLETO[set_lower]
    
    for clave, valor in TRADUCCION_SETS_COMPLETO.items():
        if clave in set_lower:
            return valor
            
    if "/" in nombre_set:
        return nombre_set.split("/")[-1].strip()
    return nombre_set

# --- FUNCIONES DE LECTURA ÓPTICA (OCR) ---

def leer_carta_con_ocr(imagen):
    try:
        img_proc = imagen.convert('L')
        w, h = img_proc.size
        img_proc = img_proc.resize((w * 2, h * 2), Image.Resampling.LANCZOS)
        enhancer = ImageEnhance.Contrast(img_proc)
        img_proc = enhancer.enhance(2.0)
        
        texto = ""
        for lang in ['spa+eng+jpn+chi_sim']:
            try:
                texto = pytesseract.image_to_string(img_proc, lang=lang)
                if texto.strip(): break
            except: continue
                
        palabras = texto.split()
        nombre_estimado = "Pikachu"
        for palabra in palabras:
            if len(palabra) > 2:
                nombre_estimado = palabra
                break
        return nombre_estimado
    except Exception:
        return "Pikachu"

def leer_producto_sellado_ocr(imagen):
    texto_extraido = ""
    try:
        img_rgb = imagen.convert('RGB')
        w, h = img_rgb.size
        
        img_proc = img_rgb.resize((w * 2, h * 2), Image.Resampling.LANCZOS).convert('L')
        enhancer = ImageEnhance.Contrast(img_proc)
        img_proc = enhancer.enhance(1.8) 
        config_custom = r'--oem 3 --psm 11'
        
        for lang in ['spa+eng+jpn+chi_sim', 'spa', 'eng', 'jpn']:
            try:
                texto = pytesseract.image_to_string(img_proc, lang=lang, config=config_custom)
                if texto.strip():
                    texto_extraido += " " + texto
            except:
                continue
                
        texto_lower = texto_extraido.lower()
        
        # Búsqueda en el diccionario maestro por nombre clave o código
        for clave, valor in TRADUCCION_SETS_COMPLETO.items():
            if clave in texto_lower:
                return valor, texto_extraido

        match_codigo = re.search(r'\b(m6a|mf|mee|mem|m6|mez|sv\d+[a-z]?|s\d+[a-z]?|swsh\d+)\b', texto_lower, re.IGNORECASE)
        if match_codigo:
            codigo = match_codigo.group(1).upper()
            return normalizar_set_para_cm(codigo), texto_extraido

        return "", texto_extraido
        
    except Exception as e:
        return "", f"Error al procesar: {str(e)}"

def obtener_precio_real(nombre_carta):
    try:
        numeros = re.findall(r'\b\d+\b', nombre_carta)
        nombre_limpio = re.sub(r'\b\d+\b', '', nombre_carta).strip()
        
        query = f"name:{nombre_limpio if nombre_limpio else 'Pikachu'}"
        if numeros:
            query += f" number:{numeros[0]}"
            
        url = f"https://api.pokemontcg.io/v2/cards?q={query}&pageSize=20"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json().get("data", [])
            if data:
                for carta in data:
                    precios = carta.get("tcgplayer", {}).get("prices", {})
                    for tipo in ["holofoil", "normal", "reverseHolofoil"]:
                        if tipo in precios and precios[tipo].get("market"):
                            return float(precios[tipo]["market"])
        return None
    except:
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
st.title("🃏 Mi TCG Collectr (Gestión de Sets ES / EN / JP)")

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
        idioma_carta = st.selectbox("Idioma de la carta", ["Español", "Inglés", "Japonés", "Chino"])
        archivo_foto = st.file_uploader("Sube la foto de tu carta", type=['jpg', 'png', 'jpeg'])
        
        if archivo_foto:
            img = Image.open(archivo_foto)
            st.image(img, caption="Imagen cargada", width=200)
            
            nombre_sugerido_ocr = leer_carta_con_ocr(img)
            nombre_carta_input = st.text_input("Nombre o código de la carta:", value=nombre_sugerido_ocr)
            
            if st.button("Consultar Precio en la API"):
                precio_ingles = obtener_precio_real(nombre_carta_input) or 20.00
                st.session_state.temp_precio_ingles = precio_ingles
                st.session_state.temp_nombre = nombre_carta_input

            if 'temp_precio_ingles' in st.session_state:
                precio_usuario_inicial = st.number_input("Precio inicial (€):", min_value=0.0, value=float(st.session_state.temp_precio_ingles), step=0.5)
                if st.button("Confirmar y Guardar en Portafolio"):
                    guardar_en_portafolio(st.session_state.temp_nombre, idioma_carta, "Carta", precio_usuario_inicial, st.session_state.temp_precio_ingles)
                    st.success("¡Carta guardada!")
                    del st.session_state.temp_precio_ingles
                    st.rerun()

    else:
        st.subheader("Producto Sellado")
        archivo_foto_sellado = st.file_uploader("📷 Sube foto del producto sellado", type=['jpg', 'png', 'jpeg'], key="foto_sellado")
        
        if archivo_foto_sellado is not None:
            if st.session_state.last_sealed_file != archivo_foto_sellado.name:
                st.session_state.last_sealed_file = archivo_foto_sellado.name
                img_sellado = Image.open(archivo_foto_sellado)
                
                with st.spinner("🤖 Escaneando set o código en la imagen..."):
                    detectado, debug_text = leer_producto_sellado_ocr(img_sellado)
                    if detectado:
                        st.session_state.auto_set_name = detectado
                        st.success(f"✨ ¡Set detectado: **{detectado}**!")
                    else:
                        st.session_state.auto_set_name = ""
                        st.warning("⚠️ No se reconoció el set automáticamente. Escríbelo abajo.")
        else:
            st.session_state.last_sealed_file = None

        tipo_sellado = st.selectbox("Categoría", ["Booster Box", "Elite Trainer Box (ETB)", "Starter Set", "Caja de Colección", "Otros"])
        custom_producto = st.text_input("Especifica el producto:", value=st.session_state.auto_set_name) if tipo_sellado == "Otros" else ""
        idioma_sellado = st.selectbox("Idioma", ["Español", "Inglés", "Japonés", "Chino"])
        nombre_set = st.text_input("Nombre del Set / Código (Ej: Chispas Vertiginosas, sv1s, M6a)", value=st.session_state.auto_set_name if tipo_sellado != "Otros" else "")
        
        set_traducido = normalizar_set_para_cm(nombre_set)
        busqueda_cm = f"{tipo_sellado} {set_traducido}".strip()
        url_cm = f"https://www.cardmarket.com/en/Pokemon/Products/Search?searchString={busqueda_cm.replace(' ', '+')}"
        st.markdown(f"🔗 **[Buscar en Cardmarket]({url_cm})**", unsafe_allow_html=True)

        precio_sellado_usuario = st.number_input("Precio estimado (€):", min_value=0.0, value=45.00, step=1.0)
        
        if st.button("Añadir Producto Sellado"):
            nombre_completo = f"{tipo_sellado} - {nombre_set}"
            guardar_en_portafolio(nombre_completo, idioma_sellado, "Sellado", precio_sellado_usuario, 45.00)
            st.success("¡Producto sellado añadido!")
            st.rerun()

with col2:
    st.header("Tu Portafolio Dinámico")
    if not st.session_state.portfolio.empty:
        edited_df = st.data_editor(st.session_state.portfolio, num_rows="dynamic", key="portfolio_editor", use_container_width=True)
        st.session_state.portfolio = edited_df
    else:
        st.info("Portafolio vacío.")

    valor_total = st.session_state.portfolio["Precio Actual (€)"].sum() if not st.session_state.portfolio.empty else 0
    st.metric(label="Valor Total de la Colección", value=f"{round(valor_total, 2)} €")
    st.line_chart(st.session_state.historial.set_index("Fecha"))
