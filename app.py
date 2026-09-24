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
    page_title="Control de Acceso Seguro - Colegio",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS VISUALES ---
ESTILOS_SEGUROS = """
<style>
    .stApp { background-color: #0f172a !important; color: #f8fafc !important; }
    h1, h2, h3 { color: #ffffff !important; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; }
    [data-testid="stSidebar"] * { color: #f8fafc !important; }
</style>
"""
st.markdown(ESTILOS_SEGUROS, unsafe_allow_html=True)

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

# --- MENÚ LATERAL ---
with st.sidebar:
    st.title("Control Escolar")
    modo = st.radio("Sección", ["⚡ Escaneo con Seguridad", "📊 Dashboard y Reportes", "👥 Directorio"])

# --- MODO 1: ESCANEO RÁPIDO CON CREDENCIALES EN CADA REGISTRO ---
if modo == "⚡ Escaneo con Seguridad":
    st.title("🛡️ Estación de Registro con Doble Validación")
    st.write("Cada marcaje requiere un carnet y la confirmación de credenciales del docente en puerta.")

    with st.form("form_registro_seguro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("1. Identificación")
            codigo_input = st.text_input("Código ID del Carnet", placeholder="Ej: 001...")
            
        with col2:
            st.subheader("2. Autorización en Puerta")
            user_input = st.text_input("Usuario Docente", placeholder="Usuario...")
            pass_input = st.text_input("Contraseña", type="password", placeholder="Contraseña...")
            
        btn_procesar = st.form_submit_button("Verificar y Registrar Asistencia")

    if btn_procesar:
        # Validación de credenciales del docente
        if user_input == "UEMES" and pass_input == "Sarratud2026":
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
                            st.success(f"✅ ¡{tipo_movimiento} registrada con éxito para {nombre} {apellido} a las {hora_actual}!")
                        except Exception as e:
                            st.error(f"Error al guardar en la base de datos: {e}")
                    else:
                        st.warning(f"⚠️ {nombre} {apellido} ya completó su Entrada y Salida el día de hoy.")
                else:
                    st.error(f"❌ El código ID '{codigo_limpio}' no se encuentra registrado en el sistema.")
            else:
                st.warning("⚠️ Por favor ingrese o escanee el código del carnet.")
        else:
            st.error("❌ Usuario o contraseña de autorización incorrectos. No se pudo procesar el registro.")

    st.markdown("---")
    st.subheader("Últimos marcajes del día:")
    db = conectar_bd()
    ultimos = consultar_sql(db, 'SELECT a.hora, a.tipo_registro, u.nombre, u.apellido, u.grado_seccion FROM asistencias a JOIN usuarios u ON a.codigo_id = u.codigo_id WHERE a.fecha = ? ORDER BY a.id DESC LIMIT 5', (datetime.now(ZoneInfo("America/Caracas")).strftime("%Y-%m-%d"),))
    if ultimos:
        df_ultimos = pd.DataFrame(ultimos, columns=["Hora", "Acción", "Nombre", "Apellido", "Grado"])
        st.dataframe(df_ultimos, use_container_width=True, hide_index=True)

# --- MODO 2: DASHBOARD Y REPORTES ---
elif modo == "📊 Dashboard y Reportes":
    st.title("📊 Resumen y Exportación")
    fecha_hoy = datetime.now(ZoneInfo("America/Caracas")).strftime("%Y-%m-%d")
    db = conectar_bd()
    filas = consultar_sql(db, 'SELECT a.hora, a.tipo_registro, a.codigo_id, u.nombre, u.apellido, u.tipo_persona, u.grado_seccion FROM asistencias a JOIN usuarios u ON a.codigo_id = u.codigo_id WHERE a.fecha = ? ORDER BY a.hora DESC', (fecha_hoy,))
    df = pd.DataFrame(filas, columns=["Hora", "Registro", "Código", "Nombre", "Apellido", "Tipo", "Grado"]) if filas else pd.DataFrame()
    
    st.metric("Total Registros Hoy", len(df))
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("Descargar CSV del Día", df.to_csv(index=False).encode('utf-8'), f"asistencia_{fecha_hoy}.csv", "text/csv")
    else:
        st.info("No hay registros hoy.")

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
