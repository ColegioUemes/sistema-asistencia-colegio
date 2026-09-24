from datetime import datetime
from zoneinfo import ZoneInfo
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st
import sqlite3
import pandas as pd
import libsql_client as libsql
import cv2
import numpy as np

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

# --- GESTIÓN INTELIGENTE DE ACCESOS ---
TOKEN_TERMINAL_PUERTA = "SarratudTerminal2026*"
query_params = st.query_params

if "terminal" in query_params and query_params["terminal"] == TOKEN_TERMINAL_PUERTA:
    st.session_state["modo_acceso"] = "terminal_porton"

if "modo_acceso" not in st.session_state:
    st.session_state["modo_acceso"] = None

if "cam_version" not in st.session_state:
    st.session_state["cam_version"] = 0

if st.session_state["modo_acceso"] is None:
    st.title("🏫 Sistema de Control de Asistencia UEMES")
    st.write("Seleccione cómo desea ingresar en este dispositivo:")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### 📱 Registro de Asistencia")
        st.write("Exclusivo para el dispositivo que lee carnets en la entrada.")
        user_reg = st.text_input("Usuario", key="user_reg_input")
        pwd_reg = st.text_input("Contraseña", type="password", key="pwd_reg_input")
        if st.button("Ingresar a Registro de Asistencia"):
            if user_reg == "UEMES" and pwd_reg == "Sarratud2026":
                st.session_state["modo_acceso"] = "terminal_porton"
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
            
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

# --- MENÚ LATERAL ---
with st.sidebar:
    st.title("Control Escolar")
    if st.button("🚪 Salir / Cambiar Modo"):
        st.session_state["modo_acceso"] = None
        st.rerun()
    st.markdown("---")
    
    if st.session_state["modo_acceso"] == "terminal_porton":
        modo = "⚡ Registro de Asistencia"
        st.info("📱 Terminal de Asistencia Activa.")
    else:
        # En modo administración, fijamos la sección principal ya que ahora usamos solapas internas
        modo = "💻 Panel de Administración"

# --- LÓGICA DE PROCESAMIENTO DE MARCAJE ---
def procesar_codigo_qr(codigo_limpio):
    if not codigo_limpio:
        return
        
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

# --- MODO 1: REGISTRO DE ASISTENCIA (CÁMARA O TECLADO) ---
if modo == "⚡ Registro de Asistencia":
    st.title("⚡ Estación de Registro en Vivo")
    
    metodo_escaneo = st.radio("Seleccione método de lectura:", ["📷 Usar Cámara del Teléfono", "⌨️ Ingresar / Pistola USB"], horizontal=True)

    codigo_detectado = None

    if metodo_escaneo == "📷 Usar Cámara del Teléfono":
        st.write("Apunta con la cámara de tu teléfono hacia el código QR del carnet:")
        
        if st.button("🔄 Tomar nuevo registro"):
            st.session_state["cam_version"] += 1
            st.rerun()

        foto_qr = st.camera_input("Capturar Código QR", key=f"cam_{st.session_state['cam_version']}")
        
        if foto_qr is not None:
            bytes_data = foto_qr.getvalue()
            array_bytes = np.frombuffer(bytes_data, np.uint8)
            frame = cv2.imdecode(array_bytes, cv2.IMREAD_COLOR)
            
            detector = cv2.QRCodeDetector()
            val, points, straight_qrcode = detector.detectAndDecode(frame)
            
            if val:
                val_limpio = val.strip()
                if "id=" in val_limpio:
                    codigo_detectado = val_limpio.split("id=")[-1].split("&")[0].strip()
                else:
                    codigo_detectado = val_limpio
                    
                procesar_codigo_qr(codigo_detectado)
            else:
                st.warning("No se detectó ningún código QR claro en la foto. Intenta de nuevo enfocando mejor.")
    
    else:
        codigo_input = st.text_input("Escanee o ingrese el Código ID del carnet:", key="input_lector", placeholder="Pase el carnet aquí...")
        if codigo_input:
            procesar_codigo_qr(codigo_input.strip())

    st.markdown("---")
    st.subheader("Últimos marcajes de esta sesión:")
    db = conectar_bd()
    ultimos = consultar_sql(db, 'SELECT a.hora, a.tipo_registro, u.nombre, u.apellido, u.grado_seccion FROM asistencias a JOIN usuarios u ON a.codigo_id = u.codigo_id WHERE a.fecha = ? ORDER BY a.id DESC LIMIT 5', (datetime.now(ZoneInfo("America/Caracas")).strftime("%Y-%m-%d"),))
    if ultimos:
        df_ultimos = pd.DataFrame(ultimos, columns=["Hora", "Acción", "Nombre", "Apellido", "Grado"])
        st.dataframe(df_ultimos, use_container_width=True, hide_index=True)

