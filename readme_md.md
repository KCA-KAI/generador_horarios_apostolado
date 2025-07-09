# 📚 Generador de Horarios Escolares v2.0
**Colegio Apostolado del Sagrado Corazón**

Sistema automatizado avanzado para generar horarios escolares sin conflictos, con soporte para **franjas de 30 minutos** y **restricciones específicas por profesor**. Diseñado para facilitar la gestión académica completa del colegio.

## 🎯 Características Principales

- ✅ **Sistema de franjas de 30 minutos** - Soporte completo para clases de 0.5h, 1h, 1.5h, 2h, etc.
- ✅ **Algoritmo de optimización matemática** con OR-Tools de Google
- ✅ **Restricciones específicas por profesor** - Horarios personalizados y conflictos automáticos
- ✅ **Interfaz visual mejorada** con pestañas organizadas y diagnósticos
- ✅ **Carga desde Excel** con validación automática de datos
- ✅ **Múltiples formatos** de descarga (Excel completo con hojas separadas)
- ✅ **Generación de versiones alternativas** con semillas aleatorias
- ✅ **Validación inteligente** de viabilidad y verificación de restricciones
- ✅ **Franjas consecutivas** automáticas para clases largas
- ✅ **Respeto del recreo** (12:00-12:30 sin clases programadas)

## 🚀 Instalación y Configuración

### Prerequisitos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Instalación

1. **Clona o descarga el proyecto**
```bash
git clone [URL-del-repositorio]
cd generador-horarios-v2
```

2. **Instala las dependencias**
```bash
pip install streamlit pandas ortools xlsxwriter openpyxl
```

3. **Ejecuta la aplicación**
```bash
streamlit run generador_horarios_apostolado_v2.py
```

4. **Abre tu navegador**
   - La aplicación se abrirá automáticamente en `http://localhost:8501`
   - Si no se abre, ve manualmente a esa dirección

## 📋 Formato de Datos Requerido

El archivo Excel debe contener **exactamente** estas columnas:

| Profesor | Asignatura | Curso | Horas por semana |
|----------|------------|-------|------------------|
| María García | Matemáticas | 1ºA | 2.5 |
| Juan Pérez | Lengua | 1ºB | 1.5 |
| Ana López | Inglés | 2ºA | 3.0 |
| Juan Carlos | Educación física | secundaria | 2.0 |

### Especificaciones Actualizadas:
- **Profesor**: Nombre completo del profesor (sensible a mayúsculas/minúsculas)
- **Asignatura**: Materia que imparte (ej: Matemáticas, Inglés, Educación física)
- **Curso**: Curso al que va dirigida (ej: 1ºA, 2ºB, 6ºC, secundaria, infantil)
- **Horas por semana**: **IMPORTANTE**: Debe ser múltiplo de 0.5 (ej: 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, etc.)

## ⏰ Sistema de Franjas de 30 Minutos

### Franjas Horarias Disponibles:
- 📚 **09:00 - 09:30** (Franja 1)
- 📚 **09:30 - 10:00** (Franja 2)
- 📚 **10:00 - 10:30** (Franja 3)
- 📚 **10:30 - 11:00** (Franja 4)
- 📚 **11:00 - 11:30** (Franja 5)
- 📚 **11:30 - 12:00** (Franja 6)
- 🍎 **12:00 - 12:30** (RECREO - Sin clases)
- 📚 **12:30 - 13:00** (Franja 7)
- 📚 **13:00 - 13:30** (Franja 8)
- 📚 **13:30 - 14:00** (Franja 9)

### Equivalencias de Horas:
- **0.5 horas** = 1 franja de 30 minutos
- **1.0 hora** = 2 franjas consecutivas (ej: 09:00-10:00)
- **1.5 horas** = 3 franjas consecutivas (ej: 09:00-10:30)
- **2.0 horas** = 4 franjas consecutivas (ej: 09:00-11:00)
- **2.5 horas** = 5 franjas consecutivas (ej: 09:00-11:30)

