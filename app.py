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

# ======================================================================
# 0. CONFIGURACIÓN INICIAL
# ======================================================================

# 1. Configuración de la pestaña (breve y concisa)
st.set_page_config(
    page_title="Asistente Médico - Mauricio Niño G.",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Título y créditos dentro de la aplicación
st.title("ASISTENTE DE AGENDAMIENTO Y RECORDATORIO DE RETIRO DE MEDICINAS, EXÁMENES CLÍNICOS Y CONSULTAS MÉDICAS.")
st.subheader("Sistema Inteligente de Recordatorios Médicos")
st.caption("Desarrollado por Mauricio Niño Gamboa. Enero 2026.")

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
TELEGRAM_CHAT_ID = '1677957851'

# Configuración de Festivos y Zona Horaria Colombia
festivos_co = holidays.CO(years=[2026, 2027, 2028, 2029])
tz_co = pytz.timezone('America/Bogota')

# URLs de Imágenes
AVATAR_URL = "https://i.ibb.co/zVFp4SmV/avatar-Mauricio.png"
CIUDAD_URL = "https://i.ibb.co/QjpntM88/i6.png"
ABUELO_URL = "https://i.ibb.co/spG69fPs/i7.png"

# ======================================================================
# 1. ESTILOS CSS PERSONALIZADOS (CORREGIDO)
# ======================================================================

def aplicar_estilos():
    st.markdown(f"""
    <style>
        /* Fondo principal con avatar */
        .stApp {{
            background: linear-gradient(135deg, #001f3f 0%, #003366 50%, #004d80 100%);
            background-image: 
                linear-gradient(135deg, rgba(0, 31, 63, 0.95), rgba(0, 77, 128, 0.95)),
                url('{AVATAR_URL}');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        
        /* Contenedor principal - TEXTO NEGRO SOBRE BLANCO */
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
        p, div, span, label {{
            color: #000000 !important;
        }}
        
        /* Título principal */
        h1 {{
            color: #0066ff !important;
            text-align: center;
            font-weight: 800;
            text-shadow: 2px 2px 4px rgba(255, 215, 0, 0.3);
            margin-bottom: 1rem;
        }}
        
        /* Subtítulos */
        h2, h3 {{
            color: #8b0000 !important;
            font-weight: 700;
        }}
        
        /* Inputs de texto - AMARILLO con texto AZUL OSCURO */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > select,
        .stNumberInput > div > div > input {{
            background-color: #ffff00 !important;
            color: #0000cd !important;
            border: 3px solid #000000 !important;
            border-radius: 10px;
            font-weight: 600;
            font-size: 16px;
        }}
        
        /* Radio buttons - TEXTO NEGRO */
        .stRadio > label {{
            color: #000000 !important;
            font-weight: 600;
        }}
        
        .stRadio > div > label > div {{
            color: #000000 !important;
        }}
        
        /* Botones principales */
        .stButton > button {{
            background: linear-gradient(135deg, #00ff00, #008000);
            color: white;
            font-weight: 700;
            border: none;
            border-radius: 10px;
            padding: 0.75rem 2rem;
            font-size: 18px;
            box-shadow: 0 4px 15px rgba(0, 255, 0, 0.4);
            transition: all 0.3s;
        }}
        
        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 255, 0, 0.6);
        }}
        
        /* Cajas de información */
        .stAlert {{
            background-color: rgba(192, 192, 192, 0.9) !important;
            border-left: 5px solid #0066ff;
            border-radius: 10px;
            color: #000000 !important;
        }}
        
        /* Mensajes de voz */
        .mensaje-voz {{
            background: linear-gradient(135deg, #4169e1, #1e90ff);
            color: white !important;
            padding: 1rem;
            border-radius: 15px;
            margin: 1rem 0;
            border-left: 5px solid #ffd700;
            box-shadow: 0 4px 15px rgba(65, 105, 225, 0.3);
        }}
        
        .mensaje-voz strong {{
            color: white !important;
        }}
        
        /* Footer */
        .footer {{
            text-align: center;
            padding: 2rem 1rem;
            background: linear-gradient(135deg, #c0c0c0, #808080);
            border-radius: 15px;
            margin-top: 3rem;
            color: #000000 !important;
            font-weight: 600;
        }}
        
        /* Avatar pequeño */
        .avatar-esquina {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 80px;
            height: 80px;
            border-radius: 50%;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            z-index: 1000;
        }}
        
        /* Fondos de secciones con imágenes - TRANSPARENCIA 80% */
        .seccion-medicinas {{
            background-image: linear-gradient(rgba(255,255,255,0.8), rgba(255,255,255,0.8)),
                              url('{CIUDAD_URL}');
            background-size: cover;
            background-position: center;
            padding: 2rem;
            border-radius: 15px;
            margin: 1rem 0;
        }}
        
        .seccion-examenes {{
            background-image: linear-gradient(rgba(255,255,255,0.8), rgba(255,255,255,0.8)),
                              url('{CIUDAD_URL}');
            background-size: cover;
            background-position: center;
            padding: 2rem;
            border-radius: 15px;
            margin: 1rem 0;
        }}
        
        .seccion-citas {{
            background-image: linear-gradient(rgba(255,255,255,0.8), rgba(255,255,255,0.8)),
                              url('{ABUELO_URL}');
            background-size: cover;
            background-position: center;
            padding: 2rem;
            border-radius: 15px;
            margin: 1rem 0;
        }}
        
        .seccion-programadas {{
            background-image: linear-gradient(rgba(255,255,255,0.8), rgba(255,255,255,0.8)),
                              url('{ABUELO_URL}');
            background-size: cover;
            background-position: center;
            padding: 2rem;
            border-radius: 15px;
            margin: 1rem 0;
        }}
    </style>
    """, unsafe_allow_html=True)

# ======================================================================
# 2. FUNCIONES DE LÓGICA DE FECHAS (COLOMBIA)
# ======================================================================

def obtener_dia_habil_anterior(fecha, festivos):
    """Retrocede hasta encontrar un día hábil (no domingo ni festivo)"""
    while fecha.weekday() == 6 or fecha in festivos:
        fecha -= timedelta(days=1)
    return fecha

def sumar_dias_habiles(fecha_inicio, dias_a_sumar, festivos):
    """Suma días hábiles excluyendo domingos y festivos"""
    fecha_actual = fecha_inicio
    dias_contados = 0
    while dias_contados < dias_a_sumar:
        fecha_actual += timedelta(days=1)
        if fecha_actual.weekday() != 6 and fecha_actual not in festivos:
            dias_contados += 1
    return fecha_actual

# ======================================================================
# 3. FUNCIONES DE VOZ Y NOTIFICACIONES (CORREGIDO)
# ======================================================================

def generar_audio(texto, filename="audio_temp.mp3"):
    """Genera archivo de audio con gTTS"""
    try:
        tts = gTTS(text=texto, lang='es', tld='com.co')
        tts.save(filename)
        return filename
    except Exception as e:
        st.warning(f"⚠️ Audio no disponible: {e}")
        return None

def mostrar_mensaje_voz(texto):
    """Muestra mensaje y genera audio reproducible AUTOMÁTICO"""
    st.markdown(f'<div class="mensaje-voz">🔊 <strong>Asistente:</strong> {texto}</div>', unsafe_allow_html=True)
    
    audio_file = generar_audio(texto)
    if audio_file and os.path.exists(audio_file):
        with open(audio_file, 'rb') as f:
            audio_bytes = f.read()
        
        # Convertir a base64 para autoplay HTML5
        audio_base64 = base64.b64encode(audio_bytes).decode()
        
        # HTML5 audio con autoplay (oculto)
        st.markdown(f"""
            <audio autoplay style="display:none;">
                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            </audio>
        """, unsafe_allow_html=True)
        
        # Mostrar reproductor manual también (por si el navegador bloquea autoplay)
        st.audio(audio_bytes, format='audio/mp3')

def enviar_notificaciones(mensaje_texto, nombre_paciente):
    """Envía notificaciones vía Telegram y Email"""
    mensaje_personalizado = f"PACIENTE: {nombre_paciente}\n{mensaje_texto}"
    
    # Telegram
    try:
        url_tg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': f"🔔 RECORDATORIO SALUD:\n{mensaje_personalizado}",
            'parse_mode': 'Markdown'
        }
        requests.post(url_tg, data=payload, timeout=10)
    except Exception as e:
        st.warning(f"Error enviando Telegram: {e}")
    
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
    except Exception as e:
        st.warning(f"Error enviando Email: {e}")

