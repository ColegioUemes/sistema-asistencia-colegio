import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import libsql_client as libsql

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Sistema de Asistencia Escolar",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- URL BASE ACTIVA ---
URL_BASE = "https://sistema-asistencia-colegio-zjggkkwftvrnj2w9kkjvrg.streamlit.app"

# --- ESTILOS CSS PERSONALIZADOS ---
ESTILOS_MODERNOS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .stApp {
        background-color: #ffffff !important;
        font-family: 'Inter', sans-serif;
        color: #0f172a !important;
    }

    header[data-testid="stHeader"] {
        background-color: rgba(255, 255, 255, 0.8) !important;
        backdrop-filter: blur(8px);
        border-bottom: 1px solid #e2e8f0;
    }

    header[data-testid="stHeader"] button,
    header[data-testid="stHeader"] [data-testid="baseButton-header"],
    header[data-testid="stHeader"] svg {
        color: #475569 !important;
        fill: #475569 !important;
    }
    
    header[data-testid="stHeader"] button:hover,
    header[data-testid="stHeader"] [data-testid="baseButton-header"]:hover {
        background-color: #f1f5f9 !important;
        color: #0f172a !important;
    }
    
    header[data-testid="stHeader"] button:hover svg,
    header[data-testid="stHeader"] [data-testid="baseButton-header"]:hover svg {
        fill: #0f172a !important;
    }

    [data-testid="stSidebar"] {
        background-color: #1e293b !important;
        border-right: 1px solid #cbd5e1;
    }
    
    [data-testid="stSidebar"] * {
        color: #f1f5f9 !important;
    }

    [data-testid="stSidebar"] .stRadio label {
        font-size: 15px !important;
        font-weight: 500;
        padding: 6px 10px;
        border-radius: 6px;
        transition: background 0.2s;
    }
    
    [data-testid="stSidebar"] .stRadio label:hover {
        background-color: #334155 !important;
    }

    [data-testid="stSidebar"] div.stButton > button,
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        box-shadow: none !important;
    }
    
    [data-testid="stSidebar"] div.stButton > button p, 
    [data-testid="stSidebar"] div.stButton > button span {
        color: #f1f5f9 !important;
    }
    
    [data-testid="stSidebar"] div.stButton > button:hover,
    [data-testid="stSidebar"] div.stButton > button:active,
    [data-testid="stSidebar"] div.stButton > button:focus {
        background-color: #1e293b !important;
        border-color: #475569 !important;
        transform: none !important;
    }

    h1, h2, h3, h4 {
        color: #0f172a !important;
        font-weight: 700 !important;
    }
    p, label, span, div {
        color: #334155;
    }

    [data-testid="stMetric"] {
        background-color: #f1f5f9 !important;
        border: 1px solid #cbd5e1 !important;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }
    [data-testid="stMetricValue"] {
        color: #0f172a !important;
        font-weight: 800 !important;
        font-size: 1.8rem !important;
    }
    [data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
    }

    .stExpander {
        background-color: #f1f5f9 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 12px !important;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }

    div.stButton > button {
        width: 100% !important;
        height: 60px !important;
        background-color: #f1f5f9 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 10px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    }

    div.stButton > button p, div.stButton > button span {
        color: #0f172a !important;
        font-size: 15px !important;
        font-weight: 600 !important;
    }

    div.stButton > button:hover, 
    div.stButton > button:active, 
    div.stButton > button:focus {
        background-color: #f1f5f9 !important;
        border-color: #cbd5e1 !important;
        color: #0f172a !important;
        transform: none !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    }

    div.stButton > button[kind="primary"] {
        background: #0f172a !important;
        border: 1px solid #0f172a !important;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.2) !important;
    }
    
    div.stButton > button[kind="primary"] p, 
    div.stButton > button[kind="primary"] span {
        color: #ffffff !important;
    }

    div[data-testid="stForm"] div.stButton > button, div.stFormSubmitButton > button {
        background-color: #0f172a !important;
        border: 1px solid #0f172a !important;
        height: 50px !important;
    }
    
    div[data-testid="stForm"] div.stButton > button p, 
    div[data-testid="stForm"] div.stButton > button span {
        color: #ffffff !important;
    }

    div.stDownloadButton > button {
        background: #0f172a !important;
        border: none !important;
        border-radius: 10px !important;
        height: 50px !important;
        padding: 0px 24px !important;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
    }

    div.stDownloadButton > button p, div.stDownloadButton > button span {
        color: #ffffff !important;
        font-size: 15px !important;
        font-weight: 600 !important;
    }

    div.stDownloadButton > button:hover {
        background: #334155 !important;
        transform: translateY(-1px);
    }

    .stTextInput input, .stNumberInput input, .stSelectbox select {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
    }
</style>
"""

st.markdown(ESTILOS_MODERNOS, unsafe_allow_html=True)

# --- CONEXIÓN Y CONSULTAS A BASE DE DATOS (TURSO / SQLITE) ---
def conectar_bd():
    try:
        url = st.secrets["turso"]["url"]
        auth_token = st.secrets["turso"]["auth_token"]
        if url.startswith("libsql://"):
            url = url.replace("libsql://", "https://")
        client = libsql.create_client_sync(url=url, auth_token=auth_token)
        return client
    except Exception:
        return sqlite3.connect("colegio.db")

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
        # Si la conexión es de tipo Turso sync y soporta commit/sync explícito
        if hasattr(db, 'commit'):
            db.commit()
    except Exception as e:
        if "'result'" not in str(e):
            raise e

def inicializar_tablas():
    try:
        db = conectar_bd()
        ejecutar_sql(db, '''
            CREATE TABLE IF NOT EXISTS usuarios (
                codigo_id TEXT PRIMARY KEY,
                nombre TEXT,
                apellido TEXT,
                tipo_persona TEXT,
                grado_seccion TEXT,
                funcion_cargo TEXT,
                email TEXT
            )
        ''')
        ejecutar_sql(db, '''
            CREATE TABLE IF NOT EXISTS asistencias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_id TEXT,
                fecha TEXT,
                hora TEXT,
                tipo_registro TEXT,
                UNIQUE(codigo_id, fecha, tipo_registro)
            )
        ''')
        ejecutar_sql(db, '''
            CREATE TABLE IF NOT EXISTS notas_asistencia (
                asistencia_id INTEGER PRIMARY KEY,
                nota TEXT
            )
        ''')
    except Exception:
        pass

inicializar_tablas()

# --- FUNCIÓN DE ENVÍO DE CORREO ELECTRÓNICO ---
def enviar_correo_confirmacion(destinatario, nombre_completo, tipo_persona, grado, fecha, hora, tipo_registro):
    try:
        smtp_server = st.secrets["smtp"]["server"]
        smtp_port = st.secrets["smtp"]["port"]
        remitente = st.secrets["smtp"]["email"]
        password = st.secrets["smtp"]["password"]
    except Exception:
        smtp_server = st.session_state.get("smtp_server", "smtp.gmail.com")
        smtp_port = st.session_state.get("smtp_port", 587)
        remitente = st.session_state.get("smtp_email", "")
        password = st.session_state.get("smtp_password", "")

    if not remitente or not password:
        return False, "Credenciales SMTP no configuradas."

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Notificación de Asistencia Escolar ({tipo_registro}) - {nombre_completo}"
        msg["From"] = remitente
        msg["To"] = destinatario

        titulo_correo = f"Confirmación de {tipo_registro} Escolar"
        etiqueta_hora = f"Hora de {tipo_registro}"

        cuerpo_html = f"""
        <html>
          <body style="font-family: 'Inter', Arial, sans-serif; color: #1e293b; background-color: #f1f5f9; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #cbd5e1; border-radius: 12px; padding: 24px; background-color: #ffffff; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
              <h2 style="color: #0284c7; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px; margin-top: 0;">{titulo_correo}</h2>
              <p style="color: #475569;">Estimado/a representante o usuario,</p>
              <p style="color: #475569;">Se ha registrado un marcaje de asistencia con los siguientes detalles:</p>
              <ul style="line-height: 1.8; color: #334155;">
                <li><strong>Nombre:</strong> {nombre_completo}</li>
                <li><strong>Rol / Tipo:</strong> {tipo_persona}</li>
                <li><strong>Grado / Sección:</strong> {grado}</li>
                <li><strong>Fecha:</strong> {fecha}</li>
                <li><strong>{etiqueta_hora}:</strong> {hora}</li>
              </ul>
              <p style="font-size: 12px; color: #94a3b8; margin-top: 24px; border-top: 1px solid #f1f5f9; pt-2">Este es un mensaje automático enviado por el Sistema de Asistencia Escolar.</p>
            </div>
          </body>
        </html>
        """
        msg.attach(MIMEText(cuerpo_html, "html"))

        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(remitente, password)
        server.sendmail(remitente, destinatario, msg.as_string())
        server.quit()
        return True, "Correo enviado exitosamente."
    except Exception as e:
        return False, str(e)

# --- LÓGICA DE REGISTRO VÍA URL (ENTRADA / SALIDA) ---
query_params = st.query_params
if "id" in query_params:
    codigo_qr = query_params["id"]
    
    ahora_ve = datetime.now(ZoneInfo("America/Caracas"))
    fecha_hoy = ahora_ve.strftime("%Y-%m-%d")
    hora_actual = ahora_ve.strftime("%H:%M:%S")

    db = conectar_bd()
    filas_usr = consultar_sql(db, "SELECT nombre, apellido, tipo_persona, grado_seccion, email FROM usuarios WHERE codigo_id = ?", (codigo_qr,))
    usuario = filas_usr[0] if filas_usr else None

    if usuario:
        nombre, apellido, tipo_persona, grado, email_usuario = usuario[0], usuario[1], usuario[2], usuario[3], usuario[4]
        
        registros_hoy = consultar_sql(
            db, 
            "SELECT tipo_registro FROM asistencias WHERE codigo_id = ? AND fecha = ?", 
            (codigo_qr, fecha_hoy)
        )
        
        tipos_registrados = [r[0] for r in registros_hoy] if registros_hoy else []

        if "Entrada" not in tipos_registrados:
            tipo_movimiento = "Entrada"
        elif "Salida" not in tipos_registrados:
            tipo_movimiento = "Salida"
        else:
            tipo_movimiento = None

        if tipo_movimiento:
            try:
                ejecutar_sql(
                    db,
                    '''
                    INSERT INTO asistencias (codigo_id, fecha, hora, tipo_registro)
                    VALUES (?, ?, ?, ?)
                    ''',
                    (codigo_qr, fecha_hoy, hora_actual, tipo_movimiento)
                )

                st.success(f"¡{tipo_movimiento} registrada correctamente! Marcaje para {nombre} {apellido} ({tipo_persona} - {grado}) a las {hora_actual}.")

                if email_usuario:
                    exito, msg = enviar_correo_confirmacion(
                        destinatario=email_usuario,
                        nombre_completo=f"{nombre} {apellido}",
                        tipo_persona=tipo_persona,
                        grado=grado,
                        fecha=fecha_hoy,
                        hora=hora_actual,
                        tipo_registro=tipo_movimiento
                    )
                    if exito:
                        st.info(f"Se ha enviado una notificación de {tipo_movimiento.lower()} por correo a: {email_usuario}")
                    else:
                        st.warning(f"{tipo_movimiento} registrada, pero no se pudo enviar el correo ({msg}).")
                else:
                    st.caption("El usuario no tiene un correo electrónico asociado para notificaciones.")

            except Exception as e:
                st.error(f"Error al guardar la asistencia: {e}")
        else:
            st.warning(f"{nombre} {apellido}, ya registraste tanto tu ENTRADA como tu SALIDA para la jornada de hoy.")

    else:
        st.error(f"El código ID '{codigo_qr}' no está registrado en el sistema.")
    
    st.markdown("---")

# Variables de estado para navegación
if "grado_seleccionado" not in st.session_state:
    st.session_state["grado_seleccionado"] = "Inicial"

if "reporte_grado_sel" not in st.session_state:
    st.session_state["reporte_grado_sel"] = "Inicial"

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("Control Escolar")
    st.markdown("---")
    
    opcion = st.radio(
        "Menú Principal",
        ["Dashboard & Asistencias", "Directorio por Grados", "Exportar Reportes"]
    )

    st.markdown("---")
    with st.expander("Configuración Correo (SMTP)"):
        st.caption("Ajustes para envío automático:")
        st.session_state["smtp_server"] = st.text_input("Servidor SMTP", value=st.session_state.get("smtp_server", "smtp.gmail.com"))
        st.session_state["smtp_port"] = st.number_input("Puerto", value=st.session_state.get("smtp_port", 587))
        st.session_state["smtp_email"] = st.text_input("Correo Emisor", value=st.session_state.get("smtp_email", ""))
        st.session_state["smtp_password"] = st.text_input("Contraseña / App Pass", type="password", value=st.session_state.get("smtp_password", ""))

# --- SECCIÓN 1: DASHBOARD & ASISTENCIAS ---
if opcion == "Dashboard & Asistencias":
    st.title("Resumen de Asistencia Diaria")
    st.write("Monitoreo en tiempo real de entradas y salidas en el colegio.")
    
    fecha_hoy = datetime.now(ZoneInfo("America/Caracas")).strftime("%Y-%m-%d")
    
    db = conectar_bd()
    filas = consultar_sql(db, '''
        SELECT a.hora, a.tipo_registro, a.codigo_id, u.nombre, u.apellido, u.tipo_persona, u.grado_seccion, u.funcion_cargo 
        FROM asistencias a
        JOIN usuarios u ON a.codigo_id = u.codigo_id
        WHERE a.fecha = ?
        ORDER BY a.hora DESC
    ''', (fecha_hoy,))
    
    columnas = ["Hora", "Registro", "Código ID", "Nombre", "Apellido", "Tipo", "Grado", "Cargo / Función"]
    df_asistencias = pd.DataFrame(filas, columns=columnas) if filas else pd.DataFrame(columns=columnas)

    if not df_asistencias.empty:
        df_asistencias['Registro'] = df_asistencias['Registro'].astype(str).str.strip()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Marcajes Hoy", len(df_asistencias))
    with col2:
        entradas_hoy = len(df_asistencias[df_asistencias['Registro'] == 'Entrada']) if not df_asistencias.empty else 0
        st.metric("Total Entradas", entradas_hoy)
    with col3:
        salidas_hoy = len(df_asistencias[df_asistencias['Registro'] == 'Salida']) if not df_asistencias.empty else 0
        st.metric("Total Salidas", salidas_hoy)

    st.markdown("---")
    st.subheader("Últimos Movimientos Marcados Hoy")
    
    if not df_asistencias.empty:
        st.dataframe(df_asistencias, use_container_width=True, hide_index=True)
    else:
        st.info("Aún no hay registros de asistencia para la fecha de hoy.")

# --- SECCIÓN 2: DIRECTORIO POR GRADOS Y PERSONAL ---
elif opcion == "Directorio por Grados":
    st.title("Directorio por Grados y Personal")
    st.write("Seleccione una categoría para consultar y editar directamente en la tabla interactiva:")

    categorias = [
        ("Inicial", "Inicial"),
        ("1er Grado", "1ro"),
        ("2do Grado", "2do"),
        ("3er Grado", "3ro"),
        ("4to Grado", "4to"),
        ("5to Grado", "5to"),
        ("6to Grado", "6to"),
        ("Personal", "Personal")
    ]

    col1, col2, col3, col4 = st.columns(4)
    cols_f1 = [col1, col2, col3, col4]
    
    for idx, (label, clave) in enumerate(categorias[:4]):
        es_activo = (st.session_state["grado_seleccionado"] == clave)
        tipo_btn = "primary" if es_activo else "secondary"
        if cols_f1[idx].button(label, key=f"btn_{clave}", type=tipo_btn):
            st.session_state["grado_seleccionado"] = clave
            st.rerun()

    st.write("")

    col5, col6, col7, col8 = st.columns(4)
    cols_f2 = [col5, col6, col7, col8]
    
    for idx, (label, clave) in enumerate(categorias[4:]):
        es_activo = (st.session_state["grado_seleccionado"] == clave)
        tipo_btn = "primary" if es_activo else "secondary"
        if cols_f2[idx].button(label, key=f"btn_{clave}", type=tipo_btn):
            st.session_state["grado_seleccionado"] = clave
            st.rerun()

    st.markdown("---")

    cat_activa = st.session_state["grado_seleccionado"]
    db = conectar_bd()
    filas = consultar_sql(db, "SELECT codigo_id, nombre, apellido, tipo_persona, grado_seccion, funcion_cargo, email FROM usuarios")
    cols = ["codigo_id", "nombre", "apellido", "tipo_persona", "grado_seccion", "funcion_cargo", "email"]
    df_usuarios = pd.DataFrame(filas, columns=cols) if filas else pd.DataFrame(columns=cols)

    if cat_activa == "Personal":
        df_grupo = df_usuarios[df_usuarios["tipo_persona"] == "Personal"] if not df_usuarios.empty else df_usuarios
        titulo_seccion = "Personal de la Institución"
    else:
        df_grupo = df_usuarios[df_usuarios["grado_seccion"] == cat_activa] if not df_usuarios.empty else df_usuarios
        titulo_seccion = f"Lista de Alumnos: Grado {cat_activa}"

    st.subheader(f"{titulo_seccion} ({len(df_grupo)} asignados)")
    st.caption("💡 Puede editar cualquier celda haciendo doble clic sobre ella en la tabla inferior. Al finalizar, haga clic en el botón de guardar cambios dentro del formulario.")

    if not df_grupo.empty:
        df_tabla_limpia = df_grupo.rename(columns={
            "codigo_id": "Código ID", "nombre": "Nombre", "apellido": "Apellido",
            "tipo_persona": "Rol", "grado_seccion": "Grado", "funcion_cargo": "Cargo / Función",
            "email": "Correo Electrónico"
        })

        with st.form(key=f"form_editor_{cat_activa}"):
            df_editado = st.data_editor(
                df_tabla_limpia,
                use_container_width=True,
                hide_index=True,
                key=f"editor_{cat_activa}",
                disabled=["Código ID"]
            )

            submitted = st.form_submit_button("💾 Guardar Cambios Realizados")

            if submitted:
                db_save = conectar_bd()
                try:
                    for _, row in df_editado.iterrows():
                        ejecutar_sql(db_save, '''
                            UPDATE usuarios 
                            SET nombre = ?, apellido = ?, tipo_persona = ?, grado_seccion = ?, funcion_cargo = ?, email = ?
                            WHERE codigo_id = ?
                        ''', (
                            row["Nombre"], row["Apellido"], row["Rol"], 
                            row["Grado"], row["Cargo / Función"], row["Correo Electrónico"], 
                            row["Código ID"]
                        ))
                    st.success("¡Todos los cambios se han guardado exitosamente en la base de datos!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al actualizar los datos: {e}")
    else:
        st.info("No hay usuarios registrados en esta categoría.")

# --- SECCIÓN 3: EXPORTAR REPORTES POR GRADO Y GENERAL ---
elif opcion == "Exportar Reportes":
    st.title("Exportación de Reportes de Asistencia")
    st.write("Seleccione la fecha deseada para consultar, agregar notas en la tabla y descargar reportes:")

    col_fecha, _ = st.columns([1, 2])
    with col_fecha:
        fecha_sel = st.date_input("Seleccionar Fecha", datetime.now(ZoneInfo("America/Caracas")))

    st.write("")

    db = conectar_bd()
    filas = consultar_sql(db, '''
        SELECT a.id as ID_Asistencia, a.fecha as Fecha, a.hora as Hora, a.tipo_registro as Movimiento, a.codigo_id as Código, u.nombre as Nombre, u.apellido as Apellido, 
               u.tipo_persona as Rol, u.grado_seccion as Grado, u.funcion_cargo as Cargo, u.email as Correo, COALESCE(n.nota, '') as Notas 
        FROM asistencias a
        JOIN usuarios u ON a.codigo_id = u.codigo_id
        LEFT JOIN notas_asistencia n ON a.id = n.asistencia_id
        WHERE a.fecha = ?
        ORDER BY a.hora ASC
    ''', (fecha_sel.strftime("%Y-%m-%d"),))
    
    cols_exp = ["ID_Asistencia", "Fecha", "Hora", "Movimiento", "Código", "Nombre", "Apellido", "Rol", "Grado", "Cargo", "Correo", "Notas"]
    df_global = pd.DataFrame(filas, columns=cols_exp) if filas else pd.DataFrame(columns=cols_exp)

    df_global_vista = df_global.drop(columns=["ID_Asistencia"]) if not df_global.empty else df_global

    st.subheader(f"Reporte General Consolidado ({len(df_global_vista)} registros)")
    st.caption("💡 Haz doble clic en la columna **Notas**, escribe tus observaciones, haz clic en **Guardar Cambios** y tus datos quedarán almacenados permanentemente en Turso.")

    if not df_global.empty:
        with st.form(key="form_reporte_global"):
            df_global_editado = st.data_editor(
                df_global_vista,
                use_container_width=True,
                hide_index=True,
                key="editor_reporte_global",
                disabled=["Fecha", "Hora", "Movimiento", "Código", "Nombre", "Apellido", "Rol", "Grado", "Cargo", "Correo"]
            )
            
            btn_guardar_global = st.form_submit_button("💾 Guardar Cambios en Notas (General)")
            
            if btn_guardar_global:
                db_save = conectar_bd()
                try:
                    for idx, row in df_global_editado.iterrows():
                        asist_id = df_global.iloc[idx]["ID_Asistencia"]
                        nota_val = row["Notas"]
                        ejecutar_sql(db_save, '''
                            INSERT OR REPLACE INTO notas_asistencia (asistencia_id, nota)
                            VALUES (?, ?)
                        ''', (asist_id, nota_val))
                    st.success("¡Notas guardadas permanentemente en Turso con éxito!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar las notas en la base de datos: {e}")

        csv_global = df_global_editado.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label=f"Descargar Reporte COMPLETO en Excel (CSV) - {len(df_global_editado)} registros",
            data=csv_global,
            file_name=f"asistencia_GENERAL_{fecha_sel.strftime('%Y-%m-%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info(f"No hay registros generales para la fecha {fecha_sel.strftime('%Y-%m-%d')}.")

    st.markdown("---")
    st.subheader("Filtrar o Descargar por Grado Específico")

    categorias_rep = [
        ("Inicial", "Inicial"),
        ("1er Grado", "1ro"),
        ("2do Grado", "2do"),
        ("3er Grado", "3ro"),
        ("4to Grado", "4to"),
        ("5to Grado", "5to"),
        ("6to Grado", "6to"),
        ("Personal", "Personal")
    ]

    col1, col2, col3, col4 = st.columns(4)
    cols_f1 = [col1, col2, col3, col4]
    
    for idx, (label, clave) in enumerate(categorias_rep[:4]):
        es_activo = (st.session_state["reporte_grado_sel"] == clave)
        tipo_btn = "primary" if es_activo else "secondary"
        if cols_f1[idx].button(label, key=f"rep_btn_{clave}", type=tipo_btn):
            st.session_state["reporte_grado_sel"] = clave
            st.rerun()

    st.write("")

    col5, col6, col7, col8 = st.columns(4)
    cols_f2 = [col5, col6, col7, col8]
    
    for idx, (label, clave) in enumerate(categorias_rep[4:]):
        es_activo = (st.session_state["reporte_grado_sel"] == clave)
        tipo_btn = "primary" if es_activo else "secondary"
        if cols_f2[idx].button(label, key=f"rep_btn_{clave}", type=tipo_btn):
            st.session_state["reporte_grado_sel"] = clave
            st.rerun()

    st.markdown("---")

    cat_rep_activa = st.session_state["reporte_grado_sel"]

    db = conectar_bd()
    if cat_rep_activa == "Personal":
        filas = consultar_sql(db, '''
            SELECT a.id as ID_Asistencia, a.fecha as Fecha, a.hora as Hora, a.tipo_registro as Movimiento, a.codigo_id as Código, u.nombre as Nombre, u.apellido as Apellido, 
                   u.tipo_persona as Rol, u.grado_seccion as Grado, u.funcion_cargo as Cargo, u.email as Correo, COALESCE(n.nota, '') as Notas 
            FROM asistencias a
            JOIN usuarios u ON a.codigo_id = u.codigo_id
            LEFT JOIN notas_asistencia n ON a.id = n.asistencia_id
            WHERE a.fecha = ? AND u.tipo_persona = 'Personal'
            ORDER BY a.hora ASC
        ''', (fecha_sel.strftime("%Y-%m-%d"),))
        nombre_archivo = f"asistencia_Personal_{fecha_sel.strftime('%Y-%m-%d')}.csv"
        etiqueta_seccion = "Reporte de Asistencia: Personal"
    else:
        filas = consultar_sql(db, '''
            SELECT a.id as ID_Asistencia, a.fecha as Fecha, a.hora as Hora, a.tipo_registro as Movimiento, a.codigo_id as Código, u.nombre as Nombre, u.apellido as Apellido, 
                   u.tipo_persona as Rol, u.grado_seccion as Grado, u.funcion_cargo as Cargo, u.email as Correo, COALESCE(n.nota, '') as Notas 
            FROM asistencias a
            JOIN usuarios u ON a.codigo_id = u.codigo_id
            LEFT JOIN notas_asistencia n ON a.id = n.asistencia_id
            WHERE a.fecha = ? AND u.grado_seccion = ?
            ORDER BY a.hora ASC
        ''', (fecha_sel.strftime("%Y-%m-%d"), cat_rep_activa))
        nombre_archivo = f"asistencia_{cat_rep_activa}_{fecha_sel.strftime('%Y-%m-%d')}.csv"
        etiqueta_seccion = f"Reporte de Asistencia: Grado {cat_rep_activa}"

    df_export = pd.DataFrame(filas, columns=cols_exp) if filas else pd.DataFrame(columns=cols_exp)
    df_export_vista = df_export.drop(columns=["ID_Asistencia"]) if not df_export.empty else df_export

    st.write(f"**{etiqueta_seccion} ({len(df_export_vista)} marcajes registrados)**")

    if not df_export.empty:
        with st.form(key=f"form_reporte_{cat_rep_activa}"):
            df_export_editado = st.data_editor(
                df_export_vista,
                use_container_width=True,
                hide_index=True,
                key=f"editor_reporte_{cat_rep_activa}",
                disabled=["Fecha", "Hora", "Movimiento", "Código", "Nombre", "Apellido", "Rol", "Grado", "Cargo", "Correo"]
            )
            
            btn_guardar_grado = st.form_submit_button(f"💾 Guardar Cambios en Notas ({cat_rep_activa})")
            
            if btn_guardar_grado:
                db_save = conectar_bd()
                try:
                    for idx, row in df_export_editado.iterrows():
                        asist_id = df_export.iloc[idx]["ID_Asistencia"]
                        nota_val = row["Notas"]
                        ejecutar_sql(db_save, '''
                            INSERT OR REPLACE INTO notas_asistencia (asistencia_id, nota)
                            VALUES (?, ?)
                        ''', (asist_id, nota_val))
                    st.success(f"¡Notas para {cat_rep_activa} guardadas permanentemente en Turso con éxito!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar las notas en la base de datos: {e}")

        csv = df_export_editado.to_csv(index=False, encoding='utf-8-sig')
        
        st.download_button(
            label=f"Descargar Reporte ({cat_rep_activa}) en Excel (CSV)",
            data=csv,
            file_name=nombre_archivo,
            mime="text/csv"
        )
    else:
        st.info(f"No hay marcajes de asistencia registrados para {cat_rep_activa} en la fecha {fecha_sel.strftime('%Y-%m-%d')}.")
