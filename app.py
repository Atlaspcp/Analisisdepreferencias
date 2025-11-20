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

# Estilos CSS
st.markdown("""
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    .stMetric {background-color: #f9f9f9; padding: 15px; border-radius: 10px; border: 1px solid #e6e6e6;}
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE LÓGICA ---

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
    
    for nombre_display, info in datos_completos.items():
        clave = info['clave_busqueda']
        indegree[clave] = 0
        reverse_selections[clave] = []

    for nombre_origen, info in datos_completos.items():
        preferencias = info['data'].get("Seleccion_Jerarquica", {})
        for elegido, _ in preferencias.items():
            elegido_clave = elegido.upper().strip()
            
            if elegido_clave not in indegree:
                indegree[elegido_clave] = 0
                reverse_selections[elegido_clave] = []
            
            indegree[elegido_clave] += 1
            reverse_selections[elegido_clave].append(nombre_origen)
                    
    return indegree, reverse_selections

# --- CARGA DE DATOS ---
datos, lista_nombres = cargar_datos("datos")

if not datos:
    st.error("⚠️ No se encontraron datos.")
    st.stop()

indegree, reverse_selections = calcular_estadisticas(datos)

# --- LÓGICA DE NAVEGACIÓN (NUEVO) ---
# Función para cambiar el alumno cuando se hace clic en una tabla
def cambiar_alumno(nombre_nuevo):
    # Verificar si el nombre existe en la lista actual (por si hay filtros)
    if nombre_nuevo in lista_nombres:
        st.session_state["alumno_seleccionado_key"] = nombre_nuevo

# --- SIDEBAR ---
with st.sidebar:
    st.title("🧩 Configuración")
    st.markdown("---")
    
    cursos_disponibles = sorted(list(set(d['curso'] for d in datos.values() if d['curso'])))
    filtro_curso = st.multiselect("Filtrar Alumnos por Curso:", cursos_disponibles, default=cursos_disponibles)
    
    nombres_filtrados = [n for n in lista_nombres if datos[n]['curso'] in filtro_curso or not filtro_curso]
    
    st.markdown("### Selección")
    
    # IMPORTANTE: Agregamos 'key' para poder controlarlo desde el código
    if "alumno_seleccionado_key" not in st.session_state:
        st.session_state["alumno_seleccionado_key"] = nombres_filtrados[0] if nombres_filtrados else None

    # Asegurarnos de que el valor en session state sea válido para la lista filtrada
    if st.session_state["alumno_seleccionado_key"] not in nombres_filtrados and nombres_filtrados:
         st.session_state["alumno_seleccionado_key"] = nombres_filtrados[0]

    alumno_seleccionado = st.selectbox(
        "Buscar Alumno:", 
        nombres_filtrados,
        key="alumno_seleccionado_key" # Conectado al estado
    ) if nombres_filtrados else None
    
    st.markdown("---")
    limite_preferencias = st.slider("Nivel de afinidad (Top N):", 1, 10, 3)

# --- DASHBOARD PRINCIPAL ---

st.title("Análisis Sociométrico")

# Métricas
col_m1, col_m2, col_m3 = st.columns(3)
total_alumnos = len(nombres_filtrados)
promedio_selecciones = sum(indegree.values()) / len(indegree) if indegree else 0
max_seleccionado = max(indegree.values()) if indegree else 0

col_m1.metric("Total Alumnos (Visibles)", total_alumnos)
col_m2.metric("Promedio de Elecciones", f"{promedio_selecciones:.1f}")
col_m3.metric("Máximo de Elecciones", max_seleccionado)

st.markdown("---")

tab1, tab2 = st.tabs(["👤 Análisis Individual", "🏆 Ranking Global"])

# --- TAB 1: INDIVIDUAL ---
with tab1:
    if alumno_seleccionado:
        info = datos[alumno_seleccionado]
        clave_alumno_actual = info['clave_busqueda']
        
        st.subheader(f"Detalle: {alumno_seleccionado}")
        
        c1, c2 = st.columns(2)
        
        # IZQUIERDA: A QUIÉN ELIGIÓ
        with c1:
            st.markdown("#### 👉 Sus Preferencias (A quién eligió)")
            prefs = info['data'].get("Seleccion_Jerarquica", {})
            prefs_sorted = sorted(prefs.items(), key=lambda x: x[1])
            prefs_visible = [p for p in prefs_sorted if p[1] <= limite_preferencias]
            
            if prefs_visible:
                datos_tabla = []
                for nombre_elegido, ranking_otorgado in prefs_visible:
                    clave_elegido = nombre_elegido.upper().strip()
                    es_match = False
                    ranking_reciproco = None
                    
                    datos_compañero = None
                    for d in datos.values():
                        if d['clave_busqueda'] == clave_elegido:
                            datos_compañero = d
                            break
                    
                    if datos_compañero:
                        sus_preferencias = datos_compañero['data'].get("Seleccion_Jerarquica", {})
                        for k, v in sus_preferencias.items():
                            if k.upper().strip() == clave_alumno_actual:
                                es_match = True
                                ranking_reciproco = v
                                break
                    
                    nombre_mostrar = f"{nombre_elegido} ↔️ (Te eligió #{ranking_reciproco})" if es_match else nombre_elegido
                    
                    datos_tabla.append({
                        "Compañero": nombre_mostrar,
                        "Ranking": ranking_otorgado,
                        "Match": es_match,
                        "NombreReal": nombre_elegido # Guardamos el nombre limpio para la navegación
                    })
                
                df_prefs = pd.DataFrame(datos_tabla)
                
                def colorear_matches(row):
                    return ['background-color: #d4edda; color: #155724; font-weight: bold'] * len(row) if row["Match"] else [''] * len(row)

                st.dataframe(
                    df_prefs.style.apply(colorear_matches, axis=1),
                    column_config={"Match": None, "NombreReal": None},
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info(f"No tiene preferencias en el Top {limite_preferencias}.")

        # DERECHA: QUIÉN LO ELIGIÓ (INTERACTIVO)
        with c2:
            st.markdown("#### 👈 Seleccionado por (Quién lo eligió)")
            st.caption("💡 Haz clic en un nombre para ver su perfil")
            selectors = reverse_selections.get(clave_alumno_actual, [])
            
            if selectors:
                selectors = sorted(selectors)
                df_sel = pd.DataFrame(selectors, columns=["Compañero"])
                
                # CONFIGURACIÓN DE SELECCIÓN
                evento_seleccion = st.dataframe(
                    df_sel, 
                    use_container_width=True, 
                    hide_index=True, 
                    height=300,
                    on_select="rerun", # Recargar al seleccionar
                    selection_mode="single-row"
                )
                
                # LÓGICA DE CAMBIO DE PERFIL
                if evento_seleccion.selection.rows:
                    indice = evento_seleccion.selection.rows[0]
                    nombre_clic = df_sel.iloc[indice]["Compañero"]
                    cambiar_alumno(nombre_clic)
                    st.rerun() # Forzar recarga inmediata
                    
                st.success(f"Ha sido elegido por **{len(selectors)}** compañeros en total.")
            else:
                st.warning("Nadie ha seleccionado a este alumno todavía.")

# --- TAB 2: GLOBAL (INTERACTIVO) ---
with tab2:
    st.subheader("Ranking de Popularidad (Indegree)")
    st.caption("💡 Haz clic en una fila de la tabla inferior para ir al perfil del alumno.")
    
    data_global = []
    for nombre in nombres_filtrados:
        clave = datos[nombre]['clave_busqueda']
        total = int(indegree.get(clave, 0))
        curso = datos[nombre]['curso']
        data_global.append({"Alumno": nombre, "Veces Seleccionado": total, "Curso": curso})
    
    df_global = pd.DataFrame(data_global)
    
    if not df_global.empty:
        df_global = df_global.sort_values(by="Veces Seleccionado", ascending=True)
        
        # Gráfico (Visual solamente)
        fig = px.bar(
            df_global, 
            x="Veces Seleccionado", 
            y="Alumno", 
            orientation='h',
            color="Veces Seleccionado",
            color_continuous_scale="Blues",
            text="Veces Seleccionado",
            height=min(len(df_global) * 30 + 100, 800)
        )
        fig.update_layout(xaxis_title="", yaxis_title="", showlegend=False, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabla Interactiva para Navegación
        with st.expander("Ver tabla interactiva (Clic para navegar)", expanded=True):
            df_tabla_global = df_global.sort_values(by="Veces Seleccionado", ascending=False)
            
            evento_global = st.dataframe(
                df_tabla_global,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row"
            )
            
            if evento_global.selection.rows:
                indice = evento_global.selection.rows[0]
                nombre_clic = df_tabla_global.iloc[indice]["Alumno"]
                cambiar_alumno(nombre_clic)
                st.rerun()
    else:
        st.warning("No hay datos para mostrar.")