### Días de la Semana:
- Lunes a Viernes (5 días laborables)
- **Total**: 45 franjas de 30 minutos disponibles por semana

## 🎯 Restricciones Específicas Implementadas

### Profesores con Horarios Limitados:

**🏃‍♂️ Juan Carlos (Educación física - secundaria)**
- Solo puede impartir clases entre 10:00-12:00 (Lunes y Martes)
- Franjas válidas: 10:00-10:30, 10:30-11:00, 11:00-11:30, 11:30-12:00

**🎵 Toni (Coro - coro secundaria)**
- Solo puede impartir clases de 10:00-11:00 cualquier día
- Debe tener exactamente 2 horas semanales (4 franjas de 30 min)

**👨‍🏫 Iván**
- Debe tener hora libre cuando se imparte Inglés en cursos: 2ºA, 2ºB, 2ºC, 4ºA, 4ºB, 4ºC, 6ºA, 6ºB, 6ºC

**👨‍🏫 Fernando**
- Debe tener hora libre cuando se imparte Inglés en cursos: 1ºA, 1ºB, 1ºC, 3ºA, 3ºB, 3ºC, 5ºA, 5ºB, 5ºC

**👩‍🏫 Andrea (Inglés - infantil)**
- Debe impartir exactamente 1 clase diaria de 12:30-13:00 (Lunes a Viernes)

### Lista de Profesores con Clases Obligatorias 12:30-13:00:
Los siguientes profesores DEBEN tener exactamente 1 clase en horario 12:30-13:00 durante la semana:

- Alicia González (Lengua - 2ºA)
- Alicia Iglesias (Lengua - 2ºB)
- Álvaro Encinas (Lengua - 2ºC)
- Lucia Alegre (Religión - 1ºA)
- Arancha (Religión - 1ºB, 1ºC)
- Mª José López (Religión - 3ºA, 3ºB, 3ºC)
- María Sierra (Lengua - 4ºA)
- Miriam (Lengua/Matemáticas - 4ºB)
- Lili (Lengua/Matemáticas - 4ºC)
- Toni (Educación física - 4ºA, 4ºB, 4ºC)
- Laura Velasco (Matemáticas - 4ºA)
- Mercedes (Matemáticas/Religión - 5ºA, 5ºB)
- Inés (Inglés - 5ºA, 5ºB, 5ºC)
- Ana Isabel (Religión/Matemáticas - 5ºC)
- Raquel Díez (Religión/Matemáticas - 5ºB, 6ºA, Naturales - 6ºB)
- Fernando (Inglés/Valores/Sociales - 6ºA, 6ºB, 6ºC)
- Irene (Matemáticas/Valores - 6ºB)
- Juan Carlos (Valores/Sociales/Naturales/Matemáticas - 6ºA, 6ºC)
- Toni (Sociales - 6ºB)

### Preferencias de Horario:
- **📚 Lengua y Matemáticas**: Preferencia por primeras horas (09:00-11:00)
- **🎨 Arts/Arte**: Preferencia por últimas horas (13:00-14:00)

## 🎮 Guía de Uso Actualizada

### Paso 1: Preparar Datos
1. Crea un archivo Excel con las columnas requeridas
2. **IMPORTANTE**: Asegúrate de que "Horas por semana" sea múltiplo de 0.5
3. Verifica nombres exactos de profesores (respeta mayúsculas y acentos)
4. Usa nombres consistentes para cursos (ej: 1ºA, 2ºB, 6ºC)

### Paso 2: Cargar y Validar
1. Ve a la pestaña **📁 Cargar Datos**
2. Sube tu archivo Excel o CSV
3. Verifica que los datos se carguen correctamente
4. Ve a la pestaña **🔍 Diagnóstico** para revisar viabilidad

