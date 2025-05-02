import streamlit as st
import sqlite3
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="CRUD App", layout="wide")
st.title("Sistema de Gestión de Registros")

# Crear o conectar a la base de datos
def init_db():
    conn = sqlite3.connect('registros.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS registros
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nombre TEXT NOT NULL,
                  identificacion TEXT NOT NULL UNIQUE)''')
    conn.commit()
    conn.close()

# Inicializar la base de datos
init_db()

# Función para agregar un registro
def agregar_registro(nombre, identificacion):
    try:
        conn = sqlite3.connect('registros.db')
        c = conn.cursor()
        c.execute("INSERT INTO registros (nombre, identificacion) VALUES (?, ?)",
                  (nombre, identificacion))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

# Función para obtener todos los registros
def obtener_registros():
    conn = sqlite3.connect('registros.db')
    df = pd.read_sql_query("SELECT * FROM registros", conn)
    conn.close()
    return df

# Función para buscar registros por nombre, identificación o ID
def buscar_registros(termino_busqueda, tipo_busqueda):
    conn = sqlite3.connect('registros.db')
    c = conn.cursor()
    query = "SELECT * FROM registros WHERE"

    if tipo_busqueda == "Nombre":
        c.execute(f"{query} nombre LIKE ?", ('%' + termino_busqueda + '%',))
    elif tipo_busqueda == "Identificación":
        c.execute(f"{query} identificacion = ?", (termino_busqueda,))
    elif tipo_busqueda == "ID":
         try:
             id_busqueda = int(termino_busqueda)
             c.execute(f"{query} id = ?", (id_busqueda,))
         except ValueError:
             conn.close()
             return pd.DataFrame()

    rows = c.fetchall()
    conn.close()

    if rows:
        cols = [description[0] for description in c.description]
        df = pd.DataFrame(rows, columns=cols)
        return df
    else:
        return pd.DataFrame()

# Función para actualizar un registro
def actualizar_registro(id, nombre, identificacion):
    try:
        conn = sqlite3.connect('registros.db')
        c = conn.cursor()
        c.execute("UPDATE registros SET nombre = ?, identificacion = ? WHERE id = ?",
                  (nombre, identificacion, id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

# Función para eliminar un registro(s) por ID, nombre o identificación
def eliminar_registro(criterio, tipo_criterio):
    conn = sqlite3.connect('registros.db')
    c = conn.cursor()

    if tipo_criterio == "ID":
        try:
            id_eliminar = int(criterio)
            c.execute("DELETE FROM registros WHERE id = ?", (id_eliminar,))
            deleted_count = c.rowcount
        except ValueError:
             deleted_count = 0
    elif tipo_criterio == "Nombre":
        c.execute("DELETE FROM registros WHERE nombre = ?", (criterio,))
        deleted_count = c.rowcount
    elif tipo_criterio == "Identificación":
        c.execute("DELETE FROM registros WHERE identificacion = ?", (criterio,))
        deleted_count = c.rowcount

    conn.commit()
    conn.close()
    return deleted_count > 0

# Interfaz de usuario con Streamlit
st.sidebar.header("Operaciones")
operacion = st.sidebar.selectbox(
    "Seleccione una operación",
    ["Crear", "Leer", "Actualizar", "Eliminar"]
)

if operacion == "Crear":
    st.header("Crear Nuevo Registro")
    nombre = st.text_input("Nombre")
    identificacion = st.text_input("Identificación")
    if st.button("Agregar"):
        if nombre and identificacion:
            if agregar_registro(nombre, identificacion):
                st.success("Registro agregado exitosamente!")
            else:
                st.error("Error: La identificación ya existe en la base de datos")
        else:
            st.warning("Por favor complete todos los campos")

elif operacion == "Leer":
    st.header("Buscar y Ver Registros")

    termino_busqueda = st.text_input("Ingrese término de búsqueda")
    tipo_busqueda = st.selectbox("Buscar por", ["Nombre", "Identificación", "ID"])

    if termino_busqueda:
        df = buscar_registros(termino_busqueda, tipo_busqueda)
        if not df.empty:
            st.dataframe(df)
        else:
            st.info("No se encontraron registros que coincidan con la búsqueda.")
    else:
        st.info("Mostrando todos los registros. Ingrese un término para buscar.")
        df = obtener_registros()
        if not df.empty:
            st.dataframe(df)
        else:
            st.info("No hay registros en la base de datos.")


elif operacion == "Actualizar":
    st.header("Actualizar Registro")
    df = obtener_registros()
    if not df.empty:
        registro_a_actualizar_id = st.selectbox(
            "Seleccione el ID del registro a actualizar",
            df['id'].tolist()
        )

        registro = df[df['id'] == registro_a_actualizar_id].iloc[0]

        nuevo_nombre = st.text_input("Nuevo nombre", value=registro['nombre'])
        nueva_identificacion = st.text_input("Nueva identificación", value=registro['identificacion'])

        if st.button("Actualizar"):
            if nuevo_nombre and nueva_identificacion:
                if actualizar_registro(registro_a_actualizar_id, nuevo_nombre, nueva_identificacion):
                    st.success(f"Registro con ID {registro_a_actualizar_id} actualizado exitosamente!")
                else:
                    st.error(f"Error: La identificación '{nueva_identificacion}' ya existe en la base de datos")
            else:
                st.warning("Por favor complete todos los campos")
    else:
        st.info("No hay registros para actualizar")

elif operacion == "Eliminar":
    st.header("Eliminar Registro")

    df = obtener_registros()
    if not df.empty:
        criterio_eliminar = st.text_input("Ingrese el valor para buscar (ID, Nombre o Identificación)")
        tipo_criterio_eliminar = st.selectbox("Buscar para eliminar por", ["ID", "Nombre", "Identificación"])

        # Botón para buscar registros que coinciden antes de eliminar
        if st.button("Buscar para eliminar"):
             if criterio_eliminar:
                 df_a_eliminar = buscar_registros(criterio_eliminar, tipo_criterio_eliminar)
                 if not df_a_eliminar.empty:
                     st.session_state['registros_encontrados'] = df_a_eliminar # Guardar en estado de sesión
                     st.warning("Se encontraron los siguientes registros que coinciden:")
                     st.dataframe(df_a_eliminar)
                 else:
                     st.info("No se encontraron registros que coincidan con el criterio de búsqueda.")
                     st.session_state['registros_encontrados'] = pd.DataFrame() # Limpiar estado si no se encuentra nada
             else:
                 st.warning("Por favor ingrese el valor para buscar.")
                 st.session_state['registros_encontrados'] = pd.DataFrame() # Limpiar estado

        # Si hay registros encontrados en el estado de la sesión, mostrar el botón de confirmación
        if 'registros_encontrados' in st.session_state and not st.session_state['registros_encontrados'].empty:
            st.warning("¿Está seguro de que desea eliminar los registros mostrados arriba?")
            if st.button("Confirmar Eliminación"):
                # Usar los valores que generaron la búsqueda para eliminar
                if eliminar_registro(criterio_eliminar, tipo_criterio_eliminar):
                    st.success("Registro(s) eliminado(s) exitosamente!")
                    st.session_state['registros_encontrados'] = pd.DataFrame() # Limpiar estado después de eliminar
                    st.rerun() # Recargar para mostrar la tabla actualizada
                else:
                    st.error("Hubo un error al intentar eliminar los registros.")
                    st.session_state['registros_encontrados'] = pd.DataFrame() # Limpiar estado en caso de error
    else:
        st.info("No hay registros para eliminar")