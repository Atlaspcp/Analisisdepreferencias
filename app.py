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
#      SISTEMA DE LOGIN Y PERMISOS
# ==========================================

# 1. LISTA DE USUARIOS PERMITIDOS
USUARIOS_PERMITIDOS = [
    "EROS",  
    "Annia",
    "Diego",
    "Camila",
    "Mauricio"
]

# 2. DEFINIR QUIÉN ES EL ADMINISTRADOR
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
#      FIN LOGIN
# ==========================================

# --- FUNCIONES DE LÓGICA Y CORRECCIÓN ---

def corregir_typos(texto):
    """Corrige errores de tipeo conocidos en los nombres."""
    if not isinstance(texto, str): return texto
    texto_corregido = texto.replace("MAKOUZI", "NAKOUZI")
    return texto_corregido

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
                        
                        nombre_raw = data.get("Nombre", "Desconoc
