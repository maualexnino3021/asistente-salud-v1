import streamlit as st
import mysql.connector
import holidays
import pytz
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta, date, time as dt_time
from gtts import gTTS
import io
import time

# --- CONFIGURACIÓN DE PÁGINA Y ESTILOS ---
st.set_page_config(
    page_title="HealthTrack AI - Gestión Premium",
    page_icon="🏥",
    layout="centered"
)

# Colores: Azul Marino (#001f3f), Dorado (#FFD700), Plateado (#C0C0C0), Verde (#2ECC40), Amarillo (#FFDC00)
st.markdown("""
    <style>
    /* Fondo general y fuentes */
    .stApp {
        background-color: #f4f4f4;
    }
    
    /* Encabezados Azul Marino con borde Dorado */
    h1, h2, h3 {
        color: #001f3f;
        font-family: 'Helvetica', sans-serif;
        border-bottom: 2px solid #FFD700;
        padding-bottom: 10px;
    }
    
    /* Sidebar Azul Marino */
    section[data-testid="stSidebar"] {
        background-color: #001f3f;
    }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] label {
        color: #FFD700 !important;
        border-bottom: none;
    }
    
    /* Botones Dorados con texto Azul */
    div.stButton > button {
        background-color: #FFD700;
        color: #001f3f;
        border-radius: 8px;
        border: 1px solid #C0C0C0;
        font-weight: bold;
        width: 100%;
        transition: all 0.3s;
    }
    div.stButton > button:hover {
        background-color: #DAA520; /* Dorado más oscuro */
        color: white;
        border-color: #FFD700;
    }

    /* Cajas de éxito y alerta */
    div[data-baseweb="notification"] {
        border-radius: 8px;
    }
    
    /* Input Fields styling */
    div[data-baseweb="input"] {
        border: 1px solid #001f3f;
    }
    </style>
""", unsafe_allow_html=True)

# --- 1. CONFIGURACIÓN Y CREDENCIALES (Respetando tu código) ---

CONFIG_DB = {
    'host': 'gateway01.us-east-1.prod.aws.tidbcloud.com',
    'port': 4000,
    'user': '39hpidXc8KL7sEA.root',
    'password': 'HwJbEPQQNL7rhRjF',
    'database': 'test',
    'autocommit': True,
    'ssl_verify_cert': True,
    'ssl_ca': '/etc/ssl/certs/ca-certificates.crt'
}

# Credenciales de Notificación
TELEGRAM_TOKEN = '8444851001:AAEZBqfJcgUasPLeu1nsD2xcG0OrkPvrwbM'
TELEGRAM_CHAT_ID = '1677957851'
EMAIL_APP_PASSWORD = 'wspb oiqd zriv tqpl'
EMAIL_SENDER = 'unamauricio2013@gmail.com'
EMAIL_RECEIVER = 'maualexnino@gmail.com'

# Festivos y Zona Horaria
festivos_co = holidays.CO(years=[2025, 2026, 2027, 2028, 2029])
tz_co = pytz.timezone('America/Bogota')

# --- 2. FUNCIONES BASE Y LÓGICA ---

def get_db_connection():
    try:
        return mysql.connector.connect(**CONFIG_DB)
    except Exception as e:
        st.error(f"❌ Error crítico de conexión DB: {e}")
        return None

def obtener_dia_habil_anterior(fecha_in):
    if isinstance(fecha_in, datetime): fecha_in = fecha_in.date()
    while fecha_in.weekday() == 6 or fecha_in in festivos_co:
        fecha_in -= timedelta(days=1)
    return fecha_in

def sumar_dias_habiles(fecha_inicio, dias_a_sumar):
    if isinstance(fecha_inicio, datetime): fecha_inicio = fecha_inicio.date()
    fecha_actual = fecha_inicio
    dias_contados = 0
    while dias_contados < dias_a_sumar:
        fecha_actual += timedelta(days=1)
        if fecha_actual.weekday() != 6 and fecha_actual not in festivos_co:
            dias_contados += 1
    return fecha_actual

def hablar(texto):
    """Genera audio TTS y lo reproduce si el texto ha cambiado."""
    if 'ultimo_audio' not in st.session_state:
        st.session_state.ultimo_audio = ""
    
    # Evitar reproducir lo mismo en cada recarga de streamlit si no ha cambiado
    if texto != st.session_state.ultimo_audio:
        try:
            tts = gTTS(text=texto, lang='es', tld='com.co')
            audio_bytes = io.BytesIO()
            tts.write_to_fp(audio_bytes)
            audio_bytes.seek(0)
            st.session_state.ultimo_audio = texto
            st.session_state.audio_data = audio_bytes
        except Exception:
            pass
            
    if 'audio_data' in st.session_state:
        st.audio(st.session_state.audio_data, format='audio/mp3', autoplay=True)

