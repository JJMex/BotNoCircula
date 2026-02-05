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

# --- 1. HOY NO CIRCULA NORMAL ---
def obtener_regla_normal(fecha):
    dia_semana = fecha.weekday() 
    nombres_dias = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO"]
    nombre_dia = nombres_dias[dia_semana]
    
    regla = ""
    if dia_semana == 0: regla = "🟡 <b>Engomado AMARILLO</b>\n🔢 Terminación <b>5 y 6</b>"
    elif dia_semana == 1: regla = "🌸 <b>Engomado ROSA</b>\n🔢 Terminación <b>7 y 8</b>"
    elif dia_semana == 2: regla = "🔴 <b>Engomado ROJO</b>\n🔢 Terminación <b>3 y 4</b>"
    elif dia_semana == 3: regla = "🟢 <b>Engomado VERDE</b>\n🔢 Terminación <b>1 y 2</b>"
    elif dia_semana == 4: regla = "🔵 <b>Engomado AZUL</b>\n🔢 Terminación <b>9 y 0</b>"
    elif dia_semana == 5: regla = "⚠️ <b>SÁBADO:</b> Revisar holograma.\n<i>(Impares 1er/3er sáb - Pares 2do/4to sáb)</i>"
    elif dia_semana == 6: regla = "✅ <b>DOMINGO:</b> Todos circulan (Salvo contingencia)."
    
    return nombre_dia, regla

# --- 2. DETECTOR DE CONTINGENCIA ---
def revisar_contingencia(fecha_hoy_mx):
    print("🔎 Buscando alertas de Contingencia (Noticias de HOY)...")
    alerta_encontrada = False
    fuente = ""
    detalles = ""
    dia_actual = fecha_hoy_mx.date()

    # Fuente A: Google News
    try:
        feed = feedparser.parse(RSS_NEWS)
        for entry in feed.entries:
            if hasattr(entry, 'published_parsed'):
                fecha_noticia = datetime(*entry.published_parsed[:6], tzinfo=pytz.utc).astimezone(fecha_hoy_mx.tzinfo).date()
                if fecha_noticia != dia_actual: continue 

                txt = entry.title.lower()
                if "activa" in txt and "contingencia" in txt:
                    alerta_encontrada = True
                    fuente = "Google News"
                    detalles = f"<a href='{entry.link}'>{entry.title}</a>"
                    break
    except: pass

    # Fuente B: Twitter
    if not alerta_encontrada:
        try:
            scraper = Nitter(log_level=1, skip_instance_check=False)
            tweets = scraper.get_tweets(TWITTER_USER, mode='user', number=5)
            if tweets and 'tweets' in tweets:
                for t in tweets['tweets']:
                    txt = t['text'].lower()
                    es_reciente = False
                    fecha_str = t['date']
                    hoy_str = fecha_hoy_mx.strftime("%b %-d")
                    if "m" in fecha_str or "h" in fecha_str or hoy_str in fecha_str:
                         es_reciente = True

                    if es_reciente and "se activa" in txt and "contingencia" in txt:
                        alerta_encontrada = True
                        fuente = "Twitter @CAMegalopolis"
                        detalles = f"{t['text'][:100]}..."
                        break
        except: pass

    return alerta_encontrada, fuente, detalles

def main():
    tz_mx = pytz.timezone('America/Mexico_City')
    fecha_hoy = datetime.now(tz_mx)
    hora = fecha_hoy.hour
    
    # Determinar si es reporte de Mañana (HOY) o Noche (MAÑANA)
    es_manana = (hora < 12)
    
    if es_manana:
        fecha_objetivo = fecha_hoy
        titulo = "☀️ <b>BUENOS DÍAS</b>"
        contexto_tiempo = "HOY"
    else:
        fecha_objetivo = fecha_hoy + timedelta(days=1)
        titulo = "🌙 <b>REPORTE NOCTURNO</b>"
        contexto_tiempo = "MAÑANA"

    # Regla normal del día objetivo
    nombre_dia_obj, regla_obj = obtener_regla_normal(fecha_objetivo)
    
    # Revisamos contingencia (basado en noticias de HOY)
    hay_contingencia, fuente_cont, info_cont = revisar_contingencia(fecha_hoy)
    
    # --- CONSTRUCCIÓN DEL MENSAJE ---
    msg = f"{titulo}\n"
    msg += f"📅 <b>{contexto_tiempo} {nombre_dia_obj}</b> ({fecha_objetivo.strftime('%d/%m')})\n\n"
    
    if hay_contingencia:
        # --- MENSAJE DE ALERTA MODIFICADO ---
        msg += "🚨🚨 <b>¡ALERTA: CONTINGENCIA AMBIENTAL!</b> 🚨🚨\n"
        msg += f"Se detectaron avisos oficiales activados hoy.\n"
        msg += f"<b>Fuente:</b> {fuente_cont}\n"
        msg += f"<b>Detalle:</b> {info_cont}\n\n"
        
        msg += "⛔ <b>VEHÍCULOS QUE NO CIRCULAN (Fase 1):</b>\n"
        msg += "🚫 <b>Holograma 2:</b> TODOS descansan.\n"
        msg += "🚫 <b>Holograma 1:</b> Descansan placas habituales + Terminación Par/Impar (ver enlace).\n"
        msg += "🚫 <b>Sin Holograma:</b> TODOS descansan.\n"
        msg += "✅ <b>Hologramas 0 y 00:</b> EXENTOS (Circulan)."
    else:
        # --- MENSAJE NORMAL ---
        msg += f"🚗 <b>{contexto_tiempo} NO CIRCULA:</b>\n"
        msg += f"{regla_obj}\n\n"
        msg += "✅ <b>Sin Contingencia Ambiental</b> reportada.\n"

    enviar_telegram(msg)

if __name__ == "__main__":
    main()
