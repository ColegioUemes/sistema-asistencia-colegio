from datetime import datetime
from zoneinfo import ZoneInfo
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st
import sqlite3
import pandas as pd
import libsql_client as libsql

st.set_page_config(
    page_title="Control de Acceso Escolar",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS VISUALES ---
ESTILOS_GENERALES = """
<style>
    .stApp { background-color: #0f172a !important; color: #f8fafc !important; }
    h1, h2, h3 { color: #ffffff !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; }
    [data-testid="stSidebar"] * { color: #f8fafc !important; }
</style>
"""
st.markdown(ESTILOS_GENERALES, unsafe_allow_html=True)

def conectar_bd():
    try:
        url = st.secrets["turso"]["url"]
        auth_token = st.secrets["turso"]["auth_token"]
        if url.startswith("libsql://"):
            url = url.replace("libsql://", "https://")
        return libsql.create_client_sync(url=url, auth_token=auth_token)
    except Exception:
        return sqlite3.connect("colegio.db", check_same_thread=False)

def consultar_sql(db, consulta, parametros=()):
    res = db.execute(consulta, parametros)
    if hasattr(res, 'rows'):
        return res.rows
    if hasattr(res, 'fetchall'):
        return res.fetchall()
    return []

def ejecutar_sql(db, consulta, parametros=()):
    try:
        db.execute(consulta, parametros)
        if hasattr(db, 'commit'):
            db.commit()
    except Exception:
        pass

def inicializar_tablas():
    try:
        db = conectar_bd()
        ejecutar_sql(db, 'CREATE TABLE IF NOT EXISTS usuarios (codigo_id TEXT PRIMARY KEY, nombre TEXT, apellido TEXT, tipo_persona TEXT, grado_seccion TEXT, funcion_cargo TEXT, email TEXT)')
        ejecutar_sql(db, 'CREATE TABLE IF NOT EXISTS asistencias (id INTEGER PRIMARY KEY AUTOINCREMENT, codigo_id TEXT, fecha TEXT, hora TEXT, tipo_registro TEXT, UNIQUE(codigo_id, fecha, tipo_registro))')
    except Exception:
        pass

inicializar_tablas()

# --- GESTIÓN INTELIGENTE DE ACCESOS (TELÉFONO VS COMPUTADORA) ---
TOKEN_TERMINAL_PUERTA = "SarratudTerminal2026*"
query_params = st.query_params

# Si entra desde el teléfono con el enlace secreto, lo autorizamos como terminal
if "terminal" in query_params and query_params["terminal"] == TOKEN_TERMINAL_PUERTA:
    st.session_state["modo_acceso"] = "terminal_porton"

if "modo_acceso" not in st.session_state:
    st.session_state["modo_acceso"] = None

# Si no está autenticado ni viene por enlace secreto, mostramos pantalla de selección de ingreso
if st.session_state["modo_acceso"] is None:
    st.title("🏫 Sistema de Control de Asistencia UEMES")
    st.write("Seleccione cómo desea ingresar en este dispositivo:")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("### 📱 Modo Portón (Teléfono)")
        st.write("Exclusivo para el dispositivo que lee carnets en la entrada.")
        if st.button("Activar Teléfono de Puerta"):
            st.session_state["modo_acceso"] = "terminal_porton"
            st.rerun()
            
    with col_b:
        st.markdown("### 💻 Modo Administración (PC)")
        st.write("Para ver reportes, estadísticas y gestionar el sistema.")
        pwd_admin = st.text_input("Clave de Administrador", type="password", key="pwd_admin_input")
        if st.button("Ingresar a Administración"):
            if pwd_admin == "Sarratud.89":
                st.session_state["modo_acceso"] = "admin_pc"
                st.rerun()
            else:
                st.error("Clave de administración incorrecta.")
    st.stop()

# --- MENÚ LATERAL SEGÚN EL TIPO DE DISPOSITIVO ---
with st.sidebar:
    st.title("Control Escolar")
    
    if st.button("🚪 Salir / Cambiar Modo"):
        st.session_state["modo_acceso"] = None
        st.rerun()
        
    st.markdown("---")
    
    # Si entró como Terminal de Portón, limitamos las opciones para que el docente solo escanee rápido
    if st.session_state["modo_acceso"] == "terminal_porton":
        modo = "⚡ Escaneo Rápido (Puerta)"
        st.info("📱 Este dispositivo está fijo como Terminal de Puerta.")
    else:
        # Si entró desde la PC, tiene acceso completo a todo
        modo = st.radio("Sección", ["📊 Dashboard y Reportes", "⚡ Escaneo Rápido (Puerta)", "👥 Directorio"])

# --- MODO 1: ESCANEO RÁPIDO CONTINUO (PUERTA) ---
if modo == "⚡ Escaneo Rápido (Puerta)":
    st.title("⚡ Estación de Registro en Vivo")
    st.write("Coloque el cursor en el campo e ingrese o escanee el código del carnet.")

    codigo_input = st.text_input("Escanee o ingrese el Código ID del carnet:", key="input_lector", placeholder="Pase el carnet aquí...")

    if codigo_input:
        codigo_limpio = codigo_input.strip()
        ahora_ve = datetime.now(ZoneInfo("America/Caracas"))
        fecha_hoy = ahora_ve.strftime("%Y-%m-%d")
        hora_actual = ahora_ve.strftime("%H:%M:%S")

        db = conectar_bd()
        filas_usr = consultar_sql(db, "SELECT nombre, apellido, tipo_persona, grado_seccion, email FROM usuarios WHERE codigo_id = ?", (codigo_limpio,))
        
        if filas_usr:
            nombre, apellido, tipo_persona, grado, email_usuario = filas_usr[0]

            registros_hoy = consultar_sql(db, "SELECT tipo_registro FROM asistencias WHERE codigo_id = ? AND fecha = ?", (codigo_limpio, fecha_hoy))
            tipos_registrados = [r[0] for r in registros_hoy] if registros_hoy else []

            tipo_movimiento = "Entrada" if "Entrada" not in tipos_registrados else ("Salida" if "Salida" not in tipos_registrados else None)

            if tipo_movimiento:
                try:
                    ejecutar_sql(db, 'INSERT INTO asistencias (codigo_id, fecha, hora, tipo_registro) VALUES (?, ?, ?, ?)', (codigo_limpio, fecha_hoy, hora_actual, tipo_movimiento))
                    st.success(f"✅ ¡{tipo_movimiento} registrada con éxito!")
                    st.markdown(f"### 👤 {nombre} {apellido}")
                    st.write(f"**Grado/Rol:** {grado} ({tipo_persona}) | **Hora:** {hora_actual}")
                except Exception as e:
                    st.error(f"Error al guardar: {e}")
            else:
                st.warning(f"⚠️ {nombre} {apellido} ya completó su Entrada y Salida el día de hoy.")
        else:
            st.error(f"❌ El código '{codigo_limpio}' no existe en la base de datos.")

    st.markdown("---")
    st.subheader("Últimos marcajes de esta sesión:")
    db = conectar_bd()
    ultimos = consultar_sql(db, 'SELECT a.hora, a.tipo_registro, u.nombre, u.apellido, u.grado_seccion FROM asistencias a JOIN usuarios u ON a.codigo_id = u.codigo_id WHERE a.fecha = ? ORDER BY a.id DESC LIMIT 5', (datetime.now(ZoneInfo("America/Caracas")).strftime("%Y-%m-%d"),))
    if ultimos:
        df_ultimos = pd.DataFrame(ultimos, columns=["Hora", "Acción", "Nombre", "Apellido", "Grado"])
        st.dataframe(df_ultimos, use_container_width=True, hide_index=True)

# --- MODO 2: DASHBOARD Y REPORTES (PRINCIPALMENTE PARA PC) ---
elif modo == "📊 Dashboard y Reportes":
    st.title("📊 Resumen y Exportación de Asistencia")
    fecha_hoy = datetime.now(ZoneInfo("America/Caracas")).strftime("%Y-%m-%d")
    db = conectar_bd()
    filas = consultar_sql(db, 'SELECT a.hora, a.tipo_registro, a.codigo_id, u.nombre, u.apellido, u.tipo_persona, u.grado_seccion FROM asistencias a JOIN usuarios u ON a.codigo_id = u.codigo_id WHERE a.fecha = ? ORDER BY a.hora DESC', (fecha_hoy,))
    df = pd.DataFrame(filas, columns=["Hora", "Registro", "Código", "Nombre", "Apellido", "Tipo", "Grado"]) if filas else pd.DataFrame()
    
    st.metric("Total Registros Hoy", len(df))
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("Descargar CSV del Día", df.to_csv(index=False).encode('utf-8'), f"asistencia_{fecha_hoy}.csv", "text/csv")
    else:
        st.info("No hay registros hoy en la base de datos.")

# --- MODO 3: DIRECTORIO ---
elif modo == "👥 Directorio":
    st.title("👥 Directorio de Estudiantes y Personal")
    db = conectar_bd()
    filas = consultar_sql(db, "SELECT codigo_id, nombre, apellido, tipo_persona, grado_seccion, funcion_cargo, email FROM usuarios")
    df = pd.DataFrame(filas, columns=["Código", "Nombre", "Apellido", "Rol", "Grado", "Cargo", "Correo"]) if filas else pd.DataFrame()
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Sin usuarios cargados.")
