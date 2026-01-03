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

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Gestión de Salud - HealthTrack",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #ff4b4b;
        color: white;
    }
    .reportview-container {
        background: #f0f2f6;
    }
    </style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN REGIONAL ---
# Ampliamos el rango de años como en tu código original
festivos_co = holidays.CO(years=[2025, 2026, 2027, 2028, 2029])
tz_co = pytz.timezone('America/Bogota')

# --- FUNCIONES DE BASE DE DATOS (TiDB) ---
def get_db_connection():
    """Establece conexión con TiDB usando st.secrets"""
    try:
        return mysql.connector.connect(
            host=st.secrets["tidb"]["host"],
            port=st.secrets["tidb"]["port"],
            user=st.secrets["tidb"]["user"],
            password=st.secrets["tidb"]["password"],
            database=st.secrets["tidb"]["database"],
            autocommit=True,
            ssl_verify_cert=True,
            ssl_ca="/etc/ssl/certs/ca-certificates.crt" # Ruta estándar en servidores Linux (Streamlit Cloud)
        )
    except Exception as e:
        st.error(f"❌ Error de conexión DB: {e}")
        return None

def guardar_registro(datos):
    """Guarda el registro en TiDB"""
    conn = get_db_connection()
    if not conn:
        return False

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

def consultar_historial_db(paciente):
    conn = get_db_connection()
    if not conn: return []
    
    try:
        cursor = conn.cursor()
        query = """
            SELECT fecha_registro, med_tipo, prox_retiro, ex_tipo, prox_examen, cita_tipo, prox_cita, prog_categoria, prog_fecha 
            FROM registros_salud 
            WHERE paciente LIKE %s COLLATE utf8mb4_general_ci
            ORDER BY fecha_registro DESC LIMIT 4
        """
        cursor.execute(query, (paciente,))
        resultados = cursor.fetchall()
        cursor.close()
        conn.close()
        return resultados
    except Exception as e:
        st.error(f"Error consultando historial: {e}")
        return []

# --- MOTOR DE LÓGICA DE FECHAS (Tu lógica original) ---
def obtener_dia_habil_anterior(fecha):
    if isinstance(fecha, datetime): fecha = fecha.date()
    while fecha.weekday() == 6 or fecha in festivos_co: # 6 es Domingo
        fecha -= timedelta(days=1)
    return fecha

def sumar_dias_habiles(fecha_inicio, dias_a_sumar):
    if isinstance(fecha_inicio, datetime): fecha_inicio = fecha_inicio.date()
    fecha_actual = fecha_inicio
    dias_contados = 0
    while dias_contados < dias_a_sumar:
        fecha_actual += timedelta(days=1)
        if fecha_actual.weekday() != 6 and fecha_actual not in festivos_co:
            dias_contados += 1
    return fecha_actual

# --- FUNCIONES DE INTERACCIÓN (VOZ Y NOTIFICACIONES) ---

def hablar_respuesta(texto):
    """Genera audio TTS y lo reproduce automáticamente en el navegador"""
    try:
        tts = gTTS(text=texto, lang='es', tld='com.co')
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        
        # Reproductor de audio (autoplay=True intenta reproducir solo)
        st.audio(audio_bytes, format='audio/mp3', autoplay=True)
    except Exception as e:
        st.warning(f"No se pudo generar el audio: {e}")

def enviar_notificaciones(mensaje, paciente):
    """Envía alertas por Telegram y Gmail"""
    try:
        tg_token = st.secrets["telegram"]["token"]
        tg_chat_id = st.secrets["telegram"]["chat_id"]
        
        email_sender = st.secrets["gmail"]["sender"]
        email_pass = st.secrets["gmail"]["app_password"]
        email_receiver = st.secrets["gmail"]["receiver"]
    except KeyError:
        st.warning("⚠️ Credenciales no configuradas en secrets.toml")
        return

    mensaje_personalizado = f"PACIENTE: {paciente}\n{mensaje}"

    # 1. Telegram
    try:
        url_tg = f"https://api.telegram.org/bot{tg_token}/sendMessage"
        payload = {
            'chat_id': tg_chat_id,
            'text': f"🔔 RECORDATORIO SALUD:\n{mensaje_personalizado}"
        }
        requests.post(url_tg, json=payload, timeout=5)
    except Exception as e:
        st.error(f"Error Telegram: {e}")

    # 2. Gmail
    try:
        msg = MIMEText(mensaje_personalizado)
        msg['Subject'] = f'Recordatorio de Salud - {paciente}'
        msg['From'] = email_sender
        msg['To'] = email_receiver

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(email_sender, email_pass)
            server.send_message(msg)
    except Exception as e:
        st.error(f"Error Gmail: {e}")

