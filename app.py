import streamlit as st
import json
import os
import pandas as pd
import plotly.express as px
from datetime import datetime

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
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
#      SISTEMA DE LOGIN Y PERMISOS
# ==========================================

# 1. LISTA DE USUARIOS PERMITIDOS (Total 5)
USUARIOS_PERMITIDOS = [
    "EROS",  # <--- Digamos que este será el JEFE
    "Annia",
    "Diego",
    "Camila",
    "Mauricio"
]

# 2. DEFINIR QUIÉN ES EL ADMINISTRADOR
# (Debe ser uno de los nombres de la lista de arriba, en MAYÚSCULAS)
USUARIO_ADMIN = "EROS"

def registrar_ingreso(nombre_usuario):
    """Guarda el historial de quién entró."""
    archivo_log = "historial_accesos.csv"
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    nueva_linea = {
        "Fecha_Hora": [ahora],
        "Usuario": [nombre_usuario]
    }
    df_nuevo = pd.DataFrame(nueva_linea)

    if not os.path.exists(archivo_log):
        df_nuevo.to_csv(archivo_log, index=False)
    else:
        df_nuevo.to_csv(archivo_log, mode='a', header=False, index=False)

def normalizar_texto(texto):
    """Quita espacios y convierte a mayúsculas."""
    if not texto: return ""
    return texto.strip().upper()

def pantalla_login():
    st.markdown("## 🔒 Acceso Restringido")
    st.markdown("Por favor, ingrese su **Nombre de Usuario** para acceder.")

    col1, col2 = st.columns([1, 2])
    with col1:
        user_input = st.text_input("Usuario:")
        boton_entrar = st.button("Ingresar")

    if boton_entrar:
        usuario_ingresado = normalizar_texto(user_input)
        lista_limpia = [normalizar_texto(u) for u in USUARIOS_PERMITIDOS]

        if usuario_ingresado in lista_limpia:
            st.session_state['autenticado'] = True
            st.session_state['usuario_actual'] = usuario_ingresado
            registrar_ingreso(usuario_ingresado)
            st.success(f"Bienvenido, {usuario_ingresado}. Cargando...")
            st.rerun()
        else:
            st.error("⛔ Usuario no autorizado.")

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    pantalla_login()
    st.stop()

# ==========================================
#      FIN LOGIN
# ==========================================

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
    st.error("⚠️ No se encontraron datos. Verifica la carpeta en GitHub.")
    st.stop()

indegree, reverse_selections = calcular_estadisticas(datos)

# --- SIDEBAR ---
with st.sidebar:
    st.caption(f"Logueado como: {st.session_state.get('usuario_actual', 'Usuario')}")

    if st.button("Cerrar Sesión"):
        st.session_state['autenticado'] = False
        st.rerun()

    st.title("🧩 Configuración")
    st.markdown("---")

    cursos_disponibles = sorted(list(set(d['curso'] for d in datos.values() if d['curso'])))
    filtro_curso = st.multiselect("Filtrar Alumnos por Curso:", cursos_disponibles, default=cursos_disponibles)
    nombres_filtrados = [n for n in lista_nombres if datos[n]['curso'] in filtro_curso or not filtro_curso]

    st.markdown("### Selección")
    alumno_seleccionado = st.selectbox("Buscar Alumno:", nombres_filtrados) if nombres_filtrados else None

    st.markdown("---")
    limite_preferencias = st.slider("Nivel de afinidad (Top N):", 1, 10, 3)
    st.caption("Define cuántas preferencias mostrar en las tablas.")

    # =======================================================
    #  ZONA ADMIN (SOLO VISIBLE PARA EL USUARIO ELEGIDO)
    # =======================================================
    if st.session_state.get('usuario_actual') == USUARIO_ADMIN:
        st.markdown("---")
        with st.expander("👮 Zona Admin (Privado)"):
            st.write("Solo tú puedes ver esto.")
            if os.path.exists("historial_accesos.csv"):
                with open("historial_accesos.csv", "rb") as f:
                    st.download_button(
                        label="📥 Descargar Historial",
                        data=f,
                        file_name="historial_accesos.csv",
                        mime="text/csv"
                    )
            else:
                st.info("Aún no hay registros de acceso.")

    # --- LOGO AL FINAL DEL SIDEBAR ---
    st.markdown("---")
    st.image("image_4.png", use_column_width=True)


# --- DASHBOARD PRINCIPAL ---

st.title("Análisis Sociométrico")
st.markdown("Visión consolidada de las interacciones entre estudiantes.")
st.markdown("---")

tab1, tab2 = st.tabs(["👤 Análisis Individual", "🏆 Ranking Global"])

# --- TAB 1: INDIVIDUAL ---
with tab1:
    if alumno_seleccionado:
        info = datos[alumno_seleccionado]
        clave_alumno_actual = info['clave_busqueda']
        st.subheader(f"Detalle: {alumno_seleccionado}")
        c1, c2 = st.columns(2)
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
                        "Match": es_match
                    })

                df_prefs = pd.DataFrame(datos_tabla)

                def colorear_matches(row):
                    return ['background-color: #d4edda; color: #155724; font-weight: bold'] * len(row) if row["Match"] else [''] * len(row)

                st.dataframe(
                    df_prefs.style.apply(colorear_matches, axis=1),
                    column_config={"Match": None},
                    use_container_width=True,
                    hide_index=True
                )
                st.caption("↔️ : Indica selección mutua (Match).")
            else:
                st.info(f"No tiene preferencias en el Top {limite_preferencias}.")

        with c2:
            st.markdown("#### 👈 Seleccionado por (Quién lo eligió)")
            selectors = reverse_selections.get(clave_alumno_actual, [])
            if selectors:
                selectors = sorted(selectors)
                df_sel = pd.DataFrame(selectors, columns=["Compañero"])
                st.dataframe(df_sel, use_container_width=True, hide_index=True, height=300)
                st.success(f"Ha sido elegido por **{len(selectors)}** compañeros en total.")
            else:
                st.warning("Nadie ha seleccionado a este alumno todavía.")
    else:
        st.info("Selecciona un curso y un alumno en el menú lateral.")

# --- TAB 2: GLOBAL ---
with tab2:
    st.subheader("Ranking de Popularidad")

    data_global = []
    for nombre in nombres_filtrados:
        clave = datos[nombre]['clave_busqueda']
        total = int(indegree.get(clave, 0))
        curso = datos[nombre]['curso']
        data_global.append({"Alumno": nombre, "Veces Seleccionado": total, "Curso": curso})

    df_global = pd.DataFrame(data_global)

    if not df_global.empty:
        df_global = df_global.sort_values(by="Veces Seleccionado", ascending=True)

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

        fig.update_layout(xaxis_title="Cantidad de Elecciones", yaxis_title="", showlegend=False, template="plotly_white")
        fig.update_xaxes(fixedrange=True)
        fig.update_yaxes(fixedrange=True)

        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})

        with st.expander("Ver tabla de datos completa"):
            st.dataframe(df_global.sort_values(by="Veces Seleccionado", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.warning("No hay datos para mostrar con los filtros actuales.")

Tengo los datos del 8A pero no cargan, que agrego en el codigo