# ======================================================================
# 4. FUNCIONES DE BASE DE DATOS
# ======================================================================

def verificar_conexion():
    """Verifica conectividad con la base de datos"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            conn.close()
            return True
    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")
        return False

def consultar_historial(nombre):
    """Consulta los últimos 4 registros del paciente"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        query = """
        SELECT med_tipo, prox_retiro, ex_tipo, prox_examen, cita_tipo, prox_cita, prog_categoria, prog_fecha
        FROM registros_salud
        WHERE paciente LIKE %s COLLATE utf8mb4_general_ci
        ORDER BY fecha_registro DESC LIMIT 4
        """
        cursor.execute(query, (nombre,))
        filas = cursor.fetchall()
        cursor.close()
        conn.close()
        return filas
    except Exception as e:
        st.warning(f"Error al consultar historial: {e}")
        return []

def guardar_en_db(p):
    """Guarda registro en la base de datos"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Crear tabla si no existe
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
            p.get('paciente'),
            datetime.now(tz_co).replace(tzinfo=None),
            p.get('med_tipo'),
            p['prox_retiro_dt'].date() if 'prox_retiro_dt' in p else None,
            p.get('ex_tipo'),
            p['prox_examen_dt'].date() if 'prox_examen_dt' in p else None,
            p.get('cita_tipo'),
            p['prox_cita_dt'].date() if 'prox_cita_dt' in p and p['prox_cita_dt'] else None,
            p.get('prog_categoria'),
            datetime.strptime(p['prog_fecha_str'], "%d/%m/%Y").date() if 'prog_fecha_str' in p else None,
            p.get('prog_hora')
        )
        cursor.execute(query, vals)
        conn.commit()
        cursor.close()
        conn.close()
        st.success("✅ Información guardada exitosamente")
        return True
    except Exception as e:
        st.error(f"❌ Error al guardar: {e}")
        return False

# ======================================================================
# 5. FUNCIONES DE VALIDACIÓN
# ======================================================================

def normalizar_si_no(texto):
    """Normaliza respuestas sí/no"""
    if not texto:
        return None
    t = texto.lower().strip().replace('í', 'i').replace('á', 'a')
    if t in ['si', 's', 'sip', 'correcto', 'afirmativo']:
        return True
    if t in ['no', 'n', 'nop', 'incorrecto']:
        return False
    return None

def validar_fecha(fecha_str, futura=False):
    """Valida formato y rango de fecha"""
    try:
        fecha_dt = datetime.strptime(fecha_str, "%d/%m/%Y")
        hoy = datetime.now(tz_co).replace(tzinfo=None)
        
        if futura:
            return fecha_dt >= datetime(2025, 5, 31)
        else:
            return datetime(2025, 5, 31) <= fecha_dt <= hoy
    except:
        return False

def validar_hora(hora_str):
    """Valida formato de hora HH:MM"""
    try:
        time.strptime(hora_str, "%H:%M")
        return True
    except:
        return False

