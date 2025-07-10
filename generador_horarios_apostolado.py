import streamlit as st
import pandas as pd
from ortools.sat.python import cp_model
from datetime import datetime
import matplotlib.pyplot as plt
import io

st.set_page_config(
    page_title="Generador de Horarios Flexible - Apostolado del Sagrado Corazón",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<div style="background: linear-gradient(90deg, #1f4e79, #2e5984); padding: 1rem; border-radius: 10px; margin-bottom: 2rem;">
    <h1 style="color:white; text-align:center; margin:0;">📚 Generador de Horarios Flexible</h1>
    <h3 style="color:#e8f4fd; text-align:center; margin:0;">Colegio Apostolado del Sagrado Corazón</h3>
</div>
""", unsafe_allow_html=True)

tabs = st.tabs([
    "📁 Cargar Datos",
    "🔍 Diagnóstico",
    "⚙️ Configurar Restricciones",
    "🚀 Generar Horario",
    "🗕️ Visualización",
    "📅 Exportar"
])

# -----------------------------------------------
# 📁 TAB 1: CARGA DE DATOS
with tabs[0]:
    st.header("📁 Subir archivo de datos")
    archivo = st.file_uploader(
        "Sube un archivo Excel/CSV con columnas: Profesor, Asignatura, Curso, Horas por semana",
        type=["xlsx", "csv"]
    )

    if archivo:
        try:
            df = pd.read_excel(archivo) if archivo.name.endswith(".xlsx") else pd.read_csv(archivo)
            
            # Validar columnas
            columnas_requeridas = ["Profesor", "Asignatura", "Curso", "Horas por semana"]
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
            
            if columnas_faltantes:
                st.error(f"❌ Faltan las siguientes columnas: {', '.join(columnas_faltantes)}")
            else:
                # Limpiar datos
                df["Profesor"] = df["Profesor"].astype(str).str.strip()
                df["Asignatura"] = df["Asignatura"].astype(str).str.strip()
                df["Curso"] = df["Curso"].astype(str).str.strip()
                
                # Convertir comas a puntos en horas
                if df["Horas por semana"].dtype == 'object':
                    df["Horas por semana"] = df["Horas por semana"].astype(str).str.replace(',', '.').astype(float)
                
                # Convertir a franjas de 30 minutos
                df["Franjas_necesarias"] = (df["Horas por semana"] * 2).astype(int)
                
                st.success(f"✅ Archivo '{archivo.name}' cargado correctamente.")
                st.session_state["df"] = df
                
                st.subheader("🔍 Vista previa de datos")
                df_preview = df.copy()
                df_preview["Franjas de 30min"] = df_preview["Franjas_necesarias"]
                st.dataframe(df_preview, use_container_width=True, height=400)
                
        except Exception as e:
            st.error(f"❌ Error al procesar el archivo: {e}")

# -----------------------------------------------
# 🔍 TAB 2: DIAGNÓSTICO
with tabs[1]:
    st.header("🔍 Diagnóstico de Viabilidad")
    if "df" not in st.session_state:
        st.info("🔔 Por favor, sube primero un archivo en la pestaña 📁 Cargar Datos.")
    else:
        df = st.session_state["df"]
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("👨‍🏫 Profesores únicos", df['Profesor'].nunique())
            st.metric("🎓 Cursos únicos", df['Curso'].nunique())
            
        with col2:
            st.metric("📚 Asignaturas únicas", df['Asignatura'].nunique())
            st.metric("⏰ Franjas totales necesarias", int(df['Franjas_necesarias'].sum()))
        
        # Análisis de capacidad corregido (descontando recreo)
        franjas_por_curso = 5 * 9  # 5 días x 9 franjas útiles (10 - 1 recreo)
        total_cursos = df["Curso"].nunique()
        capacidad_total = franjas_por_curso * total_cursos
        franjas_necesarias = df['Franjas_necesarias'].sum()
        
        st.subheader("📊 Análisis de Capacidad")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📅 Franjas útiles por curso", franjas_por_curso)
        with col2:
            st.metric("🏫 Capacidad total", capacidad_total)
        with col3:
            porcentaje_uso = (franjas_necesarias / capacidad_total) * 100
            st.metric("📈 % de ocupación", f"{porcentaje_uso:.1f}%")
        
        st.info("🔔 **Recreo descontado**: 12:00-12:30 diariamente (5 franjas menos)")
        
        # Análisis por profesor
        st.subheader("👨‍🏫 Carga por Profesor")
        carga_profesor = df.groupby("Profesor")["Horas por semana"].sum().sort_values(ascending=False)
        profesores_sobrecargados = carga_profesor[carga_profesor > 25]
        
        if not profesores_sobrecargados.empty:
            st.warning("⚠️ Profesores con más de 25 horas semanales:")
            for prof, horas in profesores_sobrecargados.items():
                st.write(f"• {prof}: {horas} horas")
        
        if porcentaje_uso <= 80:
            st.success("✅ La carga horaria es viable.")
        else:
            st.error("❌ Sobrecarga horaria detectada.")

# -----------------------------------------------
# ⚙️ TAB 3: CONFIGURAR RESTRICCIONES
with tabs[2]:
    st.header("⚙️ Configurar Restricciones")
    
    if "df" not in st.session_state:
        st.info("🔔 Carga datos primero.")
    else:
        st.subheader("🔧 Nivel de Flexibilidad")
        
        flexibilidad = st.select_slider(
            "Selecciona el nivel de restricciones:",
            options=["Muy Estricto", "Estricto", "Moderado", "Flexible", "Muy Flexible"],
            value="Moderado",
            help="Más flexible = más posibilidades de encontrar solución"
        )
        
        st.session_state["flexibilidad"] = flexibilidad
        
        st.subheader("📋 Restricciones Específicas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Restricciones de Profesores:**")
            
            # Ana Inaraja
            ana_restriccion = st.checkbox(
                "Ana Inaraja: Solo martes, miércoles, jueves 11:00-14:00",
                value=(flexibilidad in ["Muy Estricto", "Estricto"])
            )
            
            # Juan Carlos Ed. Física
            jc_restriccion = st.checkbox(
                "Juan Carlos: Ed. Física solo martes/miércoles 9:00-11:00",
                value=(flexibilidad in ["Muy Estricto", "Estricto"])
            )
            
            # Mª José López
            mariajose_restriccion = st.checkbox(
                "Mª José López: No puede jueves 11:00-12:00",
                value=(flexibilidad != "Muy Flexible")
            )
        
        with col2:
            st.write("**Restricciones de Asignaturas:**")
            
            # Inglés-Fernando/Iván
            ingles_restriccion = st.checkbox(
                "Fernando/Iván libres durante clases de Inglés específicas",
                value=(flexibilidad in ["Muy Estricto", "Estricto"])
            )
            
            # Toni Coro
            coro_restriccion = st.checkbox(
                "Toni: Coro solo 10:00-11:00",
                value=(flexibilidad != "Muy Flexible")
            )
            
            # Andrea Inglés Infantil
            andrea_restriccion = st.checkbox(
                "Andrea: Una clase diaria de Inglés Infantil",
                value=(flexibilidad in ["Muy Estricto", "Estricto", "Moderado"])
            )
        
        # Guardar configuración
        st.session_state["restricciones"] = {
            "ana_horario": ana_restriccion,
            "juan_carlos_ef": jc_restriccion,
            "mariajose_jueves": mariajose_restriccion,
            "ingles_fernando_ivan": ingles_restriccion,
            "toni_coro": coro_restriccion,
            "andrea_diaria": andrea_restriccion
        }
        
        if flexibilidad in ["Flexible", "Muy Flexible"]:
            st.info("🔔 **Modo flexible activado**: Se priorizará encontrar una solución viable.")

# -----------------------------------------------
# 🚀 TAB 4: GENERAR HORARIO FLEXIBLE
with tabs[3]:
    st.header("🚀 Generar Horario")
    
    if "df" not in st.session_state:
        st.info("🔔 Sube un archivo antes de generar el horario.")
    else:
        df = st.session_state["df"]
        
        # Configuración de horario
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
        franjas_por_dia = [
            "09:00-09:30", "09:30-10:00", "10:00-10:30", "10:30-11:00", "11:00-11:30", 
            "11:30-12:00", "12:00-12:30", "12:30-13:00", "13:00-13:30", "13:30-14:00"
        ]
        franjas_totales = len(dias) * len(franjas_por_dia)
        
        # 🔔 RECREO: 12:00-12:30 todos los días (franja 6 de cada día)
        franja_recreo = 6  # Posición de "12:00-12:30" en la lista
        franjas_recreo = [d * len(franjas_por_dia) + franja_recreo for d in range(len(dias))]
        
        # Mostrar configuración actual
        flexibilidad = st.session_state.get("flexibilidad", "Moderado")
        restricciones = st.session_state.get("restricciones", {})
        
        st.info(f"📋 **Nivel de flexibilidad**: {flexibilidad}")
        st.info(f"🔔 **Recreo programado**: 12:00-12:30 (lunes a viernes)")
        
        restricciones_activas = sum(restricciones.values()) if restricciones else 0
        st.info(f"🔧 **Restricciones activas**: {restricciones_activas} de 6")
        
        # Botones de generación
        col1, col2 = st.columns([1, 1])
        with col1:
            generar_horario = st.button("🚀 Generar Horario", type="primary")
        with col2:
            regenerar_horario = st.button("🔄 Generar Versión Alternativa")
        
        if generar_horario or regenerar_horario:
            with st.spinner("🔄 Generando horario optimizado..."):
                
                # Crear modelo
                model = cp_model.CpModel()
                variables = {}
                
                # Variables binarias
                for i in range(len(df)):
                    for f in range(franjas_totales):
                        variables[(i, f)] = model.NewBoolVar(f"clase_{i}_franja_{f}")
                
                # RESTRICCIONES BÁSICAS (siempre activas)
                
                # 🔔 RECREO: Prohibir clases durante 12:00-12:30 todos los días
                for i in range(len(df)):
                    for franja in franjas_recreo:
                        model.Add(variables[(i, franja)] == 0)
                
                # Cada clase debe tener exactamente sus franjas necesarias
                for i, fila in df.iterrows():
                    franjas_requeridas = int(fila["Franjas_necesarias"])
                    model.Add(
                        sum(variables[(i, f)] for f in range(franjas_totales)) == franjas_requeridas
                    )
                
                # Un profesor no puede estar en dos sitios a la vez
                for f in range(franjas_totales):
                    for profesor in df["Profesor"].unique():
                        indices_profesor = df[df["Profesor"] == profesor].index
                        model.Add(
                            sum(variables[(i, f)] for i in indices_profesor) <= 1
                        )
                
                # Un curso no puede tener dos clases simultáneas
                for f in range(franjas_totales):
                    for curso in df["Curso"].unique():
                        indices_curso = df[df["Curso"] == curso].index
                        model.Add(
                            sum(variables[(i, f)] for i in indices_curso) <= 1
                        )
                
                # RESTRICCIONES ESPECÍFICAS (configurables)
                restricciones_aplicadas = 0
                
                if restricciones.get("ana_horario", False):
                    # Ana Inaraja: solo martes, miércoles, jueves 11:00-14:00
                    indices_ana = df[df["Profesor"].str.contains("Ana Inaraja", case=False, na=False)].index
                    
                    franjas_validas_ana = []
                    for d in [1, 2, 3]:  # Martes, Miércoles, Jueves
                        franjas_validas_ana.extend([d * len(franjas_por_dia) + h for h in range(4, 10)])
                    
                    for i in indices_ana:
                        for f in range(franjas_totales):
                            if f not in franjas_validas_ana:
                                model.Add(variables[(i, f)] == 0)
                    
                    restricciones_aplicadas += 1
                
                if restricciones.get("juan_carlos_ef", False):
                    # Juan Carlos: Ed. Física solo martes/miércoles 9:00-11:00
                    indices_jc_ef = df[
                        (df["Profesor"].str.contains("Juan Carlos", case=False, na=False)) &
                        (df["Asignatura"].str.contains("Educación Física", case=False, na=False))
                    ].index
                    
                    franjas_validas_jc = []
                    for d in [1, 2]:  # Martes, Miércoles
                        franjas_validas_jc.extend([d * len(franjas_por_dia) + h for h in range(4)])
                    
                    for i in indices_jc_ef:
                        for f in range(franjas_totales):
                            if f not in franjas_validas_jc:
                                model.Add(variables[(i, f)] == 0)
                    
                    restricciones_aplicadas += 1
                
                if restricciones.get("mariajose_jueves", False):
                    # Mª José López: no puede jueves 11:00-12:00
                    indices_mariajose = df[df["Profesor"].str.contains("Mª José López", case=False, na=False)].index
                    
                    franjas_prohibidas = [3 * len(franjas_por_dia) + 4, 3 * len(franjas_por_dia) + 5]
                    
                    for i in indices_mariajose:
                        for f in franjas_prohibidas:
                            model.Add(variables[(i, f)] == 0)
                    
                    restricciones_aplicadas += 1
                
                if restricciones.get("toni_coro", False):
                    # Toni: Coro solo 10:00-11:00
                    indices_toni_coro = df[
                        (df["Profesor"].str.contains("Toni", case=False, na=False)) &
                        (df["Asignatura"].str.contains("Coro", case=False, na=False))
                    ].index
                    
                    franjas_validas_coro = []
                    for d in range(len(dias)):
                        franjas_validas_coro.extend([d * len(franjas_por_dia) + 4, d * len(franjas_por_dia) + 5])
                    
                    for i in indices_toni_coro:
                        for f in range(franjas_totales):
                            if f not in franjas_validas_coro:
                                model.Add(variables[(i, f)] == 0)
                    
                    restricciones_aplicadas += 1
                
                if restricciones.get("andrea_diaria", False):
                    # Andrea: una clase diaria de Inglés Infantil
                    indices_andrea = df[
                        (df["Profesor"].str.contains("Andrea", case=False, na=False)) &
                        (df["Asignatura"].str.contains("Inglés", case=False, na=False)) &
                        (df["Curso"].str.contains("Infantil", case=False, na=False))
                    ].index
                    
                    if not indices_andrea.empty:
                        for d in range(len(dias)):
                            franjas_dia = [d * len(franjas_por_dia) + h for h in range(len(franjas_por_dia))]
                            clases_dia = [variables[(i, f)] for i in indices_andrea for f in franjas_dia]
                            if clases_dia:
                                model.Add(sum(clases_dia) >= 1)
                    
                    restricciones_aplicadas += 1
                
                # Solo aplicar restricción de Inglés en modo estricto
                if restricciones.get("ingles_fernando_ivan", False) and flexibilidad in ["Muy Estricto", "Estricto"]:
                    # Fernando libre cuando hay Inglés en ciertos cursos
                    cursos_fernando = ["1ºA", "1ºB", "1ºC", "3ºA", "3ºB", "3ºC", "5ºA", "5ºB", "5ºC"]
                    indices_ingles_f = df[
                        (df["Curso"].isin(cursos_fernando)) & 
                        (df["Asignatura"].str.contains("Inglés", case=False, na=False))
                    ].index
                    indices_fernando = df[df["Profesor"].str.contains("Fernando", case=False, na=False)].index
                    
                    for f in range(franjas_totales):
                        clases_ingles = [variables[(i, f)] for i in indices_ingles_f]
                        clases_fernando = [variables[(i, f)] for i in indices_fernando]
                        
                        if clases_ingles and clases_fernando:
                            model.Add(sum(clases_ingles + clases_fernando) <= 1)
                    
                    restricciones_aplicadas += 1
                
                # Configurar solver
                solver = cp_model.CpSolver()
                
                # Ajustar tiempo según flexibilidad
                if flexibilidad in ["Muy Flexible", "Flexible"]:
                    solver.parameters.max_time_in_seconds = 300.0  # 5 minutos
                elif flexibilidad == "Moderado":
                    solver.parameters.max_time_in_seconds = 180.0  # 3 minutos
                else:
                    solver.parameters.max_time_in_seconds = 120.0  # 2 minutos
                
                if regenerar_horario:
                    import random
                    solver.parameters.random_seed = random.randint(1, 1000000)
                
                # Resolver
                status = solver.Solve(model)
                
                st.info(f"🔧 **Restricciones aplicadas**: {restricciones_aplicadas} + Recreo obligatorio")
                
                if status in [cp_model.FEASIBLE, cp_model.OPTIMAL]:
                    st.success("✅ ¡Horario generado con éxito!")
                    
                    # Guardar resultados
                    st.session_state["solver"] = solver
                    st.session_state["variables"] = variables
                    st.session_state["df"] = df
                    st.session_state["dias"] = dias
                    st.session_state["franjas_por_dia"] = franjas_por_dia
                    st.session_state["fecha_generacion"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                    
                    # Estadísticas
                    total_asignadas = sum(solver.BooleanValue(variables[(i, f)]) 
                                        for i in range(len(df)) 
                                        for f in range(franjas_totales))
                    
                    st.info(f"📊 **{total_asignadas} franjas asignadas** con nivel '{flexibilidad}'")
                    
                    if status == cp_model.OPTIMAL:
                        st.success("🎯 **Solución óptima encontrada**")
                    else:
                        st.info("✅ **Solución factible encontrada**")
                    
                elif status == cp_model.INFEASIBLE:
                    st.error("❌ **No se pudo generar un horario** con las restricciones actuales.")
                    
                    if restricciones_aplicadas > 3:
                        st.warning("💡 **Sugerencia**: Reduce las restricciones en la pestaña ⚙️ Configurar")
                    
                    st.error("🔧 **Opciones:**")
                    st.error("• Cambiar a modo 'Flexible' o 'Muy Flexible'")
                    st.error("• Desactivar algunas restricciones específicas")
                    st.error("• Revisar si hay profesores sobrecargados")
                    
                else:
                    st.warning("⏰ **Tiempo agotado** - Intenta con modo más flexible")

# -----------------------------------------------
# 🗕️ TAB 5: VISUALIZACIÓN (igual que antes)
with tabs[4]:
    st.header("🗕️ Visualización del Horario")
    if "solver" not in st.session_state:
        st.info("🔔 Genera un horario en la pestaña 🚀 Generar Horario.")
    else:
        solver = st.session_state["solver"]
        variables = st.session_state["variables"]
        df = st.session_state["df"]
        dias = st.session_state["dias"]
        franjas_por_dia = st.session_state["franjas_por_dia"]
        franjas_totales = len(dias) * len(franjas_por_dia)

        sub_tabs = st.tabs(["🎓 Ver por Curso", "👨‍🏫 Ver por Profesor"])

        # Por Curso
        with sub_tabs[0]:
            curso_seleccionado = st.selectbox("📘 Selecciona un curso", sorted(df["Curso"].unique()))
            
            tabla = pd.DataFrame(index=franjas_por_dia, columns=dias)
            
            for f in range(franjas_totales):
                dia = dias[f // len(franjas_por_dia)]
                franja = franjas_por_dia[f % len(franjas_por_dia)]
                
                # Mostrar RECREO en la franja correspondiente
                if f in franjas_recreo:
                    tabla.at[franja, dia] = "🔔 RECREO"
                else:
                    clases = []
                    for i, fila in df.iterrows():
                        if fila["Curso"] == curso_seleccionado and solver.BooleanValue(variables[(i, f)]):
                            clases.append(f"{fila['Asignatura']} ({fila['Profesor']})")
                    
                    tabla.at[franja, dia] = "\n".join(clases) if clases else ""
            
            st.subheader(f"🗓 Horario para {curso_seleccionado}")
            st.dataframe(tabla, use_container_width=True, height=500)

        # Por Profesor
        with sub_tabs[1]:
            profe_seleccionado = st.selectbox("👨‍🏫 Selecciona un profesor", sorted(df["Profesor"].unique()))
            
            tabla = pd.DataFrame(index=franjas_por_dia, columns=dias)
            
            for f in range(franjas_totales):
                dia = dias[f // len(franjas_por_dia)]
                franja = franjas_por_dia[f % len(franjas_por_dia)]
                
                # Mostrar RECREO en la franja correspondiente
                if f in franjas_recreo:
                    tabla.at[franja, dia] = "🔔 RECREO"
                else:
                    clases = []
                    for i, fila in df.iterrows():
                        if fila["Profesor"] == profe_seleccionado and solver.BooleanValue(variables[(i, f)]):
                            clases.append(f"{fila['Asignatura']} ({fila['Curso']})")
                    
                    tabla.at[franja, dia] = "\n".join(clases) if clases else ""
            
            st.subheader(f"🗓 Horario para {profe_seleccionado}")
            st.dataframe(tabla, use_container_width=True, height=500)

# -----------------------------------------------
# 📅 TAB 6: EXPORTACIÓN (igual que antes)
with tabs[5]:
    st.header("📅 Exportar Horario Generado")

    if "solver" not in st.session_state or "df" not in st.session_state:
        st.info("🔔 Genera un horario antes de exportarlo.")
    else:
        df = st.session_state["df"]
        solver = st.session_state["solver"]
        variables = st.session_state["variables"]
        dias = st.session_state["dias"]
        franjas_por_dia = st.session_state["franjas_por_dia"]
        franjas_totales = len(dias) * len(franjas_por_dia)

        buffer = io.BytesIO()

        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            # Exportar por Curso
            for curso in sorted(df["Curso"].unique()):
                tabla = pd.DataFrame(index=franjas_por_dia, columns=dias)
                
                for f in range(franjas_totales):
                    dia = dias[f // len(franjas_por_dia)]
                    franja = franjas_por_dia[f % len(franjas_por_dia)]
                    
                    # Mostrar RECREO en la exportación
                    if f in [d * len(franjas_por_dia) + 6 for d in range(len(dias))]:
                        tabla.at[franja, dia] = "🔔 RECREO"
                    else:
                        clases = []
                        for i, fila in df.iterrows():
                            if fila["Curso"] == curso and solver.BooleanValue(variables[(i, f)]):
                                clases.append(f"{fila['Asignatura']} ({fila['Profesor']})")
                        
                        tabla.at[franja, dia] = " | ".join(clases) if clases else ""
                
                tabla.index.name = "Franja"
                tabla.to_excel(writer, sheet_name=f"Curso_{curso.replace('º', 'o')}")

            # Exportar por Profesor  
            for profesor in sorted(df["Profesor"].unique()):
                tabla = pd.DataFrame(index=franjas_por_dia, columns=dias)
                
                for f in range(franjas_totales):
                    dia = dias[f // len(franjas_por_dia)]
                    franja = franjas_por_dia[f % len(franjas_por_dia)]
                    
                    # Mostrar RECREO en la exportación para profesores
                    if f in [d * len(franjas_por_dia) + 6 for d in range(len(dias))]:
                        tabla.at[franja, dia] = "🔔 RECREO"
                    else:
                        clases = []
                        for i, fila in df.iterrows():
                            if fila["Profesor"] == profesor and solver.BooleanValue(variables[(i, f)]):
                                clases.append(f"{fila['Asignatura']} ({fila['Curso']})")
                        
                        tabla.at[franja, dia] = " | ".join(clases) if clases else ""
                
                tabla.index.name = "Franja"
                nombre_hoja = profesor.replace(" ", "_")[:25]
                tabla.to_excel(writer, sheet_name=f"Prof_{nombre_hoja}")

        buffer.seek(0)
        
        flexibilidad = st.session_state.get("flexibilidad", "Normal")
        filename = f"horario_{flexibilidad.lower()}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

        st.download_button(
            label="📥 Descargar horario completo en Excel",
            data=buffer,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.success(f"✅ Horario generado con nivel de flexibilidad: **{flexibilidad}**")
