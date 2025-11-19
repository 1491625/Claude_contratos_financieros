"""
Sistema Inteligente de Análisis de Contratos de Préstamo
Interfaz principal Streamlit
"""

import streamlit as st
import pandas as pd
import tempfile
import os
from pathlib import Path
from datetime import datetime

# Importar módulos del sistema
from src.contract_parser import ContractParser, ContratoParseado
from src.financial_calculator import FinancialCalculator, ResultadoCalculo
from src.risk_assessor import RiskAssessor, ResultadoRiesgo, NivelRiesgo
from src.report_generator import ReportGenerator


# Configuración de la página
st.set_page_config(
    page_title="Análisis de Contratos de Préstamo",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1e3a5f;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4a5568;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f7fafc;
        border-radius: 10px;
        padding: 1rem;
        border-left: 4px solid #2c5282;
    }
    .risk-very-low { color: #22c55e; font-weight: bold; }
    .risk-low { color: #84cc16; font-weight: bold; }
    .risk-moderate { color: #eab308; font-weight: bold; }
    .risk-high { color: #f97316; font-weight: bold; }
    .risk-very-high { color: #ef4444; font-weight: bold; }
    .stAlert {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Función principal de la aplicación"""

    # Header
    st.markdown('<p class="main-header">Sistema de Análisis de Contratos de Préstamo</p>',
                unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Análisis automatizado de condiciones financieras, '
                'evaluación de riesgos y generación de reportes profesionales</p>',
                unsafe_allow_html=True)

    # Sidebar - Configuración
    with st.sidebar:
        st.header("Configuración")

        tipo_analisis = st.selectbox(
            "Tipo de Análisis",
            ["Completo", "Básico", "Enfocado en Riesgos"],
            help="Completo: Análisis financiero + riesgos + recomendaciones\n"
                 "Básico: Solo extracción y métricas principales\n"
                 "Enfocado en Riesgos: Análisis detallado de riesgos"
        )

        st.divider()

        st.subheader("Acerca del Sistema")
        st.info(
            "Este sistema analiza contratos de préstamo en formato PDF, "
            "extrayendo información clave, calculando métricas financieras, "
            "evaluando riesgos y generando recomendaciones."
        )

        st.divider()

        # Contratos de ejemplo
        st.subheader("Contratos de Ejemplo")
        ejemplo_dir = Path(__file__).parent
        ejemplos = list(ejemplo_dir.glob("*.pdf"))

        if ejemplos:
            ejemplo_seleccionado = st.selectbox(
                "Cargar ejemplo",
                ["Seleccionar..."] + [e.name for e in ejemplos]
            )

            if ejemplo_seleccionado != "Seleccionar...":
                ejemplo_path = ejemplo_dir / ejemplo_seleccionado
                if st.button("Usar este ejemplo"):
                    st.session_state['ejemplo_path'] = str(ejemplo_path)
                    st.rerun()

    # Área principal
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Cargar Contrato")

        # Carga de archivo
        archivo_subido = st.file_uploader(
            "Arrastra o selecciona un archivo PDF",
            type=['pdf'],
            help="Tamaño máximo: 10MB"
        )

        # O usar ejemplo
        if 'ejemplo_path' in st.session_state:
            archivo_path = st.session_state['ejemplo_path']
            st.success(f"Usando ejemplo: {Path(archivo_path).name}")
        elif archivo_subido:
            # Guardar archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                tmp.write(archivo_subido.getvalue())
                archivo_path = tmp.name
        else:
            archivo_path = None

    with col2:
        if archivo_path:
            st.subheader("Archivo Cargado")
            nombre_archivo = Path(archivo_path).name
            st.metric("Archivo", nombre_archivo)

            if st.button("Analizar Contrato", type="primary", use_container_width=True):
                st.session_state['analizar'] = True
                st.session_state['archivo_path'] = archivo_path

    # Ejecutar análisis
    if st.session_state.get('analizar') and st.session_state.get('archivo_path'):
        ejecutar_analisis(
            st.session_state['archivo_path'],
            tipo_analisis
        )


def ejecutar_analisis(archivo_path: str, tipo_analisis: str):
    """Ejecuta el análisis del contrato"""

    # Inicializar componentes
    parser = ContractParser()
    calculator = FinancialCalculator()
    assessor = RiskAssessor()
    generator = ReportGenerator()

    # Progress bar
    progress = st.progress(0)
    status = st.empty()

    try:
        # Paso 1: Parsear contrato
        status.text("Extrayendo información del contrato...")
        progress.progress(20)
        contrato = parser.parsear_contrato(archivo_path)

        if contrato.confianza_extraccion < 50:
            st.warning(
                f"La confianza de extracción es baja ({contrato.confianza_extraccion}%). "
                "Algunos datos pueden requerir revisión manual."
            )

        # Paso 2: Cálculos financieros
        status.text("Realizando cálculos financieros...")
        progress.progress(50)
        resultado_financiero = calculator.calcular(contrato)

        # Paso 3: Evaluación de riesgos
        status.text("Evaluando riesgos...")
        progress.progress(70)
        resultado_riesgo = assessor.evaluar(contrato, resultado_financiero)

        # Paso 4: Generar visualizaciones
        status.text("Generando visualizaciones...")
        progress.progress(90)
        figuras = generator.generar_visualizaciones(
            contrato, resultado_financiero, resultado_riesgo
        )

        progress.progress(100)
        status.empty()

        # Mostrar resultados
        mostrar_resultados(
            contrato,
            resultado_financiero,
            resultado_riesgo,
            figuras,
            tipo_analisis,
            generator
        )

    except Exception as e:
        progress.empty()
        status.empty()
        st.error(f"Error durante el análisis: {str(e)}")
        st.exception(e)


def mostrar_resultados(
    contrato: ContratoParseado,
    resultado_fin: ResultadoCalculo,
    resultado_riesgo: ResultadoRiesgo,
    figuras: dict,
    tipo_analisis: str,
    generator: ReportGenerator
):
    """Muestra los resultados del análisis"""

    st.divider()

    # Tabs principales
    if tipo_analisis == "Básico":
        tabs = st.tabs(["Resumen", "Datos Extraídos", "Exportar"])
    elif tipo_analisis == "Enfocado en Riesgos":
        tabs = st.tabs(["Resumen", "Riesgos", "Datos Extraídos", "Exportar"])
    else:
        tabs = st.tabs(["Resumen", "Análisis Financiero", "Riesgos", "Datos Extraídos", "Exportar"])

    tab_idx = 0

    # Tab Resumen
    with tabs[tab_idx]:
        mostrar_resumen(contrato, resultado_fin, resultado_riesgo)
    tab_idx += 1

    # Tab Análisis Financiero (solo en Completo)
    if tipo_analisis == "Completo":
        with tabs[tab_idx]:
            mostrar_analisis_financiero(contrato, resultado_fin, figuras)
        tab_idx += 1

    # Tab Riesgos (en Completo y Enfocado)
    if tipo_analisis in ["Completo", "Enfocado en Riesgos"]:
        with tabs[tab_idx]:
            mostrar_riesgos(resultado_riesgo, figuras)
        tab_idx += 1

    # Tab Datos Extraídos
    with tabs[tab_idx]:
        mostrar_datos_extraidos(contrato)
    tab_idx += 1

    # Tab Exportar
    with tabs[tab_idx]:
        mostrar_exportar(contrato, resultado_fin, resultado_riesgo, generator)


def mostrar_resumen(
    contrato: ContratoParseado,
    resultado_fin: ResultadoCalculo,
    resultado_riesgo: ResultadoRiesgo
):
    """Muestra el resumen ejecutivo"""

    st.header("Resumen Ejecutivo")

    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Monto",
            f"{contrato.moneda} {contrato.monto_principal:,.0f}"
        )

    with col2:
        st.metric(
            "CAT",
            f"{resultado_fin.costo_anual_total}%",
            delta=f"{resultado_fin.diferencia_vs_mercado:+.1f}% vs mercado",
            delta_color="inverse"
        )

    with col3:
        st.metric(
            "Cuota Mensual",
            f"{contrato.moneda} {resultado_fin.cuota_mensual:,.2f}"
        )

    with col4:
        nivel = resultado_riesgo.nivel_riesgo.value.replace("_", " ").title()
        st.metric(
            "Score Riesgo",
            f"{resultado_riesgo.score_total}/100",
            delta=nivel
        )

    st.divider()

    # Recomendación
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Recomendación")

        if resultado_riesgo.accion_sugerida == "Aceptar":
            st.success(resultado_riesgo.recomendacion_general)
        elif resultado_riesgo.accion_sugerida == "Negociar":
            st.warning(resultado_riesgo.recomendacion_general)
        else:
            st.error(resultado_riesgo.recomendacion_general)

    with col2:
        st.subheader("Acción Sugerida")
        if resultado_riesgo.accion_sugerida == "Aceptar":
            st.markdown(f"### :green[{resultado_riesgo.accion_sugerida}]")
        elif resultado_riesgo.accion_sugerida == "Negociar":
            st.markdown(f"### :orange[{resultado_riesgo.accion_sugerida}]")
        else:
            st.markdown(f"### :red[{resultado_riesgo.accion_sugerida}]")

    # Puntos clave
    if resultado_riesgo.puntos_negociacion:
        st.subheader("Puntos a Negociar")
        for i, punto in enumerate(resultado_riesgo.puntos_negociacion[:5], 1):
            st.markdown(f"{i}. {punto}")


def mostrar_analisis_financiero(
    contrato: ContratoParseado,
    resultado: ResultadoCalculo,
    figuras: dict
):
    """Muestra el análisis financiero detallado"""

    st.header("Análisis Financiero")

    col1, col2 = st.columns(2)

    with col1:
        # Desglose de costos
        st.subheader("Desglose de Costos")

        costo_total = resultado.costo_total_financiamiento
        datos_costos = {
            "Concepto": ["Capital", "Intereses", "Comisiones", "TOTAL"],
            "Monto": [
                f"{contrato.moneda} {contrato.monto_principal:,.2f}",
                f"{contrato.moneda} {resultado.total_intereses:,.2f}",
                f"{contrato.moneda} {resultado.total_comisiones:,.2f}",
                f"{contrato.moneda} {costo_total:,.2f}"
            ],
            "% del Total": [
                f"{(contrato.monto_principal/costo_total*100):.1f}%",
                f"{(resultado.total_intereses/costo_total*100):.1f}%",
                f"{(resultado.total_comisiones/costo_total*100):.1f}%",
                "100%"
            ]
        }

        st.dataframe(
            pd.DataFrame(datos_costos),
            use_container_width=True,
            hide_index=True
        )

    with col2:
        # Gráfico de distribución
        if 'distribucion_costos' in figuras:
            st.plotly_chart(figuras['distribucion_costos'], use_container_width=True)

    # Gráfico de amortización
    st.subheader("Evolución de Amortización")
    if 'amortizacion' in figuras:
        st.plotly_chart(figuras['amortizacion'], use_container_width=True)

    # Tabla de amortización
    with st.expander("Ver Tabla de Amortización Completa"):
        df_amort = pd.DataFrame([
            {
                'Período': f.periodo,
                'Fecha': f.fecha,
                'Cuota': f"{f.cuota:,.2f}",
                'Capital': f"{f.capital:,.2f}",
                'Interés': f"{f.interes:,.2f}",
                'Saldo': f"{f.saldo:,.2f}"
            }
            for f in resultado.tabla_amortizacion
        ])
        st.dataframe(df_amort, use_container_width=True, hide_index=True)

    # Análisis de sensibilidad
    if resultado.sensibilidad:
        st.subheader("Análisis de Sensibilidad")
        st.info(f"Índice de referencia: {resultado.sensibilidad.get('indice_referencia', 'N/A')}")

        if 'sensibilidad' in figuras:
            st.plotly_chart(figuras['sensibilidad'], use_container_width=True)


def mostrar_riesgos(resultado_riesgo: ResultadoRiesgo, figuras: dict):
    """Muestra la evaluación de riesgos"""

    st.header("Evaluación de Riesgos")

    col1, col2 = st.columns([1, 1])

    with col1:
        # Score general
        st.subheader("Score General")

        score = resultado_riesgo.score_total
        if score >= 80:
            color = "green"
        elif score >= 60:
            color = "blue"
        elif score >= 40:
            color = "orange"
        else:
            color = "red"

        st.markdown(f"### :{color}[{score}/100]")
        st.caption(resultado_riesgo.nivel_riesgo.value.replace("_", " ").title())

        # Radar de riesgos
        if 'radar_riesgos' in figuras:
            st.plotly_chart(figuras['radar_riesgos'], use_container_width=True)

    with col2:
        # Scores por categoría
        st.subheader("Por Categoría")

        for sc in resultado_riesgo.scores_categorias:
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.progress(sc.score / 100)
            with col_b:
                st.caption(f"{sc.categoria}: {sc.score}")

    # Red flags
    if resultado_riesgo.red_flags:
        st.subheader("Alertas Identificadas")

        for rf in resultado_riesgo.red_flags:
            if rf.severidad.value in ["alta", "critica"]:
                st.error(f"**{rf.tipo.upper()}**: {rf.descripcion}")
            elif rf.severidad.value == "media":
                st.warning(f"**{rf.tipo.upper()}**: {rf.descripcion}")
            else:
                st.info(f"**{rf.tipo.upper()}**: {rf.descripcion}")

    # Fortalezas y debilidades
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Fortalezas")
        for f in resultado_riesgo.fortalezas:
            st.markdown(f"✅ {f}")

    with col2:
        st.subheader("Debilidades")
        for d in resultado_riesgo.debilidades:
            st.markdown(f"⚠️ {d}")


def mostrar_datos_extraidos(contrato: ContratoParseado):
    """Muestra los datos extraídos del contrato"""

    st.header("Datos Extraídos")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Información General")

        datos_generales = {
            "Prestamista": contrato.prestamista or "No identificado",
            "Prestatario": contrato.prestatario or "No identificado",
            "Monto": f"{contrato.moneda} {contrato.monto_principal:,.2f}",
            "Plazo": f"{contrato.plazo_meses} meses",
            "Frecuencia de Pago": contrato.frecuencia_pago.value.title()
        }

        for k, v in datos_generales.items():
            st.markdown(f"**{k}:** {v}")

        st.subheader("Tasa de Interés")

        if contrato.tipo_tasa.value == "variable":
            st.markdown(f"**Tipo:** Variable")
            st.markdown(f"**Referencia:** {contrato.indice_referencia or 'N/A'}")
            st.markdown(f"**Spread:** {contrato.spread_bps or 0} bps")
            if contrato.cap:
                st.markdown(f"**Cap:** {contrato.cap}%")
            if contrato.floor:
                st.markdown(f"**Floor:** {contrato.floor}%")
        else:
            st.markdown(f"**Tipo:** Fija")
            st.markdown(f"**Tasa Nominal:** {contrato.tasa_nominal}%")

    with col2:
        st.subheader("Garantías")

        if contrato.garantias:
            for g in contrato.garantias:
                st.markdown(f"• {g.descripcion}")
        else:
            st.markdown("Sin garantías identificadas")

        st.subheader("Comisiones")

        if contrato.comisiones:
            for c in contrato.comisiones:
                valor = f"{c.valor}%" if c.es_porcentaje else f"{contrato.moneda} {c.valor:,.2f}"
                st.markdown(f"• **{c.tipo.title()}:** {valor}")
        else:
            st.markdown("Sin comisiones identificadas")

        st.subheader("Prepago")

        if contrato.prepago:
            st.markdown(f"**Permitido:** {'Sí' if contrato.prepago.permitido else 'No'}")
            if contrato.prepago.penalizacion > 0:
                st.markdown(f"**Penalización:** {contrato.prepago.penalizacion}%")
                st.markdown(f"**Período:** Primeros {contrato.prepago.periodo_penalizacion_meses} meses")

    # Covenants
    if contrato.covenants:
        st.subheader("Covenants")
        for cov in contrato.covenants:
            st.markdown(f"• **{cov.tipo}** {cov.operador} {cov.valor}")

    # Metadatos de extracción
    with st.expander("Metadatos de Extracción"):
        st.metric("Confianza", f"{contrato.confianza_extraccion}%")

        if contrato.advertencias:
            st.warning("Advertencias:")
            for adv in contrato.advertencias:
                st.markdown(f"• {adv}")


def mostrar_exportar(
    contrato: ContratoParseado,
    resultado_fin: ResultadoCalculo,
    resultado_riesgo: ResultadoRiesgo,
    generator: ReportGenerator
):
    """Muestra opciones de exportación"""

    st.header("Exportar Resultados")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Reporte PDF")

        if st.button("Generar Reporte PDF", type="primary"):
            with st.spinner("Generando reporte..."):
                # Crear archivo temporal
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                    ruta_pdf = tmp.name

                generator.generar_reporte_completo(
                    contrato, resultado_fin, resultado_riesgo, ruta_pdf
                )

                # Leer y ofrecer descarga
                with open(ruta_pdf, 'rb') as f:
                    pdf_bytes = f.read()

                st.download_button(
                    label="Descargar Reporte PDF",
                    data=pdf_bytes,
                    file_name=f"analisis_contrato_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf"
                )

                # Limpiar archivo temporal
                os.unlink(ruta_pdf)

    with col2:
        st.subheader("Datos Excel")

        if st.button("Exportar a Excel"):
            with st.spinner("Generando Excel..."):
                # Crear DataFrame de amortización
                df_amort = pd.DataFrame([
                    {
                        'Período': f.periodo,
                        'Fecha': f.fecha,
                        'Cuota': f.cuota,
                        'Capital': f.capital,
                        'Interés': f.interes,
                        'Saldo': f.saldo
                    }
                    for f in resultado_fin.tabla_amortizacion
                ])

                # Crear buffer
                buffer = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')

                with pd.ExcelWriter(buffer.name, engine='openpyxl') as writer:
                    # Hoja de resumen
                    resumen = pd.DataFrame([{
                        'Monto': contrato.monto_principal,
                        'Moneda': contrato.moneda,
                        'Tasa Nominal': contrato.tasa_nominal,
                        'Plazo (meses)': contrato.plazo_meses,
                        'CAT': resultado_fin.costo_anual_total,
                        'TEA': resultado_fin.tasa_efectiva_anual,
                        'Total Intereses': resultado_fin.total_intereses,
                        'Total Comisiones': resultado_fin.total_comisiones,
                        'Score Riesgo': resultado_riesgo.score_total
                    }])
                    resumen.to_excel(writer, sheet_name='Resumen', index=False)

                    # Hoja de amortización
                    df_amort.to_excel(writer, sheet_name='Amortización', index=False)

                # Leer y ofrecer descarga
                with open(buffer.name, 'rb') as f:
                    excel_bytes = f.read()

                st.download_button(
                    label="Descargar Excel",
                    data=excel_bytes,
                    file_name=f"analisis_contrato_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                # Limpiar
                os.unlink(buffer.name)


if __name__ == "__main__":
    main()
