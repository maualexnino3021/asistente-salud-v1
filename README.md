🏥 Asistente de Salud v1
Aplicación web para gestión de citas médicas, exámenes y medicamentos con recordatorios automáticos por Telegram y Gmail, guiada por voz mediante síntesis de audio.
---
Motivación
Este proyecto nació de una necesidad real del entorno familiar: dos adultos mayores de 80 años con una agenda médica activa — retiros periódicos de medicamentos, citas y exámenes frecuentes — cuya gestión recaía de forma centralizada en un único cuidador. La ausencia de un sistema de recordatorios estructurado provocaba que parte de esas acciones se perdieran, generando sobrecarga en quien las coordinaba y discontinuidad en el seguimiento médico.
El asistente fue diseñado para distribuir esa carga mediante notificaciones automáticas anticipadas, garantizando que cada evento llegue a tiempo a quienes corresponde, sin depender de la memoria ni de la disponibilidad de una sola persona.
---
¿Qué hace?
Registra citas médicas, exámenes y fechas de retiro de medicamentos
Calcula automáticamente las fechas de recordatorio a partir de cada evento
Envía notificaciones por Telegram y Gmail desde 6 días antes del evento, cada 2 días, 2 veces al día
Narra por voz lo que la pantalla pregunta y muestra (guía de voz de salida — no reconoce voz del usuario)
Persiste todos los datos en una base de datos MySQL
---
Tecnologías utilizadas
Tecnología	Uso
Python	Lenguaje principal
Streamlit	Interfaz web
MySQL	Base de datos
Telegram Bot API	Notificaciones por Telegram
Gmail SMTP	Notificaciones por correo
pyttsx3 / gTTS	Síntesis de voz (narración)
GitHub Actions	Automatización / despliegue
---
Estructura del proyecto
```
asistente-salud-v1/
├── app.py               # Aplicación principal Streamlit
├── vigilante.py         # Motor de recordatorios y notificaciones
├── requirements.txt     # Dependencias del proyecto
├── .streamlit/
│   └── config.toml      # Configuración de Streamlit
└── .github/
    └── workflows/       # GitHub Actions
```
---
Instalación y uso local
1. Clonar el repositorio
```bash
git clone https://github.com/maualexnino3021/asistente-salud-v1.git
cd asistente-salud-v1
```
2. Instalar dependencias
```bash
pip install -r requirements.txt
```
3. Configurar variables de entorno
Crea un archivo `.env` en la raíz con:
```env
DB_HOST=localhost
DB_USER=tu_usuario_mysql
DB_PASSWORD=tu_contraseña
DB_NAME=salud_db

TELEGRAM_TOKEN=tu_token_de_telegram
TELEGRAM_CHAT_ID=tu_chat_id

GMAIL_USER=tu_correo@gmail.com
GMAIL_PASSWORD=tu_contraseña_de_aplicacion
```
4. Ejecutar la aplicación
```bash
streamlit run app.py
```
5. Ejecutar el vigilante de recordatorios
```bash
python vigilante.py
```
---
Lógica de recordatorios
Para cada evento registrado (cita, examen o retiro de medicamento), el sistema calcula automáticamente las fechas de notificación:
```
Evento programado (día 0)
        ↑
Día -6 → Día -4 → Día -2 → Día 0
  2 notif/día en cada fecha (mañana y tarde)
  Canal: Telegram + Gmail simultáneamente
```
---
Requisitos previos
Python 3.8+
MySQL instalado y corriendo
Cuenta de Telegram con bot creado via @BotFather
Cuenta Gmail con contraseña de aplicación habilitada (verificación en 2 pasos requerida)
---
Autor
Mauricio Alexander Niño Gamboa  
Ingeniero Mecánico | MSc Ingeniería Industrial  
GitHub
