import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import libsql_client as libsql

# Configuración de página
st.set_page_config(
    page_title="Sistema de Asistencia Escolar",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS
ESTILOS_AJUSTADOS = """
<style>
    /* Fondo principal */
    .stApp {
        background-color: #f8fafc;
        font-family: 'Segoe UI', Arial, sans-serif;
    }

    /* Barra superior (Header) en #E6F0FA */
    header[data-testid="stHeader"] {
        background-color: #E6F0FA !important;
    }

    /* Estilo del botón Deploy en la barra superior */
    header[data-testid="stHeader"] button {
        color: #00338D !important;
        font-weight: 700 !important;
    }

    /* Traducir texto visual de Deploy a Desplegar */
    header[data-testid="stHeader"] [data-testid="stHeaderActionElements"] button p {
        font-size: 0px !important;
    }
    header[data-testid="stHeader"] [data-testid="stHeaderActionElements"] button p::before {
        content: "Desplegar" !important;
        font-size: 14px !important;
        color: #00338D !important;
        font-weight: 700 !important;
    }
    
    /* Barra lateral azul marino */
    [data-testid="stSidebar"] {
        background-color: #00338D !important;
    }
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        font-size: 16px !important;
        font-weight: 500;
        padding: 8px;
    }

    /* Títulos principales */
    h1 {
        color: #0f172a !important;
        font-weight: 800 !important;
    }
    h2, h3, h4 {
        color: #00338D !important;
        font-weight: 700 !important;
    }
    p, label, span, div {
        color: #1e293b !important;
    }

    /* Tarjetas de métricas */
    [data-testid="stMetric"] {
        background-color: #E6F0FA !important;
        border: 1px solid #b3cde0 !important;
        padding: 16px 20px;
        border-radius: 10px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }
    [data-testid="stMetricValue"] {
        color: #00338D !important;
        font-weight: 800 !important;
    }

    /* Contenedores desplegables */
    .st-emotion-cache-1h9usn1, .stExpander {
        background-color: #E6F0FA !important;
        border: 1px solid #b3cde0 !important;
        border-radius: 8px !important;
    }
    
    /* Botones de grados */
    div.stButton > button {
        width: 100% !important;
        height: 80px !important;
        background-color: #00338D !important;
        border: none !important;
        border-radius: 10px !important;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }
    
    /* Texto blanco para botones estándar */
    div.stButton > button p, div.stButton > button span {
        color: #ffffff !important;
        font-size: 18px !important;
        font-weight: 700 !important;
    }

    /* Botón de Descarga Excel (st.download_button) */
    div.stDownloadButton > button {
        background-color: #00338D !important;
        border: none !important;
        border-radius: 8px !important;
        height: 50px !important;
        padding: 0px 24px !important;
        transition: all 0.2s ease-in-out;
    }

    div.stDownloadButton > button p, div.stDownloadButton > button span {
        color: #ffffff !important;
        font-size: 16px !important;
        font-weight: 700 !important;
    }

    div.stDownloadButton > button:hover {
        background-color: #002266 !important;
    }
    
    /* Hover en botones */
    div.stButton > button:hover {
        background-color: #002266 !important;
        transform: translateY(-2px);
    }

    /* Botón seleccionado (Azul más oscuro) */
    div.stButton > button[kind="primary"] {
        background-color: #001F54 !important;
        border: 2px solid #00338D !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
    }

    /* Tablas */
    .stDataFrame {
        background-color: #ffffff;
        border-radius: 8px;
        border: 1px solid #cbd5e1;
    }
</style>
"""

st.markdown(ESTILOS_AJUSTADOS, unsafe_allow_html=True)

# --- CONEXIÓN PERSISTENTE A BASE DE DATOS EN LA NUBE (TURSO) ---
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
    return res.fetchall()

def inicializar_tablas():
    try:
        db = conectar_bd()
        db.execute('''
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
        db.execute('''
            CREATE TABLE IF NOT EXISTS asistencias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_id TEXT,
                fecha TEXT,
                hora TEXT,
                tipo_registro TEXT,
                UNIQUE(codigo_id, fecha)
            )
        ''')
    except Exception:
        pass

inicializar_tablas()

# --- FUNCIÓN DE ENVÍO DE CORREO ELECTRÓNICO ---
def enviar_correo_confirmacion(destinatario, nombre_completo, tipo_persona, grado, fecha, hora):
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
        msg["Subject"] = f"Notificación de Asistencia Escolar - {nombre_completo}"
        msg["From"] = remitente
        msg["To"] = destinatario

        cuerpo_html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #1e293b;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #b3cde0; border-radius: 10px; padding: 20px; background-color: #f8fafc;">
              <h2 style="color: #00338D; border-bottom: 2px solid #00338D; padding-bottom: 8px;">Confirmación de Entrada Escolar</h2>
              <p>Estimado/a representante o usuario,</p>
              <p>Se ha registrado un marcaje de asistencia con los siguientes detalles:</p>
              <ul style="line-height: 1.8;">
                <li><strong>Nombre:</strong> {nombre_completo}</li>
                <li><strong>Rol / Tipo:</strong> {tipo_persona}</li>
                <li><strong>Grado / Sección:</strong> {grado}</li>
                <li><strong>Fecha:</strong> {fecha}</li>
                <li><strong>Hora de Entrada:</strong> {hora}</li>
              </ul>
              <p style="font-size: 12px; color: #64748b; margin-top: 20px;">Este es un mensaje automático enviado por el Sistema de Asistencia Escolar.</p>
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

# --- LÓGICA DE REGISTRO VÍA URL ---
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
        
        try:
            db.execute('''
                INSERT INTO asistencias (codigo_id, fecha, hora, tipo_registro)
                VALUES (?, ?, ?, ?)
            ''', (codigo_qr, fecha_hoy, hora_actual, 'Entrada'))
            st.success(f"¡Asistencia registrada correctamente! Marcaje para {nombre} {apellido} ({tipo_persona} - {grado}) a las {hora_actual}.")

            if email_usuario:
                exito, msg = enviar_correo_confirmacion(
                    destinatario=email_usuario,
                    nombre_completo=f"{nombre} {apellido}",
                    tipo_persona=tipo_persona,
                    grado=grado,
                    fecha=fecha_hoy,
                    hora=hora_actual
                )
                if exito:
                    st.info(f"📧 Se ha enviado una notificación por correo electrónico a: {email_usuario}")
                else:
                    st.warning(f"Asistencia registrada, pero no se pudo enviar el correo ({msg}).")
            else:
                st.caption("El usuario no tiene un correo electrónico asociado para notificaciones.")

        except Exception as e:
            if "UNIQUE" in str(e) or "IntegrityError" in str(e):
                st.warning(f"⚠️ {nombre} {apellido}, ya registraste tu asistencia para la jornada de hoy.")
            else:
                st.error(f"Error al guardar la asistencia: {e}")

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
    with st.expander("⚙️ Configuración Correo (SMTP)"):
        st.caption("Ajustes para envío automático de correos:")
        st.session_state["smtp_server"] = st.text_input("Servidor SMTP", value=st.session_state.get("smtp_server", "smtp.gmail.com"))
        st.session_state["smtp_port"] = st.number_input("Puerto", value=st.session_state.get("smtp_port", 587))
        st.session_state["smtp_email"] = st.text_input("Correo Emisor", value=st.session_state.get("smtp_email", ""))
        st.session_state["smtp_password"] = st.text_input("Contraseña / App Pass", type="password", value=st.session_state.get("smtp_password", ""))

# --- SECCIÓN 1: DASHBOARD & ASISTENCIAS ---
if opcion == "Dashboard & Asistencias":
    st.title("Resumen de Asistencia Diaria")
    st.write("Monitoreo en tiempo real de marcajes en la entrada del colegio.")
    
    fecha_hoy = datetime.now(ZoneInfo("America/Caracas")).strftime("%Y-%m-%d")
    
    db = conectar_bd()
    filas = consultar_sql(db, '''
        SELECT a.hora, a.codigo_id, u.nombre, u.apellido, u.tipo_persona, u.grado_seccion, u.funcion_cargo 
        FROM asistencias a
        JOIN usuarios u ON a.codigo_id = u.codigo_id
        WHERE a.fecha = ?
        ORDER BY a.hora DESC
    ''', (fecha_hoy,))
    
    columnas = ["Hora", "Código ID", "Nombre", "Apellido", "Tipo", "Grado", "Cargo / Función"]
    df_asistencias = pd.DataFrame(filas, columns=columnas) if filas else pd.DataFrame(columns=columnas)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Registrados Hoy", len(df_asistencias))
    with col2:
        alumnos_hoy = len(df_asistencias[df_asistencias['Tipo'] == 'Estudiante']) if not df_asistencias.empty else 0
        st.metric("Estudiantes Presentes", alumnos_hoy)
    with col3:
        personal_hoy = len(df_asistencias[df_asistencias['Tipo'] == 'Personal']) if not df_asistencias.empty else 0
        st.metric("Personal Presente", personal_hoy)

    st.markdown("---")
    st.subheader("Últimas Entradas Marcadas Hoy")
    
    if not df_asistencias.empty:
        st.dataframe(df_asistencias, use_container_width=True, hide_index=True)
    else:
        st.info("Aún no hay registros de asistencia para la fecha de hoy.")

# --- SECCIÓN 2: DIRECTORIO POR GRADOS Y PERSONAL ---
elif opcion == "Directorio por Grados":
    st.title("Directorio por Grados y Personal")
    st.write("Seleccione una categoría para consultar o editar la lista correspondiente:")

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

    with st.expander(f"Editar un usuario de esta categoría ({cat_activa})", expanded=False):
        if not df_grupo.empty:
            codigo_sel = st.selectbox(f"Seleccione el código a modificar:", df_grupo["codigo_id"].tolist(), key=f"select_{cat_activa}")
            usuario_actual = df_grupo[df_grupo["codigo_id"] == codigo_sel].iloc[0]

            with st.form(f"form_editar_{cat_activa}"):
                c1, c2 = st.columns(2)
                with c1:
                    nuevo_nombre = st.text_input("Nombre", value=usuario_actual["nombre"])
                    nuevo_apellido = st.text_input("Apellido", value=usuario_actual["apellido"])
                    tipo_persona = st.selectbox("Tipo", ["Estudiante", "Personal"], index=0 if usuario_actual["tipo_persona"] == "Estudiante" else 1)
                    nuevo_email = st.text_input("Correo Electrónico / Representante", value=usuario_actual["email"] if pd.notna(usuario_actual["email"]) else "")

                with c2:
                    grados_list = ["Inicial", "1ro", "2do", "3ro", "4to", "5to", "6to", "N/A"]
                    idx_grado = grados_list.index(usuario_actual["grado_seccion"]) if usuario_actual["grado_seccion"] in grados_list else 0
                    grado = st.selectbox("Grado", grados_list, index=idx_grado)
                    cargo = st.text_input("Función / Cargo", value=usuario_actual["funcion_cargo"])

                btn_guardar = st.form_submit_button("Guardar Cambios")

                if btn_guardar:
                    db = conectar_bd()
                    db.execute('''
                        UPDATE usuarios 
                        SET nombre = ?, apellido = ?, tipo_persona = ?, grado_seccion = ?, funcion_cargo = ?, email = ?
                        WHERE codigo_id = ?
                    ''', (nuevo_nombre, nuevo_apellido, tipo_persona, grado, cargo, nuevo_email, codigo_sel))
                    st.success(f"¡Datos actualizados para el código {codigo_sel}!")
                    st.rerun()
        else:
            st.write("No hay usuarios registrados en esta categoría.")

    if not df_grupo.empty:
        df_tabla_limpia = df_grupo.rename(columns={
            "codigo_id": "Código ID", "nombre": "Nombre", "apellido": "Apellido",
            "tipo_persona": "Rol", "grado_seccion": "Grado", "funcion_cargo": "Cargo / Función",
            "email": "Correo Electrónico"
        })
        st.dataframe(df_tabla_limpia, use_container_width=True, hide_index=True)

# --- SECCIÓN 3: EXPORTAR REPORTES POR GRADO Y GENERAL ---
elif opcion == "Exportar Reportes":
    st.title("Exportación de Reportes de Asistencia")
    st.write("Seleccione la fecha deseada para descargar reportes generales o filtrados por grado:")

    col_fecha, _ = st.columns([1, 2])
    with col_fecha:
        fecha_sel = st.date_input("Seleccionar Fecha", datetime.now(ZoneInfo("America/Caracas")))

    st.write("")

    db = conectar_bd()
    filas = consultar_sql(db, '''
        SELECT a.fecha as Fecha, a.hora as Hora, a.codigo_id as Código, u.nombre as Nombre, u.apellido as Apellido, 
               u.tipo_persona as Rol, u.grado_seccion as Grado, u.funcion_cargo as Cargo, u.email as Correo 
        FROM asistencias a
        JOIN usuarios u ON a.codigo_id = u.codigo_id
        WHERE a.fecha = ?
        ORDER BY a.hora ASC
    ''', (fecha_sel.strftime("%Y-%m-%d"),))
    
    cols_exp = ["Fecha", "Hora", "Código", "Nombre", "Apellido", "Rol", "Grado", "Cargo", "Correo"]
    df_global = pd.DataFrame(filas, columns=cols_exp) if filas else pd.DataFrame(columns=cols_exp)

    if not df_global.empty:
        csv_global = df_global.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label=f"Descargar Reporte COMPLETO (Todos los Grados y Personal) - {len(df_global)} registros",
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
            SELECT a.fecha as Fecha, a.hora as Hora, a.codigo_id as Código, u.nombre as Nombre, u.apellido as Apellido, 
                   u.tipo_persona as Rol, u.grado_seccion as Grado, u.funcion_cargo as Cargo, u.email as Correo 
            FROM asistencias a
            JOIN usuarios u ON a.codigo_id = u.codigo_id
            WHERE a.fecha = ? AND u.tipo_persona = 'Personal'
            ORDER BY a.hora ASC
        ''', (fecha_sel.strftime("%Y-%m-%d"),))
        nombre_archivo = f"asistencia_Personal_{fecha_sel.strftime('%Y-%m-%d')}.csv"
        etiqueta_seccion = "Reporte de Asistencia: Personal"
    else:
        filas = consultar_sql(db, '''
            SELECT a.fecha as Fecha, a.hora as Hora, a.codigo_id as Código, u.nombre as Nombre, u.apellido as Apellido, 
                   u.tipo_persona as Rol, u.grado_seccion as Grado, u.funcion_cargo as Cargo, u.email as Correo 
            FROM asistencias a
            JOIN usuarios u ON a.codigo_id = u.codigo_id
            WHERE a.fecha = ? AND u.grado_seccion = ?
            ORDER BY a.hora ASC
        ''', (fecha_sel.strftime("%Y-%m-%d"), cat_rep_activa))
        nombre_archivo = f"asistencia_{cat_rep_activa}_{fecha_sel.strftime('%Y-%m-%d')}.csv"
        etiqueta_seccion = f"Reporte de Asistencia: Grado {cat_rep_activa}"

    df_export = pd.DataFrame(filas, columns=cols_exp) if filas else pd.DataFrame(columns=cols_exp)

    st.write(f"**{etiqueta_seccion} ({len(df_export)} marcajes registrados)**")

    if not df_export.empty:
        st.dataframe(df_export, use_container_width=True, hide_index=True)
        csv = df_export.to_csv(index=False, encoding='utf-8-sig')
        
        st.download_button(
            label=f"Descargar Reporte ({cat_rep_activa}) en Excel (CSV)",
            data=csv,
            file_name=nombre_archivo,
            mime="text/csv"
        )
    else:
        st.info(f"No hay marcajes de asistencia registrados para {cat_rep_activa} en la fecha {fecha_sel.strftime('%Y-%m-%d')}.")
