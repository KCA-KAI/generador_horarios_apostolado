import streamlit as st
import pandas as pd
from ortools.sat.python import cp_model
from datetime import datetime
import matplotlib.pyplot as plt
import io

st.set_page_config(
    page_title="Generador de Horarios - Apostolado del Sagrado Corazón",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<div style="background: linear-gradient(90deg, #1f4e79, #2e5984); padding: 1rem; border-radius: 10px; margin-bottom: 2rem;">
    <h1 style="color:white; text-align:center; margin:0;">📚 Generador de Horarios Escolares</h1>
    <h3 style="color:#e8f4fd; text-align:center; margin:0;">Colegio Apostolado del Sagrado Corazón</h3>
</div>
""", unsafe_allow_html=True)

tabs = st.tabs([
    "📁 Cargar Datos",
    "🔍 Diagnóstico",
    "🚀 Generar Horario",
    "🗕️ Visualización",
    "📅 Exportar",
    "📊 Resumen de Cargas"
])

# -----------------------------------------------
# 📁 TAB 1: CARGA DE DATOS
with tabs[0]:
    st.header("📁 Subir archivo de datos")
    archivo = st.file_uploader(
        "Sube un archivo Excel con las columnas: Profesor, Asignatura, Curso, Horas por semana.",
        type=["xlsx", "csv"]
    )

    if archivo:
        try:
            df = pd.read_excel(archivo) if archivo.name.endswith(".xlsx") else pd.read_csv(archivo)
            
            # 🔧 MEJORA: Validar columnas requeridas
            columnas_requeridas = ["Profesor", "Asignatura", "Curso", "Horas por semana"]
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
            
            if columnas_faltantes:
                st.error(f"❌ Faltan las siguientes columnas: {', '.join(columnas_faltantes)}")
            else:
                # 🔧 MEJORA: Limpiar y normalizar datos
                df["Profesor"] = df["Profesor"].astype(str).str.strip()
                df["Asignatura"] = df["Asignatura"].astype(str).str.strip()
                df["Curso"] = df["Curso"].astype(str).str.strip()
                
                # 🔧 NUEVA FUNCIONALIDAD: Convertir horas a franjas de 30 minutos
                # Si una clase es de 1 hora = 2 franjas de 30 min
                # Si una clase es de 0.5 horas = 1 franja de 30 min
                df["Franjas_necesarias"] = (df["Horas por semana"] * 2).astype(int)
                
                st.success(f"✅ Archivo '{archivo.name}' cargado correctamente.")
                st.session_state["df"] = df
                
                # Mostrar vista previa con nueva columna
                st.subheader("🔍 Vista previa de datos procesados")
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
        
        # 🔧 NUEVA FUNCIONALIDAD: Análisis de viabilidad
        franjas_disponibles_por_curso = 5 * 10  # 5 días x 10 franjas de 30min por curso
        franjas_disponibles_total = franjas_disponibles_por_curso * df["Curso"].nunique()
        franjas_necesarias = df['Franjas_necesarias'].sum()
        
        st.subheader("📊 Análisis de Capacidad")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📅 Franjas por curso", franjas_disponibles_por_curso)
        with col2:
            st.metric("📋 Franjas necesarias", franjas_necesarias)
        with col3:
            porcentaje_uso = (franjas_necesarias / franjas_disponibles_total) * 100
            st.metric("📈 % de ocupación real", f"{porcentaje_uso:.1f}%")
        
        # Mostrar análisis detallado
        st.info(f"🎓 **{df['Curso'].nunique()} cursos** pueden tener clases simultáneamente")
        st.info(f"🏫 **Capacidad total**: {franjas_disponibles_total} franjas ({franjas_disponibles_total/2:.0f} horas)")
        
        if franjas_necesarias > franjas_disponibles_total:
            st.error("⚠️ No hay suficientes franjas horarias para todas las clases")
        elif porcentaje_uso > 80:
            st.warning("⚠️ El horario estará muy saturado (>80% ocupación)")
        else:
            st.success("✅ Datos listos para generar el horario.")

# -----------------------------------------------
# 🚀 TAB 3: GENERAR HORARIO CORREGIDO
with tabs[2]:
    st.header("🚀 Generar Horario")
    if "df" not in st.session_state:
        st.info("🔔 Sube un archivo antes de generar el horario.")
    else:
        df = st.session_state["df"]
        
        # 🔧 CORRECCIÓN CRÍTICA: Definir franjas de 30 minutos
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
        franjas_por_dia = [
            "09:00-09:30", "09:30-10:00", "10:00-10:30", "10:30-11:00", "11:00-11:30", 
            "11:30-12:00", "12:00-12:30", "12:30-13:00", "13:00-13:30", "13:30-14:00"
        ]
        franjas_totales = len(dias) * len(franjas_por_dia)
        
        # 🔧 CÁLCULO CORREGIDO: Considerar que múltiples cursos pueden tener clase simultáneamente
        cursos_unicos = df["Curso"].nunique()
        franjas_reales_disponibles = franjas_totales * cursos_unicos  # Cada curso puede usar todas las franjas
        
        # Mostrar configuración
        st.subheader("⚙️ Configuración del Horario")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"📅 **Días:** {len(dias)} días laborables")
            st.info(f"⏰ **Franjas por día:** {len(franjas_por_dia)} (30 min c/u)")
        with col2:
            st.info(f"🔢 **Total franjas:** {franjas_totales}")
            st.info(f"⏱️ **Horario:** 09:00 - 14:00")
        
        # Botón para generar
        col1, col2 = st.columns([1, 1])
        with col1:
            generar_horario = st.button("🚀 Generar Horario", type="primary")
        with col2:
            regenerar_horario = st.button("🔄 Generar Versión Alternativa")
        
        if generar_horario or regenerar_horario:
            with st.spinner("🔄 Generando horario optimizado..."):
                
                # 🔧 MODELO CORREGIDO
                model = cp_model.CpModel()
                variables = {}
                
                # Crear variables binarias para cada clase en cada franja
                for i in range(len(df)):
                    for f in range(franjas_totales):
                        variables[(i, f)] = model.NewBoolVar(f"clase_{i}_franja_{f}")
                
                # 🔧 RESTRICCIÓN FUNDAMENTAL: Cada clase debe tener exactamente sus franjas necesarias
                for i, fila in df.iterrows():
                    franjas_requeridas = int(fila["Franjas_necesarias"])
                    model.Add(
                        sum(variables[(i, f)] for f in range(franjas_totales)) == franjas_requeridas
                    )
                
                # 🔧 RESTRICCIÓN: Un profesor no puede estar en dos sitios a la vez
                for f in range(franjas_totales):
                    for profesor in df["Profesor"].unique():
                        indices_profesor = df[df["Profesor"] == profesor].index
                        model.Add(
                            sum(variables[(i, f)] for i in indices_profesor) <= 1
                        )
                
                # 🔧 RESTRICCIÓN: Un curso no puede tener dos clases simultáneas
                for f in range(franjas_totales):
                    for curso in df["Curso"].unique():
                        indices_curso = df[df["Curso"] == curso].index
                        model.Add(
                            sum(variables[(i, f)] for i in indices_curso) <= 1
                        )
                
                # 🔧 RESTRICCIONES ESPECÍFICAS SIMPLIFICADAS
                
                # 1. Fernando libre cuando hay Inglés en ciertos cursos
                cursos_fernando_ingles = ["1ºA", "1ºB", "1ºC", "3ºA", "3ºB", "3ºC", "5ºA", "5ºB", "5ºC"]
                indices_ingles_fernando = df[
                    (df["Curso"].isin(cursos_fernando_ingles)) & 
                    (df["Asignatura"].str.contains("Inglés", case=False, na=False))
                ].index
                indices_fernando = df[df["Profesor"].str.contains("Fernando", case=False, na=False)].index
                
                for f in range(franjas_totales):
                    clases_ingles = [variables[(i, f)] for i in indices_ingles_fernando]
                    clases_fernando = [variables[(i, f)] for i in indices_fernando]
                    
                    if clases_ingles and clases_fernando:
                        model.Add(sum(clases_ingles + clases_fernando) <= 1)
                
                # 2. Iván libre cuando hay Inglés en sus cursos
                cursos_ivan_ingles = ["2ºA", "2ºB", "2ºC", "4ºA", "4ºB", "4ºC", "6ºA", "6ºB", "6ºC"]
                indices_ingles_ivan = df[
                    (df["Curso"].isin(cursos_ivan_ingles)) & 
                    (df["Asignatura"].str.contains("Inglés", case=False, na=False))
                ].index
                indices_ivan = df[df["Profesor"].str.contains("Iván", case=False, na=False)].index
                
                for f in range(franjas_totales):
                    clases_ingles = [variables[(i, f)] for i in indices_ingles_ivan]
                    clases_ivan = [variables[(i, f)] for i in indices_ivan]
                    
                    if clases_ingles and clases_ivan:
                        model.Add(sum(clases_ingles + clases_ivan) <= 1)
                
                # 3. Andrea: una clase diaria de Inglés Infantil
                indices_andrea_infantil = df[
                    (df["Profesor"].str.contains("Andrea", case=False, na=False)) &
                    (df["Asignatura"].str.contains("Inglés", case=False, na=False)) &
                    (df["Curso"].str.contains("Infantil", case=False, na=False))
                ].index
                
                if not indices_andrea_infantil.empty:
                    for d in range(len(dias)):
                        franjas_dia = [d * len(franjas_por_dia) + h for h in range(len(franjas_por_dia))]
                        clases_dia = [variables[(i, f)] for i in indices_andrea_infantil for f in franjas_dia]
                        if clases_dia:
                            model.Add(sum(clases_dia) >= 1)  # Al menos una clase por día
                
                # 4. Toni: Coro Secundaria solo 10:00-11:00 (franjas 4-5)
                indices_toni_coro = df[
                    (df["Profesor"].str.contains("Toni", case=False, na=False)) &
                    (df["Asignatura"].str.contains("Coro", case=False, na=False)) &
                    (df["Curso"].str.contains("Secundaria", case=False, na=False))
                ].index
                
                franjas_validas_toni = []
                for d in range(len(dias)):
                    franjas_validas_toni.extend([d * len(franjas_por_dia) + 4, d * len(franjas_por_dia) + 5])
                
                for i in indices_toni_coro:
                    for f in range(franjas_totales):
                        if f not in franjas_validas_toni:
                            model.Add(variables[(i, f)] == 0)
                
                # 5. Juan Carlos: Ed. Física Secundaria martes/miércoles 9:00-11:00
                indices_jc_ef = df[
                    (df["Profesor"].str.contains("Juan Carlos", case=False, na=False)) &
                    (df["Asignatura"].str.contains("Educación Física", case=False, na=False)) &
                    (df["Curso"].str.contains("Secundaria", case=False, na=False))
                ].index
                
                franjas_validas_jc = []
                for d in [1, 2]:  # Martes (1) y Miércoles (2)
                    franjas_validas_jc.extend([d * len(franjas_por_dia) + h for h in range(4)])  # 9:00-11:00
                
                for i in indices_jc_ef:
                    for f in range(franjas_totales):
                        if f not in franjas_validas_jc:
                            model.Add(variables[(i, f)] == 0)
                
                # 6. Ana Inaraja: solo martes, miércoles, jueves 11:00-14:00
                indices_ana = df[df["Profesor"].str.contains("Ana Inaraja", case=False, na=False)].index
                
                franjas_validas_ana = []
                for d in [1, 2, 3]:  # Martes, Miércoles, Jueves
                    franjas_validas_ana.extend([d * len(franjas_por_dia) + h for h in range(4, 10)])  # 11:00-14:00
                
                for i in indices_ana:
                    for f in range(franjas_totales):
                        if f not in franjas_validas_ana:
                            model.Add(variables[(i, f)] == 0)
                
                # 7. Mª José López: no puede jueves 11:00-12:00
                indices_mariajose = df[df["Profesor"].str.contains("Mª José López", case=False, na=False)].index
                
                franjas_prohibidas_mj = [3 * len(franjas_por_dia) + 4, 3 * len(franjas_por_dia) + 5]  # Jueves 11:00-12:00
                
                for i in indices_mariajose:
                    for f in franjas_prohibidas_mj:
                        model.Add(variables[(i, f)] == 0)
                
                # 🔧 RESOLVER EL MODELO
                solver = cp_model.CpSolver()
                solver.parameters.max_time_in_seconds = 120.0  # Más tiempo para resolver
                
                if regenerar_horario:
                    import random
                    solver.parameters.random_seed = random.randint(1, 1000000)
                
                status = solver.Solve(model)
                
                if status in [cp_model.FEASIBLE, cp_model.OPTIMAL]:
                    st.success("✅ Horario generado con éxito!")
                    
                    # Guardar en session_state
                    st.session_state["solver"] = solver
                    st.session_state["variables"] = variables
                    st.session_state["df"] = df
                    st.session_state["dias"] = dias
                    st.session_state["franjas_por_dia"] = franjas_por_dia
                    st.session_state["fecha_generacion"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                    
                    # Mostrar estadísticas
                    total_asignadas = sum(solver.BooleanValue(variables[(i, f)]) 
                                        for i in range(len(df)) 
                                        for f in range(franjas_totales))
                    
                    st.info(f"📊 **Estadísticas:** {total_asignadas} franjas asignadas de {franjas_totales} disponibles")
                    
                elif status == cp_model.INFEASIBLE:
                    st.error("❌ **No se puede generar un horario** con las restricciones actuales.")
                    st.error("🔧 **Sugerencias:**")
                    st.error("- Reducir el número de horas de algunas asignaturas")
                    st.error("- Flexibilizar las restricciones de profesores")
                    st.error("- Verificar que no hay conflictos irresolubles")
                    
                else:
                    st.error("⏰ **Tiempo agotado** - El problema es muy complejo. Intenta simplificar las restricciones.")

# -----------------------------------------------
# 🗕️ TAB 4: VISUALIZACIÓN CORREGIDA
with tabs[3]:
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

        # ----------------------------
        # 🎓 POR CURSO
        with sub_tabs[0]:
            curso_seleccionado = st.selectbox("📘 Selecciona un curso", sorted(df["Curso"].unique()))
            
            # Crear tabla con franjas de 30 minutos
            tabla = pd.DataFrame(index=franjas_por_dia, columns=dias)
            
            for f in range(franjas_totales):
                dia = dias[f // len(franjas_por_dia)]
                franja = franjas_por_dia[f % len(franjas_por_dia)]
                
                clases = []
                for i, fila in df.iterrows():
                    if fila["Curso"] == curso_seleccionado and solver.BooleanValue(variables[(i, f)]):
                        clases.append(f"{fila['Asignatura']} ({fila['Profesor']})")
                
                tabla.at[franja, dia] = "\n".join(clases) if clases else ""
            
            st.subheader(f"🗓 Horario para {curso_seleccionado}")
            st.dataframe(tabla, use_container_width=True, height=500)

        # ----------------------------
        # 👨‍🏫 POR PROFESOR
        with sub_tabs[1]:
            profe_seleccionado = st.selectbox("👨‍🏫 Selecciona un profesor", sorted(df["Profesor"].unique()))
            
            tabla = pd.DataFrame(index=franjas_por_dia, columns=dias)
            
            for f in range(franjas_totales):
                dia = dias[f // len(franjas_por_dia)]
                franja = franjas_por_dia[f % len(franjas_por_dia)]
                
                clases = []
                for i, fila in df.iterrows():
                    if fila["Profesor"] == profe_seleccionado and solver.BooleanValue(variables[(i, f)]):
                        clases.append(f"{fila['Asignatura']} ({fila['Curso']})")
                
                tabla.at[franja, dia] = "\n".join(clases) if clases else ""
            
            st.subheader(f"🗓 Horario para {profe_seleccionado}")
            st.dataframe(tabla, use_container_width=True, height=500)

# -----------------------------------------------
# 📅 TAB 5: EXPORTACIÓN CORREGIDA
with tabs[4]:
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
            # 🧩 1. Exportar por Curso
            for curso in sorted(df["Curso"].unique()):
                tabla = pd.DataFrame(index=franjas_por_dia, columns=dias)
                
                for f in range(franjas_totales):
                    dia = dias[f // len(franjas_por_dia)]
                    franja = franjas_por_dia[f % len(franjas_por_dia)]
                    
                    clases = []
                    for i, fila in df.iterrows():
                        if fila["Curso"] == curso and solver.BooleanValue(variables[(i, f)]):
                            clases.append(f"{fila['Asignatura']} ({fila['Profesor']})")
                    
                    tabla.at[franja, dia] = " | ".join(clases) if clases else ""
                
                tabla.index.name = "Franja"
                tabla.to_excel(writer, sheet_name=f"Curso_{curso.replace('º', 'o')}")

            # 👩‍🏫 2. Exportar por Profesor  
            for profesor in sorted(df["Profesor"].unique()):
                tabla = pd.DataFrame(index=franjas_por_dia, columns=dias)
                
                for f in range(franjas_totales):
                    dia = dias[f // len(franjas_por_dia)]
                    franja = franjas_por_dia[f % len(franjas_por_dia)]
                    
                    clases = []
                    for i, fila in df.iterrows():
                        if fila["Profesor"] == profesor and solver.BooleanValue(variables[(i, f)]):
                            clases.append(f"{fila['Asignatura']} ({fila['Curso']})")
                    
                    tabla.at[franja, dia] = " | ".join(clases) if clases else ""
                
                tabla.index.name = "Franja"
                nombre_hoja = profesor.replace(" ", "_")[:25]  # Limitar nombre de hoja
                tabla.to_excel(writer, sheet_name=f"Prof_{nombre_hoja}")

        buffer.seek(0)

        st.download_button(
            label="📥 Descargar horario completo en Excel",
            data=buffer,
            file_name=f"horario_completo_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# 📊 TAB 6: RESUMEN DE CARGAS CORREGIDO
with tabs[5]:
    st.header("📊 Resumen de Carga Lectiva")

    if "solver" not in st.session_state or "df" not in st.session_state:
        st.info("🔔 Genera un horario antes de ver el resumen.")
    else:
        df = st.session_state["df"]
        solver = st.session_state["solver"]
        variables = st.session_state["variables"]
        dias = st.session_state["dias"]
        franjas_por_dia = st.session_state["franjas_por_dia"]
        franjas_totales = len(dias) * len(franjas_por_dia)

        # Crear registros de clases asignadas
        registros = []
        for f in range(franjas_totales):
            dia = dias[f // len(franjas_por_dia)]
            franja = franjas_por_dia[f % len(franjas_por_dia)]

            for i, fila in df.iterrows():
                if solver.BooleanValue(variables[(i, f)]):
                    registros.append({
                        "Profesor": fila["Profesor"],
                        "Asignatura": fila["Asignatura"],
                        "Curso": fila["Curso"],
                        "Día": dia,
                        "Franja": franja
                    })

        df_carga = pd.DataFrame(registros)

        if not df_carga.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("👨‍🏫 Franjas por Profesor")
                carga_prof = df_carga.groupby("Profesor").size().reset_index(name="Franjas")
                carga_prof["Horas"] = carga_prof["Franjas"] / 2  # Convertir a horas
                st.dataframe(carga_prof, use_container_width=True)
            
            with col2:
                st.subheader("🎓 Franjas por Curso")
                carga_curso = df_carga.groupby("Curso").size().reset_index(name="Franjas")
                carga_curso["Horas"] = carga_curso["Franjas"] / 2
                st.dataframe(carga_curso, use_container_width=True)

            st.subheader("📚 Franjas por Asignatura")
            carga_asig = df_carga.groupby("Asignatura").size().reset_index(name="Franjas")
            carga_asig["Horas"] = carga_asig["Franjas"] / 2
            st.dataframe(carga_asig, use_container_width=True)

            # 📊 GRÁFICOS
            st.subheader("📊 Gráficos de Distribución")
            
            # Gráfico por Profesor
            fig1, ax1 = plt.subplots(figsize=(12, 6))
            prof_data = df_carga.groupby("Profesor").size().sort_values(ascending=False)
            prof_data.plot(kind='bar', ax=ax1, color='steelblue')
            ax1.set_ylabel("Franjas de 30 min")
            ax1.set_xlabel("Profesor")
            ax1.set_title("Carga lectiva por profesor")
            ax1.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            st.pyplot(fig1)

            # Gráfico por Curso
            fig2, ax2 = plt.subplots(figsize=(10, 6))
            curso_data = df_carga.groupby("Curso").size().sort_values(ascending=False)
            curso_data.plot(kind='bar', ax=ax2, color='orange')
            ax2.set_ylabel("Franjas de 30 min")
            ax2.set_xlabel("Curso")
            ax2.set_title("Carga lectiva por curso")
            ax2.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            st.pyplot(fig2)
        else:
            st.warning("⚠️ No hay datos de horario para mostrar.")
