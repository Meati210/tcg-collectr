import difflib
import re
from datetime import datetime, timedelta
from urllib.parse import quote_plus

import pandas as pd
import pytesseract
import requests
import streamlit as st
from PIL import Image, ImageEnhance

# --- 1. DICCIONARIO ESPAÑOL -> INGLÉS (OCCIDENTAL) ---
TRADUCCION_SETS_INGLES = {
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
    "escarlata y púrpura": "Scarlet & Violet Base",
    "151": "Pokémon 151",
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
    "espada y escudo": "Sword & Shield Base",
    "zenit supremo": "Crown Zenith",
    "celebraciones": "Celebrations",
    "eclipse cósmico": "Cosmic Eclipse",
    "mentes unificadas": "Unified Minds",
    "vínculos indelebles": "Unbroken Bonds",
    "unión de aliados": "Team Up",
    "trueno perdido": "Lost Thunder",
    "tormenta celestial": "Celestial Storm",
    "luz prohibida": "Forbidden Light",
    "ultraprisma": "Ultra Prism",
    "sombras ardientes": "Burning Shadows",
    "guardianes nacientes": "Guardians Rising",
    "sol y luna": "Sun & Moon Base",
    "invasión carmesí": "Crimson Invasion",
    "leyendas luminosas": "Shining Legends",
    "majestad de dragones": "Dragon Majesty",
    "asedio de vapor": "Steam Siege",
    "destinos enfrentados": "Fates Collide",
    "turboimpulso": "BREAKpoint",
    "turbocalos": "BREAKthrough",
    "orígenes antiguos": "Ancient Origins",
    "cielos rugientes": "Roaring Skies",
    "choque primigenio": "Primal Clash",
    "fuerzas fantasmales": "Phantom Forces",
    "puños furiosos": "Furious Fists",
    "destellos de fuego": "Flashfire",
    "generaciones": "Generations",
    "evoluciones": "Evolutions",
}

# --- 2. DICCIONARIO JAPONÉS (CÓDIGOS) -> INGLÉS (CARDMARKET) ---
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
            
    if "/" in nombre_set:
        return nombre_set.split("/")[-1].strip()
        
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
        idiomas_intento = ["jpn+eng+spa", "eng+spa", "eng"]

        for lang in idiomas_intento:
            try:
                texto = pytesseract.image_to_string(img_proc, lang=lang)
                if texto.strip():
                    break
            except Exception:
                continue

        palabras = [p for p in texto.split() if len(p) > 3]
        if palabras:
            return palabras[0]
        return "Charizard"
    except Exception:
        return "Charizard"


