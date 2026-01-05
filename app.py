import streamlit as st
import mysql.connector
import holidays
import pytz
import requests
import smtplib
import time
import sys
import os
import base64
from email.mime.text import MIMEText
from gtts import gTTS
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestor de Salud IA", layout="wide", initial_sidebar_state="collapsed")

# --- ESTILOS CSS PERSONALIZADOS (Colores y Responsividad) ---
def local_css():
    st.markdown(f"""
    <style>
    /* Fondo General */
    .stApp {{
        background: url("https://i.ibb.co/5xG1Gzvh/background") no-repeat center center fixed;
        background-size: cover;
    }}
    
    /* Contenedor principal para evitar fondos blancos */
    .main .block-container {{
        background-color: rgba(0, 0, 50, 0.8); /* Azul muy oscuro semi-transparente */
        border-radius: 20px;
        padding: 20px;
        color: #D4AF37; /* Dorado */
    }}

    /* Textos y Encabezados */
    h1, h2, h3, p, span, label {{
        color: #7DF9FF !important; /* Azul Eléctrico */
        font-family: 'Arial', sans-serif;
    }}

    /* Botón REGRESAR (Superior Derecha) */
    .btn-regresar {{
        position: fixed;
        top: 10px;
        right: 10px;
        background-color: #FFFF00 !important; /* Amarillo Intenso */
        color: #0000FF !important; /* Letras Azules */
        border: 2px solid #000000 !important; /* Borde Negro */
        padding: 10px 20px;
        border-radius: 10px;
        font-weight: bold;
        text-decoration: none;
        z-index: 9999;
    }}

    /* Estilos de inputs */
    .stTextInput>div>div>input, .stSelectbox>div>div>select {{
        background-color: #C0C0C0 !important; /* Plateado Brillante */
        color: #800020 !important; /* Vinotinto */
        font-weight: bold;
    }}

    /* Pie de página fijo */
    .footer {{
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #800020; /* Vinotinto */
        color: #D4AF37; /* Dorado */
        text-align: center;
        padding: 10px;
        font-size: 12px;
        z-index: 1000;
    }}

    /* Botones de Streamlit */
    .stButton>button {{
        background-color: #D4AF37 !important; /* Dorado */
        color: #800020 !important; /* Vinotinto */
        border-radius: 10px;
        border: 1px solid #C0C0C0;
    }}
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- CONFIGURACIÓN DE CREDENCIALES (IGUAL AL ORIGINAL) ---
config = {
    'host': 'gateway01.us-east-1.prod.aws.tidbcloud.com',
    'port': 4000,
    'user': '39hpidXc8KL7sEA.root',
    'password': 'HwJbEPQQNL7rhRjF',
    'database': 'test',
    'autocommit': True,
    'ssl_verify_cert': True,
    'ssl_ca': '/etc/ssl/certs/ca-certificates.crt'
}

TELEGRAM_TOKEN = '8444851001:AAEZBqfJcgUasPLeu1nsD2xcG0OrkPvrwbM'
EMAIL_APP_PASSWORD = 'wspb oiqd zriv tqpl'
EMAIL_SENDER = 'unamauricio2013@gmail.com'
EMAIL_RECEIVER = 'maualexnino@gmail.com'
TELEGRAM_CHAT_ID = '1677957851'

festivos_co = holidays.CO(years=[2026, 2027, 2028, 2029])
tz_co = pytz.timezone('America/Bogota')

# --- FUNCIONES DE VOZ (ADAPTADA PARA STREAMLIT) ---
def hablar(texto):
    if texto:
        try:
            tts = gTTS(text=texto, lang='es', tld='com.co')
            tts.save('audio.mp3')
            audio_file = open('audio.mp3', 'rb')
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format='audio/mp3', autoplay=True)
            os.remove('audio.mp3')
        except Exception as e:
            st.error(f"Error de voz: {e}")

# --- LÓGICA DE NOTIFICACIONES ---
def enviar_notificaciones(mensaje_texto, nombre_paciente):
    mensaje_personalizado = f"PACIENTE: {nombre_paciente}\n{mensaje_texto}"
    # Telegram
    try:
        url_tg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': f"🔔 RECORDATORIO SALUD:\n{mensaje_personalizado}", 'parse_mode': 'Markdown'}
        requests.post(url_tg, data=payload, timeout=10)
    except: pass
    # Email
    try:
        msg = MIMEText(mensaje_personalizado)
        msg['Subject'] = f'Recordatorio de Salud - {nombre_paciente}'
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
    except: pass

# --- FUNCIONES DE FECHAS ---
def obtener_dia_habil_anterior(fecha, festivos):
    while fecha.weekday() == 6 or fecha in festivos:
        fecha -= timedelta(days=1)
    return fecha

def sumar_dias_habiles(fecha_inicio, dias_a_sumar, festivos):
    fecha_actual = fecha_inicio
    dias_contados = 0
    while dias_contados < dias_a_sumar:
        fecha_actual += timedelta(days=1)
        if fecha_actual.weekday() != 6 and fecha_actual not in festivos:
            dias_contados += 1
    return fecha_actual

# --- BASE DE DATOS ---
def verificar_conexion():
    try:
        conn = mysql.connector.connect(**config)
        return conn.is_connected()
    except: return False

def guardar_en_db(p):
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        query = """
            INSERT INTO registros_salud 
            (paciente, fecha_registro, med_tipo, prox_retiro, ex_tipo, prox_examen, cita_tipo, prox_cita, prog_categoria, prog_fecha, prog_hora)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        vals = (
            p.get('paciente'), datetime.now(tz_co).replace(tzinfo=None),
            p.get('med_tipo'), p.get('prox_retiro_dt').date() if 'prox_retiro_dt' in p else None,
            p.get('ex_tipo'), p.get('prox_examen_dt').date() if 'prox_examen_dt' in p else None,
            p.get('cita_tipo'), p.get('prox_cita_dt').date() if 'prox_cita_dt' in p and p['prox_cita_dt'] else None,
            p.get('prog_categoria'), 
            datetime.strptime(p['prog_fecha_str'], "%d/%m/%Y").date() if 'prog_fecha_str' in p else None,
            p.get('prog_hora')
        )
        cursor.execute(query, vals)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e: st.error(f"Error DB: {e}")

# --- GESTIÓN DE ESTADO (MÁQUINA DE ESTADOS) ---
if 'step' not in st.session_state:
    st.session_state.step = 'BIENVENIDA'
    st.session_state.p = {}
    st.session_state.contador_interacciones = 0
    st.session_state.nombre_paciente_global = ""

def gestionar_nombre():
    if st.session_state.contador_interacciones % 4 == 0 and st.session_state.nombre_paciente_global:
        st.session_state.contador_interacciones += 1
        return f"{st.session_state.nombre_paciente_global}, "
    st.session_state.contador_interacciones += 1
    return ""

# --- BOTÓN REGRESAR ---
st.markdown('<a href="/" class="btn-regresar">CANCELAR Y REGRESAR A LA PÁGINA PRINCIPAL</a>', unsafe_allow_html=True)

# --- AVATAR ---
st.image("https://i.ibb.co/XxD1CzWx/avatar", width=80)

# --- FLUJO PRINCIPAL ---
def main():
    if st.session_state.step == 'BIENVENIDA':
        msg = "Bienvenido al gestor de salud. Realizaremos preguntas para calcular o registrar sus fechas..."
        st.title(msg)
        hablar(msg)
        if st.button("Comenzar"):
            st.session_state.step = 'PEDIR_NOMBRE'
            st.rerun()

    elif st.session_state.step == 'PEDIR_NOMBRE':
        msg = "Para iniciar, por favor permítame saber el nombre del paciente"
        st.subheader(msg)
        hablar(msg)
        nombre = st.text_input("Nombre del Paciente:", key="input_nom")
        if nombre:
            if st.button("Confirmar Nombre"):
                st.session_state.nombre_paciente_global = nombre
                st.session_state.p['paciente'] = nombre
                st.session_state.step = 'MENU_PRINCIPAL'
                st.rerun()

    elif st.session_state.step == 'MENU_PRINCIPAL':
        msg_menu = "indique el motivo de su consulta: 1 Retiro medicinas, 2 Exámenes médicos, 3 Citas médicas, 4 Varias o 5 Registrar fecha programada."
        st.subheader(gestionar_nombre() + msg_menu)
        hablar(gestionar_nombre() + msg_menu)
        
        col1, col2 = st.columns(2)
        with col1:
            st.image("https://i.ibb.co/cXktVQbb/img1")
        with col2:
            opcion = st.selectbox("Seleccione una opción", ["", "1. Retiro medicinas", "2. Exámenes médicos", "3. Citas médicas", "4. Varias", "5. Registrar fecha programada"])
            
        if opcion != "":
            confirm_msg = f"Usted eligió {opcion}, ¿es correcto?"
            st.write(confirm_msg)
            hablar(confirm_msg)
            if st.button("Sí, es correcto"):
                st.session_state.opcion_menu = opcion[0]
                st.session_state.step = f'FLUJO_{opcion[0]}'
                st.rerun()
            if st.button("No, corregir"):
                st.rerun()

    # --- SIMPLIFICACIÓN DE FLUJOS (Mantenimiento de Lógica Original) ---
    elif st.session_state.step == 'FLUJO_1': # MEDICINAS
        hablar("Iniciamos cordialmente con el retiro de medicinas.")
        tipo = st.selectbox("¿Para qué es la medicina?", ["Medicina General", "Especialista", "Oncología", "Otra"])
        if tipo == "Especialista" or tipo == "Otra":
            especialidad = st.text_input("Especifique especialidad:")
            st.session_state.p["med_tipo"] = especialidad
        else:
            st.session_state.p["med_tipo"] = tipo
        
        entregas = st.number_input("¿Cuántas entregas le faltan?", min_value=0, step=1)
        fecha_ult = st.text_input("Fecha último retiro (DD/MM/AAAA):")
        
        if st.button("Calcular Fecha de Retiro"):
            try:
                fecha_base = datetime.strptime(fecha_ult, "%d/%m/%Y")
                prox = obtener_dia_habil_anterior(fecha_base + timedelta(days=28), festivos_co)
                st.session_state.p["prox_retiro_dt"] = prox
                st.session_state.p["num_entregas"] = entregas
                st.session_state.step = 'RESUMEN'
                st.rerun()
            except: st.error("Formato de fecha inválido")

    elif st.session_state.step == 'FLUJO_2': # EXÁMENES
        hablar("Continuamos gentilmente con sus exámenes médicos.")
        tipo = st.selectbox("Tipo de examen:", ["Sangre", "Rayos X", "Ultrasonido", "Resonancia o Tomografía", "Otro"])
        lugar = st.text_input("¿En qué lugar le dieron la orden?")
        fecha_o = st.text_input("Fecha de la orden (DD/MM/AAAA):")
        dias_e = st.number_input("¿En cuántos días debe entregar resultados?", min_value=0)
        
        if st.button("Programar Examen"):
            try:
                fecha_orden = datetime.strptime(fecha_o, "%d/%m/%Y")
                resta = dias_e - 32
                if resta < 0 or resta == 2: prox = sumar_dias_habiles(fecha_orden, 3, festivos_co)
                else: prox = obtener_dia_habil_anterior(fecha_orden + timedelta(days=resta), festivos_co)
                st.session_state.p["ex_tipo"] = tipo
                st.session_state.p["prox_examen_dt"] = prox
                st.session_state.step = 'RESUMEN'
                st.rerun()
            except: st.error("Fecha inválida")

    elif st.session_state.step == 'FLUJO_5': # PROGRAMADA
        st.image("https://i.ibb.co/fVVvSJFc/img2")
        hablar("Evaluaremos sus citas programadas.")
        cat = st.radio("¿Qué desea programar?", ["Examen Médico", "Cita Médica"])
        tipo = st.text_input("Especifique el área o especialidad:")
        lugar = st.text_input("Sitio a realizarse:")
        fecha_p = st.text_input("Fecha (DD/MM/AAAA):")
        hora_p = st.text_input("Hora (HH:MM):")
        
        if st.button("Confirmar Programación"):
            st.session_state.p.update({
                "prog_categoria": cat, "prog_tipo": tipo, "prog_lugar": lugar,
                "prog_fecha_str": fecha_p, "prog_hora": hora_p
            })
            # Lógica de notificaciones inmediata para opción 5
            notificacion_msg = f"Cita Programada: {cat} ({tipo}) en {lugar} el {fecha_p} a las {hora_p}."
            enviar_notificaciones(notificacion_msg, st.session_state.p['paciente'])
            st.session_state.step = 'RESUMEN'
            st.rerun()

    elif st.session_state.step == 'RESUMEN':
        st.header("--- RESUMEN DE FECHAS ---")
        p = st.session_state.p
        if "prox_retiro_dt" in p:
            msg = f"Su próximo retiro de medicina ({p.get('med_tipo', '')}) es el {p['prox_retiro_dt'].strftime('%d/%m/%Y')}"
            st.write(msg); hablar(msg)
        if "prox_examen_dt" in p:
            msg = f"Su examen ({p.get('ex_tipo', '')}) debe solicitarse el {p['prox_examen_dt'].strftime('%d/%m/%Y')}"
            st.write(msg); hablar(msg)
            
        guardar_en_db(p)
        
        notif_f = f"Se ha registrado su solicitud. Recibirá notificaciones en {EMAIL_RECEIVER} y Telegram."
        st.success(notif_f); hablar(notif_f)
        
        if st.button("¿Tiene algún otro requerimiento?"):
            st.session_state.step = 'MENU_PRINCIPAL'
            st.rerun()
        else:
            if st.button("Finalizar"):
                hablar("Muchas gracias por usar nuestro servicio. Que tenga un excelente día.")
                st.session_state.clear()
                st.rerun()

    # --- PIE DE PÁGINA ---
    st.markdown(f"""
    <div class="footer">
        Asistente IA de agendamiento y recordatorio de retiro de medicinas, exámenes clínicos y consultas médicas.<br>
        Proyecto creado y desarrollado por Mauricio Niño Gamboa. Enero 2026. Todos los derechos reservados.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    if verificar_conexion():
        main()
    else:
        st.error("Error crítico: No hay conexión con la base de datos.")
