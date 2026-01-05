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

# 1. Configuración de la pestaña
st.set_page_config(
    page_title="Asistente Médico - Mauricio Niño G.",
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

# URLs de Imágenes
AVATAR_URL = "https://i.ibb.co/zVFp4SmV/avatar-Mauricio.png"
CIUDAD_URL = "https://i.ibb.co/QjpntM88/i6.png"
ABUELO_URL = "https://i.ibb.co/spG69fPs/i7.png"
PORTADA_URL = "https://i.ibb.co/jZb8bxGk/i8.jpg" # Nueva URL portada

# ======================================================================
# 1. ESTILOS CSS PERSONALIZADOS
# ======================================================================

def aplicar_estilos():
    # Determinamos el fondo según la etapa
    bg_image = PORTADA_URL if st.session_state.paso in ['bienvenida', 'solicitar_nombre'] else AVATAR_URL
    
    st.markdown(f"""
    <style>
        /* Fondo principal dinámico */
        .stApp {{
            background: linear-gradient(135deg, #001f3f 0%, #003366 50%, #004d80 100%);
            background-image: 
                linear-gradient(135deg, rgba(0, 31, 63, 0.90), rgba(0, 77, 128, 0.90)),
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
        p, div, span, label, h1, h2, h3, h4, h5, h6 {{
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
        
        /* Botón Cancelar (Superior Derecha) */
        div[data-testid="column"] .stButton button.boton-cancelar {{
            background-color: #FFD700 !important; /* Amarillo intenso */
            color: #00008B !important; /* Azul intenso */
            border: 2px solid #000000 !important;
            font-weight: 800;
            width: 100%;
        }}
        
        /* Botón Normal */
        .stButton > button {{
            background: linear-gradient(135deg, #00ff00, #008000);
            color: white !important;
            font-weight: 700;
            border: none;
            border-radius: 10px;
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
            padding: 2rem 1rem;
            background: linear-gradient(135deg, #c0c0c0, #808080);
            border-radius: 15px;
            margin-top: 3rem;
            color: #000000 !important;
            font-weight: 600;
        }}

        /* Secciones con imágenes de fondo */
        .seccion-medicinas {{
            background-image: linear-gradient(rgba(255,255,255,0.85), rgba(255,255,255,0.85)), url('{CIUDAD_URL}');
            background-size: cover; padding: 2rem; border-radius: 15px;
        }}
        .seccion-examenes {{
            background-image: linear-gradient(rgba(255,255,255,0.85), rgba(255,255,255,0.85)), url('{CIUDAD_URL}');
            background-size: cover; padding: 2rem; border-radius: 15px;
        }}
        .seccion-citas, .seccion-programadas {{
            background-image: linear-gradient(rgba(255,255,255,0.85), rgba(255,255,255,0.85)), url('{ABUELO_URL}');
            background-size: cover; padding: 2rem; border-radius: 15px;
        }}
    </style>
    """, unsafe_allow_html=True)

# ======================================================================
# 2. FUNCIONES DE LÓGICA
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

# ======================================================================
# 3. FUNCIONES DE VOZ Y NOTIFICACIONES
# ======================================================================

def generar_audio(texto, filename="audio_temp.mp3"):
    try:
        tts = gTTS(text=texto, lang='es', tld='com.co')
        tts.save(filename)
        return filename
    except Exception as e:
        return None

def mostrar_mensaje_voz(texto):
    """Muestra mensaje y fuerza reproducción automática con HTML5"""
    st.markdown(f'<div class="mensaje-voz">🔊 <strong>Asistente:</strong> {texto}</div>', unsafe_allow_html=True)
    
    audio_file = generar_audio(texto)
    if audio_file and os.path.exists(audio_file):
        with open(audio_file, 'rb') as f:
            audio_bytes = f.read()
            audio_base64 = base64.b64encode(audio_bytes).decode()
            
        # ID único para forzar recarga del elemento de audio
        unique_id = int(time.time() * 1000)
        
        # HTML5 Audio con autoplay forzado
        audio_html = f"""
            <audio id="audio-{unique_id}" autoplay="true" style="display:none;">
                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            </audio>
            <script>
                var audio = document.getElementById("audio-{unique_id}");
                audio.volume = 1.0;
                audio.play().catch(function(error) {{
                    console.log("Autoplay bloqueado por el navegador: " + error);
                }});
            </script>
        """
        st.components.v1.html(audio_html, height=0)

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
    """Botón superior derecha: CANCELAR Y REGRESAR"""
    col_spacer, col_btn = st.columns([8, 2])
    with col_btn:
        # Inyectar estilo específico para el botón de cancelar en esta columna
        st.markdown("""
        <style>
        div[data-testid="column"]:nth-of-type(2) button {
            background-color: #FFD700 !important;
            color: #00008B !important;
            border: 2px solid #000000 !important;
            font-weight: 800 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        if st.button("CANCELAR Y REGRESAR", key="btn_cancel_top"):
            st.session_state.paso = 'menu_principal'
            st.session_state.subfase = 0
            st.rerun()

def mostrar_flecha_volver():
    """Flecha inferior derecha de retorno"""
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2 = st.columns([9, 1])
    with col2:
        if st.button("⬅️ Volver", key="btn_volver_atras"):
            if st.session_state.subfase > 0:
                st.session_state.subfase -= 1
                st.rerun()
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

# ======================================================================
# 6. INTERFAZ PRINCIPAL
# ======================================================================

def main():
    inicializar_session_state()
    aplicar_estilos()
    
    # Header y Créditos
    st.title("ASISTENTE DE AGENDAMIENTO Y RECORDATORIO DE RETIRO DE MEDICINAS, EXÁMENES CLÍNICOS Y CONSULTAS MÉDICAS.")
    st.subheader("Sistema Inteligente de Recordatorios Médicos")
    st.caption("Desarrollado por Mauricio Niño Gamboa. Enero 2026.")
    
    # Verificación inicial y Bienvenida
    if st.session_state.paso == 'bienvenida':
        with st.spinner('Verificando conexión con el sistema de salud...'):
            if not verificar_conexion():
                st.error("❌ No se pudo establecer conexión con la base de datos.")
                st.stop()
            else:
                st.success("✅ Conexión establecida correctamente")
                time.sleep(1)
        
        mostrar_mensaje_voz("Bienvenido al gestor de salud. Realizaremos preguntas para calcular o registrar sus fechas médicas importantes.")
        time.sleep(2)
        st.session_state.paso = 'solicitar_nombre'
        st.rerun()
    
    # Solicitar Nombre
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
    
    # Historial
    elif st.session_state.paso == 'consultar_historial':
        consultar_historial_flow()
    
    # Menú Principal
    elif st.session_state.paso == 'menu_principal':
        mostrar_menu_principal()
    
    # Flujos
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
    
    # Footer
    st.markdown(f"""
    <div class='footer'>
        <strong>🏥 ASISTENTE DE AGENDAMIENTO Y RECORDATORIO</strong><br>
        Desarrollado por <strong>Mauricio Niño Gamboa</strong><br>
        © 2026 - Todos los derechos reservados<br>
        <small>Notificaciones: {EMAIL_RECEIVER} | Telegram: {TELEGRAM_DISPLAY_PHONE}</small>
    </div>
    """, unsafe_allow_html=True)

# ======================================================================
# 7. LÓGICA DEL HISTORIAL (CORREGIDA)
# ======================================================================

def consultar_historial_flow():
    # Consulta una sola vez
    if 'historial_datos' not in st.session_state:
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

    historial = st.session_state.historial_datos
    
    if historial:
        if not st.session_state.ver_historial:
            mostrar_mensaje_voz(f"¿Desea visualizar las consultas previas de {st.session_state.nombre_paciente}?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Sí, mostrar historial"):
                    st.session_state.ver_historial = True
                    st.rerun()
            with col2:
                if st.button("⏭️ Continuar sin ver"):
                    st.session_state.paso = 'menu_principal'
                    st.rerun()
        else:
            # MOSTRAR EL HISTORIAL Y QUEDARSE AHÍ
            st.info(f"📋 Registros previos de **{st.session_state.nombre_paciente}**")
            msg_resumen = f"He encontrado sus últimos registros, {st.session_state.nombre_paciente}. Aquí tiene un resumen:"
            mostrar_mensaje_voz(msg_resumen)
            
            st.markdown("### 📊 HISTORIAL RECIENTE")
            for i, f in enumerate(historial, 1):
                detalles = []
                if f[1]: detalles.append(f"**Retiro {f[0]}:** {f[1]}")
                if f[3]: detalles.append(f"**Examen {f[2]}:** {f[3]}")
                if f[5]: detalles.append(f"**Cita {f[4]}:** {f[5]}")
                if f[7]: detalles.append(f"**Programado ({f[6]}):** {f[7]}")
                if detalles:
                    st.markdown(f"**Registro {i}:** {' | '.join(detalles)}")
            
            st.markdown("---")
            if st.button("▶️ Continuar al Menú"):
                st.session_state.paso = 'menu_principal'
                st.rerun()
    else:
        # Si no hay historial, pasa directo
        st.session_state.paso = 'menu_principal'
        st.rerun()

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
    
    seleccion = st.radio("**Seleccione una opción:**", list(opciones.keys()))
    
    if st.button("▶️ Continuar", use_container_width=True):
        opcion = opciones[seleccion]
        st.session_state.subfase = 0
        if opcion == "1": st.session_state.paso = 'flujo_medicinas'
        elif opcion == "2": st.session_state.paso = 'flujo_examenes'
        elif opcion == "3": st.session_state.paso = 'flujo_citas'
        elif opcion == "4": st.session_state.paso = 'flujo_varias'
        elif opcion == "5": st.session_state.paso = 'flujo_fechas_programadas'
        st.rerun()

# ======================================================================
# 9. FLUJO MEDICINAS
# ======================================================================

def flujo_medicinas_streamlit():
    mostrar_boton_cancelar()
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
            if st.button("✅ Sí", key="mg_si"):
                p['med_tipo'] = "Medicina General"
                st.session_state.subfase = 5
                st.rerun()
        with col2:
            if st.button("❌ No", key="mg_no"):
                st.session_state.subfase = 2
                st.rerun()
                
    elif st.session_state.subfase == 2:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Por favor, podría indicarme: ¿Es para Especialista?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sí", key="me_si"):
                st.session_state.subfase = 3
                st.rerun()
        with col2:
            if st.button("❌ No", key="me_no"):
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
            if st.button("✅ Sí", key="mo_si"):
                p['med_tipo'] = "Oncología"
                st.session_state.subfase = 5
                st.rerun()
        with col2:
            if st.button("❌ No", key="mo_no"):
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
        st.session_state.paso = 'mostrar_resumen'
        st.rerun()

    mostrar_flecha_volver()
    st.markdown('</div>', unsafe_allow_html=True)

# ======================================================================
# 10. FLUJO EXÁMENES
# ======================================================================

def flujo_examenes_streamlit():
    mostrar_boton_cancelar()
    st.markdown('<div class="seccion-examenes">', unsafe_allow_html=True)
    p = st.session_state.paciente
    
    if st.session_state.subfase == 0:
        mostrar_mensaje_voz("Continuamos gentilmente con sus exámenes médicos.")
        st.session_state.subfase = 1
        time.sleep(2)
        st.rerun()
        
    elif st.session_state.subfase == 1:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿Es examen de Sangre?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sí", key="ex_s_si"):
                p['ex_tipo'] = "Sangre"
                st.session_state.subfase = 5
                st.rerun()
        with col2:
            if st.button("❌ No", key="ex_s_no"):
                st.session_state.subfase = 2
                st.rerun()
                
    elif st.session_state.subfase == 2:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿Es examen de Rayos X?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sí", key="ex_r_si"):
                p['ex_tipo'] = "Rayos X"
                st.session_state.subfase = 5
                st.rerun()
        with col2:
            if st.button("❌ No", key="ex_r_no"):
                st.session_state.subfase = 3
                st.rerun()
                
    elif st.session_state.subfase == 3:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿Es examen de Ultrasonido?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sí", key="ex_u_si"):
                p['ex_tipo'] = "Ultrasonido"
                st.session_state.subfase = 5
                st.rerun()
        with col2:
            if st.button("❌ No", key="ex_u_no"):
                st.session_state.subfase = 4
                st.rerun()

    elif st.session_state.subfase == 4:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿Es Resonancia o Tomografía?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sí", key="ex_rt_si"):
                p['ex_tipo'] = "Resonancia o Tomografía"
                st.session_state.subfase = 5
                st.rerun()
        with col2:
            if st.button("❌ No", key="ex_rt_no"):
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
        st.session_state.paso = 'mostrar_resumen'
        st.rerun()

    mostrar_flecha_volver()
    st.markdown('</div>', unsafe_allow_html=True)

# ======================================================================
# 11. FLUJO CITAS (CORREGIDO)
# ======================================================================

def flujo_citas_streamlit():
    mostrar_boton_cancelar()
    st.markdown('<div class="seccion-citas">', unsafe_allow_html=True)
    p = st.session_state.paciente
    
    # 1. Inicio y Tipo de Cita
    if st.session_state.subfase == 0:
        mostrar_mensaje_voz("Pasamos amablemente a sus citas médicas.")
        st.session_state.subfase = 1
        time.sleep(2)
        st.rerun()

    elif st.session_state.subfase == 1:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿Es cita de Medicina General?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sí", key="ci_mg_si"):
                p['cita_tipo'] = "Medicina General"
                st.session_state.subfase = 5
                st.rerun()
        with col2:
            if st.button("❌ No", key="ci_mg_no"):
                st.session_state.subfase = 2
                st.rerun()

    elif st.session_state.subfase == 2:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿Es cita de Especialista?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sí", key="ci_esp_si"):
                st.session_state.subfase = 3
                st.rerun()
        with col2:
            if st.button("❌ No", key="ci_esp_no"):
                st.session_state.subfase = 4
                st.rerun()

    elif st.session_state.subfase == 3:
        mostrar_mensaje_voz(f"{gestionar_nombre()}Especifique la especialidad")
        esp = st.text_input("Especialidad:", key="ci_esp_in")
        if st.button("Confirmar Especialidad"):
            if esp.strip():
                p['cita_tipo'] = esp.strip()
                st.session_state.subfase = 5
                st.rerun()

    elif st.session_state.subfase == 4:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿Es Oncología u Odontología?")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Oncología"):
                p['cita_tipo'] = "Oncología"
                st.session_state.subfase = 5
                st.rerun()
        with c2:
            if st.button("Odontología"):
                p['cita_tipo'] = "Odontología"
                st.session_state.subfase = 5
                st.rerun()
        with c3:
            if st.button("Otra"):
                st.session_state.subfase = 3
                st.rerun()

    # 2. Lugar
    elif st.session_state.subfase == 5:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿En qué lugar es la cita?")
        lug = st.text_input("Lugar:", key="ci_lugar")
        if st.button("Confirmar Lugar"):
            if lug.strip():
                p['cita_lugar'] = lug.strip()
                st.session_state.subfase = 6
                st.rerun()

    # 3. Primera vez o Control (Fecha)
    elif st.session_state.subfase == 6:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿Es primera vez de la cita?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Sí, primera vez"):
                st.session_state.valor_temporal = True # Es primera vez
                st.session_state.subfase = 7
                st.rerun()
        with c2:
            if st.button("❌ No, es control"):
                st.session_state.valor_temporal = False # No es primera vez
                st.session_state.subfase = 7
                st.rerun()

    elif st.session_state.subfase == 7:
        if st.session_state.valor_temporal:
            msg_f = "Por favor, la fecha de la orden de la cita."
        else:
            msg_f = "Por favor, la fecha de su última cita."
        mostrar_mensaje_voz(f"{gestionar_nombre()}{msg_f}")
        
        f_cita = st.text_input("Fecha (DD/MM/AAAA):", key="ci_fecha")
        if st.button("Confirmar Fecha"):
            if validar_fecha(f_cita):
                p['cita_fecha_ult'] = f_cita
                st.session_state.subfase = 8
                st.rerun()
            else:
                st.error("Fecha inválida.")

    # 4. Control Futuro
    elif st.session_state.subfase == 8:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿Tiene usted un control por esa cita?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Sí"):
                st.session_state.subfase = 9
                st.rerun()
        with c2:
            if st.button("❌ No"):
                p['prox_cita_dt'] = None
                st.session_state.subfase = 10
                st.rerun()

    elif st.session_state.subfase == 9:
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
            st.session_state.subfase = 10
            st.rerun()

    elif st.session_state.subfase == 10:
        st.session_state.paso = 'mostrar_resumen'
        st.rerun()

    mostrar_flecha_volver()
    st.markdown('</div>', unsafe_allow_html=True)

# ======================================================================
# 12. FLUJO VARIAS
# ======================================================================

def flujo_varias_streamlit():
    mostrar_boton_cancelar()
    # Lógica de sub-flows usando subfase por rangos
    # 0: Inicio -> Pregunta Med
    # 1-9: Flujo Med
    # 10: Pregunta Ex
    # 11-19: Flujo Ex
    # 20: Pregunta Cita
    # 21-29: Flujo Cita
    
    if st.session_state.subfase == 0:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿Necesita hacer retiro de medicina?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Sí", key="v_m_s"):
                st.session_state.subfase = 1
                st.rerun()
        with c2:
            if st.button("❌ No", key="v_m_n"):
                st.session_state.subfase = 10
                st.rerun()
                
    elif 1 <= st.session_state.subfase < 10:
        # Mapear subfase local a subfase del flujo
        # Necesitamos un estado temporal para el subflujo
        if 'temp_subfase' not in st.session_state: st.session_state.temp_subfase = 1
        
        # Guardamos el estado original para restaurar
        original = st.session_state.subfase
        st.session_state.subfase = st.session_state.temp_subfase
        
        # Ejecutamos flujo medicina modificado para retornar
        # Hack: Usamos el flujo normal pero interceptamos el final
        flujo_medicinas_streamlit() # Ojo: este usa st.session_state.subfase
        
        # Si el flujo terminó (llegó a 7), volvemos al flujo varias
        if st.session_state.subfase == 7:
             st.session_state.subfase = 10 # Siguiente pregunta
             del st.session_state.temp_subfase
             st.rerun()
        else:
            # Si no terminó, guardamos el estado temporal y restauramos el 'macro' estado
            st.session_state.temp_subfase = st.session_state.subfase
            st.session_state.subfase = original # Restauramos para mantenernos en este bloque

    elif st.session_state.subfase == 10:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿Necesita hacerse exámenes médicos?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Sí", key="v_e_s"):
                st.session_state.subfase = 11
                st.rerun()
        with c2:
            if st.button("❌ No", key="v_e_n"):
                st.session_state.subfase = 20
                st.rerun()

    elif 11 <= st.session_state.subfase < 20:
        if 'temp_subfase_ex' not in st.session_state: st.session_state.temp_subfase_ex = 1
        original = st.session_state.subfase
        st.session_state.subfase = st.session_state.temp_subfase_ex
        
        flujo_examenes_streamlit()
        
        if st.session_state.subfase == 8:
            st.session_state.subfase = 20
            del st.session_state.temp_subfase_ex
            st.rerun()
        else:
            st.session_state.temp_subfase_ex = st.session_state.subfase
            st.session_state.subfase = original

    elif st.session_state.subfase == 20:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿Necesita programar una cita médica?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Sí", key="v_c_s"):
                st.session_state.subfase = 21
                st.rerun()
        with c2:
            if st.button("❌ No", key="v_c_n"):
                st.session_state.paso = 'mostrar_resumen'
                st.rerun()

    elif 21 <= st.session_state.subfase < 30:
        if 'temp_subfase_ci' not in st.session_state: st.session_state.temp_subfase_ci = 1
        original = st.session_state.subfase
        st.session_state.subfase = st.session_state.temp_subfase_ci
        
        flujo_citas_streamlit()
        
        if st.session_state.subfase == 10:
            st.session_state.paso = 'mostrar_resumen'
            del st.session_state.temp_subfase_ci
            st.rerun()
        else:
            st.session_state.temp_subfase_ci = st.session_state.subfase
            st.session_state.subfase = original

# ======================================================================
# 13. FLUJO PROGRAMADAS
# ======================================================================

def flujo_fechas_programadas_streamlit():
    mostrar_boton_cancelar()
    st.markdown('<div class="seccion-programadas">', unsafe_allow_html=True)
    p = st.session_state.paciente
    
    if st.session_state.subfase == 0:
        mostrar_mensaje_voz("Evaluaremos sus citas programadas.")
        st.session_state.subfase = 1
        time.sleep(2)
        st.rerun()
        
    elif st.session_state.subfase == 1:
        mostrar_mensaje_voz(f"{gestionar_nombre()}¿Tiene cita programada de examen médico?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Sí", key="fp_e_s"):
                p['prog_categoria'] = "Examen Médico"
                st.session_state.subfase = 2
                st.rerun()
        with c2:
            if st.button("❌ No", key="fp_e_n"):
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
        tipo = st.text_input("Especifique:")
        if st.button("Confirmar"):
            p['prog_tipo'] = tipo
            st.session_state.subfase = 4
            st.rerun()
            
    elif st.session_state.subfase == 4:
        lug = st.text_input("Lugar:")
        if st.button("Confirmar Lugar"):
            p['prog_lugar'] = lug
            st.session_state.subfase = 5
            st.rerun()
            
    elif st.session_state.subfase == 5:
        fecha = st.text_input("Fecha Futura (DD/MM/AAAA):")
        if st.button("Confirmar Fecha"):
            if validar_fecha(fecha, futura=True):
                p['prog_fecha_str'] = fecha
                st.session_state.subfase = 6
                st.rerun()
            else:
                st.error("Fecha inválida (debe ser posterior a 31/05/2025).")

    elif st.session_state.subfase == 6:
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
            if st.button("✅ Sí", key="fp_c_s"):
                p['prog_categoria'] = "Cita Médica"
                st.session_state.subfase = 11
                st.rerun()
        with c2:
            if st.button("❌ No", key="fp_c_n"):
                st.info("Sesión finalizada.")
                st.stop()

    elif st.session_state.subfase == 11:
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
        esp = st.text_input("Especialidad:")
        if st.button("Confirmar"):
            p['prog_tipo'] = esp
            st.session_state.subfase = 13
            st.rerun()
            
    elif st.session_state.subfase == 13:
        lug = st.text_input("Lugar:")
        if st.button("Confirmar Lugar"):
            p['prog_lugar'] = lug
            st.session_state.subfase = 14
            st.rerun()
            
    elif st.session_state.subfase == 14:
        fecha = st.text_input("Fecha Futura (DD/MM/AAAA):")
        if st.button("Confirmar Fecha"):
            if validar_fecha(fecha, futura=True):
                p['prog_fecha_str'] = fecha
                st.session_state.subfase = 15
                st.rerun()
            else:
                st.error("Fecha inválida.")
                
    elif st.session_state.subfase == 15:
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
            
        mostrar_mensaje_voz("Notificaciones programadas.")
        enviar_notificaciones(msg, p['paciente'])
        
        if st.button("Ir al Resumen"):
            st.session_state.paso = 'mostrar_resumen'
            st.rerun()

    mostrar_flecha_volver()
    st.markdown('</div>', unsafe_allow_html=True)

# ======================================================================
# 14. RESUMEN FINAL
# ======================================================================

def mostrar_resumen_final():
    p = st.session_state.paciente
    st.markdown("## 📋 RESUMEN FINAL")
    
    if "prox_retiro_dt" in p:
        msg = f"Próximo retiro ({p.get('med_tipo')}): {p['prox_retiro_dt'].strftime('%d/%m/%Y')}"
        st.success(msg)
        mostrar_mensaje_voz(msg)
        time.sleep(5)
        
    if "prox_examen_dt" in p:
        msg = f"Solicitar examen ({p.get('ex_tipo')}): {p['prox_examen_dt'].strftime('%d/%m/%Y')}"
        st.info(msg)
        mostrar_mensaje_voz(msg)
        time.sleep(5)
        
    if "prox_cita_dt" in p and p["prox_cita_dt"]:
        msg = f"Solicitar cita ({p.get('cita_tipo')}): {p['prox_cita_dt'].strftime('%d/%m/%Y')}"
        st.warning(msg)
        mostrar_mensaje_voz(msg)
        time.sleep(5)
        
    if guardar_en_db(p):
        st.success("✅ Datos guardados en BD.")
        notif = f"Recibirá notificaciones en {EMAIL_RECEIVER} y Telegram {TELEGRAM_DISPLAY_PHONE}"
        st.info(notif)
        mostrar_mensaje_voz(notif)
        time.sleep(10)
        
    st.markdown("---")
    mostrar_mensaje_voz(f"{gestionar_nombre()}¿Tiene algún otro requerimiento?")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ Sí, Nuevo Requerimiento"):
            st.session_state.paso = 'menu_principal'
            # Mantener nombre, limpiar resto
            nom = st.session_state.nombre_paciente
            st.session_state.paciente = {"paciente": nom}
            st.session_state.subfase = 0
            st.rerun()
    with c2:
        if st.button("❌ No, Finalizar"):
            mostrar_mensaje_voz("Gracias por usar nuestro servicio.")
            st.balloons()
            time.sleep(3)
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()