def simplificar_pregunta(pregunta):
    """Simplifica texto de pregunta para confirmación"""
    pregunta = pregunta.replace("¿", "").replace("?", "").lower()
    palabras_a_quitar = [
        "para", "de", "la", "el", "en", "donde", "su", "una", "con", "es", "que",
        "cuál", "por", "favor", "sería", "tan", "amable", "gentil", "dígame", "indique"
    ]
    palabras = pregunta.split()
    filtradas = [p for p in palabras if p not in palabras_a_quitar]
    return " ".join(filtradas).capitalize()

# ======================================================================
# 6. INICIALIZACIÓN DE SESSION STATE
# ======================================================================

def inicializar_session_state():
    """Inicializa todas las variables de sesión"""
    if 'paso' not in st.session_state:
        st.session_state.paso = 'bienvenida'
    if 'paciente' not in st.session_state:
        st.session_state.paciente = {}
    if 'nombre_paciente' not in st.session_state:
        st.session_state.nombre_paciente = ""
    if 'contador_interacciones' not in st.session_state:
        st.session_state.contador_interacciones = 0
    if 'opcion_menu' not in st.session_state:
        st.session_state.opcion_menu = None
    if 'historial_mostrado' not in st.session_state:
        st.session_state.historial_mostrado = False
    if 'flujo_actual' not in st.session_state:
        st.session_state.flujo_actual = None
    if 'subfase' not in st.session_state:
        st.session_state.subfase = 0
    if 'intentos' not in st.session_state:
        st.session_state.intentos = 0
    if 'confirmando' not in st.session_state:
        st.session_state.confirmando = False
    if 'valor_temporal' not in st.session_state:
        st.session_state.valor_temporal = None

def gestionar_nombre():
    """Retorna nombre del paciente cada 4 interacciones"""
    st.session_state.contador_interacciones += 1
    if st.session_state.contador_interacciones % 4 == 0 and st.session_state.nombre_paciente:
        return f"{st.session_state.nombre_paciente}, "
    return ""

# ======================================================================
# 7. INTERFAZ PRINCIPAL
# ======================================================================

def main():
    aplicar_estilos()
    inicializar_session_state()
    
    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div style='text-align: center;'>
            <img src='{AVATAR_URL}' width='150' style='border-radius: 50%; box-shadow: 0 4px 15px rgba(0,0,0,0.3);'>
            <h1>🏥 ASISTENTE DE SALUD</h1>
            <p style='color: #8b0000; font-size: 18px; font-weight: 600;'>
                Sistema Inteligente de Recordatorios Médicos
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Verificación de conexión
    if st.session_state.paso == 'bienvenida':
        with st.spinner('🔄 Verificando conexión con el sistema de salud...'):
            if not verificar_conexion():
                st.error("❌ No se pudo establecer conexión con la base de datos. Intente más tarde.")
                st.stop()
            else:
                st.success("✅ Conexión establecida correctamente")
                time.sleep(1)
        
        mostrar_mensaje_voz("Bienvenido al gestor de salud. Realizaremos preguntas para calcular o registrar sus fechas médicas importantes.")
        time.sleep(1.5)  # PAUSA como en código Python
        
        st.session_state.paso = 'solicitar_nombre'
        st.rerun()
    
    # Solicitar nombre del paciente
    elif st.session_state.paso == 'solicitar_nombre':
        mostrar_mensaje_voz("Para iniciar, por favor permítame saber el nombre del paciente")
        
        nombre = st.text_input("**Nombre del Paciente:**", key="input_nombre")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("✅ Confirmar Nombre", use_container_width=True):
                if nombre.strip():
                    st.session_state.nombre_paciente = nombre.strip()
                    st.session_state.paciente['paciente'] = nombre.strip()
                    st.session_state.paso = 'consultar_historial'
                    st.rerun()
                else:
                    st.warning("⚠️ Por favor ingrese un nombre válido")
    
    # Consultar historial
    elif st.session_state.paso == 'consultar_historial':
        if not st.session_state.historial_mostrado:
            historial = consultar_historial(st.session_state.nombre_paciente)
            
            if historial:
                st.info(f"📋 Se encontraron {len(historial)} registros previos de **{st.session_state.nombre_paciente}**")
                mostrar_mensaje_voz(f"¿Desea visualizar las consultas previas de {st.session_state.nombre_paciente}?")
                
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    if st.button("✅ Sí, mostrar historial", use_container_width=True):
                        msg_resumen = f"He encontrado sus últimos registros, {st.session_state.nombre_paciente}. Aquí tiene un resumen:"
                        mostrar_mensaje_voz(msg_resumen)
                        st.markdown("### 📊 HISTORIAL RECIENTE (Últimos 4)")
                        for i, f in enumerate(historial, 1):
                            detalles = []
                            if f[1]: detalles.append(f"**Retiro {f[0]}:** {f[1]}")
                            if f[3]: detalles.append(f"**Examen {f[2]}:** {f[3]}")
                            if f[5]: detalles.append(f"**Cita {f[4]}:** {f[5]}")
                            if f[7]: detalles.append(f"**Programado ({f[6]}):** {f[7]}")
                            if detalles:
                                st.markdown(f"**Registro {i}:** {' | '.join(detalles)}")
                        st.session_state.historial_mostrado = True
                        time.sleep(2)
                        st.session_state.paso = 'menu_principal'
                        st.rerun()
                with col2:
                    if st.button("⏭️ Continuar sin ver", use_container_width=True):
                        st.session_state.historial_mostrado = True
                        st.session_state.paso = 'menu_principal'
                        st.rerun()
            else:
                st.session_state.historial_mostrado = True
                st.session_state.paso = 'menu_principal'
                st.rerun()
        else:
            st.session_state.paso = 'menu_principal'
            st.rerun()
    
    # Menú principal
    elif st.session_state.paso == 'menu_principal':
        mostrar_menu_principal()
    
    # Flujos específicos
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
    
    # Avatar flotante
    st.markdown(f'<img src="{AVATAR_URL}" class="avatar-esquina">', unsafe_allow_html=True)
    
    # Footer (CORREGIDO - cierre de etiqueta)
    st.markdown(f"""
    <div class='footer'>
        <strong>🏥 ASISTENTE DE AGENDAMIENTO Y RECORDATORIO DE RETIRO DE MEDICINAS, 
        EXÁMENES CLÍNICOS Y CONSULTAS MÉDICAS.</strong><br>
        Sistema Inteligente de Recordatorios Médicos<br>
        Desarrollado por <strong>Mauricio Niño Gamboa</strong><br>
        © 2026 - Todos los derechos reservados<br>
        <small>Notificaciones: {EMAIL_RECEIVER} | Telegram: +57 {TELEGRAM_CHAT_ID[2:5]} {TELEGRAM_CHAT_ID[5:8]} {TELEGRAM_CHAT_ID[8:]}</small>
    </div>
    """, unsafe_allow_html=True)

