import streamlit as st
import pandas as pd
from ortools.sat.python import cp_model
from datetime import datetime

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
            st.success(f"✅ Archivo '{archivo.name}' cargado correctamente.")
            st.session_state["df"] = df
            st.dataframe(df, use_container_width=True, height=400)
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
        st.metric("👨‍🏫 Profesores únicos", df['Profesor'].nunique())
        st.metric("🎓 Cursos únicos", df['Curso'].nunique())
        st.metric("📚 Asignaturas únicas", df['Asignatura'].nunique())
        st.metric("⏰ Horas totales", int(df['Horas por semana'].sum()))
        st.success("✅ Datos listos para generar el horario.")

# -----------------------------------------------
# 🚀 TAB 3: GENERAR HORARIO
with tabs[2]:
    st.header("🚀 Generar Horario")
    if "df" not in st.session_state:
        st.info("🔔 Sube un archivo antes de generar el horario.")
    else:
        df = st.session_state["df"]
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
        horas_por_dia = [
            "09:00-10:00", "10:00-11:00", "11:00-12:00", "12:30-13:00", "13:00-14:00"
        ]
        franjas_totales = len(dias) * len(horas_por_dia)
        model = cp_model.CpModel()
        variables = {}

        for i in range(len(df)):
            for f in range(franjas_totales):
                variables[(i, f)] = model.NewBoolVar(f"clase_{i}_franja_{f}")

        # REGLAS BÁSICAS
        for i, fila in df.iterrows():
            model.Add(sum(variables[(i, f)] for f in range(franjas_totales)) == int(fila["Horas por semana"]))

        for f in range(franjas_totales):
            for profesor in df["Profesor"].unique():
                indices = df[df["Profesor"] == profesor].index
                model.Add(sum(variables[(i, f)] for i in indices) <= 1)
            for curso in df["Curso"].unique():
                indices = df[df["Curso"] == curso].index
                model.Add(sum(variables[(i, f)] for i in indices) <= 1)

        # 🔒 Fernando debe tener libre si hay Inglés en ciertos cursos
        cursos_con_ingles = ["1ºA", "1ºB", "1ºC", "3ºA", "3ºB", "3ºC", "5ºA", "5ºB", "5ºC"]

        for f in range(franjas_totales):
            # Índices donde se imparte inglés en los cursos definidos
            indices_ingles = df[
            (df["Curso"].isin(cursos_con_ingles)) &
            (df["Asignatura"].str.lower() == "inglés")
        ].index

        # Índices de las clases de Fernando
        indices_fernando = df[df["Profesor"].str.lower() == "fernando"].index

        # Creamos la condición: si hay inglés en esa franja, entonces Fernando no puede dar clase
        ingles_en_f = [variables[(i, f)] for i in indices_ingles]
        fernando_en_f = [variables[(i, f)] for i in indices_fernando]

        if ingles_en_f and fernando_en_f:
            model.AddBoolOr([cl.Not() for cl in ingles_en_f + fernando_en_f])

        # 🔒 Iván debe tener libre si hay Inglés en ciertos cursos
        cursos_ivan = ["2ºA", "2ºB", "2ºC", "4ºA", "4ºB", "4ºC", "6ºA", "6ºB", "6ºC"]

        for f in range(franjas_totales):
            indices_ingles = df[
                (df["Curso"].isin(cursos_ivan)) &
                (df["Asignatura"].str.lower() == "inglés")
            ].index

            indices_ivan = df[df["Profesor"].str.lower() == "iván"].index

            ingles_en_f = [variables[(i, f)] for i in indices_ingles]
            ivan_en_f = [variables[(i, f)] for i in indices_ivan]

            if ingles_en_f and ivan_en_f:
                model.AddBoolOr([cl.Not() for cl in ingles_en_f + ivan_en_f])

        # 📅 Andrea debe impartir una clase diaria (lunes a viernes) de Inglés Infantil
        indices_andrea = df[
            (df["Profesor"].str.lower() == "andrea") &
            (df["Asignatura"].str.lower().str.contains("inglés")) &
            (df["Curso"].str.lower().str.contains("infantil"))
        ].index

        if not indices_andrea.empty:
            franjas_por_dia = len(horas_por_dia)
            for d in range(len(dias)):
                franjas_dia = [d * franjas_por_dia + h for h in range(franjas_por_dia)]

        clases_en_dia = [variables[(i, f)] for i in indices_andrea for f in franjas_dia]
        model.Add(sum(clases_en_dia) == 1)

        # Asegurar al menos una clase de Matemáticas y una de Lengua cada día
        franjas_por_dia = len(horas_por_dia)

        for d in range(len(dias)):
            franjas_dia = [d * franjas_por_dia + h for h in range(franjas_por_dia)]

            # Matemáticas
            indices_mates = df[df["Asignatura"].str.lower().str.contains("matemáticas")].index
            clases_mates_en_dia = [variables[(i, f)] for i in indices_mates for f in franjas_dia]
            model.Add(sum(clases_mates_en_dia) >= 1)

            # Lengua
            indices_lengua = df[df["Asignatura"].str.lower().str.contains("lengua")].index
            clases_lengua_en_dia = [variables[(i, f)] for i in indices_lengua for f in franjas_dia]
            model.Add(sum(clases_lengua_en_dia) >= 1)

        # 🎶 Toni debe impartir Coro (Secundaria) solo de 10:00 a 11:00
        franja_valida = "10:00-11:00"
        indice_franja_valida = horas_por_dia.index(franja_valida)

        indices_toni_coro = df[
            (df["Profesor"].str.lower() == "toni") &
            (df["Asignatura"].str.lower().str.contains("coro")) &
            (df["Curso"].str.lower().str.contains("secundaria"))
        ].index

        if not indices_toni_coro.empty:
            for i in indices_toni_coro:
                # Solo puede dar clase en las franjas [d*franjas_por_dia + franja_valida] para cada día
                posibles_franjas = [d * franjas_por_dia + indice_franja_valida for d in range(len(dias))]
        
                # El resto de franjas se prohíben explícitamente
                for f in range(franjas_totales):
                    if f not in posibles_franjas:
                        model.Add(variables[(i, f)] == 0)

        # 🏃‍♂️ Juan Carlos debe dar Educación Física (Secundaria) solo martes y miércoles de 9:00 a 11:00
        franjas_validas = []

        # Ubicamos las posiciones de las franjas válidas
        horas_objetivo = ["09:00-10:00", "10:00-11:00"]
        dias_objetivo = ["Martes", "Miércoles"]

        for d in dias_objetivo:
            dia_idx = dias.index(d)
            for h in horas_objetivo:
                hora_idx = horas_por_dia.index(h)
                franja = dia_idx * len(horas_por_dia) + hora_idx
                franjas_validas.append(franja)

        # Buscamos las clases de Juan Carlos (Educación Física, Secundaria)
        indices_jc = df[
            (df["Profesor"].str.lower() == "juan carlos") &
            (df["Asignatura"].str.lower().str.contains("educación física")) &
            (df["Curso"].str.lower().str.contains("secundaria"))
        ].index

        # Solo puede dar clase en esas franjas válidas
        for i in indices_jc:
            for f in range(franjas_totales):
                if f not in franjas_validas:
                    model.Add(variables[(i, f)] == 0)

        # Y debe dar exactamente 4 clases
        model.Add(sum(variables[(i, f)] for i in indices_jc for f in franjas_validas) == 4)

        # ⏳ Ana Inaraja solo puede impartir clases martes, miércoles y jueves de 11:00 a 14:00
        dias_ana = ["Martes", "Miércoles", "Jueves"]
        horas_ana = ["11:00-12:00", "12:30-13:00", "13:00-14:00"]

        franjas_validas_ana = []

        for d in dias_ana:
            dia_idx = dias.index(d)
            for h in horas_ana:
                if h in horas_por_dia:
                    hora_idx = horas_por_dia.index(h)
                    franja = dia_idx * len(horas_por_dia) + hora_idx
                    franjas_validas_ana.append(franja)

        # Localizamos las clases de Ana Inaraja
        indices_ana = df[df["Profesor"].str.lower() == "ana inaraja"].index

        # Solo puede impartir clase en las franjas válidas
        for i in indices_ana:
            for f in range(franjas_totales):
                if f not in franjas_validas_ana:
                    model.Add(variables[(i, f)] == 0)

        # ⛔ Mª José López no puede impartir clase los jueves de 11:00 a 12:00
        dia_jueves = dias.index("Jueves")
        hora_prohibida = "11:00-12:00"

        if hora_prohibida in horas_por_dia:
            hora_idx = horas_por_dia.index(hora_prohibida)
            franja_prohibida = dia_jueves * len(horas_por_dia) + hora_idx

            indices_mariajose = df[df["Profesor"].str.lower().str.contains("mª josé lópez")].index

            for i in indices_mariajose:
                model.Add(variables[(i, franja_prohibida)] == 0)

        # 🎨 Preferencia: Arts a última hora del día (si es posible)
        ultima_hora = "13:00-14:00"
        if ultima_hora in horas_por_dia:
            hora_idx = horas_por_dia.index(ultima_hora)
            franjas_ultima_hora = [d * len(horas_por_dia) + hora_idx for d in range(len(dias))]

            indices_arts = df[df["Asignatura"].str.lower().str.contains("arts")].index

            for i in indices_arts:
                total_clases = int(df.loc[i, "Horas por semana"])
                if total_clases <= len(franjas_ultima_hora):
                    for f in range(franjas_totales):
                        if f not in franjas_ultima_hora:
                            model.Add(variables[(i, f)] == 0)

        # ✅ Restricción: Toni o Isabel Prieto deben impartir clase en 4ºA el miércoles de 09:00 a 10:00
        indices_objetivo = df[
            (df["Profesor"].isin(["Toni", "Isabel Prieto"])) &
            (df["Curso"] == "4ºA")
        ].index.tolist()

        # Calcular la franja correspondiente al miércoles 09:00-10:00
        dia_idx = dias.index("Miércoles")
        hora_idx = horas_por_dia.index("09:00-10:00")
        franja_objetivo = dia_idx * len(horas_por_dia) + hora_idx

        # Añadir restricción: al menos uno de los dos debe dar clase en esa franja
        model.Add(sum(variables[(i, franja_objetivo)] for i in indices_objetivo) >= 1)

        # 🔒 RESTRICCIÓN REVISADA: Máximo 1 clase diaria por asignatura en cada curso
        franjas_por_dia = len(horas_por_dia)

        # Creamos un conjunto único de combinaciones curso + asignatura
        combinaciones = df[["Curso", "Asignatura"]].drop_duplicates()

        for _, fila in combinaciones.iterrows():
            curso = fila["Curso"]
            asignatura = fila["Asignatura"]

            # Obtenemos todos los índices (filas) que tienen esa combinación
            indices = df[
                (df["Curso"] == curso) &
                (df["Asignatura"] == asignatura)
            ].index

            if indices.empty:
                continue

            for d in range(len(dias)):
                franjas_dia = [d * franjas_por_dia + h for h in range(franjas_por_dia)]
                clases_dia = [variables[(i, f)] for i in indices for f in franjas_dia]

                # ⚠️ Solo una clase por día para esa asignatura en ese curso
                model.Add(sum(clases_dia) <= 1)

        # RESOLVER
        # 👉 Permitir a la Jefa de Estudios regenerar el horario
        if st.button("🔄 Generar otro horario (versión alternativa)"):
            st.session_state["fuerza_regenerar"] = True

        # Usamos el mismo modelo pero reiniciando la semilla
        with st.spinner("🔄 Generando horario..."):
            solver = cp_model.CpSolver()
            solver.parameters.max_time_in_seconds = 60.0

            # Si el usuario pide una nueva versión, usamos una semilla aleatoria
            if st.session_state.get("fuerza_regenerar", False):
                import random
                random_seed = random.randint(1, 1000000)
                solver.parameters.random_seed = random_seed
                st.session_state["fuerza_regenerar"] = False  # Reinicia el estado

            status = solver.Solve(model)

        if status in [cp_model.FEASIBLE, cp_model.OPTIMAL]:
            st.success("✅ Horario generado con éxito.")
            st.session_state["solver"] = solver
            st.session_state["variables"] = variables
            st.session_state["df"] = df
            st.session_state["fecha_generacion"] = datetime.now().strftime("%d/%m/%Y %H:%M")
        else:
            st.error("❌ No se pudo generar un horario válido con las restricciones actuales.")

