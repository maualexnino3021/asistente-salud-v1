import mysql.connector
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta

# --- CONFIGURACIÓN (Tus credenciales actuales) ---
config = {
    'host': 'gateway01.us-east-1.prod.aws.tidbcloud.com',
    'port': 4000,
    'user': '39hpidXc8KL7sEA.root',
    'password': 'HwJbEPQQNL7rhRjF',
    'database': 'test',
    'autocommit': True
}

TELEGRAM_TOKEN = '8444851001:AAEZBqfJcgUasPLeu1nsD2xcG0OrkPvrwbM'
TELEGRAM_CHAT_ID = '1677957851'
EMAIL_APP_PASSWORD = 'wspb oiqd zriv tqpl'
EMAIL_SENDER = 'unamauricio2013@gmail.com'
EMAIL_RECEIVER = 'maualexnino@gmail.com'

def enviar_alerta(mensaje, paciente):
    """Envía la notificación física a Telegram y Email."""
    texto_final = f"⚠️ RECORDATORIO PRÓXIMO\nPACIENTE: {paciente}\n\n{mensaje}"
    
    # Enviar Telegram
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={'chat_id': TELEGRAM_CHAT_ID, 'text': texto_final}, timeout=10)
    except Exception as e:
        print(f"Error Telegram: {e}")

    # Enviar Email
    try:
        msg = MIMEText(texto_final)
        msg['Subject'] = f'Recordatorio de Salud - {paciente}'
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
    except Exception as e:
        print(f"Error Email: {e}")

def revisar_base_de_datos():
    hoy = datetime.now().date()
    # Revisamos eventos para hoy, mañana y pasado mañana (margen de 3 días)
    rango_fechas = [hoy, hoy + timedelta(days=1), hoy + timedelta(days=3)]
    
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        
        # Buscamos en todas las columnas de fechas de tu tabla
        query = """
            SELECT * FROM registros_salud 
            WHERE prox_retiro IN (%s, %s, %s) 
               OR prox_examen IN (%s, %s, %s)
               OR prox_cita IN (%s, %s, %s)
               OR prog_fecha IN (%s, %s, %s)
        """
        params = rango_fechas * 4 # Repetimos las 3 fechas para las 4 columnas
        cursor.execute(query, params)
        pendientes = cursor.fetchall()

        if not pendientes:
            print("No hay recordatorios para los próximos días.")
            return

        for p in pendientes:
            # Construimos un mensaje sencillo basado en lo que encuentre
            msg = "Tiene un evento de salud programado para los próximos días. Por favor, revise su historial."
            enviar_alerta(msg, p['paciente'])
            print(f"Alerta enviada para {p['paciente']}")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error de conexión: {e}")

if __name__ == "__main__":
    revisar_base_de_datos()