# ======================================================================
# 8. MENÚ PRINCIPAL
# ======================================================================

def mostrar_menu_principal():
    msg = f"{gestionar_nombre()}Por favor, indique el motivo de su consulta:"
    mostrar_mensaje_voz(msg)
    
    opciones = {
        "1️⃣ Retiro de Medicinas": "1",
        "2️⃣ Exámenes Médicos": "2",
        "3️⃣ Citas Médicas": "3",
        "4️⃣ Varias Opciones": "4",
        "5️⃣ Registrar Fecha Programada": "5"
    }
    
    seleccion = st.radio("**Seleccione una opción:**", list(opciones.keys()), key="menu_radio")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("▶️ Continuar", use_container_width=True):
            opcion = opciones[seleccion]
            st.session_state.opcion_menu = opcion
            
            if opcion == "1":
                st.session_state.paso = 'flujo_medicinas'
            elif opcion == "2":
                st.session_state.paso = 'flujo_examenes'
            elif opcion == "3":
                st.session_state.paso = 'flujo_citas'
            elif opcion == "4":
                st.session_state.paso = 'flujo_varias'
            elif opcion == "5":
                st.session_state.paso = 'flujo_fechas_programadas'
            
            st.session_state.subfase = 0
            st.rerun()

# ======================================================================
# 9. FLUJO DE MEDICINAS (CON FONDO CIUDAD)
# ======================================================================

def flujo_medicinas_streamlit():
    st.markdown('<div class="seccion-medicinas">', unsafe_allow_html=True)
    
    p = st.session_state.paciente
    
    if st.session_state.subfase == 0:
        mostrar_mensaje_voz("Iniciamos cordialmente con el retiro de medicinas.")
        st.session_state.subfase = 1
        time.sleep(2)
        st.rerun()
    
    elif st.session_state.subfase == 1:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, podría indicarme: ¿Es para Medicina General?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sí", key="med_gral_si"):
                p['med_tipo'] = "Medicina General"
                st.session_state.subfase = 5
                st.rerun()
        with col2:
            if st.button("❌ No", key="med_gral_no"):
                st.session_state.subfase = 2
                st.rerun()
    
    elif st.session_state.subfase == 2:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, podría indicarme: ¿Es para Especialista?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sí", key="med_esp_si"):
                st.session_state.subfase = 3
                st.rerun()
        with col2:
            if st.button("❌ No", key="med_esp_no"):
                st.session_state.subfase = 4
                st.rerun()
    
    elif st.session_state.subfase == 3:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, especifique cuál es la especialidad para el retiro de medicina")
        especialidad = st.text_input("**Especialidad:**", key="med_especialidad")
        if st.button("✅ Confirmar", key="med_esp_conf"):
            if especialidad.strip():
                p['med_tipo'] = especialidad.strip()
                st.session_state.subfase = 5
                st.rerun()
            else:
                st.warning("⚠️ Por favor ingrese la especialidad")
    
    elif st.session_state.subfase == 4:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, podría indicarme: ¿Es para Oncología?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sí", key="med_onco_si"):
                p['med_tipo'] = "Oncología"
                st.session_state.subfase = 5
                st.rerun()
        with col2:
            if st.button("❌ No", key="med_onco_no"):
                p['med_tipo'] = "especialidad no especificada"
                st.session_state.subfase = 5
                st.rerun()
    
    elif st.session_state.subfase == 5:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, indíqueme ¿Cuántas entregas le faltan?")
        num_entregas = st.number_input("**Número de entregas:**", min_value=1, max_value=12, value=1, key="med_num_entregas")
        if st.button("✅ Confirmar", key="med_num_conf"):
            p['num_entregas'] = int(num_entregas)
            st.session_state.subfase = 6
            st.rerun()
    
    elif st.session_state.subfase == 6:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, la fecha de su último retiro, dígame el día, el mes y el año.")
        fecha = st.text_input("**Fecha último retiro (DD/MM/AAAA):**", key="med_fecha_retiro")
        if st.button("✅ Confirmar", key="med_fecha_conf"):
            if validar_fecha(fecha):
                p['fecha_ult_retiro'] = fecha
                fecha_base = datetime.strptime(fecha, "%d/%m/%Y")
                p['prox_retiro_dt'] = obtener_dia_habil_anterior(fecha_base + timedelta(days=28), festivos_co)
                st.session_state.subfase = 7
                st.rerun()
            else:
                st.error("❌ Fecha inválida. Debe estar entre 31/05/2025 y hoy en formato DD/MM/AAAA")
    
    elif st.session_state.subfase == 7:
        st.success("✅ Información de medicinas registrada correctamente")
        if st.button("▶️ Continuar al resumen", key="med_finalizar"):
            st.session_state.paso = 'mostrar_resumen'
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ======================================================================
# 10. FLUJO DE EXÁMENES (CON FONDO CIUDAD)
# ======================================================================

