import sqlite3
import streamlit as st

# ... (tu código previo de conexión)

# Capturar parámetro de la URL (?id=...)
query_params = st.query_params
codigo_qr = query_params.get("id", None)

if codigo_qr:
    conn = sqlite3.connect("colegio.db")
    cursor = conn.cursor()

    # 1. Verificar si el usuario existe
    cursor.execute("SELECT nombre, apellido FROM usuarios WHERE codigo_id = ?", (codigo_qr,))
    usuario = cursor.fetchone()

    if usuario:
        nombre, apellido = usuario
        try:
            # 2. Intentar registrar la asistencia
            cursor.execute('''
                INSERT INTO asistencias (codigo_id, fecha, hora)
                VALUES (?, DATE('now'), TIME('now'))
            ''', (codigo_qr,))
            conn.commit()
            
            st.success(f"✅ ¡Asistencia registrada con éxito para {nombre} {apellido}!")
            # Aquí va tu función de envío de correo SMTP
            
        except sqlite3.IntegrityError:
            st.warning(f"⚠️ {nombre} {apellido}, tu asistencia ya fue registrada anteriormente.")
        except Exception as e:
            st.error(f"Error al registrar asistencia: {e}")
    else:
        st.error("❌ Código QR no válido o usuario no encontrado en el sistema.")

    conn.close()
