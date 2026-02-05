import os
import time
import requests
import feedparser
import pytz
from datetime import datetime
from ntscraper import Nitter

# --- CONFIGURACIÓN ---
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# RSS: Pedimos noticias de último momento (when:1d), pero filtraremos en Python
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

# --- 1. CÁLCULO MATEMÁTICO (HOY NO CIRCULA NORMAL) ---
def obtener_regla_normal(fecha):
    dia_semana = fecha.weekday() 
    if dia_semana == 0: return "🟡 <b>Engomado AMARILLO</b>\n🔢 Terminación <b>5 y 6</b>"
    elif dia_semana == 1: return "🌸 <b>Engomado ROSA</b>\n🔢 Terminación <b>7 y 8</b>"
    elif dia_semana == 2: return "🔴 <b>Engomado ROJO</b>\n🔢 Terminación <b>3 y 4</b>"
    elif dia_semana == 3: return "🟢 <b>Engomado VERDE</b>\n🔢 Terminación <b>1 y 2</b>"
    elif dia_semana == 4: return "🔵 <b>Engomado AZUL</b>\n🔢 Terminación <b>9 y 0</b>"
    elif dia_semana == 5: return "⚠️ <b>SÁBADO:</b> Revisar holograma.\n<i>(Impares 1er/3er sáb - Pares 2do/4to sáb)</i>"
    elif dia_semana == 6: return "✅ <b>DOMINGO:</b> Todos circulan (Salvo contingencia)."
    return "Error fecha"

# --- 2. DETECTOR DE CONTINGENCIA (CON FILTRO DE FECHA) ---
def revisar_contingencia(fecha_hoy_mx):
    print("🔎 Buscando alertas de Contingencia (SOLO DE HOY)...")
    alerta_encontrada = False
    fuente = ""
    detalles = ""
    
    # Extraemos solo la fecha (YYYY-MM-DD) para comparar
    dia_actual = fecha_hoy_mx.date()

    # --- FUENTE A: Google News ---
    try:
        feed = feedparser.parse(RSS_NEWS)
        for entry in feed.entries:
            if hasattr(entry, 'published_parsed'):
                # Convertir fecha de la noticia a Zona Horaria México
                fecha_noticia = datetime(*entry.published_parsed[:6], tzinfo=pytz.utc).astimezone(fecha_hoy_mx.tzinfo).date()
                
                # 🛑 FILTRO ESTRICTO: Si la noticia no es de HOY, la ignoramos.
                if fecha_noticia != dia_actual:
                    continue 

                # Si es de hoy, revisamos el texto
                txt = entry.title.lower()
                if "activa" in txt and "contingencia" in txt:
                    alerta_encontrada = True
                    fuente = "Google News (Hoy)"
                    detalles = f"<a href='{entry.link}'>{entry.title}</a>"
                    break
    except Exception as e: print(f"Error RSS: {e}")

    # --- FUENTE B: Twitter CAMe ---
    if not alerta_encontrada:
        try:
            scraper = Nitter(log_level=1, skip_instance_check=False)
            tweets = scraper.get_tweets(TWITTER_USER, mode='user', number=5)
            if tweets and 'tweets' in tweets:
                for t in tweets['tweets']:
                    txt = t['text'].lower()
                    
                    # Parsear fecha del tweet (Nitter suele dar formato "Feb 5, 2024 · ...")
                    # Método simplificado: Checar si dice "h" (horas) o "m" (minutos) en la fecha relativa
                    # O intentar parsear si es posible. Para ser robustos, usamos palabras clave urgentes.
                    
                    es_reciente = False
                    fecha_tweet_str = t['date']
                    
                    # Si dice "m" (minutos) o "h" (horas) es de hoy seguro. 
                    # Si dice "Feb 5" y hoy es Feb 5, también.
                    mes_dia_hoy = fecha_hoy_mx.strftime("%b %-d") # Ej: "Feb 5"
                    
                    if "m" in fecha_tweet_str or "h" in fecha_tweet_str or mes_dia_hoy in fecha_tweet_str:
                         es_reciente = True

                    if es_reciente and "se activa" in txt and "contingencia" in txt:
                        alerta_encontrada = True
                        fuente = "Twitter @CAMegalopolis (Hoy)"
                        detalles = f"{t['text'][:100]}..."
                        break
        except Exception as e: print(f"Error Twitter: {e}")

    return alerta_encontrada, fuente, detalles

def main():
    # Definir zona horaria y fecha actual UNA SOLA VEZ
    tz_mx = pytz.timezone('America/Mexico_City')
    fecha_hoy = datetime.now(tz_mx)
    hora = fecha_hoy.hour
    
    # 1. Hoy No Circula Normal
    regla_normal = obtener_regla_normal(fecha_hoy)
    
    # 2. Revisar Contingencia (Pasamos la fecha para filtrar)
    hay_contingencia, fuente_cont, info_cont = revisar_contingencia(fecha_hoy)
    
    # --- MENSAJE ---
    saludo = "☀️ <b>BUENOS DÍAS</b>" if hora < 12 else "🌙 <b>REPORTE NOCTURNO</b>"
    msg = f"{saludo}\n📅 <b>{fecha_hoy.strftime('%d/%m/%Y')}</b>\n\n"
    
    if hay_contingencia:
        msg += "🚨🚨 <b>¡ALERTA: CONTINGENCIA AMBIENTAL!</b> 🚨🚨\n"
        msg += f"Se detectaron avisos OFICIALES emitidos HOY.\n"
        msg += f"<b>Fuente:</b> {fuente_cont}\n"
        msg += f"<b>Detalle:</b> {info_cont}\n\n"
        msg += "<i>⚠️ Es altamente probable que aplique DOBLE HOY NO CIRCULA.</i>"
    else:
        msg += "🚗 <b>HOY NO CIRCULA (Normal):</b>\n"
        msg += f"{regla_normal}\n\n"
        msg += "✅ <b>Sin Contingencia Ambiental.</b>\n"
        msg += "<i>(Se escanearon noticias exclusivamente del día de hoy)</i>"

    enviar_telegram(msg)

if __name__ == "__main__":
    main()
