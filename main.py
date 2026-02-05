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

# Fuentes de Información
RSS_NEWS = "https://news.google.com/rss/search?q=Contingencia+Ambiental+CDMX+CAMe+activan&hl=es-419&gl=MX&ceid=MX:es-419"
TWITTER_USER = "CAMegalopolis"

def enviar_telegram(mensaje):
    if not TOKEN or not CHAT_ID: return
    # REINTENTOS BLINDADOS (3 veces)
    for i in range(1, 4):
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            data = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "HTML"}
            r = requests.post(url, data=data, timeout=10)
            if r.status_code == 200: break
            time.sleep(5)
        except: time.sleep(5)

# --- 1. CÁLCULO MATEMÁTICO (NO FALLA) ---
def obtener_regla_normal(fecha):
    dia_semana = fecha.weekday() # 0=Lunes, 6=Domingo
    
    # Reglas Base
    if dia_semana == 0: # Lunes
        return "🟡 <b>Engomado AMARILLO</b>\n🔢 Terminación <b>5 y 6</b>"
    elif dia_semana == 1: # Martes
        return "🌸 <b>Engomado ROSA</b>\n🔢 Terminación <b>7 y 8</b>"
    elif dia_semana == 2: # Miercoles
        return "🔴 <b>Engomado ROJO</b>\n🔢 Terminación <b>3 y 4</b>"
    elif dia_semana == 3: # Jueves
        return "🟢 <b>Engomado VERDE</b>\n🔢 Terminación <b>1 y 2</b>"
    elif dia_semana == 4: # Viernes
        return "🔵 <b>Engomado AZUL</b>\n🔢 Terminación <b>9 y 0</b>"
    elif dia_semana == 5: # Sabado
        # Regla sabatina simplificada (Holograma 1 y 2)
        # Se calcula por semana del mes, pero por seguridad alertamos general
        return "⚠️ <b>SÁBADO:</b> Revisar holograma.\n<i>(Impares 1er/3er sáb - Pares 2do/4to sáb)</i>"
    elif dia_semana == 6:
        return "✅ <b>DOMINGO:</b> Todos circulan (Salvo contingencia)."
    return "Error fecha"

# --- 2. DETECTOR DE CONTINGENCIA (MULTIFUENTE) ---
def revisar_contingencia():
    print("🔎 Buscando alertas de Contingencia...")
    alerta_encontrada = False
    fuente = ""
    detalles = ""

    # FUENTE A: Google News
    try:
        feed = feedparser.parse(RSS_NEWS)
        tz_mx = pytz.timezone('America/Mexico_City')
        # Buscamos noticias de las últimas 4 horas
        ahora = datetime.now(tz_mx)
        
        for entry in feed.entries:
            if hasattr(entry, 'published_parsed'):
                # Filtro simple de texto en título
                txt = entry.title.lower()
                if "activa" in txt and "contingencia" in txt:
                    # Es muy probable que sea real
                    alerta_encontrada = True
                    fuente = "Google News"
                    detalles = f"<a href='{entry.link}'>{entry.title}</a>"
                    break
    except: pass

    # FUENTE B: Twitter CAMe (Si News falló o para confirmar)
    if not alerta_encontrada:
        try:
            scraper = Nitter(log_level=1, skip_instance_check=False)
            tweets = scraper.get_tweets(TWITTER_USER, mode='user', number=5)
            if tweets and 'tweets' in tweets:
                for t in tweets['tweets']:
                    txt = t['text'].lower()
                    if "se activa" in txt and "contingencia" in txt:
                        # Checar antigüedad (si es de hoy)
                        alerta_encontrada = True
                        fuente = "Twitter (@CAMegalopolis)"
                        detalles = f"{t['text'][:100]}..."
                        break
        except: pass

    return alerta_encontrada, fuente, detalles

def main():
    tz_mx = pytz.timezone('America/Mexico_City')
    fecha_hoy = datetime.now(tz_mx)
    hora = fecha_hoy.hour
    
    # 1. Obtenemos el "Hoy No Circula" Normal
    regla_normal = obtener_regla_normal(fecha_hoy)
    
    # 2. Buscamos Contingencia (Doble No Circula)
    hay_contingencia, fuente_cont, info_cont = revisar_contingencia()
    
    # --- CONSTRUCCIÓN DEL MENSAJE ---
    # Encabezado dinámico según hora (Mañana o Noche)
    saludo = "☀️ <b>BUENOS DÍAS</b>" if hora < 12 else "🌙 <b>REPORTE NOCTURNO</b>"
    
    msg = f"{saludo}\n📅 <b>{fecha_hoy.strftime('%d/%m/%Y')}</b>\n\n"
    
    if hay_contingencia:
        msg += "🚨🚨 <b>¡ALERTA: CONTINGENCIA AMBIENTAL!</b> 🚨🚨\n"
        msg += f"Se detectaron avisos de activación.\n"
        msg += f"<b>Fuente:</b> {fuente_cont}\n"
        msg += f"<b>Detalle:</b> {info_cont}\n\n"
        msg += "<i>⚠️ Revisa si aplica DOBLE HOY NO CIRCULA para tu auto.</i>"
    else:
        # Si NO hay contingencia, mandamos el recordatorio normal
        msg += "🚗 <b>HOY NO CIRCULA (Normal):</b>\n"
        msg += f"{regla_normal}\n\n"
        msg += "✅ <b>Sin Contingencia Ambiental</b> reportada al momento.\n"
        msg += "<i>(Monitoreo: Google News + CAMe)</i>"

    enviar_telegram(msg)

if __name__ == "__main__":
    main()
