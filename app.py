# ======================================================================
# GESTOR DE SALUD - STREAMLIT APP
# Adaptación ESTRICTA del código Python de Google Colab
# ======================================================================

import streamlit as st
import mysql.connector
import holidays
import pytz
import requests
import smtplib
from email.mime.text import MIMEText
from gtts import gTTS
from datetime import datetime, timedelta
import time
import base64
import os
import random
import hashlib # Agregado para optimización de velocidad (caching)

# ======================================================================
# 0. CONFIGURACIÓN INICIAL
# ======================================================================

# 1. Configuración de la pestaña
st.set_page_config(
    page_title="Asistente Médico",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Configuración de Base de Datos
DB_CONFIG = {
    'host': 'gateway01.us-east-1.prod.aws.tidbcloud.com',
    'port': 4000,
    'user': '39hpidXc8KL7sEA.root',
    'password': 'HwJbEPQQNL7rhRjF',
    'database': 'test',
    'autocommit': True,
    'ssl_verify_cert': True,
    'ssl_ca': '/etc/ssl/certs/ca-certificates.crt'
}

# Credenciales de Notificaciones
TELEGRAM_TOKEN = '8444851001:AAEZBqfJcgUasPLeu1nsD2xcG0OrkPvrwbM'
EMAIL_APP_PASSWORD = 'wspb oiqd zriv tqpl'
EMAIL_SENDER = 'unamauricio2013@gmail.com'
EMAIL_RECEIVER = 'maualexnino@gmail.com'
TELEGRAM_CHAT_ID_INTERNAL = '1677957851' # ID Real para envío
TELEGRAM_DISPLAY_PHONE = "🇨🇴 +57 324 2818869" # ID Visual para usuario

# Configuración de Festivos y Zona Horaria Colombia
festivos_co = holidays.CO(years=[2026, 2027, 2028, 2029])
tz_co = pytz.timezone('America/Bogota')

# URLs de Imágenes y Fondos (Lista para rotación)
CIUDAD_URL = "https://i.ibb.co/QjpntM88/i6.png"
ABUELO_URL = "https://i.ibb.co/spG69fPs/i7.png"
PORTADA_URL = "https://i.ibb.co/jZb8bxGk/i8.jpg"
AVATAR_MAURICIO = "https://i.ibb.co/zVFp4SmV/avatar-Mauricio.png"

FONDO_IMAGENES = [CIUDAD_URL, ABUELO_URL, PORTADA_URL]

# ======================================================================
# 1. ESTILOS CSS PERSONALIZADOS
# ======================================================================

def aplicar_estilos():
    # Lógica de rotación de fondo optimizada
    identificador_paso = f"{st.session_state.paso}_{st.session_state.subfase}"
    
    if st.session_state.last_step_id != identificador_paso:
        opciones_disponibles = [img for img in FONDO_IMAGENES if img != st.session_state.current_bg_url]
        nueva_imagen = random.choice(opciones_disponibles)
        st.session_state.current_bg_url = nueva_imagen
        st.session_state.last_step_id = identificador_paso

    bg_image = st.session_state.current_bg_url
    
    # Opacidad de la superposición (35% de blanco)
    overlay_opacity = "0.35" 

    st.markdown(f"""
    <style>
        /* Importar fuente Gótica de Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=UnifrakturMaguntia&display=swap');

        /* Fondo principal dinámico */
        .stApp {{
            background: linear-gradient(135deg, #001f3f 0%, #003366 50%, #004d80 100%);
            background-image: 
                linear-gradient(rgba(255, 255, 255, {overlay_opacity}), rgba(255, 255, 255, {overlay_opacity})),
                url('{bg_image}');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        
        /* Contenedor principal */
        .main .block-container {{
            padding: 2rem;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
            max-width: 1200px;
            margin: auto;
            color: #000000 !important;
        }}
        
        /* Texto general NEGRO */
        p, div, span, label, h2, h3, h4, h5, h6 {{
            color: #000000 !important;
        }}
        
        /* Título principal ASISTENTE MÉDICO (Gótico Dorado) */
        h1 {{
            font-family: 'UnifrakturMaguntia', cursive !important;
            color: #FFD700 !important; /* Dorado */
            text-align: center;
            font-weight: 400; /* Las fuentes góticas suelen ser gruesas por defecto */
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8), 0 0 10px #FFD700; /* Efecto brillante */
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
            font-size: 3rem !important;
        }}

        /* Inputs */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input {{
            background-color: #ffff00 !important;
            color: #0000cd !important;
            border: 3px solid #000000 !important;
            border-radius: 10px;
            font-weight: 600;
            font-size: 16px;
        }}
        
        /* Botones */
        .stButton > button {{
            background-color: #FFD700 !important;
            color: #0000CD !important;
            border: 3px solid #000000 !important;
            font-weight: 800 !important;
            font-size: 1.2rem !important;
            border-radius: 12px !important;
            padding: 0.5rem 1rem !important;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.4) !important;
            width: 100%;
        }}
        
        .stButton > button:hover {{
            transform: scale(1.02);
            box-shadow: 4px 4px 8px rgba(0,0,0,0.6) !important;
        }}
        
        /* Mensajes de voz */
        .mensaje-voz {{
            background: linear-gradient(135deg, #4169e1, #1e90ff);
            padding: 1rem;
            border-radius: 15px;
            margin: 1rem 0;
            border-left: 5px solid #ffd700;
            color: white !important;
        }}
        .mensaje-voz strong {{ color: white !important; }}
        
        /* Footer */
        .footer {{
            text-align: center;
            padding: 1rem;
            background: linear-gradient(135deg, #c0c0c0, #808080);
            border-radius: 15px;
            margin-top: 3rem;
            color: #000000 !important;
            font-weight: 600;
            font-size: 0.8rem !important;
        }}

        /* Responsividad */
        @media (max-width: 640px) {{
            .main .block-container {{ padding: 1rem; }}
            h1 {{ font-size: 2rem !important; }}
            .stButton > button {{ font-size: 1rem !important; }}
        }}
    </style>
    """, unsafe_allow_html=True)

# ======================================================================
# 2. FUNCIONES DE LÓGICA Y AUDIO (OPTIMIZADO)
# ======================================================================

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

def verificar_conexion():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            conn.close()
            return True
    except:
        return False

# --- OPTIMIZACIÓN: CACHING DE AUDIO ---
def generar_audio(texto):
    """Genera audio solo si no existe, usando hash del texto como nombre."""
    try:
        # Crear un hash único para el texto
        hash_texto = hashlib.md5(texto.encode('utf-8')).hexdigest()
        filename = f"audio_{hash_texto}.mp3"
        
        # Si el archivo ya existe, lo usamos (Optimización de velocidad)
        if not os.path.exists(filename):
            tts = gTTS(text=texto, lang='es', tld='com.co')
            tts.save(filename)
            
        return filename
    except Exception as e:
        return None

def calcular_espera_voz(texto):
    # Aumentamos un poco el tiempo base para evitar superposiciones
    return (len(texto) / 15) + 2.0 

def mostrar_mensaje_voz(texto, esperar=True):
    texto_limpio = texto.replace("**", "")
    
    st.markdown(f'<div class="mensaje-voz">🔊 <strong>Asistente:</strong> {texto_limpio}</div>', unsafe_allow_html=True)
    
    # Evitar repetir el mismo audio si no ha cambiado el contexto
    if st.session_state.last_played_text == texto_limpio:
        return

    st.session_state.last_played_text = texto_limpio
    
    audio_file = generar_audio(texto_limpio)
    if audio_file and os.path.exists(audio_file):
        with open(audio_file, 'rb') as f:
            audio_bytes = f.read()
            audio_base64 = base64.b64encode(audio_bytes).decode()
            
        unique_id = int(time.time() * 1000)
        
        audio_html = f"""
            <audio id="audio-{unique_id}" autoplay="true" style="display:none;">
                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            </audio>
            <script>
                var audio = document.getElementById("audio-{unique_id}");
                audio.volume = 1.0;
                audio.play().catch(function(error) {{ console.log(error); }});
            </script>
        """
        st.components.v1.html(audio_html, height=0)
        
        if esperar:
            duracion = calcular_espera_voz(texto_limpio)
            time.sleep(duracion)

def enviar_notificaciones(mensaje_texto, nombre_paciente):
    mensaje_personalizado = f"PACIENTE: {nombre_paciente}\n{mensaje_texto}"
    try:
        url_tg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID_INTERNAL,
            'text': f"🔔 RECORDATORIO SALUD:\n{mensaje_personalizado}",
            'parse_mode': 'Markdown'
        }
        requests.post(url_tg, data=payload, timeout=5)
    except: pass
    
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

