import difflib
import re
from datetime import datetime, timedelta
from urllib.parse import quote_plus

import cv2
import numpy as np
import pandas as pd
import pytesseract
import requests
import streamlit as st
from PIL import Image, ImageEnhance

# --- 1. DICCIONARIO ESPAÑOL/INGLÉS MASIVO DE SETS (COMPLETO) ---
TRADUCCION_SETS_INGLES = {
    # Scarlet & Violet / Megaevolución y recientes
    "fuegos fantasmales": "Phantasmal Flames",
    "phantasmal flames": "Phantasmal Flames",
    "prismáticas": "Prismatic Evolutions",
    "prismatic evolutions": "Prismatic Evolutions",
    "chispas vertiginosas": "Surging Sparks",
    "surging sparks": "Surging Sparks",
    "corona estelar": "Stellar Crown",
    "stellar crown": "Stellar Crown",
    "fábulas sombrías": "Shrouded Fable",
    "shrouded fable": "Shrouded Fable",
    "mascarada crepuscular": "Twilight Masquerade",
    "twilight masquerade": "Twilight Masquerade",
    "fuerzas temporales": "Temporal Forces",
    "temporal forces": "Temporal Forces",
    "brechas paradox": "Paradox Rift",
    "paradox rift": "Paradox Rift",
    "llamas obsidianas": "Obsidian Flames",
    "obsidian flames": "Obsidian Flames",
    "evoluciones en paldea": "Paldea Evolved",
    "paldea evolved": "Paldea Evolved",
    "escarlata y púrpura": "Scarlet & Violet Base",
    "scarlet & violet": "Scarlet & Violet Base",
    "151": "Pokémon 151",
    "pokémon 151": "Pokémon 151",
    
    # Sword & Shield
    "zenit supremo": "Crown Zenith",
    "crown zenith": "Crown Zenith",
    "tempestad plateada": "Silver Tempest",
    "silver tempest": "Silver Tempest",
    "origen perdido": "Lost Origin",
    "lost origin": "Lost Origin",
    "resplandor astral": "Astral Radiance",
    "astral radiance": "Astral Radiance",
    "astros brillantes": "Brilliant Stars",
    "brilliant stars": "Brilliant Stars",
    "golpe furioso": "Fusion Strike",
    "fusion strike": "Fusion Strike",
    "cielos evolutivos": "Evolving Skies",
    "evolving skies": "Evolving Skies",
    "reino escalofriante": "Chilling Reign",
    "chilling reign": "Chilling Reign",
    "estilos de combate": "Battle Styles",
    "battle styles": "Battle Styles",
    "voltaje vívido": "Vivid Voltage",
    "vivid voltage": "Vivid Voltage",
    "oscuridad incandescente": "Darkness Ablaze",
    "darkness ablaze": "Darkness Ablaze",
    "choque rebelde": "Rebel Clash",
    "rebel clash": "Rebel Clash",
    "espada y escudo": "Sword & Shield Base",
    "sword & shield": "Sword & Shield Base",
    "celebraciones": "Celebrations",
    "celebrations": "Celebrations",
    
    # Sun & Moon
    "eclipse cósmico": "Cosmic Eclipse",
    "cosmic eclipse": "Cosmic Eclipse",
    "mentes unificadas": "Unified Minds",
    "unified minds": "Unified Minds",
    "vínculos indelebles": "Unbroken Bonds",
    "unbroken bonds": "Unbroken Bonds",
    "unión de aliados": "Team Up",
    "team up": "Team Up",
    "trueno perdido": "Lost Thunder",
    "lost thunder": "Lost Thunder",
    "tormenta celestial": "Celestial Storm",
    "celestial storm": "Celestial Storm",
    "luz prohibida": "Forbidden Light",
    "forbidden light": "Forbidden Light",
    "ultraprisma": "Ultra Prism",
    "ultra prism": "Ultra Prism",
    "sombras ardientes": "Burning Shadows",
    "burning shadows": "Burning Shadows",
    "guardianes nacientes": "Guardians Rising",
    "guardians rising": "Guardians Rising",
    "sol y luna": "Sun & Moon Base",
    "sun & moon": "Sun & Moon Base",
    "invasión carmesí": "Crimson Invasion",
    "crimson invasion": "Crimson Invasion",
    "leyendas luminosas": "Shining Legends",
    "shining legends": "Shining Legends",
    "majestad de dragones": "Dragon Majesty",
    "dragon majesty": "Dragon Majesty",
    
    # XY y Clásicos
    "asedio de vapor": "Steam Siege",
    "steam siege": "Steam Siege",
    "destinos enfrentados": "Fates Collide",
    "fates collide": "Fates Collide",
    "turboimpulso": "BREAKpoint",
    "breakpoint": "BREAKpoint",
    "turbocalos": "BREAKthrough",
    "breakthrough": "BREAKthrough",
    "orígenes antiguos": "Ancient Origins",
    "ancient origins": "Ancient Origins",
    "cielos rugientes": "Roaring Skies",
    "roaring skies": "Roaring Skies",
    "choque primigenio": "Primal Clash",
    "primal clash": "Primal Clash",
    "puños furiosos": "Furious Fists",
    "furious fists": "Furious Fists",
    "destellos de fuego": "Flashfire",
    "flashfire": "Flashfire",
    "generaciones": "Generations",
    "generations": "Generations",
    "evoluciones": "Evolutions",
    "evolutions": "Evolutions",
}

