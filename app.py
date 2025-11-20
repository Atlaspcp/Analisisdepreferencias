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
            
            # Filtrar hasta el limite seleccionado
            prefs_visible = [p for p in prefs_sorted if p[1] <= limite_preferencias]
            
            if prefs_visible:
                # --- LÓGICA DE RECIPROCIDAD (NUEVO) ---
                datos_tabla = []
                for nombre_elegido, ranking_otorgado in prefs_visible:
                    clave_elegido = nombre_elegido.upper().strip()
                    
                    # Variables para determinar si hubo match
                    es_match = False
                    ranking_reciproco = None
                    
                    # Buscar los datos de la persona elegida
                    # (Buscamos en todos los datos cargados quién coincide con la clave)
                    datos_compañero = None
                    for d in datos.values():
                        if d['clave_busqueda'] == clave_elegido:
                            datos_compañero = d
                            break
                    
                    # Si encontramos al compañero, miramos dentro de sus preferencias
                    if datos_compañero:
                        sus_preferencias = datos_compañero['data'].get("Seleccion_Jerarquica", {})
                        # Buscamos si el alumno actual está en esas preferencias
                        for k, v in sus_preferencias.items():
                            if k.upper().strip() == clave_alumno_actual:
                                es_match = True
                                ranking_reciproco = v
                                break
                    
                    # Formatear el texto para mostrar
                    if es_match:
                        nombre_mostrar = f"{nombre_elegido} ↔️ (Te eligió #{ranking_reciproco})"
                    else:
                        nombre_mostrar = nombre_elegido
                        
                    datos_tabla.append({
                        "Compañero": nombre_mostrar,
                        "Ranking": ranking_otorgado,
                        "Match": es_match # Columna oculta para colorear
                    })
                
                # Crear DataFrame
                df_prefs = pd.DataFrame(datos_tabla)
                
                # --- ESTILOS VISUALES (PANDAS STYLER) ---
                def colorear_matches(row):
                    # Si es match, pintamos la fila de verde suave y letra oscura
                    if row["Match"]:
                        return ['background-color: #d4edda; color: #155724; font-weight: bold'] * len(row)
                    else:
                        return [''] * len(row)

                # Aplicar estilos y ocultar la columna "Match" (solo la usamos para pintar)
                st.dataframe(
                    df_prefs.style.apply(colorear_matches, axis=1),
                    column_config={
                        "Match": None # Ocultar columna auxiliar
                    },
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
                # Ordenamos alfabéticamente
                selectors = sorted(selectors)
                df_sel = pd.DataFrame(selectors, columns=["Compañero"])
                
                # Mostramos tabla limpia
                st.dataframe(
                    df_sel, 
                    use_container_width=True, 
                    hide_index=True, 
                    height=300
                )
                st.success(f"Ha sido elegido por **{len(selectors)}** compañeros en total.")
            else:
                st.warning("Nadie ha seleccionado a este alumno todavía.")
    else:
        st.info("Selecciona un curso y un alumno en el menú lateral.")