# --- MODO 2: PANEL DE ADMINISTRACIÓN ---
elif modo == "💻 Panel de Administración":
    st.title("💻 Panel de Administración UEMES")
    
    # Pestañas organizadas para el administrador
    tab1, tab2, tab3 = st.tabs([
        "📊 Dashboard y Reportes", 
        "👥 Directorio General", 
        "🎓 Estudiantes por Grado y Personal"
    ])
    
    db = conectar_bd()
    
    with tab1:
        st.subheader("📊 Resumen y Exportación de Asistencia de Hoy")
        fecha_hoy = datetime.now(ZoneInfo("America/Caracas")).strftime("%Y-%m-%d")
        filas_hoy = consultar_sql(db, 'SELECT a.hora, a.tipo_registro, a.codigo_id, u.nombre, u.apellido, u.tipo_persona, u.grado_seccion FROM asistencias a JOIN usuarios u ON a.codigo_id = u.codigo_id WHERE a.fecha = ? ORDER BY a.hora DESC', (fecha_hoy,))
        df_hoy = pd.DataFrame(filas_hoy, columns=["Hora", "Registro", "Código", "Nombre", "Apellido", "Tipo", "Grado"]) if filas_hoy else pd.DataFrame()
        
        st.metric("Total Registros Hoy", len(df_hoy))
        if not df_hoy.empty:
            st.dataframe(df_hoy, use_container_width=True, hide_index=True)
            st.download_button("Descargar CSV del Día", df_hoy.to_csv(index=False).encode('utf-8'), f"asistencia_{fecha_hoy}.csv", "text/csv")
        else:
            st.info("No hay registros hoy en la base de datos.")

    with tab2:
        st.subheader("👥 Directorio Completo")
        filas_dir = consultar_sql(db, "SELECT codigo_id, nombre, apellido, tipo_persona, grado_seccion, funcion_cargo, email FROM usuarios")
        df_dir = pd.DataFrame(filas_dir, columns=["Código", "Nombre", "Apellido", "Rol", "Grado", "Cargo", "Correo"]) if filas_dir else pd.DataFrame()
        if not df_dir.empty:
            st.dataframe(df_dir, use_container_width=True, hide_index=True)
        else:
            st.info("Sin usuarios cargados.")

    with tab3:
        st.subheader("🎓 Listado por Grado, Sección y Personal")
        
        # Obtener grados/secciones y tipos de persona únicos disponibles
        filas_opciones = consultar_sql(db, "SELECT DISTINCT grado_seccion, tipo_persona FROM usuarios")
        if filas_opciones:
            grados_disponibles = sorted(list(set([f[0] for f in filas_opciones if f[0]])))
            tipos_disponibles = sorted(list(set([f[1] for f in filas_opciones if f[1]])))
            
            filtro_tipo = st.selectbox("Filtrar por tipo de persona:", ["Todos"] + tipos_disponibles)
            
            if filtro_tipo != "Todos":
                filas_filtradas = consultar_sql(db, "SELECT codigo_id, nombre, apellido, tipo_persona, grado_seccion, funcion_cargo, email FROM usuarios WHERE tipo_persona = ?", (filtro_tipo,))
            else:
                if grados_disponibles:
                    opcion_grado = st.selectbox("O filtrar por Grado/Sección específico:", ["Todos los Grados"] + grados_disponibles)
                    if opcion_grado != "Todos los Grados":
                        filas_filtradas = consultar_sql(db, "SELECT codigo_id, nombre, apellido, tipo_persona, grado_seccion, funcion_cargo, email FROM usuarios WHERE grado_seccion = ?", (opcion_grado,))
                    else:
                        filas_filtradas = consultar_sql(db, "SELECT codigo_id, nombre, apellido, tipo_persona, grado_seccion, funcion_cargo, email FROM usuarios")
                else:
                    filas_filtradas = consultar_sql(db, "SELECT codigo_id, nombre, apellido, tipo_persona, grado_seccion, funcion_cargo, email FROM usuarios")
            
            df_filtrado = pd.DataFrame(filas_filtradas, columns=["Código", "Nombre", "Apellido", "Rol", "Grado/Sección", "Cargo", "Correo"]) if filas_filtradas else pd.DataFrame()
            
            if not df_filtrado.empty:
                st.write(f"Mostrando **{len(df_filtrado)}** registros:")
                st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
                st.download_button("Descargar esta lista en CSV", df_filtrado.to_csv(index=False).encode('utf-8'), "listado_filtrado.csv", "text/csv")
            else:
                st.info("No se encontraron registros con los filtros seleccionados.")
        else:
            st.info("No hay datos de usuarios registrados en el sistema.")