def flujo_examenes_streamlit():
    st.markdown('<div class="seccion-examenes">', unsafe_allow_html=True)
    
    p = st.session_state.paciente
    
    if st.session_state.subfase == 0:
        mostrar_mensaje_voz("Continuamos gentilmente con sus exámenes médicos.")
        st.session_state.subfase = 1
        time.sleep(2)
        st.rerun()
    
    elif st.session_state.subfase == 1:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, podría indicarme: ¿Es examen de Sangre?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sí", key="ex_sangre_si"):
                p['ex_tipo'] = "Sangre"
                st.session_state.subfase = 5
                st.rerun()
        with col2:
            if st.button("❌ No", key="ex_sangre_no"):
                st.session_state.subfase = 2
                st.rerun()
    
    elif st.session_state.subfase == 2:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, podría indicarme: ¿Es examen de Rayos X?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sí", key="ex_rayosx_si"):
                p['ex_tipo'] = "Rayos X"
                st.session_state.subfase = 5
                st.rerun()
        with col2:
            if st.button("❌ No", key="ex_rayosx_no"):
                st.session_state.subfase = 3
                st.rerun()
    
    elif st.session_state.subfase == 3:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, podría indicarme: ¿Es examen de Ultrasonido?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sí", key="ex_ultra_si"):
                p['ex_tipo'] = "Ultrasonido"
                st.session_state.subfase = 5
                st.rerun()
        with col2:
            if st.button("❌ No", key="ex_ultra_no"):
                st.session_state.subfase = 4
                st.rerun()
    
    elif st.session_state.subfase == 4:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, podría indicarme: ¿Es examen de Resonancia o Tomografía?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sí", key="ex_reso_si"):
                p['ex_tipo'] = "Resonancia o Tomografía"
                st.session_state.subfase = 5
                st.rerun()
        with col2:
            if st.button("❌ No", key="ex_reso_no"):
                p['ex_tipo'] = "examen no especificado"
                st.session_state.subfase = 5
                st.rerun()
    
    elif st.session_state.subfase == 5:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Dígame, ¿en qué lugar le dieron la orden?")
        lugar = st.text_input("**Lugar de la orden:**", key="ex_lugar")
        if st.button("✅ Confirmar", key="ex_lugar_conf"):
            if lugar.strip():
                p['ex_lugar'] = lugar.strip()
                st.session_state.subfase = 6
                st.rerun()
            else:
                st.warning("⚠️ Por favor ingrese el lugar")
    
    elif st.session_state.subfase == 6:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, la fecha de la orden, dígame el día, el mes y el año.")
        fecha = st.text_input("**Fecha de la orden (DD/MM/AAAA):**", key="ex_fecha_orden")
        if st.button("✅ Confirmar", key="ex_fecha_conf"):
            if validar_fecha(fecha):
                p['ex_fecha_orden'] = fecha
                st.session_state.subfase = 7
                st.rerun()
            else:
                st.error("❌ Fecha inválida. Debe estar entre 31/05/2025 y hoy en formato DD/MM/AAAA")
    
    elif st.session_state.subfase == 7:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, indíqueme ¿en cuántos días debe entregar los resultados?")
        dias = st.number_input("**Días para entregar resultados:**", min_value=1, max_value=365, value=30, key="ex_dias")
        if st.button("✅ Confirmar", key="ex_dias_conf"):
            p['ex_dias_entrega'] = int(dias)
            fecha_orden = datetime.strptime(p['ex_fecha_orden'], "%d/%m/%Y")
            resta = p['ex_dias_entrega'] - 32
            if resta < 0 or resta == 2:
                p['prox_examen_dt'] = sumar_dias_habiles(fecha_orden, 3, festivos_co)
            else:
                p['prox_examen_dt'] = obtener_dia_habil_anterior(fecha_orden + timedelta(days=resta), festivos_co)
            st.session_state.subfase = 8
            st.rerun()
    
    elif st.session_state.subfase == 8:
        st.success("✅ Información de exámenes registrada correctamente")
        if st.button("▶️ Continuar al resumen", key="ex_finalizar"):
            st.session_state.paso = 'mostrar_resumen'
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ======================================================================
# 11. FLUJO DE CITAS (CON FONDO ABUELO)
# ======================================================================