# --- 2. DICCIONARIO COMPLETO DE CÓDIGOS JAPONESES ---
TRADUCCION_CODIGOS_JAPONESES = {
    # Scarlet & Violet
    "sv8a": "Terastal Fest ex",
    "sv8": "Super Electric Breaker",
    "sv7a": "Paradise Dragona", 
    "sv7": "Stellar Miracle",
    "sv6a": "Night Wanderer",
    "sv6": "Mask of Change", 
    "sv5a": "Crimson Haze",
    "sv5m": "Cyber Judge",
    "sv5k": "Wild Force", 
    "sv4a": "Shiny Treasure ex",
    "sv4m": "Future Flash",
    "sv4k": "Ancient Roar", 
    "sv3a": "Raging Surf",
    "sv3": "Ruler of the Black Flame",
    "sv2a": "Pokémon 151", 
    "sv2d": "Clay Burst",
    "sv2p": "Snow Hazard",
    "sv1a": "Triplet Beat", 
    "sv1v": "Violet ex",
    "sv1s": "Scarlet ex",
    # Sword & Shield
    "s12a": "VSTAR Universe",
    "s12": "Paradigm Trigger",
    "s11a": "Incandescent Arcana", 
    "s11": "Lost Abyss",
    "s10a": "Dark Phantasma",
    "s10d": "Time Gazer", 
    "s10p": "Space Juggler",
    "s9a": "Battle Region",
    "s9": "Star Birth", 
    "s8b": "VMAX Climax",
    "s8a": "25th Anniversary Collection",
    "s8": "Fusion Arts", 
    "s7d": "Towering Perfection",
    "s7r": "Blue Sky Stream",
    "s6a": "Eevee Heroes", 
    "s6h": "Silver Lance",
    "s6k": "Jet-Black Spirit",
    "s5a": "Matchless Fighters", 
    "s5i": "Single Strike Master",
    "s5r": "Rapid Strike Master",
    "s4a": "Shiny Star V", 
    "s4": "Amazing Volt Tackle",
    "s3a": "Legendary Heartbeat",
    "s3": "Infinity Zone", 
    "s2a": "Explosive Walker",
    "s2": "Rebellion Crash",
    "s1a": "VMAX Rising", 
    "s1h": "Shield",
    "s1w": "Sword",
    # Sun & Moon
    "sm12a": "Tag All Stars",
    "sm12": "Alter Genesis",
    "sm11b": "Dream League", 
    "sm11a": "Remix Bout",
    "sm11": "Miracle Twin",
    "sm10b": "Sky Legend", 
    "sm10a": "GG End",
    "sm10": "Double Blaze",
    "sm9b": "Full Metal Wall", 
    "sm9a": "Night Unison",
    "sm9": "Tag Bolt",
    "sm8b": "GX Ultra Shiny", 
    "sm8a": "Dark Order",
    "sm8": "Super-Burst Impact",
    "sm7b": "Fairy Rise",
    "sm7a": "Thunderclap Spark",
    "sm7": "Charisma of the Wrecked Sky",
    "sm6b": "Champion Road",
    "sm6a": "Dragon Storm",
    "sm6": "Forbidden Light",
    "sm5plus": "Ultra Force",
    "sm5m": "Ultra Moon",
    "sm5s": "Ultra Sun",
    "sm4plus": "GX Battle Boost",
    "sm4a": "Ultradimensional Beasts",
    "sm4s": "Awakened Heroes",
    "sm3plus": "Shining Legends",
    "sm3n": "Darkness that Consumes Light",
    "sm3h": "Have You Seen the Battle Rainbow?",
    "sm2k": "Facing a New Trial",
    "sm2l": "Alolan Moonlight",
    "sm1plus": "Sun & Moon Plus",
    "sm1m": "Collection Moon",
    "sm1s": "Collection Sun",
    # XY & Black/White
    "xy11": "Cruel Traitor / Explosive Fighter",
    "xy10": "Awakening Psychic King",
    "xy9": "Rage of the Broken Heavens",
    "xy8": "Blue Shock / Red Flash",
    "xy7": "Bandit Ring",
    "xy6": "Emerald Break",
    "xy5": "Tidal Storm / Gaia Volcano",
    "xy4": "Phantom Gate",
    "xy3": "Rising Fist",
    "xy2": "Wild Blaze",
    "xy1": "Collection X / Y",
    "cp6": "20th Anniversary Concept Pack",
    "cp5": "Mythical & Legendary Dream",
    "cp4": "Premium Champion Pack",
    "cp3": "PokéKyun Collection",
    "cp2": "Legendary Holo",
    "cp1": "Magma Gang vs Aqua Gang",
    "bw9": "Megalo Cannon",
    "bw8": "Spiral Force / Thunder Knuckle",
    "bw7": "Plasma Gale",
    "bw6": "Cold Flare / Freeze Bolt",
    "bw5": "Dragon Blade / Dragon Blast", 
    "bw4": "Dark Rush",
    "bw3": "Hail Blizzard / Psycho Drive",
    "bw2": "Red Collection",
    "bw1": "White Collection / Black Collection"
}