def leer_producto_sellado_ocr(imagen: Image.Image) -> tuple[str, str]:
    texto_extraido = ""
    try:
        img_rgb = imagen.convert("RGB")
        w, h = img_rgb.size

        img_proc = img_rgb.resize((w * 2, h * 2), Image.Resampling.LANCZOS).convert("L")
        enhancer = ImageEnhance.Contrast(img_proc)
        img_proc = enhancer.enhance(1.8)
        config_custom = r"--oem 3 --psm 11"

        idiomas_intento = ["jpn+spa+eng", "spa+eng", "eng"]
        for lang in idiomas_intento:
            try:
                texto = pytesseract.image_to_string(img_proc, lang=lang, config=config_custom)
                if texto.strip():
                    texto_extraido += " " + texto
            except Exception:
                continue

        texto_lower = texto_extraido.lower()

        # 1. Búsqueda de códigos Japoneses puros
        match_jp = re.search(r'\b(sv[0-9]{1,2}[a-z]?|s[0-9]{1,2}[a-z]?|sm[0-9]{1,2}[a-z]?|xy[0-9]{1,2}[a-z]?|bw[0-9]{1,2}[a-z]?|cp[0-9])\b', texto_lower)
        if match_jp:
            codigo = match_jp.group(1)
            if codigo in TRADUCCION_CODIGOS_JAPONESES:
                return TRADUCCION_CODIGOS_JAPONESES[codigo], texto_extraido
            return codigo.upper(), texto_extraido

        # 2. CATÁLOGO DE SETS (Occidentales ESP/ENG integrados + Japoneses por nombre)
        catalogo_sets = {
            # Scarlet & Violet (ENG + ESP)
            "Phantasmal Flames": ["phantasmal", "flames", "fuegos", "fantasmales"],
            "Prismatic Evolutions": ["prismatic", "prismaticas", "pre", "eevee"],
            "Surging Sparks": ["surging", "sparks", "chispas", "vertiginosas", "ssp"],
            "Stellar Crown": ["stellar", "crown", "corona", "estelar", "scr"],
            "Shrouded Fable": ["shrouded", "fable", "fabulas", "sombrias", "sfa"],
            "Twilight Masquerade": ["twilight", "masquerade", "mascarada", "crepuscular", "twm"],
            "Temporal Forces": ["temporal", "forces", "fuerzas", "tef"],
            "Paradox Rift": ["paradox", "rift", "brechas", "par"],
            "Obsidian Flames": ["obsidian", "flames", "llamas", "obsidianas", "obf"],
            "Paldea Evolved": ["paldea", "evolved", "evoluciones", "pal"],
            "Scarlet & Violet Base": ["scarlet", "violet", "escarlata", "purpura", "svi"],
            "Pokémon 151": ["151", "mew", "sv2a"],
            
            # Sword & Shield (ENG + ESP)
            "Crown Zenith": ["crown", "zenith", "zenit", "supremo", "crz"],
            "Silver Tempest": ["silver", "tempest", "tempestad", "plateada", "sit"],
            "Lost Origin": ["lost", "origin", "origen", "perdido", "lor"],
            "Astral Radiance": ["astral", "radiance", "resplandor", "asr"],
            "Brilliant Stars": ["brilliant", "stars", "astros", "brillantes", "brs"],
            "Fusion Strike": ["fusion", "strike", "golpe", "furioso", "fst"],
            "Evolving Skies": ["evolving", "skies", "cielos", "evolutivos", "evs"],
            "Chilling Reign": ["chilling", "reign", "reino", "escalofriante", "cre"],
            "Battle Styles": ["battle", "styles", "estilos", "combate", "bst"],
            "Vivid Voltage": ["vivid", "voltage", "voltaje", "vivido", "vvd"],
            "Darkness Ablaze": ["darkness", "ablaze", "oscuridad", "incandescente", "daa"],
            "Rebel Clash": ["rebel", "clash", "choque", "rebelde", "rcl"],
            "Sword & Shield Base": ["sword", "shield", "espada", "escudo", "ssh"],
            
            # Sun & Moon (ENG + ESP)
            "Cosmic Eclipse": ["cosmic", "eclipse", "cosmico", "cec"],
            "Unified Minds": ["unified", "minds", "mentes", "unificadas", "umi"],
            "Unbroken Bonds": ["unbroken", "bonds", "vinculos", "indelebles", "unb"],
            "Team Up": ["team", "up", "union", "aliados", "teu"],
            "Lost Thunder": ["lost", "thunder", "trueno", "perdido", "lot"],
            "Celestial Storm": ["celestial", "storm", "tormenta", "ces"],
            "Forbidden Light": ["forbidden", "light", "luz", "prohibida", "fli"],
            "Ultra Prism": ["ultra", "prism", "ultraprisma", "upr"],
            "Crimson Invasion": ["crimson", "invasion", "carmesi", "cin"],
            "Burning Shadows": ["burning", "shadows", "sombras", "ardientes", "bus"],
            "Guardians Rising": ["guardians", "rising", "guardianes", "nacientes", "gri"],
            "Sun & Moon Base": ["sun", "moon", "sol", "luna", "sum"],
            
            # XY - Megaevoluciones (ENG + ESP)
            "Evolutions": ["evolutions", "evoluciones", "evo"],
            "Steam Siege": ["steam", "siege", "asedio", "vapor", "sts"],
            "Fates Collide": ["fates", "collide", "destinos", "enfrentados", "fco"],
            "Generations": ["generations", "generaciones", "gen"],
            "BREAKpoint": ["breakpoint", "turboimpulso", "bkp"],
            "BREAKthrough": ["breakthrough", "turbocalos", "bkt"],
            "Ancient Origins": ["ancient", "origins", "origenes", "antiguos", "aor"],
            "Roaring Skies": ["roaring", "skies", "cielos", "rugientes", "ros"],
            "Primal Clash": ["primal", "clash", "choque", "primigenio", "prc"],
            "Phantom Forces": ["phantom", "forces", "fuerzas", "fantasmales", "phf"],
            "Furious Fists": ["furious", "fists", "puños", "furiosos", "ffi"],
            "Flashfire": ["flashfire", "destellos", "fuego", "flf"],
            "XY Base": ["xy", "base"],

            # Japoneses (Apoyo por nombre directo sin depender solo del código)
            "VSTAR Universe": ["vstar", "universe", "s12a"],
            "Shiny Treasure ex": ["shiny", "treasure", "sv4a"],
            "Shiny Star V": ["shiny", "star", "v", "s4a"],
            "Tag All Stars": ["tag", "stars", "sm12a"],
            "Eevee Heroes": ["eevee", "heroes", "s6a"],
        }

        mejor_coincidencia = ""
        puntuacion_maxima = 0

        # Extraemos las palabras exactas que leyó el OCR para validar los códigos cortos
        palabras_ocr = set(re.findall(r'\b\w+\b', texto_lower))

        for nombre_set, palabras_clave in catalogo_sets.items():
            puntuacion_actual = 0
            for palabra in palabras_clave:
                if len(palabra) <= 3:
                    # Si es un código corto (ej: lot, par, sum), exigimos que sea la palabra exacta
                    if palabra in palabras_ocr:
                        puntuacion_actual += 5 
                else:
                    # Si es una palabra larga (ej: phantasmal, flames), permitimos coincidencias parciales
                    if palabra in texto_lower:
                        puntuacion_actual += len(palabra)

            if puntuacion_actual > puntuacion_maxima:
                puntuacion_maxima = puntuacion_actual
                mejor_coincidencia = nombre_set

        if puntuacion_maxima > 0 and mejor_coincidencia:
            return mejor_coincidencia, texto_extraido

        matches_difflib = difflib.get_close_matches(texto_lower, list(catalogo_sets.keys()), n=1, cutoff=0.4)
        if matches_difflib:
            return matches_difflib[0], texto_extraido

        if not texto_extraido.strip():
            return "", "El OCR no detectó texto legible."

        return "", texto_extraido

    except Exception as e:
        return "", f"Error al procesar la imagen: {str(e)}"


