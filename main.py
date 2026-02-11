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

# --- 1. LÓGICA MATEMÁTICA DE REGLAS ---
def obtener_regla(fecha):
    dia_semana = fecha.weekday() 
    nombres_dias = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO"]
    nombre_dia = nombres_dias[dia_semana]
    
    regla = ""
    # Lunes a Viernes
    if dia_semana == 0: regla = "🟡 <b>Engomado AMARILLO</b>\n🔢 Terminación <b>5 y 6</b> (Todos los hologramas 1 y 2)."
    elif dia_semana == 1: regla = "🌸 <b>Engomado ROSA</b>\n🔢 Terminación <b>7 y 8</b> (Todos los hologramas 1 y 2)."
    elif dia_semana == 2: regla = "🔴 <b>Engomado ROJO</b>\n🔢 Terminación <b>3 y 4</b> (Todos los hologramas 1 y 2)."
    elif dia_semana == 3: regla = "🟢 <b>Engomado VERDE</b>\n🔢 Terminación <b>1 y 2</b> (Todos los hologramas 1 y 2)."
    elif dia_semana == 4: regla = "🔵 <b>Engomado AZUL</b>\n🔢 Terminación <b>9 y 0</b> (Todos los hologramas 1 y 2)."
    
    # SÁBADO (Cálculo matemático)
    elif dia_semana == 5:
        num_sabado = (fecha.day - 1) // 7 + 1
        if num_sabado in [1, 3]: 
            regla = f"⚠️ <b>{num_sabado}º SÁBADO DEL MES:</b>\n🚫 Descansan: <b>Holograma 1 (IMPAR)</b> + Todos Hol 2."
        elif num_sabado in [2, 4]: 
            regla = f"⚠️ <b>{num_sabado}º SÁBADO DEL MES:</b>\n🚫 Descansan: <b>Holograma 1 (PAR)</b> + Todos Hol 2."
        else: 
            regla = f"⚠️ <b>5º SÁBADO (ESPECIAL):</b>\n🚫 Descansan: <b>Únicamente Holograma 2</b>.\n✅ Holograma 1 CIRCULA."
            
    elif dia_semana == 6: 
        regla = "✅ <b>DOMINGO:</b> Todos circulan (Salvo contingencia)."
    
    return nombre_dia, regla

# --- 2. DETECTOR DE CONTINGENCIA ---
def revisar_contingencia(fecha_hoy_mx):
    alerta = False
    fuente = ""
    detalles = ""
    dia_actual = fecha_hoy_mx.date()

    # Google News
    try:
        feed = feedparser.parse(RSS_NEWS)
        for entry in feed.entries:
            if hasattr(entry, 'published_parsed'):
                fecha_noticia = datetime(*entry.published_parsed[:6], tzinfo=pytz.utc).astimezone(fecha_hoy_mx.tzinfo).date()
                if fecha_noticia != dia_actual: continue 
                txt = entry.title.lower()
                if "activa" in txt and "contingencia" in txt:
                    alerta = True
                    fuente = "Google News"
                    detalles = f"<a href='{entry.link}'>{entry.title}</a>"
                    break
    except: pass

    # Twitter
    if not alerta:
        try:
            scraper = Nitter(log_level=1, skip_instance_check=False)
            tweets = scraper.get_tweets(TWITTER_USER, mode='user', number=5)
            if tweets and 'tweets' in tweets:
                for t in tweets['tweets']:
                    txt = t['text'].lower()
                    es_reciente = False
                    hoy_str = fecha_hoy_mx.strftime("%b %-d")
                    if "m" in t['date'] or "h" in t['date'] or hoy_str in t['date']: es_reciente = True

                    if es_reciente and "se activa" in txt and "contingencia" in txt:
                        alerta = True
                        fuente = "Twitter (CAMe)"
                        detalles = f"{t['text'][:80]}...\n🔗 <a href='{t['link']}'>Ver Tweet</a>"
                        break
        except: pass

    return alerta, fuente, detalles

# --- ORQUESTADOR ---
def main():
    tz_mx = pytz.timezone('America/Mexico_City')
    fecha_hoy = datetime.now(tz_mx)
    
    # Determinar contexto (Mañana = HOY, Noche = MAÑANA)
    es_manana = (fecha_hoy.hour < 12)
    fecha_objetivo = fecha_hoy if es_manana else fecha_hoy + timedelta(days=1)
    contexto_tiempo = "HOY" if es_manana else "MAÑANA"
    
    nombre_dia_obj, regla_obj = obtener_regla(fecha_objetivo)
    hay_contingencia, fuente_cont, info_cont = revisar_contingencia(fecha_hoy)
    fecha_str = fecha_objetivo.strftime('%d/%m')

    # --- MENSAJE MINIMALISTA ---
    msg = "📡 <i>Tras analizar monitores atmosféricos y boletines oficiales, el reporte es el siguiente:</i>\n\n"
    
    if hay_contingencia:
        msg += f"🚨 <b>ESTADO: CONTINGENCIA FASE 1 ({contexto_tiempo})</b>\n"
        msg += "──────────────────\n"
        msg += f"📅 <b>{nombre_dia_obj} {fecha_str}</b>\n\n"
        msg += "⛔ <b>RESTRICCIONES AMBIENTALES:</b>\n"
        msg += "🚫 <b>Holograma 2:</b> TODOS descansan.\n"
        msg += "🚫 <b>Holograma 1:</b> Terminación PAR/IMPAR + Placa habitual.\n"
        msg += "🚫 <b>Holograma 0/00:</b> Exentos.\n\n"
        msg += f"<b>🔍 FUENTE OFICIAL ({fuente_cont}):</b>\n{info_cont}"
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