def enviar_notificaciones(mensaje, paciente):
    """Envía alertas reales por Telegram y Gmail"""
    mensaje_personalizado = f"PACIENTE: {paciente}\n{mensaje}"
    
    # Telegram
    try:
        url_tg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url_tg, data={
            'chat_id': TELEGRAM_CHAT_ID,
            'text': f"🔔 RECORDATORIO SALUD:\n{mensaje_personalizado}"
        }, timeout=5)
    except Exception as e:
        st.error(f"Error Telegram: {e}")

    # Gmail
    try:
        msg = MIMEText(mensaje_personalizado)
        msg['Subject'] = f'Recordatorio de Salud - {paciente}'
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
    except Exception as e:
        st.error(f"Error Gmail: {e}")

def guardar_db(datos):
    conn = get_db_connection()
    if not conn: return False
    try:
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
        valores = (
            datos.get("paciente"), datetime.now(tz_co).replace(tzinfo=None),
            datos.get("med_tipo"), datos.get("prox_retiro"),
            datos.get("ex_tipo"), datos.get("prox_examen"),
            datos.get("cita_tipo"), datos.get("prox_cita"),
            datos.get("prog_categoria"), datos.get("prog_fecha"), datos.get("prog_hora")
        )
        cursor.execute(query, valores)
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"❌ Error DB: {e}")
        return False

# --- 3. ESTADO DE LA APLICACIÓN (SESSION STATE) ---
if 'paso' not in st.session_state: st.session_state.paso = 'inicio'
if 'datos' not in st.session_state: st.session_state.datos = {}
if 'paciente' not in st.session_state: st.session_state.paciente = ""

# --- 4. INTERFAZ DE USUARIO ---