def normalizar_set_para_cm(nombre_set: str) -> str:
    if not nombre_set:
        return ""
    set_lower = nombre_set.lower().strip()
    if set_lower in TRADUCCION_CODIGOS_JAPONESES:
        return TRADUCCION_CODIGOS_JAPONESES[set_lower]
    for esp, eng in TRADUCCION_SETS_INGLES.items():
        if esp in set_lower:
            return eng
    return nombre_set.strip()


# --- FUNCIONES DE LECTURA E INTEGRACIÓN ---

def leer_carta_con_ocr(imagen: Image.Image) -> str:
    try:
        img_proc = imagen.convert("L")
        w, h = img_proc.size
        img_proc = img_proc.resize((w * 2, h * 2), Image.Resampling.LANCZOS)
        enhancer = ImageEnhance.Contrast(img_proc)
        img_proc = enhancer.enhance(2.0)

        texto = ""
        for lang in ["jpn+eng+spa", "eng+spa", "eng"]:
            try:
                texto = pytesseract.image_to_string(img_proc, lang=lang)
                if texto.strip():
                    break
            except Exception:
                continue

        palabras = [p for p in texto.split() if len(p) > 3]
        return palabras[0] if palabras else "Charizard"
    except Exception:
        return "Charizard"


def leer_producto_sellado_ocr(imagen: Image.Image, nombre_archivo: str = "") -> tuple[str, str]:
    try:
        pistas_nombre = (nombre_archivo or "").replace("_", " ").replace("-", " ").lower()
        
        img_rgb = imagen.convert("RGB")
        img_np = np.array(img_rgb)
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        gray = cv2.resize(gray, (0, 0), fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        texto_ocr = pytesseract.image_to_string(thresh, lang="eng+spa+jpn", config=r"--oem 3 --psm 11")
        texto_extraido = f"Pista Archivo: {pistas_nombre}\nTexto OCR: {texto_ocr}"
        texto_lower = (pistas_nombre + " " + texto_ocr).lower()

        mejor_coincidencia = ""
        puntuacion_maxima = 0

        for nombre_set, ingles in TRADUCCION_SETS_INGLES.items():
            if nombre_set in texto_lower:
                puntos = len(nombre_set)
                if puntos > puntuacion_maxima:
                    puntuacion_maxima = puntos
                    mejor_coincidencia = ingles

        if mejor_coincidencia:
            return mejor_coincidencia, texto_extraido

        for nombre_set, ingles in TRADUCCION_SETS_INGLES.items():
            palabras = nombre_set.split()
            coincidencias = sum(1 for p in palabras if len(p) > 3 and p in texto_lower)
            if coincidencias > 0:
                return ingles, texto_extraido

        return "", texto_extraido
    except Exception as e:
        return "", f"Error general: {str(e)}"


def obtener_precio_real(nombre_carta: str) -> float | None:
    try:
        numeros = re.findall(r"\b\d+\b", nombre_carta)
        nombre_limpio = re.sub(r"\b\d+\b", "", nombre_carta).strip()
        query_name = "Charizard" if "charizard" in nombre_limpio.lower() else (nombre_limpio.split()[0] if nombre_limpio else "Charizard")

        query = f"name:{query_name}"
        if numeros:
            query += f" number:{numeros[0]}"
            
        url = f"https://api.pokemontcg.io/v2/cards?q={query}&pageSize=10"
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
    except Exception: 
        return None


def guardar_en_portafolio(nombre: str, idioma: str, tipo: str, precio_usuario: float, precio_ingles_ref: float):
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


# --- INTERFAZ Y ESTADO ---
st.set_page_config(page_title="Mi TCG Collectr Pro", layout="wide")
st.title("🃏 Mi TCG Collectr (Versión Completa Extendida)")

if "portfolio" not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(columns=[
        "Item", "Tipo", "Idioma", "Precio Inglés Ref (€)", "Precio Actual (€)", "Factor Proporción"
    ])
    
if "historial" not in st.session_state:
    fechas = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(4, -1, -1)]
    st.session_state.historial = pd.DataFrame({"Fecha": fechas, "Valor Total (€)": [0.0]*5})

