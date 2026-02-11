import os
import time
import requests
import feedparser
import pytz
from datetime import datetime, timedelta
from ntscraper import Nitter

# --- CONFIGURACIÓN ---
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

RSS_NEWS = "https://news.google.com/rss/search?q=Contingencia+Ambiental+CDMX+CAMe+activan&hl=es-419&gl=MX&ceid=MX:es-419&when:1d"
TWITTER_USER = "CAMegalopolis"

# --- PALABRAS CLAVE PARA EL SEMÁFORO ---
KEYWORDS_ACTIVACION = ["se activa", "fase 1", "doble hoy no circula", "continúa la fase", "mantiene la fase"]
KEYWORDS_POSIBILIDAD = ["posible", "podría", "podria", "probabilidad", "prevé", "preve", "riesgo", "pronóstico", "mala calidad"]

# --- TELEGRAM BLINDADO ---
def enviar_telegram(mensaje):
    if not TOKEN or not CHAT_ID: return
    for i in range(1, 4):
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            data = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "HTML", "disable_web_page_preview": True}
            r = requests.post(url, data=data, timeout=10)
            if r.status_code == 200: break
            time.sleep(5)
        except: time.sleep(5)

# --- 1. LÓGICA DE REGLAS (MATEMÁTICA) ---
def obtener_regla(fecha):
    dia_semana = fecha.weekday() 
    nombres_dias = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO"]
    nombre_dia = nombres_dias[dia_semana]
    
    regla = ""
    if dia_semana == 0: regla = "🟡 <b>Engomado AMARILLO</b>\n🔢 Terminación <b>5 y 6</b> (Hol 1 y 2)."
    elif dia_semana == 1: regla = "🌸 <b>Engomado ROSA</b>\n🔢 Terminación <b>7 y 8</b> (Hol 1 y 2)."
    elif dia_semana == 2: regla = "🔴 <b>Engomado ROJO</b>\n🔢 Terminación <b>3 y 4</b> (Hol 1 y 2)."
    elif dia_semana == 3: regla = "🟢 <b>Engomado VERDE</b>\n🔢 Terminación <b>1 y 2</b> (Hol 1 y 2)."
    elif dia_semana == 4: regla = "🔵 <b>Engomado AZUL</b>\n🔢 Terminación <b>9 y 0</b> (Hol 1 y 2)."
    elif dia_semana == 5:
        num_sabado = (fecha.day - 1) // 7 + 1
        if num_sabado in [1, 3]: 
            regla = f"⚠️ <b>{num_sabado}º SÁBADO:</b>\n🚫 Descansan: <b>Holograma 1 (IMPAR)</b> + Todos Hol 2."
        elif num_sabado in [2, 4]: 
            regla = f"⚠️ <b>{num_sabado}º SÁBADO:</b>\n🚫 Descansan: <b>Holograma 1 (PAR)</b> + Todos Hol 2."
        else: 
            regla = f"⚠️ <b>5º SÁBADO:</b>\n🚫 Descansan: <b>Solo Holograma 2</b>."
    elif dia_semana == 6: 
        regla = "✅ <b>DOMINGO:</b> Todos circulan."
    
    return nombre_dia, regla