def main():
    # BARRA LATERAL
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3063/3063176.png", width=80)
        st.title("HealthTrack AI")
        st.markdown("---")
        if st.session_state.paciente:
            st.info(f"👤 Paciente: **{st.session_state.paciente}**")
            if st.button("🔄 Cambiar Paciente"):
                st.session_state.paso = 'inicio'
                st.session_state.paciente = ""
                st.session_state.datos = {}
                st.rerun()
        
        st.markdown("### 📞 Contacto")
        st.caption(f"Telegram: ...{TELEGRAM_CHAT_ID[-4:]}")
        st.caption(f"Email: {EMAIL_RECEIVER}")

    # PANTALLA 1: BIENVENIDA
    if st.session_state.paso == 'inicio':
        st.title("Bienvenido al Gestor de Salud")
        msg_inicio = "Bienvenido. Registraremos sus datos para calcular y programar fechas. Por favor, indique el nombre del paciente."
        st.write(msg_inicio)
        hablar(msg_inicio)
        
        nombre = st.text_input("Nombre del Paciente", placeholder="Escriba aquí...")
        
        if st.button("Comenzar"):
            if nombre:
                st.session_state.paciente = nombre.upper()
                st.session_state.paso = 'menu'
                st.rerun()
            else:
                st.warning("Por favor ingrese un nombre.")

    # PANTALLA 2: MENÚ PRINCIPAL
    elif st.session_state.paso == 'menu':
        msg_menu = f"Hola {st.session_state.paciente}, ¿qué gestión desea realizar hoy?"
        st.title(f"Gestión para: {st.session_state.paciente}")
        st.write(msg_menu)
        hablar(msg_menu)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💊 Retiro Medicinas"):
                st.session_state.paso = 'med_form'
                st.rerun()
            if st.button("🧪 Exámenes Médicos"):
                st.session_state.paso = 'ex_form'
                st.rerun()
        with col2:
            if st.button("🩺 Citas Médicas"):
                st.session_state.paso = 'cita_form'
                st.rerun()
            if st.button("📅 Fecha Programada (Confirmada)"):
                st.session_state.paso = 'prog_form'
                st.rerun()
                
        st.markdown("---")
        if st.button("📂 Ver Historial Reciente"):
             st.session_state.paso = 'historial'
             st.rerun()

    # PANTALLA 3: FORMULARIO MEDICINAS
    elif st.session_state.paso == 'med_form':
        st.subheader("💊 Retiro de Medicinas")
        msg_voz = "Por favor, indique el tipo de medicina y la fecha del último retiro."
        hablar(msg_voz)
        
        with st.form("form_med"):
            tipo = st.selectbox("Tipo de Medicina", ["Medicina General", "Especialista", "Oncología", "Otro"])
            especialidad = st.text_input("Especifique (si eligió Especialista/Otro)")
            fecha_ult = st.date_input("Fecha último retiro", value=date.today())
            
            if st.form_submit_button("Calcular Fecha"):
                tipo_final = especialidad if especialidad else tipo
                prox = obtener_dia_habil_anterior(fecha_ult + timedelta(days=28))
                
                st.session_state.datos = {
                    "paciente": st.session_state.paciente,
                    "med_tipo": tipo_final,
                    "prox_retiro": prox
                }
                st.session_state.paso = 'confirmar_calculo'
                st.rerun()
        
        if st.button("🔙 Volver"): st.session_state.paso = 'menu'; st.rerun()

    # PANTALLA 4: FORMULARIO EXÁMENES
    elif st.session_state.paso == 'ex_form':
        st.subheader("🧪 Exámenes Médicos")
        hablar("Continuamos gentilmente con sus exámenes. Indique el tipo y la fecha de la orden.")
        
        with st.form("form_ex"):
            tipo = st.selectbox("Tipo", ["Sangre", "Rayos X", "Ultrasonido", "Resonancia/Tomografía", "Otro"])
            otro = st.text_input("Especifique (si eligió Otro)")
            fecha_orden = st.date_input("Fecha de la orden", value=date.today())
            dias = st.number_input("Días para entrega de resultados", min_value=1, value=5)
            
            if st.form_submit_button("Calcular Solicitud"):
                tipo_final = otro if otro else tipo
                resta = dias - 32
                if resta < 0 or resta == 2:
                    prox = sumar_dias_habiles(fecha_orden, 3)
                else:
                    prox = obtener_dia_habil_anterior(fecha_orden + timedelta(days=resta))
                
                st.session_state.datos = {
                    "paciente": st.session_state.paciente,
                    "ex_tipo": tipo_final,
                    "prox_examen": prox
                }
                st.session_state.paso = 'confirmar_calculo'
                st.rerun()
        
        if st.button("🔙 Volver"): st.session_state.paso = 'menu'; st.rerun()

    # PANTALLA 5: FORMULARIO CITAS
    elif st.session_state.paso == 'cita_form':
        st.subheader("🩺 Citas Médicas")
        hablar("Pasamos amablemente a sus citas. ¿Es un control o una nueva cita?")
        
        with st.form("form_cit"):
            tipo = st.selectbox("Especialidad", ["Medicina General", "Especialista", "Oncología", "Odontología"])
            esp = st.text_input("Especifique especialidad (si aplica)")
            fecha_base = st.date_input("Fecha última cita / orden", value=date.today())
            es_control = st.checkbox("¿Es cita de control?")
            dias_control = st.number_input("Días para el control", min_value=1, value=30, disabled=not es_control)
            
            if st.form_submit_button("Calcular"):
                tipo_final = esp if esp else tipo
                prox = None
                
                if es_control:
                    resta = dias_control - 32
                    if resta < 0 or resta == 2:
                        prox = sumar_dias_habiles(fecha_base, 3)
                    else:
                        prox = obtener_dia_habil_anterior(fecha_base + timedelta(days=resta))
                
                st.session_state.datos = {
                    "paciente": st.session_state.paciente,
                    "cita_tipo": tipo_final,
                    "prox_cita": prox 
                }
                st.session_state.paso = 'confirmar_calculo'
                st.rerun()
        
        if st.button("🔙 Volver"): st.session_state.paso = 'menu'; st.rerun()

    # PANTALLA 6: CONFIRMACIÓN DE CÁLCULO (Común para 3, 4 y 5)
    elif st.session_state.paso == 'confirmar_calculo':
        st.subheader("✅ Resultado del Cálculo")
        d = st.session_state.datos
        msg_res = ""
        
        if "med_tipo" in d:
            msg_res = f"Su próximo retiro de {d['med_tipo']} debe ser el **{d['prox_retiro'].strftime('%d de %B de %Y')}**."
            st.success(msg_res)
        elif "ex_tipo" in d:
            msg_res = f"La toma del examen {d['ex_tipo']} debe ser el **{d['prox_examen'].strftime('%d de %B de %Y')}**."
            st.info(msg_res)
        elif "cita_tipo" in d:
            if d['prox_cita']:
                msg_res = f"La solicitud de la cita de {d['cita_tipo']} debe hacerse el **{d['prox_cita'].strftime('%d de %B de %Y')}**."
                st.success(msg_res)
            else:
                msg_res = f"Se registró la cita de {d['cita_tipo']}, pero no requiere cálculo futuro (no es control)."
                st.write(msg_res)
        
        txt_voz = f"{st.session_state.paciente}, {msg_res.replace('**','')} ¿Desea guardar esta información?"
        hablar(txt_voz)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 SÍ, Guardar"):
                if guardar_db(d):
                    st.toast("Guardado exitosamente", icon="✅")
                    hablar("Información guardada correctamente.")
                    time.sleep(2)
                    st.session_state.paso = 'menu'
                    st.rerun()
        with col2:
            if st.button("❌ NO, Cancelar"):
                st.session_state.paso = 'menu'
                st.rerun()

    # PANTALLA 7: FECHA PROGRAMADA (CONFIRMADA)
    elif st.session_state.paso == 'prog_form':
        st.subheader("📅 Confirmar Fecha Exacta")
        st.warning("Use esta opción si YA tiene la cita asignada por la entidad de salud.")
        hablar("Por favor ingrese los detalles de la cita ya confirmada para programar notificaciones.")
        
        with st.form("form_prog"):
            cat = st.radio("Categoría", ["Examen Médico", "Cita Médica"])
            detalle = st.text_input("Detalle (Ej. Cardiología, Sangre)")
            lugar = st.text_input("Lugar / Clínica")
            fecha = st.date_input("Fecha Programada", min_value=date.today())
            hora = st.time_input("Hora")
            
            if st.form_submit_button("Programar y Notificar"):
                datos = {
                    "paciente": st.session_state.paciente,
                    "prog_categoria": cat,
                    "prog_fecha": fecha,
                    "prog_hora": str(hora)
                }
                if cat == "Examen Médico": datos["ex_tipo"] = detalle
                else: datos["cita_tipo"] = detalle
                
                st.session_state.datos = datos
                st.session_state.datos_extra = {"lugar": lugar} # Guardamos temporalmente para el mensaje
                st.session_state.paso = 'confirmar_prog'
                st.rerun()
        if st.button("🔙 Volver"): st.session_state.paso = 'menu'; st.rerun()

    # PANTALLA 8: CONFIRMAR Y ENVIAR NOTIFICACIONES
    elif st.session_state.paso == 'confirmar_prog':
        d = st.session_state.datos
        extra = st.session_state.datos_extra
        
        msg_res = f"Cita Confirmada: {d['prog_categoria']} - {d.get('cita_tipo') or d.get('ex_tipo')} en {extra['lugar']}. Fecha: {d['prog_fecha']} a las {d['prog_hora']}."
        
        st.subheader("🔔 Confirmación de Envío")
        st.info(msg_res)
        hablar(f"Usted ha indicado: {msg_res}. Se enviarán notificaciones a su correo y Telegram. ¿Es correcto?")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ SÍ, Confirmar y Enviar"):
                with st.spinner("Guardando y enviando alertas..."):
                    if guardar_db(d):
                        enviar_notificaciones(msg_res, st.session_state.paciente)
                        st.success("¡Notificaciones enviadas!")
                        hablar("Se han programado las notificaciones exitosamente.")
                        time.sleep(3)
                        st.session_state.paso = 'menu'
                        st.rerun()
        with col2:
            if st.button("❌ Corregir"):
                st.session_state.paso = 'prog_form'
                st.rerun()

    # PANTALLA 9: HISTORIAL
    elif st.session_state.paso == 'historial':
        st.subheader(f"📂 Historial: {st.session_state.paciente}")
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT fecha_registro, med_tipo, prox_retiro, ex_tipo, prox_examen, cita_tipo, prox_cita, prog_categoria, prog_fecha 
                FROM registros_salud 
                WHERE paciente LIKE %s ORDER BY fecha_registro DESC LIMIT 5
            """, (st.session_state.paciente,))
            registros = cursor.fetchall()
            conn.close()
            
            if registros:
                hablar(f"He encontrado {len(registros)} registros recientes.")
                for reg in registros:
                    with st.container():
                        st.markdown(f"**Fecha Registro:** {reg[0].strftime('%d/%m/%Y')}")
                        if reg[1]: st.markdown(f"💊 **Medicina:** {reg[1]} | Próx: {reg[2]}")
                        if reg[3]: st.markdown(f"🧪 **Examen:** {reg[3]} | Próx: {reg[4]}")
                        if reg[5]: st.markdown(f"🩺 **Cita:** {reg[5]} | Próx: {reg[6]}")
                        if reg[7]: st.markdown(f"📅 **Programado:** {reg[7]} para el {reg[8]}")
                        st.markdown("---")
            else:
                st.warning("No hay registros recientes.")
                hablar("No encontré registros para este paciente.")
        
        if st.button("🔙 Volver al Menú"):
            st.session_state.paso = 'menu'
            st.rerun()

if __name__ == "__main__":
    main()