if "last_sealed_file" not in st.session_state: 
    st.session_state.last_sealed_file = None
if "auto_set_name" not in st.session_state: 
    st.session_state.auto_set_name = ""

col1, col2 = st.columns([1, 2])

with col1:
    st.header("Añadir a la Colección")
    modo_registro = st.radio("¿Qué quieres añadir?", ["Carta Individual (por Foto)", "Producto Sellado"])

    if modo_registro == "Carta Individual (por Foto)":
        idioma_carta = st.selectbox("Idioma de la carta", ["Inglés", "Español", "Japonés", "Chino"])
        archivo_foto = st.file_uploader("Sube la foto de tu carta", type=["jpg", "png", "jpeg"])

        if archivo_foto:
            img = Image.open(archivo_foto)
            st.image(img, caption="Imagen cargada", width=200)
            nombre_sugerido_ocr = leer_carta_con_ocr(img)
            nombre_carta_input = st.text_input("Nombre de la carta:", value=nombre_sugerido_ocr)

            url_cardmarket = f"https://www.cardmarket.com/en/Pokemon/Products/Search?searchString={quote_plus(nombre_carta_input)}"
            st.markdown(f"🔗 **[Cardmarket]({url_cardmarket})**", unsafe_allow_html=True)

            if st.button("Consultar Precio API"):
                precio_ingles = obtener_precio_real(nombre_carta_input) or 25.50
                st.session_state.temp_precio_ingles = precio_ingles
                st.session_state.temp_nombre = nombre_carta_input
                st.success(f"Precio referencia: {precio_ingles:.2f} €")

            if "temp_precio_ingles" in st.session_state:
                precio_usuario_inicial = st.number_input("Precio inicial (€):", min_value=0.0, value=float(st.session_state.temp_precio_ingles))
                if st.button("Guardar Carta"):
                    guardar_en_portafolio(st.session_state.temp_nombre, idioma_carta, "Carta", precio_usuario_inicial, st.session_state.temp_precio_ingles)
                    st.success("¡Guardado!")
                    del st.session_state.temp_precio_ingles
                    st.rerun()

    else:
        st.subheader("Producto Sellado")
        archivo_foto_sellado = st.file_uploader("📷 Sube la foto del producto sellado", type=["jpg", "png", "jpeg"], key="foto_sellado")

        if archivo_foto_sellado is not None:
            if st.session_state.last_sealed_file != archivo_foto_sellado.name:
                st.session_state.last_sealed_file = archivo_foto_sellado.name
                img_sellado = Image.open(archivo_foto_sellado)
                with st.spinner("🤖 Analizando set..."):
                    detectado, debug_text = leer_producto_sellado_ocr(img_sellado, archivo_foto_sellado.name)
                    if detectado:
                        st.session_state.auto_set_name = detectado
                        st.success(f"✨ ¡Detectado: **{detectado}**!")
                    else:
                        st.session_state.auto_set_name = ""
                        st.warning("⚠️ No detectado automáticamente, escríbelo abajo.")
                    with st.expander("🛠️ Diagnóstico OCR"):
                        st.text(debug_text)
        else:
            st.session_state.last_sealed_file = None

        tipo_sellado = st.selectbox("Categoría", ["Booster Box", "Elite Trainer Box (ETB)", "Caja de Colección", "Blister", "Lote de Sobres", "Otros"])
        custom_producto = st.text_input("Especifica:", value=st.session_state.auto_set_name) if tipo_sellado == "Otros" else ""
        idioma_sellado = st.selectbox("Idioma", ["Inglés", "Español", "Japonés", "Chino"])
        
        nombre_set = st.text_input("Nombre del Set", value=st.session_state.auto_set_name if tipo_sellado != "Otros" else "")
        set_para_buscar = normalizar_set_para_cm(nombre_set)
        
        termino_final = set_para_buscar if tipo_sellado != 'Otros' else custom_producto
        busqueda_cm_sellado = f"{tipo_sellado} {termino_final}".strip()
        url_cm = f"https://www.cardmarket.com/en/Pokemon/Products/Search?searchString={quote_plus(busqueda_cm_sellado)}"
        st.markdown(f"🔗 **[Ver en Cardmarket]({url_cm})**", unsafe_allow_html=True)

        precio_sellado_usuario = st.number_input("Precio (€):", min_value=0.0, value=45.00)

        if st.button("Añadir Producto Sellado"):
            nombre_completo = f"{custom_producto} - {nombre_set}" if tipo_sellado == "Otros" else f"{tipo_sellado} - {nombre_set}"
            if nombre_set.strip() or custom_producto.strip():
                guardar_en_portafolio(nombre_completo, idioma_sellado, "Sellado", precio_sellado_usuario, 45.00)
                st.success("¡Añadido con éxito!")
                st.rerun()
            else:
                st.error("Rellene los campos obligatorios.")