def flujo_citas_streamlit():
    st.markdown('<div class="seccion-citas">', unsafe_allow_html=True)
    
    p = st.session_state.paciente
    
    if st.session_state.subfase == 0:
        mostrar_mensaje_voz("Pasamos amablemente a sus citas médicas.")
        st.session_state.subfase = 1
        time.sleep(2)
        st.rerun()
    
    elif st.session_state.subfase == 1:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, podría indicarme: ¿Es cita de Medicina General?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sí", key="cita_gral_si"):
                p['cita_tipo'] = "Medicina General"
                st.session_state.subfase = 5
                st.rerun()
        with col2:
            if st.button("❌ No", key="cita_gral_no"):
                st.session_state.subfase = 2
                st.rerun()
    
    elif st.session_state.subfase == 2:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, podría indicarme: ¿Es cita de Especialista?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sí", key="cita_esp_si"):
                st.session_state.subfase = 3
                st.rerun()
        with col2:
            if st.button("❌ No", key="cita_esp_no"):
                st.session_state.subfase = 4
                st.rerun()
    
    elif st.session_state.subfase == 3:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, especifique para qué especialidad es la cita médica")
        especialidad = st.text_input("**Especialidad:**", key="cita_especialidad")
        if st.button("✅ Confirmar", key="cita_esp_conf"):
            if especialidad.strip():
                p['cita_tipo'] = especialidad.strip()
                st.session_state.subfase = 5
                st.rerun()
            else:
                st.warning("⚠️ Por favor ingrese la especialidad")
    
    elif st.session_state.subfase == 4:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, podría indicarme: ¿Es cita de Oncología?")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ Sí", key="cita_onco_si"):
                p['cita_tipo'] = "Oncología"
                st.session_state.subfase = 5
                st.rerun()
        with col2:
            if st.button("🦷 Odontología", key="cita_odonto"):
                p['cita_tipo'] = "Odontología"
                st.session_state.subfase = 5
                st.rerun()
        with col3:
            if st.button("❌ Otra", key="cita_otra"):
                p['cita_tipo'] = "especialidad no especificada"
                st.session_state.subfase = 5
                st.rerun()
    
    elif st.session_state.subfase == 5:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿En qué lugar es la cita?")
        lugar = st.text_input("**Lugar de la cita:**", key="cita_lugar")
        if st.button("✅ Confirmar", key="cita_lugar_conf"):
            if lugar.strip():
                p['cita_lugar'] = lugar.strip()
                st.session_state.subfase = 6
                st.rerun()
            else:
                st.warning("⚠️ Por favor ingrese el lugar")
    
    elif st.session_state.subfase == 6:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, podría indicarme: ¿Es primera vez de la cita?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sí, primera vez", key="cita_primera_si"):
                st.session_state.valor_temporal = True
                st.session_state.subfase = 7
                st.rerun()
        with col2:
            if st.button("❌ No, es control", key="cita_primera_no"):
                st.session_state.valor_temporal = False
                st.session_state.subfase = 7
                st.rerun()
    
    elif st.session_state.subfase == 7:
        if st.session_state.valor_temporal:
            mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, la fecha de la orden de la cita, dígame el día, el mes y el año.")
        else:
            mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, la fecha de su última cita, dígame el día, el mes y el año.")
        
        fecha = st.text_input("**Fecha (DD/MM/AAAA):**", key="cita_fecha_ult")
        if st.button("✅ Confirmar", key="cita_fecha_conf"):
            if validar_fecha(fecha):
                p['cita_fecha_ult'] = fecha
                st.session_state.subfase = 8
                st.rerun()
            else:
                st.error("❌ Fecha inválida. Debe estar entre 31/05/2025 y hoy en formato DD/MM/AAAA")
    
    elif st.session_state.subfase == 8:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, podría indicarme: ¿Tiene usted un control por esa cita?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sí", key="cita_control_si"):
                st.session_state.subfase = 9
                st.rerun()
        with col2:
            if st.button("❌ No", key="cita_control_no"):
                p['prox_cita_dt'] = None
                st.session_state.subfase = 10
                st.rerun()
    
    elif st.session_state.subfase == 9:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, indíqueme ¿dentro de cuántos días es el control?")
        dias = st.number_input("**Días para control:**", min_value=1, max_value=365, value=30, key="cita_dias_control")
        if st.button("✅ Confirmar", key="cita_dias_conf"):
            p['dias_control'] = int(dias)
            fecha_u = datetime.strptime(p['cita_fecha_ult'], "%d/%m/%Y")
            resta = p['dias_control'] - 32
            if resta < 0 or resta == 2:
                p['prox_cita_dt'] = sumar_dias_habiles(fecha_u, 3, festivos_co)
            else:
                p['prox_cita_dt'] = obtener_dia_habil_anterior(fecha_u + timedelta(days=resta), festivos_co)
            st.session_state.subfase = 10
            st.rerun()
    
    elif st.session_state.subfase == 10:
        st.success("✅ Información de citas registrada correctamente")
        if st.button("▶️ Continuar al resumen", key="cita_finalizar"):
            st.session_state.paso = 'mostrar_resumen'
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ======================================================================
# 12. FLUJO VARIAS OPCIONES
# ======================================================================

def flujo_varias_streamlit():
    if st.session_state.subfase == 0:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, podría indicarme: ¿Necesita hacer retiro de medicina?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sí", key="varias_med_si"):
                st.session_state.subfase = 1
                st.session_state.flujo_actual = 'medicinas'
                st.rerun()
        with col2:
            if st.button("❌ No", key="varias_med_no"):
                st.session_state.subfase = 10
                st.rerun()
    
    elif st.session_state.subfase >= 1 and st.session_state.subfase < 10:
        if st.session_state.flujo_actual == 'medicinas':
            flujo_medicinas_streamlit()
            if st.session_state.subfase == 7:
                st.session_state.subfase = 10
                st.session_state.flujo_actual = None
                st.rerun()
    
    elif st.session_state.subfase == 10:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, podría indicarme: ¿Necesita hacerse exámenes médicos?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sí", key="varias_ex_si"):
                st.session_state.subfase = 11
                st.session_state.flujo_actual = 'examenes'
                st.rerun()
        with col2:
            if st.button("❌ No", key="varias_ex_no"):
                st.session_state.subfase = 20
                st.rerun()
    
    elif st.session_state.subfase >= 11 and st.session_state.subfase < 20:
        if st.session_state.flujo_actual == 'examenes':
            flujo_examenes_streamlit()
            if st.session_state.subfase == 8:
                st.session_state.subfase = 20
                st.session_state.flujo_actual = None
                st.rerun()
    
    elif st.session_state.subfase == 20:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, podría indicarme: ¿Necesita programar una cita médica?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sí", key="varias_cita_si"):
                st.session_state.subfase = 21
                st.session_state.flujo_actual = 'citas'
                st.rerun()
        with col2:
            if st.button("❌ No", key="varias_cita_no"):
                st.session_state.paso = 'mostrar_resumen'
                st.rerun()
    
    elif st.session_state.subfase >= 21:
        if st.session_state.flujo_actual == 'citas':
            flujo_citas_streamlit()
            if st.session_state.subfase == 10:
                st.session_state.paso = 'mostrar_resumen'
                st.rerun()