def obtener_precio_real(nombre_carta: str) -> float | None:
    try:
        numeros = re.findall(r"\b\d+\b", nombre_carta)
        nombre_limpio = re.sub(r"\b\d+\b", "", nombre_carta).strip()
        nombre_lower = nombre_limpio.lower()
        
        if "charizard" in nombre_lower:
            query_name = "Charizard"
        else:
            palabras = [p for p in nombre_limpio.replace("-", " ").split() if len(p) > 2]
            if palabras:
                query_name = palabras[0]
            else:
                query_name = nombre_limpio

        query = f"name:{query_name}"
        if numeros:
            query += f" number:{numeros[0]}"
            
        url = f"https://api.pokemontcg.io/v2/cards?q={query}&pageSize=50"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json().get("data", [])
            if not data and numeros:
                url_sin_numero = f"https://api.pokemontcg.io/v2/cards?q=name:{query_name}&pageSize=50"
                response = requests.get(url_sin_numero, timeout=5)
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


def guardar_en_portafolio(nombre: str, idioma: str, tipo: str, precio_usuario: float, precio_ingles_ref: float):
    if precio_ingles_ref > 0:
        factor = (precio_usuario / precio_ingles_ref)
    else:
        factor = 1.0
        
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

# --- INTERFAZ Y ESTADO ---
st.set_page_config(page_title="Mi TCG Collectr Pro", layout="wide")
st.title("🃏 Mi TCG Collectr (Búsqueda Avanzada y Proporcional)")

if "portfolio" not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(columns=[
        "Item", "Tipo", "Idioma", "Precio Inglés Ref (€)", "Precio Actual (€)", "Factor Proporción"
    ])
    