with col2:
    st.header("Tu Portafolio Dinámico")
    if not st.session_state.portfolio.empty:
        edited_df = st.data_editor(st.session_state.portfolio, num_rows="dynamic", key="portfolio_editor", use_container_width=True)
        for i in range(len(edited_df)):
            if edited_df.loc[i, "Precio Inglés Ref (€)"] > 0:
                edited_df.loc[i, "Factor Proporción"] = edited_df.loc[i, "Precio Actual (€)"] / edited_df.loc[i, "Precio Inglés Ref (€)"]
        st.session_state.portfolio = edited_df

        if st.button("🔄 Actualizar Precios API"):
            for i, row in st.session_state.portfolio.iterrows():
                if row["Tipo"] == "Carta":
                    nuevo_ref = obtener_precio_real(row["Item"])
                    if nuevo_ref:
                        st.session_state.portfolio.loc[i, "Precio Inglés Ref (€)"] = float(nuevo_ref)
                        st.session_state.portfolio.loc[i, "Precio Actual (€)"] = round(nuevo_ref * row["Factor Proporción"], 2)
            st.success("¡Actualizado!")
            st.rerun()
    else:
        st.info("Portafolio vacío.")

    valor_total = st.session_state.portfolio["Precio Actual (€)"].sum() if not st.session_state.portfolio.empty else 0.0
    st.metric(label="Valor Total", value=f"{round(valor_total, 2)} €")
    st.line_chart(st.session_state.historial.set_index("Fecha"))