# ======================================================================
# 13. FLUJO FECHAS PROGRAMADAS (OPCIÓN 5) - CON FONDO ABUELO
# ======================================================================

def flujo_fechas_programadas_streamlit():
    st.markdown('<div class="seccion-programadas">', unsafe_allow_html=True)
    
    p = st.session_state.paciente
    
    if st.session_state.subfase == 0:
        mostrar_mensaje_voz("Evaluaremos sus citas programadas.")
        st.session_state.subfase = 1
        time.sleep(2)
        st.rerun()
    
    elif st.session_state.subfase == 1:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Tiene usted una cita programada con fecha definida para algún examen médico, por favor, confirme sí o no")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sí, examen médico", key="prog_examen_si"):
                p['prog_categoria'] = "Examen Médico"
                st.session_state.subfase = 2
                st.rerun()
        with col2:
            if st.button("❌ No", key="prog_examen_no"):
                st.session_state.subfase = 10
                st.rerun()
    
    elif st.session_state.subfase == 2:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, podría indicarme: ¿Es examen de Sangre?")
        opciones = ["Sangre", "Rayos X", "Ultrasonido", "Resonancia o Tomografía", "Otro"]
        seleccion = st.radio("**Tipo de examen:**", opciones, key="prog_tipo_ex")
        if st.button("✅ Confirmar", key="prog_tipo_ex_conf"):
            if seleccion == "Otro":
                st.session_state.subfase = 3
            else:
                p['prog_tipo'] = seleccion
                st.session_state.subfase = 4
            st.rerun()
    
    elif st.session_state.subfase == 3:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, especifique el tipo de examen")
        tipo = st.text_input("**Tipo de examen:**", key="prog_tipo_otro")
        if st.button("✅ Confirmar", key="prog_tipo_otro_conf"):
            if tipo.strip():
                p['prog_tipo'] = tipo.strip()
                st.session_state.subfase = 4
                st.rerun()
            else:
                st.warning("⚠️ Por favor ingrese el tipo")
    
    elif st.session_state.subfase == 4:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Indique el sitio a realizarse el examen médico")
        lugar = st.text_input("**Lugar:**", key="prog_lugar_ex")
        if st.button("✅ Confirmar", key="prog_lugar_ex_conf"):
            if lugar.strip():
                p['prog_lugar'] = lugar.strip()
                st.session_state.subfase = 5
                st.rerun()
            else:
                st.warning("⚠️ Por favor ingrese el lugar")
    
    elif st.session_state.subfase == 5:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, fecha a realizarse, dígame el día, el mes y el año.")
        fecha = st.text_input("**Fecha (DD/MM/AAAA):**", key="prog_fecha_ex")
        if st.button("✅ Confirmar", key="prog_fecha_ex_conf"):
            if validar_fecha(fecha, futura=True):
                p['prog_fecha_str'] = fecha
                st.session_state.subfase = 6
                st.rerun()
            else:
                st.error("❌ Fecha inválida. Debe ser desde 31/05/2025 en adelante en formato DD/MM/AAAA")
    
    elif st.session_state.subfase == 6:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Indique la hora de su cita, formato 24 horas, ejemplo 14 y 30")
        hora = st.text_input("**Hora (HH:MM):**", placeholder="14:30", key="prog_hora_ex")
        if st.button("✅ Confirmar", key="prog_hora_ex_conf"):
            if validar_hora(hora):
                p['prog_hora'] = hora
                st.session_state.subfase = 99
                st.rerun()
            else:
                st.error("❌ Hora inválida. Use formato HH:MM (ejemplo: 14:30)")