# --- 2. DETECTOR DE CONTINGENCIA (SEMÁFORO) ---
def revisar_contingencia(fecha_hoy_mx):
    estado = "NORMAL" # Puede ser: NORMAL, POSIBLE, ACTIVADA
    fuente = ""
    detalles = ""
    dia_actual = fecha_hoy_mx.date()

    # Función auxiliar para analizar texto
    def analizar_texto(texto, link, origen):
        txt = texto.lower()
        if "contingencia" in txt:
            # Prioridad 1: Activación Confirmada
            if any(k in txt for k in KEYWORDS_ACTIVACION):
                if not "falsa" in txt and not "suspendió" in txt:
                    return "ACTIVADA", f"{origen}", f"<a href='{link}'>{texto}</a>"
            
            # Prioridad 2: Posibilidad (Solo si no encontramos activada antes)
            if any(k in txt for k in KEYWORDS_POSIBILIDAD):
                return "POSIBLE", f"{origen}", f"<a href='{link}'>{texto}</a>"
        return None, None, None

    # A) Google News
    try:
        feed = feedparser.parse(RSS_NEWS)
        for entry in feed.entries:
            if hasattr(entry, 'published_parsed'):
                fecha_noticia = datetime(*entry.published_parsed[:6], tzinfo=pytz.utc).astimezone(fecha_hoy_mx.tzinfo).date()
                if fecha_noticia != dia_actual: continue 
                
                nuevo_estado, nueva_fuente, info = analizar_texto(entry.title, entry.link, "Google News")
                
                if nuevo_estado == "ACTIVADA": # Si es roja, rompemos el ciclo y retornamos
                    return "ACTIVADA", nueva_fuente, info
                elif nuevo_estado == "POSIBLE": # Si es amarilla, guardamos pero seguimos buscando una roja
                    estado = "POSIBLE"
                    fuente = nueva_fuente
                    detalles = info
    except: pass

    # B) Twitter (Si no hemos encontrado ACTIVADA)
    if estado != "ACTIVADA":
        try:
            scraper = Nitter(log_level=1, skip_instance_check=False)
            tweets = scraper.get_tweets(TWITTER_USER, mode='user', number=5)
            if tweets and 'tweets' in tweets:
                for t in tweets['tweets']:
                    es_reciente = False
                    hoy_str = fecha_hoy_mx.strftime("%b %-d")
                    if "m" in t['date'] or "h" in t['date'] or hoy_str in t['date']: es_reciente = True

                    if es_reciente:
                        nuevo_estado, nueva_fuente, info = analizar_texto(t['text'], t['link'], "Twitter (CAMe)")
                        if nuevo_estado == "ACTIVADA":
                            return "ACTIVADA", nueva_fuente, info
                        elif nuevo_estado == "POSIBLE" and estado == "NORMAL":
                            estado = "POSIBLE"
                            fuente = nueva_fuente
                            detalles = info
        except: pass

    return estado, fuente, detalles

# --- ORQUESTADOR ---
def main():
    tz_mx = pytz.timezone('America/Mexico_City')
    fecha_hoy = datetime.now(tz_mx)
    
    es_manana = (fecha_hoy.hour < 12)
    fecha_objetivo = fecha_hoy if es_manana else fecha_hoy + timedelta(days=1)
    contexto_tiempo = "HOY" if es_manana else "MAÑANA"
    
    nombre_dia_obj, regla_obj = obtener_regla(fecha_objetivo)
    estado_alerta, fuente_cont, info_cont = revisar_contingencia(fecha_hoy)
    fecha_str = fecha_objetivo.strftime('%d/%m')

    # --- CONSTRUCCIÓN DEL MENSAJE ---
    msg = "📡 <i>Tras analizar monitores atmosféricos y boletines oficiales, el reporte es el siguiente:</i>\n\n"
    
    # CASO 1: ROJO (Activada)
    if estado_alerta == "ACTIVADA":
        msg += f"🚨 <b>ESTADO: CONTINGENCIA FASE 1 ({contexto_tiempo})</b>\n"
        msg += "──────────────────\n"
        msg += f"📅 <b>{nombre_dia_obj} {fecha_str}</b>\n\n"
        msg += "⛔ <b>RESTRICCIONES AMBIENTALES:</b>\n"
        msg += "🚫 <b>Holograma 2:</b> TODOS descansan.\n"
        msg += "🚫 <b>Holograma 1:</b> Terminación PAR/IMPAR + Placa habitual.\n"
        msg += "🚫 <b>Holograma 0/00:</b> Exentos.\n\n"
        msg += f"<b>🔍 CONFIRMACIÓN OFICIAL ({fuente_cont}):</b>\n{info_cont}"

    # CASO 2: AMARILLO (Posible) -> TU SOLICITUD
    elif estado_alerta == "POSIBLE":
        msg += f"⚠️ <b>ESTADO: RIESGO DE CONTINGENCIA ({contexto_tiempo})</b>\n"
        msg += "──────────────────\n"
        msg += f"📅 <b>{nombre_dia_obj} {fecha_str}</b>\n\n"
        msg += f"🚗 <b>NO CIRCULA (Por ahora normal):</b>\n"
        msg += f"{regla_obj}\n\n"
        msg += "👁️ <b>OJO: ALERTA PREVENTIVA</b>\n"
        msg += "Existen condiciones para una posible activación. Mantente pendiente.\n"
        msg += f"<b>📰 Noticia detectada:</b>\n{info_cont}"

    # CASO 3: VERDE (Normal)
    else:
        msg += f"✅ <b>ESTADO: SIN CONTINGENCIA ({contexto_tiempo})</b>\n"
        msg += "──────────────────\n"
        msg += f"📅 <b>{nombre_dia_obj} {fecha_str}</b>\n\n"
        msg += f"🚗 <b>NO CIRCULA:</b>\n"
        msg += f"{regla_obj}\n\n"
        msg += "<i>Calidad del aire dentro de parámetros permitidos.</i>"

    enviar_telegram(msg)

if __name__ == "__main__":
    main()