# --- INTERFAZ PRINCIPAL ---

def main():
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3063/3063176.png", width=100)
    st.sidebar.title("🏥 HealthTrack AI")
    
    # --- GESTIÓN DE PACIENTE ---
    # Usamos session_state para mantener el nombre del paciente
    if 'paciente' not in st.session_state:
        st.session_state.paciente = ""

    paciente_input = st.sidebar.text_input("Nombre del Paciente", value=st.session_state.paciente, placeholder="Ingrese nombre...").strip().upper()
    
    if paciente_input:
        st.session_state.paciente = paciente_input
    
    if not st.session_state.paciente:
        st.info("👋 **Bienvenido.** Por favor, ingrese el nombre del paciente en la barra lateral para comenzar.")
        st.markdown("---")
        st.write("El sistema le ayudará a calcular fechas óptimas para medicinas, exámenes y citas.")
        return

    paciente = st.session_state.paciente
    st.sidebar.markdown(f"👤 **{paciente}**")
    
    # Menú de navegación
    opcion = st.sidebar.radio("¿Qué desea gestionar hoy?", 
        ["💊 Retiro de Medicinas", "🧪 Exámenes Médicos", "🩺 Citas Médicas", "📅 Confirmar Fecha Exacta", "📂 Ver Historial"])

    st.title(f"Gestión para: {paciente}")

    # --- FLUJO 1: MEDICINAS ---
    if opcion == "💊 Retiro de Medicinas":
        st.subheader("Cálculo de Próximo Retiro")
        with st.form("form_medicinas"):
            tipo_med = st.selectbox("Tipo de Medicina", ["Medicina General", "Especialista", "Oncología", "Otro"])
            especialidad = ""
            if tipo_med in ["Especialista", "Otro"]:
                especialidad = st.text_input("Especifique la especialidad")
            
            fecha_ult_retiro = st.date_input("Fecha del último retiro", value=date.today())
            entregas_pendientes = st.number_input("Entregas pendientes", min_value=0, step=1)
            
            submitted = st.form_submit_button("Calcular Fecha")
            
            if submitted:
                tipo_final = especialidad if especialidad else tipo_med
                prox_retiro = obtener_dia_habil_anterior(fecha_ult_retiro + timedelta(days=28))
                
                datos = {"paciente": paciente, "med_tipo": tipo_final, "prox_retiro": prox_retiro}
                
                if guardar_registro(datos):
                    msg_voz = f"El próximo retiro de {tipo_final} para {paciente} debe ser el {prox_retiro.strftime('%d de %B')}"
                    st.success(f"✅ **Cálculo Exitoso:** {msg_voz}")
                    hablar_respuesta(msg_voz)

    # --- FLUJO 2: EXÁMENES ---
    elif opcion == "🧪 Exámenes Médicos":
        st.subheader("Gestión de Órdenes de Exámenes")
        with st.form("form_examenes"):
            tipo_ex = st.selectbox("Tipo de Examen", ["Sangre", "Rayos X", "Ultrasonido", "Resonancia/Tomografía", "Otro"])
            otro_ex = ""
            if tipo_ex == "Otro":
                otro_ex = st.text_input("Especifique el examen")
            
            lugar = st.text_input("Lugar de la orden")
            fecha_orden = st.date_input("Fecha de la orden médica", value=date.today())
            dias_entrega = st.number_input("Días para entrega de resultados", min_value=1, value=5)
            
            submitted = st.form_submit_button("Calcular Fecha de Toma")
            
            if submitted:
                tipo_final = otro_ex if otro_ex else tipo_ex
                
                # Tu lógica original de examen
                resta = dias_entrega - 32
                if resta < 0 or resta == 2:
                    prox_examen = sumar_dias_habiles(fecha_orden, 3)
                else:
                    prox_examen = obtener_dia_habil_anterior(fecha_orden + timedelta(days=resta))
                
                datos = {"paciente": paciente, "ex_tipo": tipo_final, "prox_examen": prox_examen}
                
                if guardar_registro(datos):
                    msg_voz = f"Para entregar resultados a tiempo, el examen de {tipo_final} debe tomarse el {prox_examen.strftime('%d de %B')}"
                    st.success(f"✅ **Resultado:** {msg_voz}")
                    hablar_respuesta(msg_voz)

    # --- FLUJO 3: CITAS ---
    elif opcion == "🩺 Citas Médicas":
        st.subheader("Gestión de Citas y Controles")
        with st.form("form_citas"):
            tipo_cita = st.selectbox("Especialidad", ["Medicina General", "Especialista", "Oncología", "Odontología", "Otro"])
            especialidad = ""
            if tipo_cita in ["Especialista", "Otro"]:
                especialidad = st.text_input("Especifique especialidad")
            
            lugar = st.text_input("Lugar de la cita")
            es_control = st.checkbox("¿Es un control derivado de una cita anterior?")
            
            fecha_base = st.date_input("Fecha de la última cita/orden", value=date.today())
            dias_control = st.number_input("¿Dentro de cuántos días es el control?", min_value=1, value=30, disabled=not es_control)
            
            submitted = st.form_submit_button("Calcular Solicitud")
            
            if submitted:
                tipo_final = especialidad if especialidad else tipo_cita
                prox_cita = None
                msg_voz = ""

                if es_control:
                    resta = dias_control - 32
                    if resta < 0 or resta == 2:
                        prox_cita = sumar_dias_habiles(fecha_base, 3)
                    else:
                        prox_cita = obtener_dia_habil_anterior(fecha_base + timedelta(days=resta))
                    msg_voz = f"La cita de control de {tipo_final} debe solicitarse el {prox_cita.strftime('%d de %B')}"
                else:
                    msg_voz = f"Información de cita base de {tipo_final} registrada. No se requiere cálculo futuro."

                datos = {"paciente": paciente, "cita_tipo": tipo_final, "prox_cita": prox_cita}
                
                if guardar_registro(datos):
                    st.success(f"✅ {msg_voz}")
                    hablar_respuesta(msg_voz)

    # --- FLUJO 4: PROGRAMAR FECHA EXACTA ---
    elif opcion == "📅 Confirmar Fecha Exacta":
        st.subheader("Notificar Cita Confirmada")
        st.info("Use esto cuando ya tenga la fecha y hora confirmada por la entidad de salud.")
        
        with st.form("form_prog"):
            col1, col2 = st.columns(2)
            with col1:
                categoria = st.selectbox("Categoría", ["Examen Médico", "Cita Médica"])
                fecha_prog = st.date_input("Fecha programada")
            with col2:
                detalle = st.text_input("Detalle (Ej. Cardiología, Sangre)")
                hora_prog = st.time_input("Hora programada")
            
            lugar = st.text_input("Lugar (Clínica/Hospital)")
            
            submitted = st.form_submit_button("Confirmar y Notificar")
            
            if submitted:
                datos = {
                    "paciente": paciente,
                    "prog_categoria": categoria, # Guardamos en una columna genérica o reutilizamos
                    "prog_fecha": fecha_prog,
                    "prog_hora": str(hora_prog)
                }
                # Ajustamos para guardar el detalle en alguna columna existente o genérica
                if categoria == "Examen Médico": datos["ex_tipo"] = detalle
                else: datos["cita_tipo"] = detalle

                if guardar_registro(datos):
                    mensaje_notif = f"Cita Confirmada: {categoria} - {detalle} en {lugar}. Fecha: {fecha_prog.strftime('%d/%m/%Y')} Hora: {hora_prog}."
                    
                    # Enviar Notificaciones Reales
                    with st.spinner("Enviando notificaciones a Telegram y Gmail..."):
                        enviar_notificaciones(mensaje_notif, paciente)
                    
                    msg_voz = "Confirmación exitosa. Se han enviado los recordatorios a su correo y Telegram."
                    st.success("✅ ¡Notificaciones enviadas!")
                    hablar_respuesta(msg_voz)

    # --- HISTORIAL ---
    elif opcion == "📂 Ver Historial":
        st.subheader(f"Historial Reciente: {paciente}")
        if st.button("Consultar Base de Datos"):
            registros = consultar_historial_db(paciente)
            if registros:
                hablar_respuesta(f"He encontrado {len(registros)} registros recientes para {paciente}.")
                for reg in registros:
                    # Formato de visualización limpio
                    with st.container():
                        col1, col2 = st.columns([1, 4])
                        with col1:
                            st.write(f"📅 **{reg[0].strftime('%d/%m') if reg[0] else ''}**")
                        with col2:
                            if reg[1]: st.info(f"💊 Medicina: **{reg[1]}** | Próx. Retiro: {reg[2]}")
                            if reg[3]: st.warning(f"🧪 Examen: **{reg[3]}** | Próx. Solicitud: {reg[4]}")
                            if reg[5]: st.success(f"🩺 Cita: **{reg[5]}** | Próx. Solicitud: {reg[6]}")
                            if reg[7]: st.error(f"📅 Programado: **{reg[7]}** para el {reg[8]}")
            else:
                st.warning("No se encontraron registros recientes.")
                hablar_respuesta("No encontré registros recientes para este paciente.")

if __name__ == "__main__":
    main()