# ======================================================================
# CONTINUACIÓN DE FLUJO FECHAS PROGRAMADAS - Desde subfase 10
# ======================================================================

    elif st.session_state.subfase == 10:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Tiene una cita programada con fecha definida para alguna consulta con un médico, por favor, confirme sí o no")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sí, cita médica", key="prog_cita_si"):
                p['prog_categoria'] = "Cita Médica"
                st.session_state.subfase = 11
                st.rerun()
        with col2:
            if st.button("❌ No", key="prog_cita_no"):
                mostrar_mensaje_voz("Bienvenido. Registraremos sus datos para calcular y programar las fechas de sus medicinas...")
                st.info("✅ Sesión finalizada. Recargue la página para iniciar nuevamente.")
                st.stop()
    
    elif st.session_state.subfase == 11:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, podría indicarme: ¿Es cita de Medicina General?")
        opciones = ["Medicina General", "Especialista", "Oncología", "Odontología", "Otra"]
        seleccion = st.radio("**Tipo de cita:**", opciones, key="prog_tipo_cita")
        if st.button("✅ Confirmar", key="prog_tipo_cita_conf"):
            if seleccion == "Especialista" or seleccion == "Otra":
                st.session_state.valor_temporal = seleccion
                st.session_state.subfase = 12
            else:
                p['prog_tipo'] = seleccion
                st.session_state.subfase = 13
            st.rerun()
    
    elif st.session_state.subfase == 12:
        if st.session_state.valor_temporal == "Especialista":
            mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, especifique la especialidad")
        else:
            mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, especifique el área o especialidad")
        
        tipo = st.text_input("**Especialidad:**", key="prog_especialidad_cita")
        if st.button("✅ Confirmar", key="prog_esp_cita_conf"):
            if tipo.strip():
                p['prog_tipo'] = tipo.strip()
                st.session_state.subfase = 13
                st.rerun()
            else:
                st.warning("⚠️ Por favor ingrese la especialidad")
    
    elif st.session_state.subfase == 13:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Indique el sitio a realizarse la cita médica")
        lugar = st.text_input("**Lugar:**", key="prog_lugar_cita")
        if st.button("✅ Confirmar", key="prog_lugar_cita_conf"):
            if lugar.strip():
                p['prog_lugar'] = lugar.strip()
                st.session_state.subfase = 14
                st.rerun()
            else:
                st.warning("⚠️ Por favor ingrese el lugar")
    
    elif st.session_state.subfase == 14:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, fecha a realizarse, dígame el día, el mes y el año.")
        fecha = st.text_input("**Fecha (DD/MM/AAAA):**", key="prog_fecha_cita")
        if st.button("✅ Confirmar", key="prog_fecha_cita_conf"):
            if validar_fecha(fecha, futura=True):
                p['prog_fecha_str'] = fecha
                st.session_state.subfase = 15
                st.rerun()
            else:
                st.error("❌ Fecha inválida. Debe ser desde 31/05/2025 en adelante en formato DD/MM/AAAA")
    
    elif st.session_state.subfase == 15:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Indique la hora de su cita, formato 24 horas, ejemplo 14 y 30")
        hora = st.text_input("**Hora (HH:MM):**", placeholder="14:30", key="prog_hora_cita")
        if st.button("✅ Confirmar", key="prog_hora_cita_conf"):
            if validar_hora(hora):
                p['prog_hora'] = hora
                st.session_state.subfase = 99
                st.rerun()
            else:
                st.error("❌ Hora inválida. Use formato HH:MM (ejemplo: 14:30)")
    
    elif st.session_state.subfase == 99:
        # ENVÍO DE NOTIFICACIÓN INMEDIATA (solo para opción 5)
        notificacion_msg = f"Cita Programada: {p['prog_categoria']} ({p['prog_tipo']}) en {p['prog_lugar']} el {p['prog_fecha_str']} a las {p['prog_hora']}."
        
        st.success("✅ Información guardada correctamente")
        st.info(notificacion_msg)
        
        # CRONOGRAMA DE NOTIFICACIONES (solo informativo en pantalla)
        fecha_prog = datetime.strptime(p['prog_fecha_str'], "%d/%m/%Y")
        hoy = datetime.now(tz_co).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
        dias_diff = (fecha_prog - hoy).days
        
        st.markdown("### 📅 CRONOGRAMA DE NOTIFICACIONES")
        dias_aviso = [5, 3, 1] if dias_diff > 5 else ([3, 1] if dias_diff == 4 else [1])
        for d in sorted(dias_aviso, reverse=True):
            f_aviso = (fecha_prog - timedelta(days=d)).strftime("%d/%m/%Y")
            st.write(f"📢 Recordatorio día -{d}: **{f_aviso}** a las 10:30am y 07:45pm")
        
        mostrar_mensaje_voz("Se han programado las notificaciones para su cita confirmada.")
        
        # ENVÍO FÍSICO DE NOTIFICACIÓN INMEDIATA
        enviar_notificaciones(notificacion_msg, p['paciente'])
        
        if st.button("▶️ Continuar al resumen", key="prog_finalizar"):
            st.session_state.paso = 'mostrar_resumen'
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ======================================================================
# 14. MOSTRAR RESUMEN FINAL
# ======================================================================

def mostrar_resumen_final():
    p = st.session_state.paciente
    
    st.markdown("## 📋 RESUMEN DE FECHAS CALCULADAS")
    
    resumen_items = []
    
    if "prox_retiro_dt" in p:
        msg = f"Su próximo retiro de medicina ({p.get('med_tipo', '')}) es el **{p['prox_retiro_dt'].strftime('%d/%m/%Y')}**"
        st.success(f"💊 {msg}")
        mostrar_mensaje_voz(msg)
        time.sleep(6)  # Duración del audio como en código Python
        resumen_items.append(msg)
    
    if "prox_examen_dt" in p:
        msg = f"Su examen ({p.get('ex_tipo', '')}) debe solicitarse el **{p['prox_examen_dt'].strftime('%d/%m/%Y')}**"
        st.info(f"🔬 {msg}")
        mostrar_mensaje_voz(msg)
        time.sleep(6)
        resumen_items.append(msg)
    
    if "prox_cita_dt" in p and p["prox_cita_dt"]:
        msg = f"Su cita ({p.get('cita_tipo', '')}) debe solicitarse el **{p['prox_cita_dt'].strftime('%d/%m/%Y')}**"
        st.warning(f"📅 {msg}")
        mostrar_mensaje_voz(msg)
        time.sleep(6)
        resumen_items.append(msg)
    
    # GUARDAR EN BASE DE DATOS
    if guardar_en_db(p):
        st.success("✅ Información guardada en la base de datos")
        
        # CONFIRMACIÓN DE CONTACTO (según código Python)
        notif_msg = f"Se ha registrado su solicitud. Recibirá notificaciones en **{EMAIL_RECEIVER}** y Telegram **+{TELEGRAM_CHAT_ID[:2]} {TELEGRAM_CHAT_ID[2:5]} {TELEGRAM_CHAT_ID[5:8]} {TELEGRAM_CHAT_ID[8:]}**"
        st.info(notif_msg)
        mostrar_mensaje_voz(notif_msg)
        time.sleep(14)  # Duración del audio
    
    st.markdown("---")
    
    # PREGUNTA SOBRE NUEVO REQUERIMIENTO
    mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, podría indicarme: ¿Tiene algún otro requerimiento?")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Sí, Nuevo Requerimiento", use_container_width=True):
            st.session_state.paso = 'menu_principal'
            st.session_state.paciente = {"paciente": st.session_state.nombre_paciente}
            st.session_state.subfase = 0
            st.session_state.contador_interacciones = 0
            st.rerun()
    
    with col2:
        if st.button("❌ No, Finalizar Sesión", use_container_width=True):
            mostrar_mensaje_voz("Muchas gracias por usar nuestro servicio. Que tenga un excelente día.")
            st.balloons()
            time.sleep(3)
            # Reiniciar completamente
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# ======================================================================
# EJECUTAR APLICACIÓN
# ======================================================================

if __name__ == "__main__":
    main()