### Paso 3: Generar Horario
1. Ve a la pestaña **🚀 Generar Horario**
2. El sistema aplicará automáticamente todas las restricciones
3. Haz clic en **"Generar Horario"**
4. Para obtener versiones alternativas, usa **🎲 "Generar Otra Posible Solución"**

### Paso 4: Visualizar Resultados
1. Ve a la pestaña **📅 Visualización**
2. Revisa horarios **por curso** o **por profesor**
3. Usa los filtros para ver horarios específicos
4. Verifica que no hay conflictos

### Paso 5: Exportar
1. Ve a la pestaña **💾 Exportar**
2. Descarga el archivo Excel completo con:
   - Hoja de horarios consolidados
   - Hojas separadas por curso
   - Hojas separadas por profesor
3. Revisa las verificaciones automáticas de calidad

## 🔧 Funcionalidades Técnicas Avanzadas

### Algoritmo de Optimización
- **Motor**: OR-Tools CP-SAT (Constraint Programming)
- **Método**: Programación con restricciones y optimización
- **Validaciones**: Prevención matemática de conflictos
- **Optimización**: Minimización de violaciones de preferencias
- **Escalabilidad**: Maneja cientos de restricciones simultáneamente

### Validaciones Automáticas Avanzadas
- ✅ **Verificación de franjas válidas** (múltiplos de 0.5h)
- ✅ **Detección de conflictos** imposibles de resolver
- ✅ **Validación de restricciones específicas** por profesor
- ✅ **Análisis de carga docente** y distribución
- ✅ **Verificación post-generación** de calidad del horario

### Nuevas Características v2.0
- 🎯 **Franjas consecutivas automáticas** para clases largas
- 🔄 **Generación de versiones alternativas** con diferentes semillas
- 📊 **Diagnóstico completo** de viabilidad antes de generar
- 🎨 **Interfaz mejorada** con pestañas organizadas
- 📈 **Métricas detalladas** de utilización y conflictos
- 🔍 **Verificación automática** de calidad del horario generado

## ⚠️ Solución de Problemas Actualizada

### Error: "Horas que no son múltiplos de 0.5"
**Causa:** El Excel contiene valores como 1.25, 2.33, etc.
**Solución:** Cambia todos los valores a múltiplos de 0.5 (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, etc.)

### Error: "No se pudo generar un horario válido"
**Posibles causas:**
- Restricciones conflictivas imposibles de resolver
- Demasiadas horas concentradas en pocas franjas
- Nombres de profesores inconsistentes

**Soluciones:**
1. Verifica que los nombres de profesores coincidan exactamente con las restricciones
2. Reduce la carga de profesores con muchas restricciones
3. Intenta generar varias versiones aleatorias
4. Revisa el diagnóstico de viabilidad antes de generar

### Error: "Restricción no aplicada correctamente"
**Causa:** Nombres de profesores, asignaturas o cursos no coinciden exactamente
**Solución:** 
- Juan Carlos (no "juan carlos" o "JUAN CARLOS")
- Educación física (no "educacion fisica" o "Ed. Física")
- secundaria (no "Secundaria" o "SECUNDARIA")

### Horario con conflictos
**Si el verificador detecta conflictos:**
1. Revisa que no hay duplicados en los datos de entrada
2. Verifica que las restricciones no son contradictorias
3. Regenera con una semilla diferente

## 🎨 Personalización Avanzada

### Modificar Franjas Horarias
```python
def generar_franjas_30_minutos():
    franjas_por_dia = [
        "09:00-09:30", "09:30-10:00",  # Modifica aquí
        "10:00-10:30", "10:30-11:00",
        # ... añadir más franjas
    ]
    return dias, franjas_por_dia
```

### Añadir Nuevas Restricciones de Profesor
```python
# En la función adaptar_restricciones_especificas
indices_nuevo_profesor = df[
    (df["Profesor"].str.lower() == "nombre profesor") &
    (df["Asignatura"].str.lower() == "asignatura") &
    (df["Curso"].str.lower() == "curso")
].index.tolist()

if indices_nuevo_profesor:
    # Definir restricciones específicas aquí
```