def guardar_en_db(p):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS registros_salud (
            id INT AUTO_INCREMENT PRIMARY KEY,
            paciente VARCHAR(100),
            fecha_registro DATETIME,
            med_tipo VARCHAR(100),
            prox_retiro DATE,
            ex_tipo VARCHAR(100),
            prox_examen DATE,
            cita_tipo VARCHAR(100),
            prox_cita DATE,
            prog_categoria VARCHAR(100),
            prog_fecha DATE,
            prog_hora VARCHAR(10)
        )
        """)
        query = """
            INSERT INTO registros_salud
            (paciente, fecha_registro, med_tipo, prox_retiro, ex_tipo, prox_examen, cita_tipo, prox_cita, prog_categoria, prog_fecha, prog_hora)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        vals = (
            p.get('paciente'), datetime.now(tz_co).replace(tzinfo=None),
            p.get('med_tipo'), p['prox_retiro_dt'].date() if 'prox_retiro_dt' in p else None,
            p.get('ex_tipo'), p['prox_examen_dt'].date() if 'prox_examen_dt' in p else None,
            p.get('cita_tipo'), p['prox_cita_dt'].date() if 'prox_cita_dt' in p and p['prox_cita_dt'] else None,
            p.get('prog_categoria'),
            datetime.strptime(p['prog_fecha_str'], "%d/%m/%Y").date() if 'prog_fecha_str' in p else None,
            p.get('prog_hora')
        )
        cursor.execute(query, vals)
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except:
        return False

# ======================================================================
# 4. ELEMENTOS UI (CANCELAR / VOLVER)
# ======================================================================

def mostrar_boton_cancelar():
    col_spacer, col_btn = st.columns([8, 2])
    with col_btn:
        if st.button("CANCELAR Y REGRESAR", key="btn_cancel_global"):
            st.session_state.paso = 'menu_principal'
            st.session_state.subfase = 0
            st.session_state.contexto_varias = False
            st.rerun()

