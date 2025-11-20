import streamlit as st
import json
import os
import pandas as pd
import plotly.express as px

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Sociograma Digital",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para limpiar la interfaz
st.markdown("""
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    .stMetric {background-color: #f9f9f9; padding: 15px; border-radius: 10px; border: 1px solid #e6e6e6;}
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE LÓGICA (Optimizadas) ---

@st.cache_data
def cargar_datos(ruta_base="datos"):
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
                        nombre = data.get("Nombre", "Desconocido").strip()
                        curso = data.get("Curso", "")
                        nombre_display = f"{nombre} ({curso})" if curso else nombre
                        clave = nombre.upper().strip()
                        
                        datos_completos[nombre_display] = {
                            "ruta": ruta_completa,
                            "data": data,
                            "clave_busqueda": clave,
                            "curso": curso
                        }
                        lista_nombres.append(nombre_display)
                except Exception:
                    continue
    
    return datos_completos, sorted(lista_nombres)

@st.cache_data
def calcular_estadisticas(datos_completos):
    indegree = {} 
    reverse_selections = {}
    
    # Inicializar con ceros para todos los alumnos cargados
    for nombre_display, info in datos_completos.items():
        clave = info['clave_busqueda']
        indegree[clave] = 0
        reverse_selections[clave] = []

    # Calcular votos
    for nombre_origen, info in datos_completos.items():
        preferencias = info['data'].get("Seleccion_Jerarquica", {})
        for elegido, _ in preferencias.items():
            elegido_clave = elegido.upper().strip()
            
            # Si la clave existe (sea cargada o externa)
            if elegido_clave not in indegree:
                indegree[elegido_clave] = 0
                reverse_selections[elegido_clave] = []
            
            indegree[elegido_clave] += 1
            reverse_selections[elegido_clave].append(nombre_origen)
                    
    return indegree, reverse_selections

# --- CARGA DE DATOS ---
datos, lista_nombres = cargar_datos("datos")

if not datos:
    st.error("⚠️ No se encontraron datos. Verifica la carpeta en GitHub.")
    st.stop()

indegree, reverse_selections = calcular_estadisticas(datos)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🧩 Configuración")
    st.markdown("---")
    
    # Filtro por Curso (Nuevo!)
    cursos_disponibles = sorted(list(set(d['curso'] for d in datos.values() if d['curso'])))
    filtro_curso = st.multiselect("Filtrar Alumnos por Curso:", cursos_disponibles, default=cursos_disponibles)
    
    # Filtrar lista de nombres basada en curso
    nombres_filtrados = [n for n in lista_nombres if datos[n]['curso'] in filtro_curso or not filtro_curso]
    
    st.markdown("### Selección")
    alumno_seleccionado = st.selectbox("Buscar Alumno:", nombres_filtrados) if nombres_filtrados else None
    
    st.markdown("---")
    limite_preferencias = st.slider("Nivel de afinidad (Top N):", 1, 10, 3)
    st.caption("Define cuántas preferencias mostrar en las tablas.")

# --- DASHBOARD PRINCIPAL ---

st.title("Análisis Sociométrico")
st.markdown("Visión consolidada de las interacciones entre estudiantes.")

# Métricas Superiores
col_m1, col_m2, col_m3 = st.columns(3)
total_alumnos = len(nombres_filtrados)
promedio_selecciones = sum(indegree.values()) / len(indegree) if indegree else 0
max_seleccionado = max(indegree.values()) if indegree else 0

col_m1.metric("Total Alumnos (Visibles)", total_alumnos)
col_m2.metric("Promedio de Elecciones", f"{promedio_selecciones:.1f}")
col_m3.metric("Máximo de Elecciones", max_seleccionado)

st.markdown("---")

# PESTAÑAS PARA ORGANIZAR
tab1, tab2 = st.tabs(["👤 Análisis Individual", "🏆 Ranking Global"])

# --- TAB 1: INDIVIDUAL ---
with tab1:
    if alumno_seleccionado:
        info = datos[alumno_seleccionado]
        clave = info['clave_busqueda']
        
        st.subheader(f"Detalle: {alumno_seleccionado}")
        
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("#### 👉 Sus Preferencias (A quién eligió)")
            prefs = info['data'].get("Seleccion_Jerarquica", {})
            prefs_sorted = sorted(prefs.items(), key=lambda x: x[1])
            
            # Filtrar hasta el limite seleccionado en sidebar
            prefs_visible = [p for p in prefs_sorted if p[1] <= limite_preferencias]
            
            if prefs_visible:
                df_prefs = pd.DataFrame(prefs_visible, columns=["Compañero", "Ranking"])
                st.table(df_prefs) # st.table es más limpio visualmente para listas cortas
            else:
                st.info(f"No tiene preferencias en el Top {limite_preferencias}.")

        with c2:
            st.markdown("#### 👈 Seleccionado por (Quién lo eligió)")
            selectors = reverse_selections.get(clave, [])
            
            if selectors:
                df_sel = pd.DataFrame(selectors, columns=["Compañero"])
                st.dataframe(df_sel, use_container_width=True, hide_index=True, height=300)
                st.success(f"Ha sido elegido por **{len(selectors)}** compañeros en total.")
            else:
                st.warning("Nadie ha seleccionado a este alumno todavía.")
    else:
        st.info("Selecciona un curso y un alumno en el menú lateral.")

# --- TAB 2: GLOBAL (CORREGIDO Y MEJORADO) ---
with tab2:
    st.subheader("Ranking de Popularidad (Indegree)")
    
    # 1. Crear DataFrame Global con tipos de datos seguros
    data_global = []
    for nombre in nombres_filtrados:
        clave = datos[nombre]['clave_busqueda']
        # Forzamos que sea entero (int) para evitar el TypeError
        total = int(indegree.get(clave, 0))
        curso = datos[nombre]['curso']
        data_global.append({
            "Alumno": nombre, 
            "Veces Seleccionado": total,
            "Curso": curso
        })
    
    df_global = pd.DataFrame(data_global)
    
    if not df_global.empty:
        # Ordenar para el gráfico
        df_global = df_global.sort_values(by="Veces Seleccionado", ascending=True) # Ascending para que Plotly lo ponga arriba
        
        # 2. Gráfico de Barras con Plotly (Mucho más moderno que la tabla anterior)
        fig = px.bar(
            df_global, 
            x="Veces Seleccionado", 
            y="Alumno", 
            orientation='h',
            color="Veces Seleccionado",
            color_continuous_scale="Blues",
            text="Veces Seleccionado",
            height=min(len(df_global) * 30 + 100, 800) # Altura dinámica
        )
        
        fig.update_layout(
            xaxis_title="Cantidad de Elecciones",
            yaxis_title="",
            showlegend=False,
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 3. Tabla de datos crudos (Opcional, abajo, por si quieren copiar)
        with st.expander("Ver tabla de datos completa"):
            st.dataframe(
                df_global.sort_values(by="Veces Seleccionado", ascending=False),
                use_container_width=True,
                hide_index=True
            )
    else:
        st.warning("No hay datos para mostrar con los filtros actuales.")