if "historial" not in st.session_state:
    fechas = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(4, -1, -1)]
    st.session_state.historial = pd.DataFrame({
        "Fecha": fechas,
        "Valor Total (€)": [0.0, 0.0, 0.0, 0.0, 0.0]
    })
    
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
            st.info("💡 Consejo: Escribe el nombre en inglés y su número (ej: 'Charizard 109') para afinar:")
            nombre_carta_input = st.text_input("Nombre de la carta:", value=nombre_sugerido_ocr)

            url_cardmarket = f"https://www.cardmarket.com/en/Pokemon/Products/Search?searchString={quote_plus(nombre_carta_input)}"
            st.markdown(f"🔗 **[Entra en Cardmarket (en Inglés)]({url_cardmarket})**", unsafe_allow_html=True)

            if st.button("Consultar Precio en la API"):
                st.info(f"🔍 Buscando referencias de mercado para: **{nombre_carta_input}**...")
                precio_ingles = obtener_precio_real(nombre_carta_input)
                
                if precio_ingles: 
                    st.success(f"✅ Precio de referencia encontrado: **{precio_ingles:.2f} €**")
                else: 
                    precio_ingles = 25.50
                    st.warning("⚠️ No se halló precio automático para esta variante. Usando referencia por defecto (25.50 €).")
                
                st.session_state.temp_precio_ingles = precio_ingles
                st.session_state.temp_nombre = nombre_carta_input

            if "temp_precio_ingles" in st.session_state:
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
        archivo_foto_sellado = st.file_uploader("📷 Sube la foto del producto sellado", type=["jpg", "png", "jpeg"], key="foto_sellado")

        if archivo_foto_sellado is not None:
            if st.session_state.last_sealed_file != archivo_foto_sellado.name:
                st.session_state.last_sealed_file = archivo_foto_sellado.name
                img_sellado = Image.open(archivo_foto_sellado)
                
                with st.spinner("🤖 Analizando códigos y coincidencias del set..."):
                    detectado, debug_text = leer_producto_sellado_ocr(img_sellado)
                    
                    if detectado:
                        st.session_state.auto_set_name = detectado
                        st.success(f"✨ ¡Detectado automáticamente: **{detectado}**!")
                        with st.expander("🛠️ Ver qué leyó el robot (Diagnóstico)"): 
                            st.text(debug_text)
                    else:
                        st.session_state.auto_set_name = ""
                        st.warning("⚠️ No se pudo leer automáticamente. Ingresa el set manualmente.")
                        with st.expander("🛠️ Diagnóstico OCR"): 
                            st.write(debug_text)
        else: 
            st.session_state.last_sealed_file = None

        tipo_sellado = st.selectbox("Categoría", ["Booster Box", "Elite Trainer Box (ETB)", "Caja de Colección", "Blister", "Lote de Sobres", "Otros"])
        
        if tipo_sellado == "Otros":
            custom_producto = st.text_input("Especifica el producto:", value=st.session_state.auto_set_name) 
        else:
            custom_producto = ""
            
        idioma_sellado = st.selectbox("Idioma", ["Inglés", "Español", "Japonés", "Chino"])
        
        if tipo_sellado != "Otros":
            valor_defecto = st.session_state.auto_set_name
        else:
            valor_defecto = ""
            
        nombre_set = st.text_input("Nombre del Set o Colección (Ej: 'sv4a' o '151')", value=valor_defecto)

        set_para_buscar = normalizar_set_para_cm(nombre_set)
        
        if tipo_sellado != 'Otros':
            termino_final = set_para_buscar
        else:
            termino_final = custom_producto
            
        busqueda_cm_sellado = f"{tipo_sellado} {termino_final}".strip()
        url_cardmarket_sellado = f"https://www.cardmarket.com/en/Pokemon/Products/Search?searchString={quote_plus(busqueda_cm_sellado)}"
        
        st.markdown(f"🔗 **[Ver precio de este producto sellado en Cardmarket (en Inglés)]({url_cardmarket_sellado})**", unsafe_allow_html=True)

        precio_sellado_usuario = st.number_input("Precio inicial / estimado (€):", min_value=0.0, value=45.00, step=1.0)

        if st.button("Añadir Producto Sellado"):
            if tipo_sellado == "Otros":
                nombre_completo = f"{custom_producto} - {nombre_set}"
            else:
                nombre_completo = f"{tipo_sellado} - {nombre_set}"
                
            if nombre_set.strip() != "" or (tipo_sellado == "Otros" and custom_producto.strip() != ""):
                guardar_en_portafolio(nombre_completo, idioma_sellado, "Sellado", precio_sellado_usuario, 45.00)
                st.success("¡Producto sellado añadido correctamente!")
                st.rerun()
            else: 
                st.error("Por favor, completa los campos requeridos del producto.")

with col2:
    st.header("Tu Portafolio Dinámico")
    st.subheader("Inventario (Edita el 'Precio Actual' cuando quieras)")

    if not st.session_state.portfolio.empty:
        edited_df = st.data_editor(st.session_state.portfolio, num_rows="dynamic", key="portfolio_editor", use_container_width=True)

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
                        nuevo_actual = float(nuevo_ref) * row["Factor Proporción"]
                        st.session_state.portfolio.loc[i, "Precio Actual (€)"] = round(nuevo_actual, 2)
                        actualizados += 1

            st.success(f"¡Se actualizó el mercado para {actualizados} cartas de forma proporcional!")
            nuevo_valor = st.session_state.portfolio["Precio Actual (€)"].sum()
            fecha_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            nueva_fila_hist = pd.DataFrame([{"Fecha": fecha_str, "Valor Total (€)": nuevo_valor}])
            st.session_state.historial = pd.concat([st.session_state.historial, nueva_fila_hist], ignore_index=True)
            st.rerun()
    else: 
        st.info("Tu portafolio está vacío. Añade cartas o productos a la izquierda.")

    if not st.session_state.portfolio.empty:
        valor_total = st.session_state.portfolio["Precio Actual (€)"].sum()
    else:
        valor_total = 0.0
        
    st.metric(label="Valor Total de la Colección", value=f"{round(valor_total, 2)} €")
    st.line_chart(st.session_state.historial.set_index("Fecha"))