def mostrar_flecha_volver():
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2 = st.columns([9, 1])
    with col2:
        if st.button("⬅️ Volver", key="btn_volver_atras"):
            if st.session_state.subfase > 0:
                st.session_state.subfase -= 1
                st.rerun()
            else:
                if st.session_state.get('contexto_varias', False):
                     st.session_state.paso = 'flujo_varias'
                     st.session_state.subfase = 0
                else:
                    st.session_state.paso = 'menu_principal'
                st.rerun()

# ======================================================================
# 5. VALIDACIÓN Y ESTADO
# ======================================================================

def validar_fecha(fecha_str, futura=False):
    try:
        fecha_dt = datetime.strptime(fecha_str, "%d/%m/%Y")
        hoy = datetime.now(tz_co).replace(tzinfo=None)
        if futura: return fecha_dt >= datetime(2025, 5, 31)
        else: return datetime(2025, 5, 31) <= fecha_dt <= hoy
    except: return False

def validar_hora(hora_str):
    try:
        time.strptime(hora_str, "%H:%M")
        return True
    except: return False

def gestionar_nombre():
    st.session_state.contador_interacciones += 1
    if st.session_state.contador_interacciones % 4 == 0 and st.session_state.nombre_paciente:
        return f"{st.session_state.nombre_paciente}, "
    return ""

def inicializar_session_state():
    if 'paso' not in st.session_state: st.session_state.paso = 'bienvenida'
    if 'paciente' not in st.session_state: st.session_state.paciente = {}
    if 'nombre_paciente' not in st.session_state: st.session_state.nombre_paciente = ""
    if 'contador_interacciones' not in st.session_state: st.session_state.contador_interacciones = 0
    if 'subfase' not in st.session_state: st.session_state.subfase = 0
    if 'valor_temporal' not in st.session_state: st.session_state.valor_temporal = None
    if 'ver_historial' not in st.session_state: st.session_state.ver_historial = False
    if 'contexto_varias' not in st.session_state: st.session_state.contexto_varias = False
    
    if 'last_played_text' not in st.session_state: st.session_state.last_played_text = ""
    if 'current_bg_url' not in st.session_state: st.session_state.current_bg_url = PORTADA_URL
    if 'last_step_id' not in st.session_state: st.session_state.last_step_id = ""

# ======================================================================
# 6. INTERFAZ PRINCIPAL
# ======================================================================

def main():
    inicializar_session_state()
    aplicar_estilos()
    
    # Encabezado (ASISTENTE MÉDICO) con foto i7 aumentada 19% (~60px) y letra gótica dorada brillante
    # Subtítulo Gótico Plateado Brillante (+17% tamaño) con Avatar Mauricio a la derecha
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <h1>
            ASISTENTE MÉDICO 📅 
            <img src="{ABUELO_URL}" style="width: 60px; height: 60px; border-radius: 50%; margin-left: 10px; border: 2px solid white; box-shadow: 0px 0px 5px rgba(0,0,0,0.5);">
        </h1>
        
        <div style="
            display: flex; 
            justify-content: center; 
            align-items: center; 
            gap: 20px;
            font-family: 'UnifrakturMaguntia', cursive; 
            font-size: 1.4rem; /* 1.2rem original + 17% aprox */
            color: #C0C0C0; /* Plateado */
            text-shadow: 0 0 5px #C0C0C0, 1px 1px 2px #000; /* Brillante */
        ">
            <div>
                Sistema Inteligente de Recordatorios Médicos<br>
                Desarrollado por Mauricio Niño Gamboa. Enero 2026.
            </div>
            <img src="{AVATAR_MAURICIO}" style="width: 70px; height: 70px; border-radius: 50%; border: 2px solid silver; box-shadow: 0 0 10px silver;">
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Mostrar botón cancelar solo si estamos en un flujo activo
    if st.session_state.paso in ['flujo_medicinas', 'flujo_examenes', 'flujo_citas', 'flujo_varias', 'flujo_fechas_programadas']:
        mostrar_boton_cancelar()
    
    # Lógica de pasos
    if st.session_state.paso == 'bienvenida':
        with st.spinner('Verificando conexión con el sistema de salud...'):
            if not verificar_conexion():
                st.error("No se pudo establecer conexión con la base de datos.")
                st.stop()
            else:
                st.success("Conexión establecida correctamente")
                # Reducimos sleep para mejorar velocidad
                time.sleep(0.5)
        
        mostrar_mensaje_voz("Bienvenido al gestor de salud. Realizaremos preguntas para calcular o registrar sus fechas médicas importantes.")
        st.session_state.paso = 'solicitar_nombre'
        st.rerun()
    
    elif st.session_state.paso == 'solicitar_nombre':
        mostrar_mensaje_voz("Para iniciar, por favor permítame saber el nombre del paciente")
        nombre = st.text_input("Nombre del Paciente:", key="input_nombre")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Confirmar Nombre", use_container_width=True):
                if nombre.strip():
                    st.session_state.nombre_paciente = nombre.strip()
                    st.session_state.paciente['paciente'] = nombre.strip()
                    st.session_state.paso = 'consultar_historial'
                    st.rerun()
    
    elif st.session_state.paso == 'consultar_historial':
        consultar_historial_flow()
    
    elif st.session_state.paso == 'menu_principal':
        mostrar_menu_principal()
    
    elif st.session_state.paso == 'flujo_medicinas':
        flujo_medicinas_streamlit()
    elif st.session_state.paso == 'flujo_examenes':
        flujo_examenes_streamlit()
    elif st.session_state.paso == 'flujo_citas':
        flujo_citas_streamlit()
    elif st.session_state.paso == 'flujo_varias':
        flujo_varias_streamlit()
    elif st.session_state.paso == 'flujo_fechas_programadas':
        flujo_fechas_programadas_streamlit()
    elif st.session_state.paso == 'mostrar_resumen':
        mostrar_resumen_final()
    
    # Footer pequeño (Sin cambios solicitados, mantenido)
    st.markdown(f"""
    <div class='footer'>
        🏥 ASISTENTE DE AGENDAMIENTO Y RECORDATORIO<br>
        Desarrollado por Mauricio Niño Gamboa<br>
        © 2026 - Todos los derechos reservados<br>
        Notificaciones: {EMAIL_RECEIVER} | Telegram: {TELEGRAM_DISPLAY_PHONE}
    </div>
    """, unsafe_allow_html=True)

