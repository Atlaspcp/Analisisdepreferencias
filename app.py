import streamlit as st
import json
import os
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="Visor de Sociograma",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FUNCIONES DE LÓGICA (Tu lógica original adaptada) ---

@st.cache_data # Esto hace que no recargue los datos cada vez que tocas un botón, es muy rápido
def cargar_datos(ruta_base="datos"):
    """Carga todos los JSONs de la carpeta y subcarpetas."""
    datos_completos = {}
    lista_nombres = []
    
    if not os.path.exists(ruta_base):
        return {}, []

    for root, dirs, files in os.walk(ruta_base):
        for file in files:
            if file.endswith(".json"):
                ruta_completa = os.path.join(root, file)
                try:
                    with open(ruta_completa, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Crear un nombre único incluyendo el curso si está disponible
                        nombre = data.get("Nombre", "Desconocido").strip()
                        curso = data.get("Curso", "")
                        if curso:
                            nombre_display = f"{nombre} ({curso})"
                        else:
                            nombre_display = nombre
                            
                        # Normalizar clave para búsquedas internas
                        clave = nombre.upper().strip() 
                        
                        datos_completos[nombre_display] = {
                            "ruta": ruta_completa,
                            "data": data,
                            "clave_busqueda": clave
                        }
                        lista_nombres.append(nombre_display)
                except Exception as e:
                    st.error(f"Error leyendo {file}: {e}")
    
    return datos_completos, sorted(lista_nombres)

@st.cache_data
def calcular_estadisticas(datos_completos):
    """Calcula quién eligió a quién (Reverse Selections) y conteos."""
    indegree = {} # Cuántas veces fue elegido
    reverse_selections = {} # Quiénes lo eligieron
    
    # Inicializar
    for nombre_display, info in datos_completos.items():
        clave = info['clave_busqueda']
        indegree[clave] = 0
        reverse_selections[clave] = []

    # Calcular
    for nombre_origen, info in datos_completos.items():
        preferencias = info['data'].get("Seleccion_Jerarquica", {})
        for elegido, _ in preferencias.items():
            elegido_clave = elegido.upper().strip()
            
            # Si el elegido está en nuestra base de datos
            # (Buscamos la clave en las claves existentes)
            if elegido_clave in indegree:
                indegree[elegido_clave] += 1
                reverse_selections[elegido_clave].append(nombre_origen)
            else:
                # Caso: Alguien fue votado pero no tiene archivo JSON propio (ausente/error)
                if elegido_clave not in indegree:
                    indegree[elegido_clave] = 1
                    reverse_selections[elegido_clave] = [nombre_origen]
                else:
                    indegree[elegido_clave] += 1
                    reverse_selections[elegido_clave].append(nombre_origen)
                    
    return indegree, reverse_selections

# --- INTERFAZ DE USUARIO ---

st.title("📊 Resultados Sociograma")
st.markdown("Visualización consolidada de cursos.")

# 1. Cargar datos
# Asegúrate de que la carpeta 'datos' exista junto a este archivo app.py
datos, lista_nombres = cargar_datos("datos")

if not datos:
    st.warning("⚠️ No se encontraron datos. Asegúrate de subir la carpeta 'datos' al repositorio.")
    st.stop()

indegree, reverse_selections = calcular_estadisticas(datos)

# 2. Sidebar (Controles)
with st.sidebar:
    st.header("🔍 Filtros")
    
    # Selector de Alumno
    alumno_seleccionado = st.selectbox(
        "Seleccionar Alumno:",
        lista_nombres
    )
    
    # Filtro de límite (Spinbox)
    st.markdown("---")
    limite_preferencias = st.number_input(
        "Destacar hasta preferencia #:",
        min_value=1,
        max_value=20,
        value=1
    )
    
    st.info("Usa el menú superior derecho para cambiar el tema (Claro/Oscuro).")

# 3. Mostrar Datos del Alumno
if alumno_seleccionado:
    info_alumno = datos[alumno_seleccionado]
    data_alumno = info_alumno['data']
    clave_alumno = info_alumno['clave_busqueda']
    
    st.header(f"👤 {alumno_seleccionado}")
    
    col1, col2 = st.columns(2)
    
    # COLUMNA 1: A quién eligió el alumno
    with col1:
        st.subheader("Sus Preferencias (Eligió a):")
        prefs = data_alumno.get("Seleccion_Jerarquica", {})
        
        # Ordenar por jerarquía
        prefs_ordenadas = sorted(prefs.items(), key=lambda x: x[1])
        
        if prefs_ordenadas:
            df_prefs = pd.DataFrame(prefs_ordenadas, columns=["Compañero", "Ranking"])
            
            # Función para resaltar filas
            def resaltar_top(row):
                color = '#d1ecf1' if row['Ranking'] <= limite_preferencias else ''
                return [f'background-color: {color}' for _ in row]

            st.dataframe(
                df_prefs.style.apply(resaltar_top, axis=1),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No hay preferencias registradas.")

    # COLUMNA 2: Quién eligió al alumno
    with col2:
        st.subheader("Seleccionado por (Lo eligieron):")
        seleccionadores = reverse_selections.get(clave_alumno, [])
        
        if seleccionadores:
            df_sel = pd.DataFrame(sorted(seleccionadores), columns=["Compañero"])
            st.dataframe(df_sel, use_container_width=True, hide_index=True)
            st.metric("Total de elecciones recibidas", len(seleccionadores))
        else:
            st.write("Nadie seleccionó a este alumno.")

# 4. Estadísticas Globales (Tabla general)
st.markdown("---")
st.header("📈 Estadísticas Globales (Ranking)")

# Crear tabla para mostrar todos
tabla_global = []
for nombre in lista_nombres:
    clave = datos[nombre]['clave_busqueda']
    total = indegree.get(clave, 0)
    tabla_global.append({"Alumno": nombre, "Veces Seleccionado": total})

df_global = pd.DataFrame(tabla_global)

# Streamlit permite ordenar haciendo clic en la columna, ¡así que no necesitamos botones de ordenar!
st.dataframe(
    df_global,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Veces Seleccionado": st.column_config.ProgressColumn(
            "Veces Seleccionado",
            help="Cantidad de compañeros que lo eligieron",
            format="%d",
            min_value=0,
            max_value=df_global["Veces Seleccionado"].max()
        )
    }
)
