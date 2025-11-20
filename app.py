
# 2. DEFINIR QUIÉN ES EL ADMINISTRADOR
# (Debe ser uno de los nombres de la lista de arriba, en MAYÚSCULAS)
USUARIO_ADMIN = "EROS" 
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
@@ -63,22 +63,22 @@ def normalizar_texto(texto):
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
            st.session_state['usuario_actual'] = usuario_ingresado
registrar_ingreso(usuario_ingresado)
st.success(f"Bienvenido, {usuario_ingresado}. Cargando...")
            st.rerun() 
            st.rerun()
else:
st.error("⛔ Usuario no autorizado.")

@@ -99,7 +99,7 @@ def pantalla_login():
def cargar_datos(ruta_base="datos"):
datos_completos = {}
lista_nombres = []
    

if not os.path.exists(ruta_base):
return {}, []

@@ -114,7 +114,7 @@ def cargar_datos(ruta_base="datos"):
curso = data.get("Curso", "")
nombre_display = f"{nombre} ({curso})" if curso else nombre
clave = nombre.upper().strip()
                        

datos_completos[nombre_display] = {
"ruta": ruta_completa,
"data": data,
@@ -128,7 +128,7 @@ def cargar_datos(ruta_base="datos"):

@st.cache_data
def calcular_estadisticas(datos_completos):
    indegree = {} 
    indegree = {}
reverse_selections = {}
for nombre_display, info in datos_completos.items():
clave = info['clave_busqueda']
@@ -158,21 +158,21 @@ def calcular_estadisticas(datos_completos):
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
@@ -195,6 +195,11 @@ def calcular_estadisticas(datos_completos):
else:
st.info("Aún no hay registros de acceso.")

    # --- LOGO AL FINAL DEL SIDEBAR ---
    st.markdown("---")
    st.image("image_4.png", use_column_width=True)


# --- DASHBOARD PRINCIPAL ---

st.title("Análisis Sociométrico")
@@ -215,38 +220,38 @@ def calcular_estadisticas(datos_completos):
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
                        "Match": es_match
})
                

df_prefs = pd.DataFrame(datos_tabla)
                

def colorear_matches(row):
return ['background-color: #d4edda; color: #155724; font-weight: bold'] * len(row) if row["Match"] else [''] * len(row)

@@ -276,36 +281,36 @@ def colorear_matches(row):
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