# -----------------------------------------------
# 🗕️ TAB 4: VISUALIZACIÓN
with tabs[3]:
    st.header("🗕️ Visualización del Horario")
    if "solver" not in st.session_state:
        st.info("🔔 Genera un horario en la pestaña 🚀 Generar Horario.")
    else:
        solver = st.session_state["solver"]
        variables = st.session_state["variables"]
        df = st.session_state["df"]
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
        horas_por_dia = [
            "09:00-10:00", "10:00-11:00", "11:00-12:00", "12:30-13:00", "13:00-14:00"
        ]
        franjas_totales = len(dias) * len(horas_por_dia)

        sub_tabs = st.tabs(["🎓 Ver por Curso", "👨‍🏫 Ver por Profesor"])

        # ----------------------------
        # 🎓 POR CURSO
        with sub_tabs[0]:
            curso_seleccionado = st.selectbox("📘 Selecciona un curso", sorted(df["Curso"].unique()))
            tabla = pd.DataFrame(index=horas_por_dia, columns=dias)
            for f in range(franjas_totales):
                dia = dias[f // len(horas_por_dia)]
                hora = horas_por_dia[f % len(horas_por_dia)]
                clases = []
                for i, fila in df.iterrows():
                    if fila["Curso"] == curso_seleccionado and solver.BooleanValue(variables[(i, f)]):
                        clases.append(f"{fila['Asignatura']} ({fila['Profesor']})")
                tabla.at[hora, dia] = "\n".join(clases) if clases else ""
            st.subheader(f"🗓 Horario para {curso_seleccionado}")
            st.dataframe(tabla, use_container_width=True, height=300)

        # ----------------------------
        # 👨‍🏫 POR PROFESOR
        with sub_tabs[1]:
            profe_seleccionado = st.selectbox("👨‍🏫 Selecciona un profesor", sorted(df["Profesor"].unique()))
            tabla = pd.DataFrame(index=horas_por_dia, columns=dias)
            for f in range(franjas_totales):
                dia = dias[f // len(horas_por_dia)]
                hora = horas_por_dia[f % len(horas_por_dia)]
                clases = []
                for i, fila in df.iterrows():
                    if fila["Profesor"] == profe_seleccionado and solver.BooleanValue(variables[(i, f)]):
                        clases.append(f"{fila['Asignatura']} ({fila['Curso']})")
                tabla.at[hora, dia] = "\n".join(clases) if clases else ""
            st.subheader(f"🗓 Horario para {profe_seleccionado}")
            st.dataframe(tabla, use_container_width=True, height=300)

# -----------------------------------------------
# 📅 TAB 5: EXPORTACIÓN
with tabs[4]:
    st.header("📅 Exportar Horario Generado")

    if "solver" not in st.session_state or "df" not in st.session_state:
        st.info("🔔 Genera un horario antes de exportarlo.")
    else:
        df = st.session_state["df"]
        solver = st.session_state["solver"]
        variables = st.session_state["variables"]
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
        horas_por_dia = [
            "09:00-10:00", "10:00-11:00", "11:00-12:00", "12:30-13:00", "13:00-14:00"
        ]
        franjas_totales = len(dias) * len(horas_por_dia)

        import io
        buffer = io.BytesIO()

        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            # 🧩 1. Exportar por Curso
            for curso in df["Curso"].unique():
                tabla = pd.DataFrame(index=horas_por_dia, columns=dias)
                for f in range(franjas_totales):
                    dia = dias[f // len(horas_por_dia)]
                    hora = horas_por_dia[f % len(horas_por_dia)]
                    clases = []
                    for i, fila in df.iterrows():
                        if fila["Curso"] == curso and solver.BooleanValue(variables[(i, f)]):
                            clases.append(f"{fila['Asignatura']} ({fila['Profesor']})")
                    tabla.at[hora, dia] = " | ".join(clases) if clases else ""
                tabla.index.name = "Hora"
                tabla.to_excel(writer, sheet_name=f"Curso - {curso}")

            # 👩‍🏫 2. Exportar por Profesor
            for profesor in df["Profesor"].unique():
                tabla = pd.DataFrame(index=horas_por_dia, columns=dias)
                for f in range(franjas_totales):
                    dia = dias[f // len(horas_por_dia)]
                    hora = horas_por_dia[f % len(horas_por_dia)]
                    clases = []
                    for i, fila in df.iterrows():
                        if fila["Profesor"] == profesor and solver.BooleanValue(variables[(i, f)]):
                            clases.append(f"{fila['Asignatura']} ({fila['Curso']})")
                    tabla.at[hora, dia] = " | ".join(clases) if clases else ""
                tabla.index.name = "Hora"
                tabla.to_excel(writer, sheet_name=f"Prof - {profesor[:25]}")

        buffer.seek(0)

        st.download_button(
            label="📥 Descargar horario completo en Excel",
            data=buffer,
            file_name=f"horario_completo_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# 📊 TAB 6: RESUMEN DE CARGAS
with tabs[5]:
    st.header("📊 Resumen de Carga Lectiva")

    if "df" not in st.session_state:
        st.info("🔔 Sube un archivo y genera el horario primero.")
    else:
        df = st.session_state["df"]
        solver = st.session_state["solver"]
        variables = st.session_state["variables"]

        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
        horas_por_dia = ["09:00-10:00", "10:00-11:00", "11:00-12:00", "12:30-13:00", "13:00-14:00"]
        franjas_totales = len(dias) * len(horas_por_dia)

        # Crear una lista con todas las clases asignadas finalmente
        registros = []

        for f in range(franjas_totales):
            dia = dias[f // len(horas_por_dia)]
            hora = horas_por_dia[f % len(horas_por_dia)]

            for i, fila in df.iterrows():
                if solver.BooleanValue(variables[(i, f)]):
                    registros.append({
                        "Profesor": fila["Profesor"],
                        "Asignatura": fila["Asignatura"],
                        "Curso": fila["Curso"],
                        "Día": dia,
                        "Hora": hora
                    })

        df_carga = pd.DataFrame(registros)

        st.subheader("👨‍🏫 Horas por Profesor")
        st.dataframe(df_carga.groupby("Profesor").size().reset_index(name="Horas"), use_container_width=True)

        st.subheader("📚 Horas por Asignatura")
        st.dataframe(df_carga.groupby("Asignatura").size().reset_index(name="Horas"), use_container_width=True)

        st.subheader("🎓 Horas por Curso")
        st.dataframe(df_carga.groupby("Curso").size().reset_index(name="Horas"), use_container_width=True)
        import matplotlib.pyplot as plt

        # 📊 GRÁFICO: Horas por Profesor
        st.subheader("📊 Gráfico de Carga por Profesor")
        prof_data = df_carga.groupby("Profesor").size().sort_values(ascending=False)

        fig1, ax1 = plt.subplots()
        prof_data.plot(kind='bar', ax=ax1)
        ax1.set_ylabel("Horas")
        ax1.set_xlabel("Profesor")
        ax1.set_title("Carga lectiva por profesor")
        ax1.tick_params(axis='x', rotation=45)
        st.pyplot(fig1)

        # 📚 GRÁFICO: Horas por Asignatura
        st.subheader("📚 Gráfico de Carga por Asignatura")
        asig_data = df_carga.groupby("Asignatura").size().sort_values(ascending=False)

        fig2, ax2 = plt.subplots()
        asig_data.plot(kind='bar', ax=ax2)
        ax2.set_ylabel("Horas")
        ax2.set_xlabel("Asignatura")
        ax2.set_title("Carga lectiva por asignatura")
        ax2.tick_params(axis='x', rotation=45)
        st.pyplot(fig2)

        # 🎓 GRÁFICO: Horas por Curso
        st.subheader("🎓 Gráfico de Carga por Curso")
        curso_data = df_carga.groupby("Curso").size().sort_values(ascending=False)

        fig3, ax3 = plt.subplots()
        curso_data.plot(kind='bar', ax=ax3)
        ax3.set_ylabel("Horas")
        ax3.set_xlabel("Curso")
        ax3.set_title("Carga lectiva por curso")
        ax3.tick_params(axis='x', rotation=45)
        st.pyplot(fig3)
