import streamlit as st
import mysql.connector
import holidays
import pytz
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta, date
from gtts import gTTS
import io
import time

# --- 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS ---
st.set_page_config(
    page_title="Gestión de Salud - HealthTrack",
    page_icon="🏥",
    layout="centered"
)

# ESTILOS CORREGIDOS: Letras oscuras sobre fondos claros + Inputs amarillo/azul
st.markdown("""
    <style>
    /* Fondo general */
    .stApp {
        background-color: #f4f4f4;
    }
    
    /* TÍTULO CENTRADO EN ESPAÑOL */
    h1 {
        color: #001f3f; /* Azul Marino */
        text-align: center;
        font-family: 'Arial', sans-serif;
        border-bottom: 3px solid #FFD700; /* Dorado */
        padding-bottom: 15px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    h2, h3 {
        color: #001f3f;
    }

    /* BARRA LATERAL - Fondo claro, letras oscuras */
    section[data-testid="stSidebar"] {
        background-color: #E8F4F8; /* Azul muy claro */
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] .stMarkdown {
        color: #001f3f !important; /* Texto Azul Oscuro */
    }

    /* BOTONES - Fondo claro, letras oscuras */
    div.stButton > button {
        background-color: #FFE680; /* Amarillo claro */
        color: #001f3f; /* Texto Azul Oscuro */
        border: 2px solid #C0C0C0;
        border-radius: 10px;
        font-weight: bold;
        width: 100%;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        background-color: #FFD700;
        color: #000000;
        border-color: #FFD700;
    }

    /* CAMPOS DE ENTRADA - Fondo AMARILLO INTENSO, Letras AZUL INTENSO */
    div[data-baseweb="input"] > div,
    input[type="text"],
    input[type="number"],
    input[type="date"],
    input[type="time"],
    textarea,
    .stTextInput input,
    .stNumberInput input,
    .stDateInput input,
    .stTimeInput input,
    .stTextArea textarea {
        background-color: #FFD700 !important; /* Amarillo intenso */
        color: #00008B !important; /* Azul intenso */
        border: 2px solid #001f3f !important;
        border-radius: 5px;
        font-weight: 600 !important;
    }
    
    /* Asegurar color de texto en inputs */
    input::placeholder {
        color: #4B0082 !important; /* Azul-violeta para placeholders */
        opacity: 0.8;
    }

    /* Labels de inputs - oscuros sobre fondo claro */
    label {
        color: #001f3f !important;
        font-weight: 600;
    }

    /* MENSAJES DE ESTADO */
    div[data-testid="stNotification"] {
        border-left: 5px solid #FFD700;
    }
    
    /* Asegurar legibilidad en selectbox y radio */
    .stSelectbox label,
    .stRadio label {
        color: #001f3f !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. CREDENCIALES Y CONFIGURACIÓN (Lógica Original) ---

# Configuración Base de Datos TiDB
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

# --- 3. FUNCIONES DE LÓGICA (Cálculos, DB, Voz, Notificaciones) ---

def get_db_connection():
    try:
        return mysql.connector.connect(**CONFIG_DB)
    except Exception as e:
        st.error(f"❌ No se ha podido establecer conexión con la base de datos: {e}")
        return None

def obtener_dia_habil_anterior(fecha_in):
    """Lógica exacta del script original para restar días hábiles"""
    if isinstance(fecha_in, datetime): fecha_in = fecha_in.date()
    # Mientras sea Domingo (6) o Festivo
    while fecha_in.weekday() == 6 or fecha_in in festivos_co:
        fecha_in -= timedelta(days=1)
    return fecha_in

def sumar_dias_habiles(fecha_inicio, dias_a_sumar):
    """Lógica exacta del script original para sumar días hábiles"""
    if isinstance(fecha_inicio, datetime): fecha_inicio = fecha_inicio.date()
    fecha_actual = fecha_inicio
    dias_contados = 0
    while dias_contados < dias_a_sumar:
        fecha_actual += timedelta(days=1)
        # Si no es Domingo y no es Festivo
        if fecha_actual.weekday() != 6 and fecha_actual not in festivos_co:
            dias_contados += 1
    return fecha_actual

def hablar(texto):
    """
    Genera audio TTS y lo reproduce en el navegador.
    Controla el estado para no repetir el audio infinitamente en cada rerun.
    """
    if 'ultimo_audio' not in st.session_state:
        st.session_state.ultimo_audio = ""
    
    # Solo reproducir si el texto es nuevo para esta interacción
    if texto != st.session_state.ultimo_audio:
        try:
            tts = gTTS(text=texto, lang='es', tld='com.co')
            audio_bytes = io.BytesIO()
            tts.write_to_fp(audio_bytes)
            audio_bytes.seek(0)
            
            st.session_state.ultimo_audio = texto
            st.session_state.audio_data = audio_bytes
        except Exception as e:
            st.warning(f"Audio no disponible: {e}")
            
    # Mostrar reproductor (autoplay intenta reproducir solo)
    if 'audio_data' in st.session_state and st.session_state.audio_data:
        st.audio(st.session_state.audio_data, format='audio/mp3', autoplay=True)

def enviar_notificaciones(mensaje, paciente):
    """Envía alertas reales por Telegram y Gmail tal como el script original"""
    mensaje_personalizado = f"PACIENTE: {paciente}\n{mensaje}"
    
    # Telegram
    try:
        url_tg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url_tg, data={
            'chat_id': TELEGRAM_CHAT_ID,
            'text': f"🔔 RECORDATORIO SALUD:\n{mensaje_personalizado}",
             'parse_mode': 'Markdown'
        }, timeout=10)
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
    """Guarda en TiDB usando la estructura exacta de tabla solicitada"""
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
        
        # Preparar valores (manejando Nones donde corresponda)
        valores = (
            datos.get("paciente"), 
            datetime.now(tz_co).replace(tzinfo=None),
            datos.get("med_tipo"), 
            datos.get("prox_retiro"),
            datos.get("ex_tipo"), 
            datos.get("prox_examen"),
            datos.get("cita_tipo"), 
            datos.get("prox_cita"),
            datos.get("prog_categoria"), 
            datos.get("prog_fecha"), 
            datos.get("prog_hora")
        )
        
        cursor.execute(query, valores)
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"❌ Error al guardar en base de datos: {e}")
        return False

# --- 4. GESTIÓN DE ESTADO (Session State) ---
# Usamos esto para simular el flujo "paso a paso" del while loop en consola
if 'paso' not in st.session_state: st.session_state.paso = 'inicio'
if 'datos' not in st.session_state: st.session_state.datos = {}
if 'paciente' not in st.session_state: st.session_state.paciente = ""
if 'datos_extra' not in st.session_state: st.session_state.datos_extra = {}

# --- 5. INTERFAZ DE USUARIO (WIZARD) ---

def main():
    # BARRA LATERAL
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3063/3063176.png", width=100)
        st.markdown("## ASISTENTE INTEGRAL DE SALUD")
        st.markdown("---")
        if st.session_state.paciente:
            st.markdown(f"👤 **PACIENTE:**\n\n### {st.session_state.paciente}")
            st.markdown("---")
            if st.button("🔄 Cambiar Paciente"):
                st.session_state.paso = 'inicio'
                st.session_state.paciente = ""
                st.session_state.datos = {}
                st.rerun()

    # --- PANTALLA 1: BIENVENIDA Y NOMBRE ---
    if st.session_state.paso == 'inicio':
        st.title("BIENVENIDO AL GESTOR DE SALUD")
        
        msg_voz = "Bienvenido al gestor de salud. Realizaremos preguntas para calcular o registrar sus fechas. Para iniciar, por favor permítame saber el nombre del paciente."
        st.markdown(f"<h4 style='text-align: center; color: #555;'>{msg_voz}</h4>", unsafe_allow_html=True)
        hablar(msg_voz)
        
        st.markdown("<br>", unsafe_allow_html=True)
        nombre_input = st.text_input("Ingrese el nombre del paciente:", key="input_nombre").upper()
        
        if st.button("CONTINUAR"):
            if nombre_input:
                st.session_state.paciente = nombre_input
                st.session_state.paso = 'menu'
                st.rerun()
            else:
                st.warning("Por favor, escriba un nombre para continuar.")

    # --- PANTALLA 2: MENÚ PRINCIPAL ---
    elif st.session_state.paso == 'menu':
        st.title(f"CONSULTA: {st.session_state.paciente}")
        
        msg_menu = f"Por favor, {st.session_state.paciente}, indique el motivo de su consulta: retiro medicinas, exámenes médicos, citas médicas o registrar fecha programada."
        hablar(msg_menu)
        
        st.info("Seleccione una opción para avanzar:")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("1. 💊 RETIRO DE MEDICINAS"):
                st.session_state.paso = 'med_form'
                st.rerun()
            if st.button("2. 🧪 EXÁMENES MÉDICOS"):
                st.session_state.paso = 'ex_form'
                st.rerun()
        with col2:
            if st.button("3. 🩺 CITAS MÉDICAS"):
                st.session_state.paso = 'cita_form'
                st.rerun()
            if st.button("5. 📅 CONFIRMAR FECHA EXACTA"):
                st.session_state.paso = 'prog_form'
                st.rerun()
        
        st.markdown("---")
        if st.button("📂 VER HISTORIAL RECIENTE"):
            st.session_state.paso = 'historial'
            st.rerun()

    # --- PANTALLA 3: FLUJO MEDICINAS (Opción 1) ---
    elif st.session_state.paso == 'med_form':
        st.subheader("💊 Retiro de Medicinas")
        hablar("Iniciamos cordialmente con el retiro de medicinas. Indique el tipo, entregas y la fecha del último retiro.")
        
        with st.form("form_med"):
            opcion_med = st.radio("¿Es para...?", ["Medicina General", "Especialista", "Oncología", "Otra Especialidad"])
            especialidad = ""
            if opcion_med in ["Especialista", "Otra Especialidad"]:
                especialidad = st.text_input("Por favor, especifique cuál es la especialidad")
            
            num_entregas = st.number_input("¿Cuántas entregas le faltan?", min_value=0, step=1)
            fecha_ult = st.date_input("Indique la fecha de su último retiro", value=date.today())
            
            # Botón de envío del formulario
            if st.form_submit_button("CALCULAR FECHA"):
                tipo_final = especialidad if especialidad else opcion_med
                
                # CÁLCULO EXACTO DEL SCRIPT
                fecha_base = fecha_ult # date object
                prox_retiro = obtener_dia_habil_anterior(fecha_base + timedelta(days=28))
                
                st.session_state.datos = {
                    "paciente": st.session_state.paciente,
                    "med_tipo": tipo_final,
                    "prox_retiro": prox_retiro
                }
                st.session_state.paso = 'confirmar_calculo'
                st.rerun()
        
        if st.button("🔙 Volver al Menú"): st.session_state.paso = 'menu'; st.rerun()

    # --- PANTALLA 4: FLUJO EXÁMENES (Opción 2) ---
    elif st.session_state.paso == 'ex_form':
        st.subheader("🧪 Exámenes Médicos")
        hablar("Continuamos gentilmente con sus exámenes médicos. Por favor indique el tipo y fechas.")
        
        with st.form("form_ex"):
            opcion_ex = st.selectbox("Tipo de Examen", ["Sangre", "Rayos X", "Ultrasonido", "Resonancia o Tomografía", "Otro"])
            otro_tipo = ""
            if opcion_ex == "Otro":
                otro_tipo = st.text_input("Especifique qué otro tipo de examen requiere")
            
            lugar = st.text_input("Dígame, ¿en qué lugar le dieron la orden?")
            fecha_orden = st.date_input("Indique la fecha de la orden", value=date.today())
            dias_entrega = st.number_input("¿En cuántos días debe entregar los resultados?", min_value=1, value=5)
            
            if st.form_submit_button("CALCULAR SOLICITUD"):
                tipo_final = otro_tipo if otro_tipo else opcion_ex
                
                # CÁLCULO EXACTO DEL SCRIPT
                resta = dias_entrega - 32
                if resta < 0 or resta == 2:
                    prox_examen = sumar_dias_habiles(fecha_orden, 3)
                else:
                    prox_examen = obtener_dia_habil_anterior(fecha_orden + timedelta(days=resta))
                
                st.session_state.datos = {
                    "paciente": st.session_state.paciente,
                    "ex_tipo": tipo_final,
                    "prox_examen": prox_examen
                }
                st.session_state.paso = 'confirmar_calculo'
                st.rerun()
                
        if st.button("🔙 Volver al Menú"): st.session_state.paso = 'menu'; st.rerun()

    # --- PANTALLA 5: FLUJO CITAS (Opción 3) ---
    elif st.session_state.paso == 'cita_form':
        st.subheader("🩺 Citas Médicas")
        hablar("Pasamos amablemente a sus citas médicas. Indique especialidad y si es control.")
        
        with st.form("form_cit"):
            opcion_cita = st.selectbox("Especialidad", ["Medicina General", "Especialista", "Oncología", "Odontología", "Otro"])
            especialidad = ""
            if opcion_cita in ["Especialista", "Otro"]:
                especialidad = st.text_input("Especifique para qué especialidad es la cita")
            
            lugar = st.text_input("¿En qué lugar es la cita?")
            es_control = st.radio("¿Tiene usted un control por esa cita?", ["No (Primera Vez / Nueva)", "Sí (Control)"])
            
            fecha_label = "Fecha de la orden" if "No" in es_control else "Fecha de su última cita"
            fecha_ult = st.date_input(fecha_label, value=date.today())
            
            dias_control = 0
            if "Sí" in es_control:
                dias_control = st.number_input("¿Dentro de cuántos días es el control?", min_value=1, value=30)
            
            if st.form_submit_button("CALCULAR"):
                tipo_final = especialidad if especialidad else opcion_cita
                prox_cita = None
                
                # CÁLCULO EXACTO DEL SCRIPT
                if "Sí" in es_control:
                    resta = dias_control - 32
                    if resta < 0 or resta == 2:
                        prox_cita = sumar_dias_habiles(fecha_ult, 3)
                    else:
                        prox_cita = obtener_dia_habil_anterior(fecha_ult + timedelta(days=resta))
                
                st.session_state.datos = {
                    "paciente": st.session_state.paciente,
                    "cita_tipo": tipo_final,
                    "prox_cita": prox_cita
                }
                st.session_state.paso = 'confirmar_calculo'
                st.rerun()

        if st.button("🔙 Volver al Menú"): st.session_state.paso = 'menu'; st.rerun()

    # --- PANTALLA 6: CONFIRMACIÓN DE CÁLCULO (Común para 1, 2, 3) ---
    elif st.session_state.paso == 'confirmar_calculo':
        st.subheader("✅ Confirmación de Datos")
        datos = st.session_state.datos
        msg_res = ""
        
        # Construir mensaje según lo calculado
        if "med_tipo" in datos:
            msg_res = f"Su próximo retiro de medicina ({datos['med_tipo']}) es el {datos['prox_retiro'].strftime('%d/%m/%Y')}."
            st.success(msg_res)
        elif "ex_tipo" in datos:
            msg_res = f"Su examen ({datos['ex_tipo']}) debe solicitarse el {datos['prox_examen'].strftime('%d/%m/%Y')}."
            st.warning(msg_res) # Amarillo/Naranja
        elif "cita_tipo" in datos:
            if datos['prox_cita']:
                msg_res = f"Su cita ({datos['cita_tipo']}) debe solicitarse el {datos['prox_cita'].strftime('%d/%m/%Y')}."
                st.success(msg_res)
            else:
                msg_res = f"Cita de {datos['cita_tipo']} registrada. No se requiere cálculo futuro (No es control)."
                st.info(msg_res)
        
        # Voz de confirmación y pregunta
        voz_conf = f"{st.session_state.paciente}, {msg_res}. Por favor, confirme si desea guardar estos datos."
        hablar(voz_conf)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ SÍ, GUARDAR Y NOTIFICAR"):
                # 1. Guardar en BD
                if guardar_db(datos):
                    # 2. Notificación final (sin email inmediato en cálculo, según script original se guarda para proceso batch, pero confirmamos registro)
                    notif_txt = f"Se ha registrado su solicitud. Recibirá notificaciones en {EMAIL_RECEIVER} y Telegram."
                    st.success("Información guardada correctamente.")
                    st.write(notif_txt)
                    
                    hablar(f"Información guardada. {notif_txt}. Que tenga un excelente día.")
                    time.sleep(6) # Dar tiempo al audio
                    
                    st.session_state.paso = 'menu'
                    st.rerun()
        with col2:
            if st.button("❌ NO, VOLVER"):
                st.session_state.paso = 'menu'
                st.rerun()

    # --- PANTALLA 7: FECHAS PROGRAMADAS (Opción 5) ---
    elif st.session_state.paso == 'prog_form':
        st.subheader("📅 Confirmar Fecha Exacta")
        hablar("Evaluaremos sus citas programadas. Use esta opción si ya tiene fecha y hora confirmada.")
        
        with st.form("form_prog"):
            categoria = st.radio("¿Qué tipo de evento es?", ["Examen Médico", "Cita Médica"])
            
            tipo_detalle = ""
            if categoria == "Examen Médico":
                opcion = st.selectbox("Tipo", ["Sangre", "Rayos X", "Ultrasonido", "Resonancia/Tomografía", "Otro"])
                tipo_detalle = st.text_input("Especifique (si es Otro)") if opcion == "Otro" else opcion
            else:
                opcion = st.selectbox("Especialidad", ["Medicina General", "Especialista", "Oncología", "Odontología", "Otro"])
                tipo_detalle = st.text_input("Especifique (si es Otro)") if opcion == "Otro" else opcion
            
            lugar = st.text_input("Sitio a realizarse")
            fecha_prog = st.date_input("Fecha programada (DD/MM/AAAA)", min_value=date.today())
            hora_prog = st.time_input("Hora programada (Formato 24h)")
            
  