# ======================================================================
# 7. LÓGICA DEL HISTORIAL
# ======================================================================

def consultar_historial_flow():
    if 'historial_datos' not in st.session_state:
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT med_tipo, prox_retiro, ex_tipo, prox_examen, cita_tipo, prox_cita, prog_categoria, prog_fecha 
                FROM registros_salud WHERE paciente LIKE %s COLLATE utf8mb4_general_ci 
                ORDER BY fecha_registro DESC LIMIT 4
            """, (st.session_state.nombre_paciente,))
            st.session_state.historial_datos = cursor.fetchall()
            cursor.close()
            conn.close()
        except:
            st.session_state.historial_datos = []

    historial = st.session_state.historial_datos
    
    if historial:
        if not st.session_state.ver_historial:
            mostrar_mensaje_voz(f"¿Desea visualizar las consultas previas de {st.session_state.nombre_paciente}?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Sí, mostrar historial"):
                    st.session_state.ver_historial = True
                    st.rerun()
            with col2:
                if st.button("Continuar sin ver"):
                    st.session_state.paso = 'menu_principal'
                    st.rerun()
        else:
            st.info(f"Registros previos de {st.session_state.nombre_paciente}")
            msg_resumen = f"He encontrado sus últimos registros, {st.session_state.nombre_paciente}. Aquí tiene un resumen:"
            mostrar_mensaje_voz(msg_resumen)
            
            st.markdown("### HISTORIAL RECIENTE")
            for i, f in enumerate(historial, 1):
                detalles = []
                if f[1]: detalles.append(f"Retiro {f[0]}: {f[1]}")
                if f[3]: detalles.append(f"Examen {f[2]}: {f[3]}")
                if f[5]: detalles.append(f"Cita {f[4]}: {f[5]}")
                if f[7]: detalles.append(f"Programado ({f[6]}): {f[7]}")
                if detalles:
                    st.markdown(f"Registro {i}: {' | '.join(detalles)}")
            
            st.markdown("---")
            if st.button("Continuar al Menú"):
                st.session_state.paso = 'menu_principal'
                st.rerun()
    else:
        st.session_state.paso = 'menu_principal'
        st.rerun()

# ======================================================================
# 8. MENÚ PRINCIPAL
# ======================================================================

def mostrar_menu_principal():
    msg = f"{gestionar_nombre()}Por favor, indique el motivo de su consulta:"
    mostrar_mensaje_voz(msg)
    
    opciones = {
        "1 Retiro de Medicinas": "1",
        "2 Exámenes Médicos": "2",
        "3 Citas Médicas": "3",
        "4 Varias Opciones": "4",
        "5 Registrar Fecha Programada": "5"
    }
    
    seleccion = st.radio("Seleccione una opción:", list(opciones.keys()))
    
    if st.button("Continuar", use_container_width=True):
        opcion = opciones[seleccion]
        st.session_state.subfase = 0
        st.session_state.contexto_varias = False # Resetear contexto
        
        if opcion == "1": st.session_state.paso = 'flujo_medicinas'
        elif opcion == "2": st.session_state.paso = 'flujo_examenes'
        elif opcion == "3": st.session_state.paso = 'flujo_citas'
        elif opcion == "4": 
            st.session_state.paso = 'flujo_varias'
            st.session_state.contexto_varias = True # Activar modo varias
        elif opcion == "5": st.session_state.paso = 'flujo_fechas_programadas'
        st.rerun()

# ======================================================================
# 9. FLUJO MEDICINAS
# ======================================================================

def flujo_medicinas_streamlit():
    p = st.session_state.paciente
    
    if st.session_state.subfase == 0:
        mostrar_mensaje_voz("Iniciamos cordialmente con el retiro de medicinas.")
        st.session_state.subfase = 1
        st.rerun()
        
    elif st.session_state.subfase == 1:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, podría indicarme: ¿Es para Medicina General?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Sí", key="mg_si"):
                p['med_tipo'] = "Medicina General"
                st.session_state.subfase = 5
                st.rerun()
        with col2:
            if st.button("No", key="mg_no"):
                st.session_state.subfase = 2
                st.rerun()
                
    elif st.session_state.subfase == 2:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, podría indicarme: ¿Es para Especialista?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Sí", key="me_si"):
                st.session_state.subfase = 3
                st.rerun()
        with col2:
            if st.button("No", key="me_no"):
                st.session_state.subfase = 4
                st.rerun()
                
    elif st.session_state.subfase == 3:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, especifique cuál es la especialidad")
        esp = st.text_input("Especialidad:", key="med_esp_input")
        if st.button("Confirmar"):
            if esp.strip():
                p['med_tipo'] = esp.strip()
                st.session_state.subfase = 5
                st.rerun()
                
    elif st.session_state.subfase == 4:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, podría indicarme: ¿Es para Oncología?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Sí", key="mo_si"):
                p['med_tipo'] = "Oncología"
                st.session_state.subfase = 5
                st.rerun()
        with col2:
            if st.button("No", key="mo_no"):
                if st.button("Otra Especialidad"):
                    st.session_state.subfase = 3
                    st.rerun()
                p['med_tipo'] = "especialidad no especificada"
                st.session_state.subfase = 5
                st.rerun()

    elif st.session_state.subfase == 5:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, indíqueme ¿Cuántas entregas le faltan?")
        num = st.number_input("Entregas:", min_value=1, max_value=12, value=1)
        if st.button("Confirmar Entregas"):
            p['num_entregas'] = int(num)
            st.session_state.subfase = 6
            st.rerun()
            
    elif st.session_state.subfase == 6:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, la fecha de su último retiro.")
        fecha = st.text_input("Fecha (DD/MM/AAAA):", key="med_fecha")
        if st.button("Confirmar Fecha"):
            if validar_fecha(fecha):
                p['fecha_ult_retiro'] = fecha
                fb = datetime.strptime(fecha, "%d/%m/%Y")
                p['prox_retiro_dt'] = obtener_dia_habil_anterior(fb + timedelta(days=28), festivos_co)
                st.session_state.subfase = 7
                st.rerun()
            else:
                st.error("Fecha inválida.")
                
    elif st.session_state.subfase == 7:
        # FIN DEL FLUJO MEDICINAS
        # Si estamos en contexto "Varias", volver al controlador de Varias
        if st.session_state.get('contexto_varias', False):
             st.session_state.paso = 'flujo_varias'
             st.session_state.subfase = 10 # Ir a la siguiente sección (Exámenes)
             st.rerun()
        else:
            st.session_state.paso = 'mostrar_resumen'
            st.rerun()

    mostrar_flecha_volver()

# ======================================================================
# 10. FLUJO EXÁMENES
# ======================================================================

def flujo_examenes_streamlit():
    p = st.session_state.paciente
    
    if st.session_state.subfase == 0:
        mostrar_mensaje_voz("Continuamos gentilmente con sus exámenes médicos.")
        st.session_state.subfase = 1
        st.rerun()
        
    elif st.session_state.subfase == 1:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿Es examen de Sangre?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Sí", key="ex_s_si"):
                p['ex_tipo'] = "Sangre"
                st.session_state.subfase = 5
                st.rerun()
        with col2:
            if st.button("No", key="ex_s_no"):
                st.session_state.subfase = 2
                st.rerun()
                
    elif st.session_state.subfase == 2:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿Es examen de Rayos X?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Sí", key="ex_r_si"):
                p['ex_tipo'] = "Rayos X"
                st.session_state.subfase = 5
                st.rerun()
        with col2:
            if st.button("No", key="ex_r_no"):
                st.session_state.subfase = 3
                st.rerun()
                
    elif st.session_state.subfase == 3:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿Es examen de Ultrasonido?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Sí", key="ex_u_si"):
                p['ex_tipo'] = "Ultrasonido"
                st.session_state.subfase = 5
                st.rerun()
        with col2:
            if st.button("No", key="ex_u_no"):
                st.session_state.subfase = 4
                st.rerun()

    elif st.session_state.subfase == 4:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿Es Resonancia o Tomografía?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Sí", key="ex_rt_si"):
                p['ex_tipo'] = "Resonancia o Tomografía"
                st.session_state.subfase = 5
                st.rerun()
        with col2:
            if st.button("No", key="ex_rt_no"):
                p['ex_tipo'] = "examen no especificado"
                st.session_state.subfase = 5
                st.rerun()

    elif st.session_state.subfase == 5:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Dígame, ¿en qué lugar le dieron la orden?")
        lugar = st.text_input("Lugar:", key="ex_lugar")
        if st.button("Confirmar Lugar"):
            if lugar.strip():
                p['ex_lugar'] = lugar.strip()
                st.session_state.subfase = 6
                st.rerun()
                
    elif st.session_state.subfase == 6:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, la fecha de la orden.")
        fecha = st.text_input("Fecha (DD/MM/AAAA):", key="ex_fecha")
        if st.button("Confirmar Fecha"):
            if validar_fecha(fecha):
                p['ex_fecha_orden'] = fecha
                st.session_state.subfase = 7
                st.rerun()
            else:
                st.error("Fecha inválida.")
                
    elif st.session_state.subfase == 7:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿En cuántos días debe entregar los resultados?")
        dias = st.number_input("Días:", min_value=1, max_value=365, value=30)
        if st.button("Confirmar Días"):
            p['ex_dias_entrega'] = int(dias)
            fo = datetime.strptime(p['ex_fecha_orden'], "%d/%m/%Y")
            resta = p['ex_dias_entrega'] - 32
            if resta < 0 or resta == 2:
                p['prox_examen_dt'] = sumar_dias_habiles(fo, 3, festivos_co)
            else:
                p['prox_examen_dt'] = obtener_dia_habil_anterior(fo + timedelta(days=resta), festivos_co)
            st.session_state.subfase = 8
            st.rerun()
            
    elif st.session_state.subfase == 8:
        # FIN DEL FLUJO EXAMENES
        if st.session_state.get('contexto_varias', False):
             st.session_state.paso = 'flujo_varias'
             st.session_state.subfase = 20 # Ir a la siguiente sección (Citas)
             st.rerun()
        else:
            st.session_state.paso = 'mostrar_resumen'
            st.rerun()

    mostrar_flecha_volver()

# ======================================================================
# 11. FLUJO CITAS (CORREGIDO LÓGICA SECUENCIAL)
# ======================================================================

def flujo_citas_streamlit():
    p = st.session_state.paciente
    
    # 0. Saludo
    if st.session_state.subfase == 0:
        mostrar_mensaje_voz("Pasamos amablemente a sus citas médicas.")
        st.session_state.subfase = 1
        st.rerun()

    # 1. Medicina General?
    elif st.session_state.subfase == 1:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿Es cita de Medicina General?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Sí", key="ci_mg_si"):
                p['cita_tipo'] = "Medicina General"
                st.session_state.subfase = 6 # Saltar a Lugar
                st.rerun()
        with col2:
            if st.button("No", key="ci_mg_no"):
                st.session_state.subfase = 2 # Ir a Especialista
                st.rerun()

    # 2. Especialista?
    elif st.session_state.subfase == 2:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿Es cita de Especialista?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Sí", key="ci_esp_si"):
                st.session_state.subfase = 3 # Ir a pedir nombre
                st.rerun()
        with col2:
            if st.button("No", key="ci_esp_no"):
                st.session_state.subfase = 4 # Ir a Oncología/Odontología
                st.rerun()

    # 3. Nombre Especialista
    elif st.session_state.subfase == 3:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Especifique la especialidad")
        esp = st.text_input("Especialidad:", key="ci_esp_in")
        if st.button("Confirmar Especialidad"):
            if esp.strip():
                p['cita_tipo'] = esp.strip()
                st.session_state.subfase = 6 # Saltar a Lugar
                st.rerun()

    # 4. Oncología/Odontología?
    elif st.session_state.subfase == 4:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿Es Oncología u Odontología?")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Oncología"):
                p['cita_tipo'] = "Oncología"
                st.session_state.subfase = 6 # Saltar a Lugar
                st.rerun()
        with c2:
            if st.button("Odontología"):
                p['cita_tipo'] = "Odontología"
                st.session_state.subfase = 6 # Saltar a Lugar
                st.rerun()
        with c3:
            if st.button("Otra"):
                st.session_state.subfase = 5 # Ir a Otra
                st.rerun()

    # 5. Otra Especialidad
    elif st.session_state.subfase == 5:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Especifique la otra especialidad")
        otra = st.text_input("Otra especialidad:", key="ci_otra_in")
        if st.button("Confirmar Otra"):
            if otra.strip():
                p['cita_tipo'] = otra.strip()
                st.session_state.subfase = 6 # Saltar a Lugar
                st.rerun()

    # 6. Lugar
    elif st.session_state.subfase == 6:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿En qué lugar es la cita?")
        lug = st.text_input("Lugar:", key="ci_lugar")
        if st.button("Confirmar Lugar"):
            if lug.strip():
                p['cita_lugar'] = lug.strip()
                st.session_state.subfase = 7 # Ir a Fecha
                st.rerun()

    # 7. Primera vez o Control
    elif st.session_state.subfase == 7:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿Es primera vez de la cita?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Sí, primera vez"):
                st.session_state.valor_temporal = True # Es primera vez
                st.session_state.subfase = 8
                st.rerun()
        with c2:
            if st.button("No, es control"):
                st.session_state.valor_temporal = False # No es primera vez
                st.session_state.subfase = 8
                st.rerun()

    # 8. Fecha
    elif st.session_state.subfase == 8:
        if st.session_state.valor_temporal:
            msg_f = "Por favor, la fecha de la orden de la cita."
        else:
            msg_f = "Por favor, la fecha de su última cita."
        mostrar_mensaje_voz(f"{gestionar_nombre()}{msg_f}")
        
        f_cita = st.text_input("Fecha (DD/MM/AAAA):", key="ci_fecha")
        if st.button("Confirmar Fecha"):
            if validar_fecha(f_cita):
                p['cita_fecha_ult'] = f_cita
                st.session_state.subfase = 9 # Ir a Control
                st.rerun()
            else:
                st.error("Fecha inválida.")

    # 9. Control Futuro?
    elif st.session_state.subfase == 9:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿Tiene usted un control por esa cita?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Sí"):
                st.session_state.subfase = 10 # Ir a Dias
                st.rerun()
        with c2:
            if st.button("No"):
                p['prox_cita_dt'] = None
                st.session_state.subfase = 11 # Fin
                st.rerun()

    # 10. Dias Control
    elif st.session_state.subfase == 10:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿Dentro de cuántos días es el control?")
        dc = st.number_input("Días:", min_value=1, max_value=365, value=30, key="ci_dias")
        if st.button("Confirmar Días"):
            p['dias_control'] = int(dc)
            fu = datetime.strptime(p['cita_fecha_ult'], "%d/%m/%Y")
            resta = p['dias_control'] - 32
            if resta < 0 or resta == 2:
                p['prox_cita_dt'] = sumar_dias_habiles(fu, 3, festivos_co)
            else:
                p['prox_cita_dt'] = obtener_dia_habil_anterior(fu + timedelta(days=resta), festivos_co)
            st.session_state.subfase = 11
            st.rerun()

    elif st.session_state.subfase == 11:
        # FIN DEL FLUJO CITAS
        if st.session_state.get('contexto_varias', False):
             # En Varias, Citas es la última, así que va al resumen
             st.session_state.paso = 'mostrar_resumen'
             st.rerun()
        else:
            st.session_state.paso = 'mostrar_resumen'
            st.rerun()

    mostrar_flecha_volver()

# ======================================================================
# 12. FLUJO VARIAS (CONTROLADOR CENTRAL)
# ======================================================================

def flujo_varias_streamlit():
    
    # SUBFASE 0: PREGUNTAR POR MEDICINAS
    if st.session_state.subfase == 0:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿Necesita hacer retiro de medicina?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Sí", key="v_m_s"):
                # Ir al flujo de medicinas
                st.session_state.paso = 'flujo_medicinas'
                st.session_state.subfase = 0 # Empezar medicinas desde 0
                st.rerun()
        with c2:
            if st.button("No", key="v_m_n"):
                st.session_state.subfase = 10 # Saltar a Exámenes
                st.rerun()

    # SUBFASE 10: PREGUNTAR POR EXÁMENES
    elif st.session_state.subfase == 10:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿Necesita hacerse exámenes médicos?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Sí", key="v_e_s"):
                # Ir al flujo de exámenes
                st.session_state.paso = 'flujo_examenes'
                st.session_state.subfase = 0 # Empezar exámenes desde 0
                st.rerun()
        with c2:
            if st.button("No", key="v_e_n"):
                st.session_state.subfase = 20 # Saltar a Citas
                st.rerun()

    # SUBFASE 20: PREGUNTAR POR CITAS
    elif st.session_state.subfase == 20:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿Necesita programar una cita médica?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Sí", key="v_c_s"):
                # Ir al flujo de citas
                st.session_state.paso = 'flujo_citas'
                st.session_state.subfase = 0 # Empezar citas desde 0
                st.rerun()
        with c2:
            if st.button("No", key="v_c_n"):
                # Si no a todo, o terminando, ir al resumen
                st.session_state.paso = 'mostrar_resumen'
                st.rerun()

# ======================================================================
# 13. FLUJO PROGRAMADAS
# ======================================================================

def flujo_fechas_programadas_streamlit():
    p = st.session_state.paciente
    
    if st.session_state.subfase == 0:
        mostrar_mensaje_voz("Evaluaremos sus citas programadas.")
        st.session_state.subfase = 1
        st.rerun()
        
    elif st.session_state.subfase == 1:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿Tiene cita programada de examen médico?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Sí", key="fp_e_s"):
                p['prog_categoria'] = "Examen Médico"
                st.session_state.subfase = 2
                st.rerun()
        with c2:
            if st.button("No", key="fp_e_n"):
                st.session_state.subfase = 10
                st.rerun()

    # Flujo Examen Programado
    elif st.session_state.subfase == 2:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Tipo de examen:")
        opciones = ["Sangre", "Rayos X", "Ultrasonido", "Resonancia o Tomografía", "Otro"]
        sel = st.radio("Tipo:", opciones)
        if st.button("Confirmar Tipo"):
            if sel == "Otro":
                st.session_state.subfase = 3
            else:
                p['prog_tipo'] = sel
                st.session_state.subfase = 4
            st.rerun()
            
    elif st.session_state.subfase == 3:
        mostrar_mensaje_voz("Por favor, especifique el tipo de examen.")
        tipo = st.text_input("Especifique:")
        if st.button("Confirmar"):
            p['prog_tipo'] = tipo
            st.session_state.subfase = 4
            st.rerun()
            
    elif st.session_state.subfase == 4:
        mostrar_mensaje_voz("Indíqueme el lugar.")
        lug = st.text_input("Lugar:")
        if st.button("Confirmar Lugar"):
            p['prog_lugar'] = lug
            st.session_state.subfase = 5
            st.rerun()
            
    elif st.session_state.subfase == 5:
        mostrar_mensaje_voz("Por favor, la fecha futura de la cita.")
        fecha = st.text_input("Fecha Futura (DD/MM/AAAA):")
        if st.button("Confirmar Fecha"):
            if validar_fecha(fecha, futura=True):
                p['prog_fecha_str'] = fecha
                st.session_state.subfase = 6
                st.rerun()
            else:
                st.error("Fecha inválida (debe ser posterior a 31/05/2025).")

    elif st.session_state.subfase == 6:
        mostrar_mensaje_voz("Finalmente, la hora de la cita.")
        hora = st.text_input("Hora (HH:MM):")
        if st.button("Confirmar Hora"):
            if validar_hora(hora):
                p['prog_hora'] = hora
                st.session_state.subfase = 99
                st.rerun()
            else:
                st.error("Hora inválida.")

    # Flujo Cita Programada
    elif st.session_state.subfase == 10:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿Tiene cita programada con médico?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Sí", key="fp_c_s"):
                p['prog_categoria'] = "Cita Médica"
                st.session_state.subfase = 11
                st.rerun()
        with c2:
            if st.button("No", key="fp_c_n"):
                st.info("Sesión finalizada.")
                st.stop()

    elif st.session_state.subfase == 11:
        mostrar_mensaje_voz("Seleccione el tipo de cita.")
        opciones = ["Medicina General", "Especialista", "Oncología", "Odontología", "Otra"]
        sel = st.radio("Tipo Cita:", opciones)
        if st.button("Confirmar Tipo"):
            if sel in ["Especialista", "Otra"]:
                st.session_state.valor_temporal = sel
                st.session_state.subfase = 12
            else:
                p['prog_tipo'] = sel
                st.session_state.subfase = 13
            st.rerun()
            
    elif st.session_state.subfase == 12:
        mostrar_mensaje_voz("Especifique la especialidad.")
        esp = st.text_input("Especialidad:")
        if st.button("Confirmar"):
            p['prog_tipo'] = esp
            st.session_state.subfase = 13
            st.rerun()
            
    elif st.session_state.subfase == 13:
        mostrar_mensaje_voz("Indíqueme el lugar.")
        lug = st.text_input("Lugar:")
        if st.button("Confirmar Lugar"):
            p['prog_lugar'] = lug
            st.session_state.subfase = 14
            st.rerun()
            
    elif st.session_state.subfase == 14:
        mostrar_mensaje_voz("Por favor, la fecha futura de la cita.")
        fecha = st.text_input("Fecha Futura (DD/MM/AAAA):")
        if st.button("Confirmar Fecha"):
            if validar_fecha(fecha, futura=True):
                p['prog_fecha_str'] = fecha
                st.session_state.subfase = 15
                st.rerun()
            else:
                st.error("Fecha inválida.")
                
    elif st.session_state.subfase == 15:
        mostrar_mensaje_voz("Finalmente, la hora de la cita.")
        hora = st.text_input("Hora (HH:MM):")
        if st.button("Confirmar Hora"):
            if validar_hora(hora):
                p['prog_hora'] = hora
                st.session_state.subfase = 99
                st.rerun()
            else:
                st.error("Hora inválida.")

    # Finalización Programada
    elif st.session_state.subfase == 99:
        msg = f"Cita Programada: {p['prog_categoria']} ({p['prog_tipo']}) en {p['prog_lugar']} el {p['prog_fecha_str']} a las {p['prog_hora']}."
        st.success("Información guardada.")
        st.info(msg)
        
        # Cronograma visual
        fp = datetime.strptime(p['prog_fecha_str'], "%d/%m/%Y")
        hoy = datetime.now(tz_co).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
        diff = (fp - hoy).days
        dias = [5, 3, 1] if diff > 5 else ([3, 1] if diff == 4 else [1])
        
        st.write("📅 Cronograma de Notificaciones:")
        for d in dias:
            fa = (fp - timedelta(days=d)).strftime("%d/%m/%Y")
            st.write(f"- Día -{d}: {fa} (10:30am y 07:45pm)")
            
        mostrar_mensaje_voz("Notificaciones programadas.", esperar=True)
        enviar_notificaciones(msg, p['paciente'])
        
        if st.button("Ir al Resumen"):
            st.session_state.paso = 'mostrar_resumen'
            st.rerun()

    mostrar_flecha_volver()

# ======================================================================
# 14. RESUMEN FINAL
# ======================================================================

def mostrar_resumen_final():
    p = st.session_state.paciente
    st.markdown("## 📋 RESUMEN FINAL")
    
    print("\n--- RESUMEN DE FECHAS ---")
    
    # Lógica corregida para el Resumen:
    # 1. Definir los mensajes exactamente como se solicitaron
    # 2. Reproducirlos secuencialmente controlando la espera
    
    mensajes_resumen = []

    if "prox_retiro_dt" in p:
        msg = f"Su próximo retiro de medicina ({p.get('med_tipo', '')}) es el {p['prox_retiro_dt'].strftime('%d/%m/%Y')}"
        st.success(msg)
        mensajes_resumen.append(msg)
        
    if "prox_examen_dt" in p:
        msg = f"Su examen ({p.get('ex_tipo', '')}) debe solicitarse el {p['prox_examen_dt'].strftime('%d/%m/%Y')}"
        st.info(msg)
        mensajes_resumen.append(msg)
        
    if "prox_cita_dt" in p and p["prox_cita_dt"]:
        msg = f"Su cita ({p.get('cita_tipo', '')}) debe solicitarse el {p['prox_cita_dt'].strftime('%d/%m/%Y')}"
        st.warning(msg)
        mensajes_resumen.append(msg)
        
    # Reproducción secuencial de los mensajes del resumen
    # Se concatenan en el estado si es necesario, pero aquí usaremos la función con espera estricta
    for msg in mensajes_resumen:
        mostrar_mensaje_voz(msg, esperar=True)

    if guardar_en_db(p):
        st.success("Datos guardados en BD.")
        notif = f"Recibirá notificaciones en {EMAIL_RECEIVER} y Telegram {TELEGRAM_DISPLAY_PHONE}"
        st.info(notif)
        mostrar_mensaje_voz(notif, esperar=True)
        
    st.markdown("---")
    mostrar_mensaje_voz(f"{gestionar_nombre()}¿Tiene algún otro requerimiento?", esperar=True)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Sí, Nuevo Requerimiento"):
            st.session_state.paso = 'menu_principal'
            nom = st.session_state.nombre_paciente
            st.session_state.paciente = {"paciente": nom}
            st.session_state.subfase = 0
            st.session_state.contexto_varias = False
            st.rerun()
    with c2:
        if st.button("No, Finalizar"):
            mostrar_mensaje_voz("Gracias por usar nuestro servicio.", esperar=True)
            
            # Optimización para evitar congelamiento
            # Reducir tiempos y evitar bloqueos largos
            st.balloons()
            time.sleep(2) # Reducido de 3 a 2 para mayor fluidez
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()
