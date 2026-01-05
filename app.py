import streamlit as st
import mysql.connector
import time
import holidays
import pytz
import requests
import smtplib
from email.mime.text import MIMEText
from gtts import gTTS
from datetime import datetime, timedelta
import base64
from io import BytesIO

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Asistente de Salud IA",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
<style>
    /* Eliminar todos los fondos blancos */
    .stApp {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e22ce 100%);
    }
    
    /* Contenedor principal */
    .main .block-container {
        padding: 2rem 1rem;
        max-width: 100%;
    }
    
    /* Títulos y textos */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, div {
        color: #FFD700 !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    
    /* Inputs y selectbox */
    .stTextInput input, .stSelectbox select, .stTextArea textarea, .stNumberInput input, .stDateInput input, .stTimeInput input {
        background-color: rgba(30, 60, 114, 0.8) !important;
        color: #FFD700 !important;
        border: 2px solid #00BFFF !important;
        border-radius: 10px;
        font-weight: bold;
    }
    
    /* Botones principales */
    .stButton button {
        background: linear-gradient(90deg, #00BFFF 0%, #1e90ff 100%) !important;
        color: #FFD700 !important;
        border: 3px solid #C0C0C0 !important;
        border-radius: 15px;
        font-size: 18px;
        font-weight: bold;
        padding: 12px 24px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        transition: all 0.3s;
    }
    
    .stButton button:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 12px rgba(0,0,0,0.5);
    }
    
    /* Contenedores de información */
    .info-box {
        background: rgba(30, 60, 114, 0.7);
        border: 3px solid #00BFFF;
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    
    /* Pie de página */
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: #FFD700;
        text-align: center;
        padding: 15px;
        border-top: 3px solid #00BFFF;
        font-size: 12px;
        z-index: 999;
        box-shadow: 0 -4px 8px rgba(0,0,0,0.3);
    }
    
    /* Avatar */
    .avatar-img {
        border-radius: 50%;
        border: 3px solid #FFD700;
        box-shadow: 0 4px 8px rgba(0,0,0,0.5);
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem 0.5rem;
        }
        .stButton button {
            font-size: 14px;
            padding: 8px 16px;
        }
        .footer {
            font-size: 10px;
            padding: 10px;
        }
    }
    
    @media (min-width: 1920px) {
        .main .block-container {
            max-width: 1800px;
            margin: 0 auto;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN GLOBAL ---
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

# --- INICIALIZACIÓN DE SESSION STATE ---
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'paciente' not in st.session_state:
    st.session_state.paciente = {}
if 'nombre_paciente_global' not in st.session_state:
    st.session_state.nombre_paciente_global = ""
if 'contador_interacciones' not in st.session_state:
    st.session_state.contador_interacciones = 0
if 'esperando_confirmacion' not in st.session_state:
    st.session_state.esperando_confirmacion = False
if 'valor_temporal' not in st.session_state:
    st.session_state.valor_temporal = None
if 'pregunta_temporal' not in st.session_state:
    st.session_state.pregunta_temporal = ""
if 'intentos' not in st.session_state:
    st.session_state.intentos = 0

# --- FUNCIONES DE UTILIDAD ---
def enviar_notificaciones(mensaje_texto, nombre_paciente):
    """Envía notificaciones vía Telegram y Email con el nombre del paciente al inicio."""
    mensaje_personalizado = f"PACIENTE: {nombre_paciente}
{mensaje_texto}"
    
    # 1. Envío por Telegram
    try:
        url_tg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': f"🔔 RECORDATORIO SALUD:
{mensaje_personalizado}",
            'parse_mode': 'Markdown'
        }
        requests.post(url_tg, data=payload, timeout=10)
    except Exception as e:
        st.warning(f"Error enviando Telegram: {e}")
    
    # 2. Envío por Email (SMTP Gmail)
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

def generar_audio(texto):
    """Genera audio con gTTS y lo retorna en base64"""
    try:
        tts = gTTS(text=texto, lang='es', tld='com.co')
        audio_buffer = BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        audio_b64 = base64.b64encode(audio_buffer.read()).decode()
        return audio_b64
    except:
        return None

def reproducir_audio(texto):
    """Reproduce audio en Streamlit con JavaScript mejorado"""
    audio_b64 = generar_audio(texto)
    if audio_b64:
        audio_id = f"audio_{abs(hash(texto + str(time.time()))) % 1000000}"
        audio_html = f"""
        <audio id="{audio_id}" style="display:none;">
            <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
        </audio>
        <script>
            (function() {{
                var audio = document.getElementById('{audio_id}');
                if (audio) {{
                    audio.play().catch(function(error) {{
                        console.log('Autoplay bloqueado:', error);
                    }});
                }}
            }})();
        </script>
        """
        st.markdown(audio_html, unsafe_allow_html=True)

def gestionar_nombre():
    if st.session_state.contador_interacciones % 4 == 0 and st.session_state.nombre_paciente_global:
        st.session_state.contador_interacciones += 1
        return f"{st.session_state.nombre_paciente_global}, "
    st.session_state.contador_interacciones += 1
    return ""

def simplificar_pregunta(pregunta):
    pregunta = pregunta.replace("¿", "").replace("?", "").lower()
    palabras_a_quitar = [
        "para", "de", "la", "el", "en", "donde", "su", "una", "con", "es", "que",
        "cuál", "por", "favor", "sería", "tan", "amable", "gentil", "dígame", "indique"
    ]
    palabras = pregunta.split()
    filtradas = [p for p in palabras if p not in palabras_a_quitar]
    return " ".join(filtradas).capitalize()

def verificar_conexion():
    try:
        conn = mysql.connector.connect(**config)
        if conn.is_connected():
            conn.close()
            return True
    except Exception as e:
        st.error(f"❌ Error crítico de conexión: {e}")
        return False

def consultar_historial(nombre):
    try:
        conn = mysql.connector.connect(**config)
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
        st.error(f"Error al consultar historial: {e}")
        return []

def guardar_en_db(p):
    try:
        conn = mysql.connector.connect(**config)
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
        st.success("✅ Información guardada exitosamente en la base de datos.")
        return True
    except Exception as e:
        st.error(f"❌ Error al guardar en la base de datos: {e}")
        return False

def reset_app():
    """Resetea la aplicación a la página principal"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- BOTÓN DE CANCELAR (SIEMPRE VISIBLE) ---
col_cancel1, col_cancel2, col_cancel3 = st.columns([6, 2, 1])
with col_cancel2:
    if st.button("🚫 CANCELAR Y REGRESAR A LA PÁGINA PRINCIPAL", key="cancel_button", use_container_width=True):
        mensaje_cancel = "Operación cancelada. No se ha guardado ninguna información. Regresando a la página principal."
        st.warning(mensaje_cancel)
        reproducir_audio(mensaje_cancel)
        time.sleep(2)
        reset_app()

st.markdown("""
<style>
    button[data-testid="baseButton-secondary"] {
        background: linear-gradient(90deg, #FFD700 0%, #FFA500 100%) !important;
        color: #0000FF !important;
        border: 3px solid #000000 !important;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- PÁGINA PRINCIPAL ---
if st.session_state.step == 0:
    st.markdown(f"""
    <div style="text-align: center; padding: 20px;">
        <img src="https://i.ibb.co/jZb8bxGk/i8.jpg" 
             style="max-width: 100%; border-radius: 20px; box-shadow: 0 8px 16px rgba(0,0,0,0.5);">
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1 style='text-align: center; color: #FFD700; font-size: 48px;'>🏥 Asistente IA de Salud</h1>", unsafe_allow_html=True)
    
    saludo = "Bienvenido al gestor de salud. Realizaremos preguntas para calcular o registrar sus fechas..."
    st.markdown(f"<div class='info-box'><h3 style='color: #90EE90;'>{saludo}</h3></div>", unsafe_allow_html=True)
    reproducir_audio(saludo)
    
    # Avatar
    st.markdown(f"""
    <div style="text-align: center; margin: 20px 0;">
        <img src="https://i.ibb.co/zVFp4SmV/avatar-Mauricio.png" 
             class="avatar-img" style="width: 120px; height: 120px;">
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚀 INICIAR ASISTENTE", use_container_width=True):
        if verificar_conexion():
            st.session_state.step = 1
            st.rerun()
        else:
            st.error("No se ha podido establecer conexión con la base de datos.")
            reproducir_audio("No se ha podido establecer conexión con la base de datos.")

# --- PASO 1: NOMBRE DEL PACIENTE ---
elif st.session_state.step == 1:
    st.markdown("<h2 style='color: #00BFFF;'>📝 Información del Paciente</h2>", unsafe_allow_html=True)
    
    # Imagen decorativa
    st.markdown(f"""
    <div style="text-align: center; margin: 20px 0;">
        <img src="https://i.ibb.co/spG69fPs/i7.png" 
             style="max-width: 80%; border-radius: 15px; box-shadow: 0 6px 12px rgba(0,0,0,0.4);">
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.esperando_confirmacion:
        prompt_voz = "Para iniciar, por favor permítame saber el nombre del paciente"
        st.markdown(f"<div class='info-box'><p style='color: #90EE90;'>{prompt_voz}</p></div>", unsafe_allow_html=True)
        reproducir_audio(gestionar_nombre() + prompt_voz)
        
        nombre = st.text_input("Nombre del Paciente:", key="input_nombre")
        
        if st.button("✅ Confirmar Nombre", use_container_width=True):
            if nombre.strip():
                st.session_state.valor_temporal = nombre.strip()
                st.session_state.pregunta_temporal = "Nombre del Paciente"
                st.session_state.esperando_confirmacion = True
                st.session_state.intentos = 0
                st.rerun()
            else:
                st.error("Por favor ingrese un nombre válido.")
    else:
        # Confirmación
        label_corto = simplificar_pregunta(st.session_state.pregunta_temporal)
        confirm_msg = f"{gestionar_nombre()}Usted eligió {label_corto}, respuesta {st.session_state.valor_temporal}, por favor, indique, ¿es correcto sí o no?"
        st.markdown(f"<div class='info-box'><p style='color: #FFD700;'>{confirm_msg}</p></div>", unsafe_allow_html=True)
        reproducir_audio(confirm_msg)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ SÍ, ES CORRECTO", use_container_width=True):
                st.session_state.nombre_paciente_global = st.session_state.valor_temporal
                st.session_state.paciente['paciente'] = st.session_state.valor_temporal
                st.session_state.esperando_confirmacion = False
                st.session_state.step = 2
                st.rerun()
        
        with col2:
            if st.button("❌ NO, REINTENTAR", use_container_width=True):
                st.session_state.intentos += 1
                if st.session_state.intentos < 2:
                    reproducir_audio("Entendido, vamos a intentarlo de nuevo.")
                    st.session_state.esperando_confirmacion = False
                    st.rerun()
                else:
                    msg = "Lo lamento, no hemos podido validar la información. El programa se cerrará por seguridad. Intente nuevamente desde el inicio Gracias."
                    st.error(msg)
                    reproducir_audio(msg)
                    time.sleep(5)
                    reset_app()

# --- PASO 2: CONSULTAR HISTORIAL ---
elif st.session_state.step == 2:
    st.markdown(f"<h2 style='color: #00BFFF;'>📋 Historial de {st.session_state.nombre_paciente_global}</h2>", unsafe_allow_html=True)
    
    filas = consultar_historial(st.session_state.nombre_paciente_global)
    
    if filas:
        pregunta_hist = f"¿Desea visualizar las consultas previas de {st.session_state.nombre_paciente_global}?"
        st.markdown(f"<div class='info-box'><p style='color: #90EE90;'>{pregunta_hist}</p></div>", unsafe_allow_html=True)
        reproducir_audio(pregunta_hist)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ SÍ, MOSTRAR HISTORIAL", use_container_width=True):
                msg = f"He encontrado sus últimos registros, {st.session_state.nombre_paciente_global}. Aquí tiene un resumen:"
                reproducir_audio(msg)
                st.markdown(f"<div class='info-box'><h3 style='color: #FFD700;'>Últimos 4 Registros:</h3>", unsafe_allow_html=True)
                for f in filas:
                    detalles = []
                    if f[1]: detalles.append(f"<strong>Retiro {f[0]}:</strong> {f[1]}")
                    if f[3]: detalles.append(f"<strong>Examen {f[2]}:</strong> {f[3]}")
                    if f[5]: detalles.append(f"<strong>Cita {f[4]}:</strong> {f[5]}")
                    if f[7]: detalles.append(f"<strong>Programado ({f[6]}):</strong> {f[7]}")
                    if detalles:
                        st.markdown(f"<p style='color: #C0C0C0;'>{' | '.join(detalles)}</p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                time.sleep(2)
                st.session_state.step = 3
                st.rerun()
        
        with col2:
            if st.button("⏭️ NO, CONTINUAR", use_container_width=True):
                st.session_state.step = 3
                st.rerun()
    else:
        st.info("No se encontró historial previo.")
        time.sleep(1)
        st.session_state.step = 3
        st.rerun()

# --- PASO 3: MENÚ PRINCIPAL ---
elif st.session_state.step == 3:
    st.markdown("<h2 style='color: #00BFFF;'>🎯 Seleccione el Motivo de su Consulta</h2>", unsafe_allow_html=True)
    
    # Imagen decorativa
    st.markdown(f"""
    <div style="text-align: center; margin: 20px 0;">
        <img src="https://i.ibb.co/QjpntM88/i6.png" 
             style="max-width: 80%; border-radius: 15px; box-shadow: 0 6px 12px rgba(0,0,0,0.4);">
    </div>
    """, unsafe_allow_html=True)
    
    msg_menu = "indique el motivo de su consulta: 1 Retiro medicinas, 2 Exámenes médicos, 3 Citas médicas, 4 Varias o 5 Registrar fecha programada."
    st.markdown(f"<div class='info-box'><p style='color: #90EE90;'>{gestionar_nombre()}Por favor, {msg_menu}</p></div>", unsafe_allow_html=True)
    reproducir_audio(gestionar_nombre() + "Por favor, " + msg_menu)
    
    opciones_menu = {
        "1": "💊 Retiro de Medicinas",
        "2": "🔬 Exámenes Médicos",
        "3": "👨‍⚕️ Citas Médicas",
        "4": "📋 Varias Opciones",
        "5": "📅 Registrar Fecha Programada"
    }
    
    opcion = st.selectbox(
        "Seleccione una opción:",
        options=list(opciones_menu.keys()),
        format_func=lambda x: opciones_menu[x],
        key="menu_principal"
    )
    
    if st.button("➡️ CONTINUAR", use_container_width=True):
        st.session_state.opcion_seleccionada = opcion
        st.session_state.step = 10 + int(opcion)
        st.rerun()

# --- PASO 11: FLUJO MEDICINAS ---
elif st.session_state.step == 11:
    st.markdown("<h2 style='color: #00BFFF;'>💊 Retiro de Medicinas</h2>", unsafe_allow_html=True)
    
    mensaje_inicio = "Iniciamos cordialmente con el retiro de medicinas."
    st.markdown(f"<div class='info-box'><p style='color: #90EE90;'>{mensaje_inicio}</p></div>", unsafe_allow_html=True)
    reproducir_audio(mensaje_inicio)
    
    if 'med_paso' not in st.session_state:
        st.session_state.med_paso = 0
    
    # Sub-paso 0: Selección de tipo
    if st.session_state.med_paso == 0:
        opciones = ["Medicina General", "Especialista", "Oncología"]
        
        st.markdown("<h3 style='color: #FFD700;'>Seleccione el tipo de medicina:</h3>", unsafe_allow_html=True)
        
        for opt in opciones:
            pregunta = f"¿Es para {opt}?"
            if st.button(f"✅ {opt}", key=f"med_{opt}", use_container_width=True):
                reproducir_audio(gestionar_nombre() + "Por favor, podría indicarme: " + pregunta)
                if opt == "Especialista":
                    st.session_state.med_tipo_temp = "Especialista"
                    st.session_state.med_paso = 1
                else:
                    st.session_state.paciente['med_tipo'] = opt
                    st.session_state.med_paso = 2
                st.rerun()
        
        if st.button("🔄 Otra Especialidad", use_container_width=True):
            reproducir_audio(gestionar_nombre() + "Por favor, podría indicarme: ¿Es para alguna otra especialidad?")
            st.session_state.med_paso = 1
            st.rerun()
    
    # Sub-paso 1: Especificar especialidad
    elif st.session_state.med_paso == 1:
        prompt = "Por favor, especifique cuál es la especialidad para el retiro de medicina"
        st.markdown(f"<div class='info-box'><p style='color: #90EE90;'>{prompt}</p></div>", unsafe_allow_html=True)
        reproducir_audio(gestionar_nombre() + prompt)
        
        especialidad = st.text_input("Especifique la especialidad:", key="med_especialidad")
        
        if st.button("✅ Confirmar Especialidad", use_container_width=True):
            if especialidad.strip():
                st.session_state.paciente['med_tipo'] = especialidad.strip()
                st.session_state.med_paso = 2
                st.rerun()
    
    # Sub-paso 2: Número de entregas
    elif st.session_state.med_paso == 2:
        prompt = "Por favor, indíqueme ¿Cuántas entregas le faltan?"
        st.markdown(f"<div class='info-box'><p style='color: #90EE90;'>{prompt}</p></div>", unsafe_allow_html=True)
        reproducir_audio(gestionar_nombre() + prompt)
        
        num_entregas = st.number_input("¿Cuántas entregas le faltan?", min_value=1, max_value=100, step=1, key="med_entregas")
        
        if st.button("✅ Confirmar", use_container_width=True):
            st.session_state.paciente['num_entregas'] = int(num_entregas)
            st.session_state.med_paso = 3
            st.rerun()
    
    # Sub-paso 3: Fecha último retiro
    elif st.session_state.med_paso == 3:
        prompt = "Por favor, la fecha de su último retiro, dígame el día, el mes y el año."
        st.markdown(f"<div class='info-box'><p style='color: #90EE90;'>{prompt}</p></div>", unsafe_allow_html=True)
        reproducir_audio(gestionar_nombre() + prompt)
        
        fecha_retiro = st.date_input(
            "Fecha de su último retiro:",
            min_value=datetime(2025, 5, 31),
            max_value=datetime.now(),
            key="med_fecha_retiro"
        )
        
        if st.button("✅ Confirmar Fecha", use_container_width=True):
            fecha_str = fecha_retiro.strftime("%d/%m/%Y")
            st.session_state.paciente['fecha_ult_retiro'] = fecha_str
            fecha_base = datetime.strptime(fecha_str, "%d/%m/%Y")
            st.session_state.paciente['prox_retiro_dt'] = obtener_dia_habil_anterior(
                fecha_base + timedelta(days=28), festivos_co
            )
            
            # Verificar si viene desde "Varias"
            if 'varias_desde_varias' in st.session_state and st.session_state.varias_desde_varias:
                st.session_state.varias_paso = 2
                st.session_state.step = 14
                del st.session_state['varias_desde_varias']
            else:
                st.session_state.step = 50
            
            # Limpiar estado de medicinas
            for key in list(st.session_state.keys()):
                if key.startswith('med_'):
                    del st.session_state[key]
            
            st.rerun()

# --- PASO 12: FLUJO EXÁMENES ---
elif st.session_state.step == 12:
    st.markdown("<h2 style='color: #00BFFF;'>🔬 Exámenes Médicos</h2>", unsafe_allow_html=True)
    
    mensaje_inicio = "Continuamos gentilmente con sus exámenes médicos."
    st.markdown(f"<div class='info-box'><p style='color: #90EE90;'>{mensaje_inicio}</p></div>", unsafe_allow_html=True)
    reproducir_audio(mensaje_inicio)
    
    if 'ex_paso' not in st.session_state:
        st.session_state.ex_paso = 0
    
    # Sub-paso 0: Tipo de examen
    if st.session_state.ex_paso == 0:
        opciones = ["Sangre", "Rayos X", "Ultrasonido", "Resonancia o Tomografía"]
        
        st.markdown("<h3 style='color: #FFD700;'>Seleccione el tipo de examen:</h3>", unsafe_allow_html=True)
        
        for opt in opciones:
            pregunta = f"¿Es examen de {opt}?"
            if st.button(f"✅ {opt}", key=f"ex_{opt}", use_container_width=True):
                reproducir_audio(gestionar_nombre() + "Por favor, podría indicarme: " + pregunta)
                st.session_state.paciente['ex_tipo'] = opt
                st.session_state.ex_paso = 1
                st.rerun()
        
        if st.button("🔄 Otro Tipo de Examen", use_container_width=True):
            reproducir_audio(gestionar_nombre() + "Por favor, podría indicarme: ¿Es algún otro tipo de examen?")
            st.session_state.ex_necesita_especificar = True
            st.session_state.ex_paso = 0.5
            st.rerun()
    
    # Sub-paso 0.5: Especificar otro tipo
    elif st.session_state.ex_paso == 0.5:
        prompt = "Por favor, especifique qué otro tipo de examen médico requiere"
        st.markdown(f"<div class='info-box'><p style='color: #90EE90;'>{prompt}</p></div>", unsafe_allow_html=True)
        reproducir_audio(gestionar_nombre() + prompt)
        
        otro_ex = st.text_input("Especifique el tipo de examen:", key="ex_otro")
        
        if st.button("✅ Confirmar", use_container_width=True):
            if otro_ex.strip():
                st.session_state.paciente['ex_tipo'] = otro_ex.strip()
                st.session_state.ex_paso = 1
                st.rerun()
    
    # Sub-paso 1: Lugar de la orden
    elif st.session_state.ex_paso == 1:
        prompt = "Dígame, ¿en qué lugar le dieron la orden?"
        st.markdown(f"<div class='info-box'><p style='color: #90EE90;'>{prompt}</p></div>", unsafe_allow_html=True)
        reproducir_audio(gestionar_nombre() + prompt)
        
        lugar = st.text_input("el lugar de la orden:", key="ex_lugar")
        
        if st.button("✅ Confirmar Lugar", use_container_width=True):
            if lugar.strip():
                st.session_state.paciente['ex_lugar'] = lugar.strip()
                st.session_state.ex_paso = 2
                st.rerun()
    
    # Sub-paso 2: Fecha de la orden
    elif st.session_state.ex_paso == 2:
        prompt = "Por favor, la fecha de la orden, dígame el día, el mes y el año."
        st.markdown(f"<div class='info-box'><p style='color: #90EE90;'>{prompt}</p></div>", unsafe_allow_html=True)
        reproducir_audio(gestionar_nombre() + prompt)
        
        fecha_orden = st.date_input(
            "la fecha de la orden:",
            min_value=datetime(2025, 5, 31),
            key="ex_fecha_orden"
        )
        
        if st.button("✅ Confirmar Fecha", use_container_width=True):
            st.session_state.paciente['ex_fecha_orden'] = fecha_orden.strftime("%d/%m/%Y")
            st.session_state.ex_paso = 3
            st.rerun()
    
    # Sub-paso 3: Días de entrega
    elif st.session_state.ex_paso == 3:
        prompt = "Por favor, indíqueme ¿en cuántos días debe entregar los resultados?"
        st.markdown(f"<div class='info-box'><p style='color: #90EE90;'>{prompt}</p></div>", unsafe_allow_html=True)
        reproducir_audio(gestionar_nombre() + prompt)
        
        dias = st.number_input("¿en cuántos días debe entregar los resultados?", min_value=1, max_value=365, step=1, key="ex_dias")
        
        if st.button("✅ Confirmar", use_container_width=True):
            st.session_state.paciente['ex_dias_entrega'] = int(dias)
            fecha_orden = datetime.strptime(st.session_state.paciente['ex_fecha_orden'], "%d/%m/%Y")
            resta = st.session_state.paciente['ex_dias_entrega'] - 32
            if resta < 0 or resta == 2:
                st.session_state.paciente['prox_examen_dt'] = sumar_dias_habiles(fecha_orden, 3, festivos_co)
            else:
                st.session_state.paciente['prox_examen_dt'] = obtener_dia_habil_anterior(
                    fecha_orden + timedelta(days=resta), festivos_co
                )
            
            # Verificar si viene desde "Varias"
            if 'varias_desde_varias' in st.session_state and st.session_state.varias_desde_varias:
                st.session_state.varias_paso = 4
                st.session_state.step = 14
                del st.session_state['varias_desde_varias']
            else:
                st.session_state.step = 50
            
            # Limpiar estado de exámenes
            for key in list(st.session_state.keys()):
                if key.startswith('ex_'):
                    del st.session_state[key]
            
            st.rerun()

# --- PASO 13: FLUJO CITAS ---
elif st.session_state.step == 13:
    st.markdown("<h2 style='color: #00BFFF;'>👨‍⚕️ Citas Médicas</h2>", unsafe_allow_html=True)
    
    mensaje_inicio = "Pasamos amablemente a sus citas médicas."
    st.markdown(f"<div class='info-box'><p style='color: #90EE90;'>{mensaje_inicio}</p></div>", unsafe_allow_html=True)
    reproducir_audio(mensaje_inicio)
    
    if 'cita_paso' not in st.session_state:
        st.session_state.cita_paso = 0
    
    # Sub-paso 0: Tipo de cita
    if st.session_state.cita_paso == 0:
        opciones = ["Medicina General", "Especialista", "Oncología", "Odontología"]
        
        st.markdown("<h3 style='color: #FFD700;'>Seleccione el tipo de cita:</h3>", unsafe_allow_html=True)
        
        for opt in opciones:
            pregunta = f"¿Es cita de {opt}?"
            if st.button(f"✅ {opt}", key=f"cita_{opt}", use_container_width=True):
                reproducir_audio(gestionar_nombre() + "Por favor, podría indicarme: " + pregunta)
                if opt == "Especialista":
                    st.session_state.cita_necesita_especificar = True
                    st.session_state.cita_paso = 0.5
                else:
                    st.session_state.paciente['cita_tipo'] = opt
                    st.session_state.cita_paso = 1
                st.rerun()
        
        if st.button("🔄 Otra Especialidad", use_container_width=True):
            reproducir_audio(gestionar_nombre() + "Por favor, podría indicarme: ¿Es para alguna otra especialidad?")
            st.session_state.cita_paso = 0.5
            st.rerun()
    
    # Sub-paso 0.5: Especificar especialidad
    elif st.session_state.cita_paso == 0.5:
        prompt = "Por favor, especifique para qué especialidad es la cita médica"
        st.markdown(f"<div class='info-box'><p style='color: #90EE90;'>{prompt}</p></div>", unsafe_allow_html=True)
        reproducir_audio(gestionar_nombre() + prompt)
        
        especialidad = st.text_input("Especifique la especialidad:", key="cita_especialidad")
        
        if st.button("✅ Confirmar", use_container_width=True):
            if especialidad.strip():
                st.session_state.paciente['cita_tipo'] = especialidad.strip()
                st.session_state.cita_paso = 1
                st.rerun()
    
    # Sub-paso 1: Lugar de la cita
    elif st.session_state.cita_paso == 1:
        prompt = "¿En qué lugar es la cita?"
        st.markdown(f"<div class='info-box'><p style='color: #90EE90;'>{prompt}</p></div>", unsafe_allow_html=True)
        reproducir_audio(gestionar_nombre() + prompt)
        
        lugar = st.text_input("el lugar de la cita:", key="cita_lugar")
        
        if st.button("✅ Confirmar Lugar", use_container_width=True):
            if lugar.strip():
                st.session_state.paciente['cita_lugar'] = lugar.strip()
                st.session_state.cita_paso = 2
                st.rerun()
    
    # Sub-paso 2: Primera vez o no
    elif st.session_state.cita_paso == 2:
        pregunta = "¿Es primera vez de la cita?"
        st.markdown(f"<div class='info-box'><p style='color: #90EE90;'>{pregunta}</p></div>", unsafe_allow_html=True)
        reproducir_audio(gestionar_nombre() + "Por favor, podría indicarme: " + pregunta)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ SÍ, PRIMERA VEZ", use_container_width=True):
                st.session_state.cita_es_primera = True
                st.session_state.cita_paso = 3
                st.rerun()
        with col2:
            if st.button("❌ NO, YA HE IDO", use_container_width=True):
                st.session_state.cita_es_primera = False
                st.session_state.cita_paso = 3
                st.rerun()
    
    # Sub-paso 3: Fecha (orden o última cita)
    elif st.session_state.cita_paso == 3:
        if st.session_state.cita_es_primera:
            prompt = "Por favor, la fecha de la orden de la cita, dígame el día, el mes y el año."
        else:
            prompt = "Por favor, la fecha de su última cita, dígame el día, el mes y el año."
        
        st.markdown(f"<div class='info-box'><p style='color: #90EE90;'>{prompt}</p></div>", unsafe_allow_html=True)
        reproducir_audio(gestionar_nombre() + prompt)
        
        fecha_cita = st.date_input(
            "Fecha:",
            min_value=datetime(2025, 5, 31),
            max_value=datetime.now(),
            key="cita_fecha"
        )
        
        if st.button("✅ Confirmar Fecha", use_container_width=True):
            st.session_state.paciente['cita_fecha_ult'] = fecha_cita.strftime("%d/%m/%Y")
            st.session_state.cita_paso = 4
            st.rerun()
    
    # Sub-paso 4: Tiene control?
    elif st.session_state.cita_paso == 4:
        pregunta = "¿Tiene usted un control por esa cita?"
        st.markdown(f"<div class='info-box'><p style='color: #90EE90;'>{pregunta}</p></div>", unsafe_allow_html=True)
        reproducir_audio(gestionar_nombre() + "Por favor, podría indicarme: " + pregunta)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ SÍ, TENGO CONTROL", use_container_width=True):
                st.session_state.cita_tiene_control = True
                st.session_state.cita_paso = 5
                st.rerun()
        with col2:
            if st.button("❌ NO TENGO CONTROL", use_container_width=True):
                st.session_state.paciente['prox_cita_dt'] = None
                
                # Verificar si viene desde "Varias"
                if 'varias_desde_varias' in st.session_state and st.session_state.varias_desde_varias:
                    del st.session_state['varias_desde_varias']
                
                # Limpiar estado de citas
                for key in list(st.session_state.keys()):
                    if key.startswith('cita_'):
                        del st.session_state[key]
                
                st.session_state.step = 50
                st.rerun()
    
    # Sub-paso 5: Días de control
    elif st.session_state.cita_paso == 5:
        prompt = "Por favor, indíqueme ¿dentro de cuántos días es el control?"
        st.markdown(f"<div class='info-box'><p style='color: #90EE90;'>{prompt}</p></div>", unsafe_allow_html=True)
        reproducir_audio(gestionar_nombre() + prompt)
        
        dias = st.number_input("¿dentro de cuántos días es el control?", min_value=1, max_value=365, step=1, key="cita_dias_control")
        
        if st.button("✅ Confirmar", use_container_width=True):
            st.session_state.paciente['dias_control'] = int(dias)
            fecha_u = datetime.strptime(st.session_state.paciente['cita_fecha_ult'], "%d/%m/%Y")
            resta = st.session_state.paciente['dias_control'] - 32
            if resta < 0 or resta == 2:
                st.session_state.paciente['prox_cita_dt'] = sumar_dias_habiles(fecha_u, 3, festivos_co)
            else:
                st.session_state.paciente['prox_cita_dt'] = obtener_dia_habil_anterior(
                    fecha_u + timedelta(days=resta), festivos_co
                )
            
            # Verificar si viene desde "Varias"
            if 'varias_desde_varias' in st.session_state and st.session_state.varias_desde_varias:
                del st.session_state['varias_desde_varias']
            
            # Limpiar estado de citas
            for key in list(st.session_state.keys()):
                if key.startswith('cita_'):
                    del st.session_state[key]
            
            st.session_state.step = 50
            st.rerun()

# --- PASO 14: FLUJO VARIAS ---
elif st.session_state.step == 14:
    st.markdown("<h2 style='color: #00BFFF;'>📋 Varias Opciones</h2>", unsafe_allow_html=True)
    
    if 'varias_paso' not in st.session_state:
        st.session_state.varias_paso = 0
    
    # Sub-paso 0: Medicina?
    if st.session_state.varias_paso == 0:
        pregunta = "¿Necesita hacer retiro de medicina?"
        st.markdown(f"<div class='info-box'><p style='color: #90EE90;'>{pregunta}</p></div>", unsafe_allow_html=True)
        reproducir_audio(gestionar_nombre() + "Por favor, podría indicarme: " + pregunta)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ SÍ", key="varias_med_si", use_container_width=True):
                st.session_state.varias_necesita_medicina = True
                st.session_state.varias_paso = 1
                st.rerun()
        with col2:
            if st.button("❌ NO", key="varias_med_no", use_container_width=True):
                st.session_state.varias_necesita_medicina = False
                st.session_state.varias_paso = 2
                st.rerun()
    
    # Sub-paso 1: Flujo medicina
    elif st.session_state.varias_paso == 1:
        st.session_state.step = 11
        st.session_state.varias_desde_varias = True
        st.rerun()
    
    # Sub-paso 2: Exámenes?
    elif st.session_state.varias_paso == 2:
        pregunta = "¿Necesita hacerse exámenes médicos?"
        st.markdown(f"<div class='info-box'><p style='color: #90EE90;'>{pregunta}</p></div>", unsafe_allow_html=True)
        reproducir_audio(gestionar_nombre() + "Por favor, podría indicarme: " + pregunta)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ SÍ", key="varias_ex_si", use_container_width=True):
                st.session_state.varias_necesita_examenes = True
                st.session_state.varias_paso = 3
                st.rerun()
        with col2:
            if st.button("❌ NO", key="varias_ex_no", use_container_width=True):
                st.session_state.varias_necesita_examenes = False
                st.session_state.varias_paso = 4
                st.rerun()
    
    # Sub-paso 3: Flujo exámenes
    elif st.session_state.varias_paso == 3:
        st.session_state.step = 12
        st.session_state.varias_desde_varias = True
        st.rerun()
    
    # Sub-paso 4: Citas?
    elif st.session_state.varias_paso == 4:
        pregunta = "¿Necesita programar una cita médica?"
        st.markdown(f"<div class='info-box'><p style='color: #90EE90;'>{pregunta}</p></div>", unsafe_allow_html=True)
        reproducir_audio(gestionar_nombre() + "Por favor, podría indicarme: " + pregunta)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ SÍ", key="varias_cita_si", use_container_width=True):
                st.session_state.varias_necesita_citas = True
                st.session_state.varias_paso = 5
                st.rerun()
        with col2:
            if st.button("❌ NO", key="varias_cita_no", use_container_width=True):
                st.session_state.varias_necesita_citas = False
                
                # Limpiar estado de varias
                for key in list(st.session_state.keys()):
                    if key.startswith('varias_'):
                        del st.session_state[key]
                
                st.session_state.step = 50
                st.rerun()
    
    # Sub-paso 5: Flujo citas
    elif st.session_state.varias_paso == 5:
        st.session_state.step = 13
        st.session_state.varias_desde_varias = True
        st.rerun()

# --- PASO 15: FLUJO FECHAS PROGRAMADAS ---
elif st.session_state.step == 15:
    st.markdown("<h2 style='color: #00BFFF;'>📅 Fechas Confirmadas</h2>", unsafe_allow_html=True)
    
    mensaje_inicio = "Evaluaremos sus citas programadas."
    st.markdown(f"<div class='info-box'><p style='color: #90EE90;'>{mensaje_inicio}</p></div>", unsafe_allow_html=True)
    reproducir_audio(mensaje_inicio)
    
    if 'prog_paso' not in st.session_state:
        st.session_state.prog_paso = 0
    
    # Sub-paso 0: Examen o Cita?
    if st.session_state.prog_paso == 0:
        msg_ex = "tiene usted una cita programada con fecha definida para algún exámen médico, por favor, confirme si o no"
        st.markdown(f"<div class='info-box'><p style='color: #90EE90;'>{msg_ex}</p></div>", unsafe_allow_html=True)
        reproducir_audio(gestionar_nombre() + "Por favor, podría indicarme: " + msg_ex)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ SÍ, EXAMEN", use_container_width=True):
                st.session_state.paciente['prog_categoria'] = "Examen Médico"
                st.session_state.prog_paso = 1
                st.rerun()
        with col2:
            if st.button("❌ NO ES EXAMEN", use_container_width=True):
                st.session_state.prog_paso = 10
                st.rerun()
    
    # Sub-paso 1-4: Examen programado
    elif st.session_state.prog_paso == 1:
        opciones = ["Sangre", "Rayos X", "Ultrasonido", "Resonancia o Tomografía"]
        st.markdown("<h3 style='color: #FFD700;'>Tipo de examen:</h3>", unsafe_allow_html=True)
        
        for opt in opciones:
            pregunta = f"¿Es examen de {opt}?"
            if st.button(f"✅ {opt}", key=f"prog_ex_{opt}", use_container_width=True):
                reproducir_audio(gestionar_nombre() + "Por favor, podría indicarme: " + pregunta)
                st.session_state.paciente['prog_tipo'] = opt
                st.session_state.prog_paso = 2
                st.rerun()
        
        if st.button("🔄 Otro", use_container_width=True):
            st.session_state.prog_paso = 1.5
            st.rerun()
    
    elif st.session_state.prog_paso == 1.5:
        prompt = "Por favor, especifique qué tipo de examen"
        st.markdown(f"<div class='info-box'><p style='color: #90EE90;'>{prompt}</p></div>", unsafe_allow_html=True)
        reproducir_audio(gestionar_nombre() + prompt)
        otro = st.text_input("especificar tipo de examen:", key="prog_ex_otro")
        
        if st.button("✅ Confirmar", use_container_width=True):
            if otro.strip():
                st.session_state.paciente['prog_tipo'] = otro.strip()
                st.session_state.prog_paso = 2
                st.rerun()
    
    elif st.session_state.prog_paso == 2:
        prompt = "Dígame el sitio a realizarse el examen médico"
        st.markdown(f"<div class='info-box'><p style='color: #90EE90;'>{prompt}</p></div>", unsafe_allow_html=True)
        reproducir_audio(gestionar_nombre() + prompt)
        
        lugar = st.text_input("sitio a realizarse el examen médico:", key="prog_lugar")
        
        if st.button("✅ Confirmar Lugar", use_container_width=True):
            if lugar.strip():
                st.session_state.paciente['prog_lugar'] = lugar.strip()
                st.session_state.prog_paso = 3
                st.rerun()
    
    elif st.session_state.prog_paso == 3:
        prompt = "Por favor, fecha a realizarse, dígame el día, el mes y el año."
        st.markdown(f"<div class='info-box'><p style='color: #90EE90;'>{prompt}</p></div>", unsafe_allow_html=True)
        reproducir_audio(gestionar_nombre() + prompt)
        
        fecha_prog = st.date_input(
            "fecha a realizarse:",
            min_value=datetime(2025, 5, 31),
            key="prog_fecha"
        )
        
        if st.button("✅ Confirmar Fecha", use_container_width=True):
            st.session_state.paciente['prog_fecha_str'] = fecha_prog.strftime("%d/%m/%Y")
            st.session_state.prog_paso = 4
            st.rerun()
    
    elif st.session_state.prog_paso == 4:
        prompt = "Indique la hora de su cita, formato 24 horas, ejemplo 14 y 30"
        st.markdown(f"<div class='info-box'><p style='color: #90EE90;'>{prompt}</p></div>", unsafe_allow_html=True)
        reproducir_audio(gestionar_nombre() + prompt)
        
        hora = st.time_input("Hora (HH:MM):", key="prog_hora")
        
        if st.button("✅ Confirmar Hora", use_container_width=True):
            st.session_state.paciente['prog_hora'] = hora.strftime("%H:%M")
            
            # Guardar en base de datos
            if guardar_en_db(st.session_state.paciente):
                mensaje_final = f"Perfecto, {st.session_state.nombre_paciente_global}. Hemos registrado su fecha programada para {st.session_state.paciente.get('prog_fecha_str')} a las {st.session_state.paciente.get('prog_hora')}."
                st.success(mensaje_final)
                reproducir_audio(mensaje_final)
                
                # Enviar notificaciones
                mensaje_notif = f"FECHA PROGRAMADA REGISTRADA - Tipo: {st.session_state.paciente.get('prog_categoria', 'N/A')}
Fecha: {st.session_state.paciente.get('prog_fecha_str', 'N/A')}
Hora: {st.session_state.paciente.get('prog_hora', 'N/A')}"
                enviar_notificaciones(mensaje_notif, st.session_state.nombre_paciente_global)
                
                # Limpiar estado de programación
                for key in list(st.session_state.keys()):
                    if key.startswith('prog_'):
                        del st.session_state[key]
                
                st.session_state.step = 50
                st.rerun()

# --- PASO 50: RESULTADOS FINALES ---
elif st.session_state.step == 50:
    st.markdown(f"<h1 style='text-align: center; color: #00BFFF;'>📋 RESUMEN FINAL</h1>", unsafe_allow_html=True)
    
    # Crear resumen
    resumen_lines = []
    
    if 'med_tipo' in st.session_state.paciente and 'prox_retiro_dt' in st.session_state.paciente:
        resumen_lines.append(f"💊 **Retiro de {st.session_state.paciente['med_tipo']}:** {st.session_state.paciente['prox_retiro_dt'].strftime('%d/%m/%Y')}")
    
    if 'ex_tipo' in st.session_state.paciente and 'prox_examen_dt' in st.session_state.paciente:
        resumen_lines.append(f"🔬 **Examen de {st.session_state.paciente['ex_tipo']}:** {st.session_state.paciente['prox_examen_dt'].strftime('%d/%m/%Y')}")
    
    if 'cita_tipo' in st.session_state.paciente:
        if 'prox_cita_dt' in st.session_state.paciente and st.session_state.paciente['prox_cita_dt']:
            resumen_lines.append(f"👨‍⚕️ **Cita de {st.session_state.paciente['cita_tipo']}:** {st.session_state.paciente['prox_cita_dt'].strftime('%d/%m/%Y')}")
        else:
            resumen_lines.append(f"👨‍⚕️ **Cita de {st.session_state.paciente['cita_tipo']}:** Sin fecha próxima (no tiene control)")
    
    if 'prog_categoria' in st.session_state.paciente and 'prog_fecha_str' in st.session_state.paciente:
        hora = st.session_state.paciente.get('prog_hora', 'N/A')
        resumen_lines.append(f"📅 **{st.session_state.paciente['prog_categoria']}:** {st.session_state.paciente['prog_fecha_str']} a las {hora}")
    
    if resumen_lines:
        resumen_texto = "
".join(resumen_lines)
        st.markdown(f"<div class='info-box'><h3 style='color: #FFD700;'>Resumen de {st.session_state.nombre_paciente_global}:</h3><p style='color: #C0C0C0;'>{resumen_texto}</p></div>", unsafe_allow_html=True)
        
        # Generar mensaje de notificación
        mensaje_notificacion = f"REGISTRO COMPLETADO:
" + "
".join([line.replace("**", "") for line in resumen_lines])
        enviar_notificaciones(mensaje_notificacion, st.session_state.nombre_paciente_global)
        
        # Audio de resumen
        audio_resumen = f"Resumen final para {st.session_state.nombre_paciente_global}. " + ". ".join([line.replace("**", "") for line in resumen_lines])
        reproducir_audio(audio_resumen)
    else:
        st.warning("No se registró ninguna información.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 INICIAR NUEVO REGISTRO", use_container_width=True):
            reset_app()
    
    with col2:
        if st.button("🏁 FINALIZAR APLICACIÓN", use_container_width=True):
            st.balloons()
            mensaje_final = "Gracias por usar el Asistente IA de Salud. ¡Cuide su bienestar!"
            st.success(mensaje_final)
            reproducir_audio(mensaje_final)
            time.sleep(3)
            st.stop()

# --- PIE DE PÁGINA ---
st.markdown("""
<div class="footer">
    <p>© 2026 Asistente IA de Salud v2.0 | Desarrollado por Alex Mauricio Niño | Contacto: maualexnino@gmail.com | Todos los derechos reservados</p>
</div>
""", unsafe_allow_html=True)