### Modificar Preferencias de Horario
```python
# Para añadir nuevas preferencias de asignaturas
if asignatura in ["nueva_asignatura", "otra_asignatura"]:
    # Definir preferencias horarias aquí
```

## 📊 Métricas y Análisis

### Estadísticas Generadas:
- **Utilización de franjas**: Porcentaje de uso por día/hora
- **Carga docente**: Distribución de horas por profesor
- **Eficiencia del horario**: Franjas libres vs ocupadas
- **Cumplimiento de restricciones**: Verificación automática
- **Conflictos detectados**: Análisis de problemas potenciales

### Reportes de Calidad:
- ✅ **Conflictos de profesor**: 0 (verificado automáticamente)
- ✅ **Conflictos de curso**: 0 (verificado automáticamente) 
- ✅ **Horas correctas**: Todas las asignaturas tienen las horas asignadas
- ✅ **Restricciones cumplidas**: Todas las reglas específicas respetadas

## 📞 Soporte Técnico

### Antes de Contactar Soporte:
1. **Revisa el diagnóstico** en la pestaña correspondiente
2. **Verifica el formato** de tu archivo Excel
3. **Comprueba las horas** (deben ser múltiplos de 0.5)
4. **Revisa los nombres** (deben coincidir exactamente)

### Información para Soporte:
- Archivo Excel original
- Mensaje de error completo
- Capturas de pantalla del diagnóstico
- Versión del navegador utilizado

## 📝 Notas de Versión

### Versión 2.0.0 🎉
- ✅ **Sistema de franjas de 30 minutos** completamente implementado
- ✅ **Algoritmo OR-Tools** para optimización matemática
- ✅ **Restricciones específicas** para 6 tipos de profesores
- ✅ **Lista de 42 profesores** con horarios obligatorios 12:30-13:00
- ✅ **Franjas consecutivas automáticas** para clases largas
- ✅ **Generación de versiones alternativas** aleatorias
- ✅ **Interfaz completamente rediseñada** con 5 pestañas
- ✅ **Exportación avanzada** con hojas separadas por curso/profesor
- ✅ **Verificación automática** de calidad del horario
- ✅ **Documentación completa** actualizada

### Versión 1.0.0
- ✅ Sistema básico de generación de horarios
- ✅ Interfaz web con Streamlit
- ✅ Carga desde Excel básica

## 🔮 Roadmap Futuro

### Versión 2.1 (Planificada)
- 🔄 **Modo interactivo** para ajustar horarios manualmente
- 📱 **Versión móvil** optimizada
- 🔗 **Integración con Google Calendar**
- 📧 **Notificaciones automáticas** de cambios

### Versión 2.2 (Planificada)
- 🤖 **IA para sugerencias** de mejora de horarios
- 📊 **Dashboard analítico** avanzado
- 🔄 **Sincronización automática** con sistemas escolares
- 🌐 **Multi-idioma** (Español/Inglés)

## 🏫 Implementación en el Colegio

Este sistema v2.0 ha sido **completamente rediseñado** para el **Colegio Apostolado del Sagrado Corazón**, incorporando:

- ✅ **Todos los profesores reales** del colegio con sus restricciones específicas
- ✅ **Horarios exactos** del funcionamiento actual del centro
- ✅ **Cursos específicos** desde Infantil hasta 6º de Primaria
- ✅ **Materias especiales** como Coro, Educación Física, Religión, etc.
- ✅ **Conflictos reales** resueltos automáticamente (Iván/Fernando vs Inglés)

---

**Desarrollado por:** 🚀 **Innonea Lab** - Soluciones de Automatización  
**Versión:** 2.0.0  
**Fecha:** Enero 2025  
**Tecnología:** Python + Streamlit + OR-Tools  
**Especializado para:** Colegio Apostolado del Sagrado Corazón