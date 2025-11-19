"""
Generador de Reportes Profesionales
Genera reportes PDF con análisis narrativo y visualizaciones
"""

import io
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from jinja2 import Template
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT

from .contract_parser import ContratoParseado, TipoTasa, TipoGarantia
from .financial_calculator import ResultadoCalculo, FilaAmortizacion
from .risk_assessor import ResultadoRiesgo, NivelRiesgo, SeveridadRedFlag


class ReportGenerator:
    """Generador de reportes profesionales de análisis de contratos"""

    def __init__(self):
        """Inicializa el generador con estilos y templates"""
        self.styles = self._crear_estilos()
        self.templates = self._cargar_templates()

    def _crear_estilos(self) -> Dict:
        """Crea estilos personalizados para el reporte"""
        styles = getSampleStyleSheet()

        # Título principal
        styles.add(ParagraphStyle(
            name='TituloPrincipal',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1e3a5f')
        ))

        # Subtítulo
        styles.add(ParagraphStyle(
            name='Subtitulo',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.HexColor('#2c5282')
        ))

        # Sección
        styles.add(ParagraphStyle(
            name='Seccion',
            parent=styles['Heading3'],
            fontSize=12,
            spaceAfter=8,
            spaceBefore=12,
            textColor=colors.HexColor('#2d3748')
        ))

        # Texto normal
        styles.add(ParagraphStyle(
            name='TextoNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_JUSTIFY
        ))

        # Texto destacado
        styles.add(ParagraphStyle(
            name='TextoDestacado',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            textColor=colors.HexColor('#c53030'),
            fontName='Helvetica-Bold'
        ))

        # Texto positivo
        styles.add(ParagraphStyle(
            name='TextoPositivo',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            textColor=colors.HexColor('#276749'),
            fontName='Helvetica-Bold'
        ))

        # Nota al pie
        styles.add(ParagraphStyle(
            name='NotaPie',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey
        ))

        return styles

    def _cargar_templates(self) -> Dict[str, Template]:
        """Carga templates Jinja2 para narrativas"""

        templates = {}

        # Template resumen ejecutivo
        templates['resumen_ejecutivo'] = Template("""
El contrato de préstamo analizado presenta las siguientes características principales:

{% if tipo_tasa == 'fija' %}
Se trata de un préstamo a tasa fija del {{ tasa_nominal }}% nominal anual, lo que proporciona
certidumbre sobre el costo del financiamiento durante todo el plazo.
{% else %}
Se trata de un préstamo a tasa variable referenciada a {{ indice_referencia }} + {{ spread }} puntos base.
{% if cap %}El contrato incluye un cap (techo) del {{ cap }}% que limita la exposición al alza.{% endif %}
{% if floor %}Se establece un floor (piso) del {{ floor }}%.{% endif %}
{% endif %}

El monto principal de {{ moneda }} {{ "{:,.0f}".format(monto) }} se amortizará en {{ plazo }} meses
con pagos {{ frecuencia }}s. {% if es_bullet %}La estructura es tipo bullet, con pago del capital
al vencimiento.{% endif %}{% if gracia > 0 %} Se establece un período de gracia de {{ gracia }} meses.{% endif %}

El Costo Anual Total (CAT) calculado es del {{ cat }}%, {% if diferencia_mercado > 1.5 %}
lo cual representa {{ diferencia_mercado }}% por encima del promedio de mercado para operaciones similares.
{% elif diferencia_mercado < -0.5 %}
representando condiciones favorables de {{ diferencia_mercado|abs }}% bajo el promedio de mercado.
{% else %}
en línea con las condiciones de mercado para este tipo de operaciones.
{% endif %}
""")

        # Template análisis de garantías
        templates['analisis_garantias'] = Template("""
{% if tipo_garantia == 'mixta' %}
El préstamo está respaldado por garantías mixtas, combinando garantías reales y personales:
{% for g in garantias %}
- {{ g.descripcion }}
{% endfor %}
Esta combinación de garantías indica un perfil de riesgo que el prestamista considera relevante.
{% elif tipo_garantia == 'real' %}
El préstamo cuenta con garantías reales:
{% for g in garantias %}
- {{ g.descripcion }}
{% endfor %}
Las garantías reales proporcionan al prestamista mayor seguridad de recuperación.
{% elif tipo_garantia == 'personal' %}
El préstamo se respalda únicamente con garantías personales:
{% for g in garantias %}
- {{ g.descripcion }}
{% endfor %}
{% else %}
El préstamo no requiere garantías específicas, lo cual puede reflejar un perfil crediticio sólido.
{% endif %}
""")

        # Template análisis de riesgos
        templates['analisis_riesgos'] = Template("""
La evaluación integral de riesgos arroja un score de {{ score }}/100, clasificado como
riesgo {{ nivel }}.

{% if score >= 70 %}
El contrato presenta un perfil de riesgo aceptable para el prestatario, con condiciones
generalmente favorables en las principales categorías evaluadas.
{% elif score >= 40 %}
Se identifican áreas de atención que requieren consideración antes de proceder:
{% for debilidad in debilidades[:3] %}
• {{ debilidad }}
{% endfor %}
{% else %}
El análisis identifica múltiples factores de riesgo significativo:
{% for debilidad in debilidades[:4] %}
• {{ debilidad }}
{% endfor %}
Se recomienda evaluar cuidadosamente las alternativas disponibles.
{% endif %}
""")

        # Template recomendaciones
        templates['recomendaciones'] = Template("""
{% if accion == 'Aceptar' %}
RECOMENDACIÓN: PROCEDER CON LA FIRMA

Las condiciones del contrato son favorables y el nivel de riesgo es aceptable.
Se recomienda proceder con la operación, asegurando:

1. Revisión legal del contrato antes de la firma
2. Verificación de todas las condiciones numéricas
3. Confirmación de capacidad de pago según proyecciones de flujo

{% elif accion == 'Negociar' %}
RECOMENDACIÓN: NEGOCIAR ANTES DE PROCEDER

Se identifican puntos que pueden mejorarse mediante negociación:

{% for punto in puntos_negociacion[:5] %}
{{ loop.index }}. {{ punto }}
{% endfor %}

Se sugiere presentar estos puntos al prestamista antes de proceder con la firma.

{% else %}
RECOMENDACIÓN: NO PROCEDER / BUSCAR ALTERNATIVAS

Las condiciones actuales del contrato presentan un nivel de riesgo o costo
que no se considera favorable. Se recomienda:

1. Solicitar al prestamista una revisión sustancial de las condiciones
2. Evaluar alternativas de financiamiento en el mercado
3. Considerar ajustar el monto o plazo solicitado

{% endif %}
""")

        return templates

    def generar_reporte_completo(
        self,
        contrato: ContratoParseado,
        resultado_financiero: ResultadoCalculo,
        resultado_riesgo: ResultadoRiesgo,
        ruta_salida: str
    ) -> str:
        """Genera el reporte PDF completo"""

        # Crear documento
        doc = SimpleDocTemplate(
            ruta_salida,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        # Contenido del reporte
        contenido = []

        # Portada
        contenido.extend(self._generar_portada(contrato))

        # Resumen ejecutivo
        contenido.extend(self._generar_resumen_ejecutivo(
            contrato, resultado_financiero, resultado_riesgo
        ))

        # Análisis financiero
        contenido.append(PageBreak())
        contenido.extend(self._generar_analisis_financiero(
            contrato, resultado_financiero
        ))

        # Evaluación de riesgos
        contenido.append(PageBreak())
        contenido.extend(self._generar_seccion_riesgos(resultado_riesgo))

        # Recomendaciones
        contenido.extend(self._generar_recomendaciones(resultado_riesgo))

        # Anexo: Tabla de amortización
        contenido.append(PageBreak())
        contenido.extend(self._generar_anexo_amortizacion(resultado_financiero))

        # Pie de página
        contenido.extend(self._generar_pie_pagina())

        # Construir PDF
        doc.build(contenido)

        return ruta_salida

    def _generar_portada(self, contrato: ContratoParseado) -> List:
        """Genera la portada del reporte"""

        contenido = []

        # Título
        contenido.append(Spacer(1, 2*cm))
        contenido.append(Paragraph(
            "ANÁLISIS DE CONTRATO DE PRÉSTAMO",
            self.styles['TituloPrincipal']
        ))

        contenido.append(Spacer(1, 1*cm))

        # Información básica
        info = [
            ["Prestatario:", contrato.prestatario or "No especificado"],
            ["Prestamista:", contrato.prestamista or "No especificado"],
            ["Monto:", f"{contrato.moneda} {contrato.monto_principal:,.0f}"],
            ["Plazo:", f"{contrato.plazo_meses} meses"],
            ["Fecha de análisis:", datetime.now().strftime("%d/%m/%Y")]
        ]

        tabla = Table(info, colWidths=[4*cm, 8*cm])
        tabla.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ]))

        contenido.append(tabla)
        contenido.append(Spacer(1, 2*cm))

        # Línea separadora
        contenido.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor('#2c5282')
        ))

        return contenido

    def _generar_resumen_ejecutivo(
        self,
        contrato: ContratoParseado,
        resultado_fin: ResultadoCalculo,
        resultado_riesgo: ResultadoRiesgo
    ) -> List:
        """Genera la sección de resumen ejecutivo"""

        contenido = []

        contenido.append(Paragraph("RESUMEN EJECUTIVO", self.styles['Subtitulo']))

        # Generar narrativa
        narrativa = self.templates['resumen_ejecutivo'].render(
            tipo_tasa=contrato.tipo_tasa.value,
            tasa_nominal=contrato.tasa_nominal,
            indice_referencia=contrato.indice_referencia or "",
            spread=contrato.spread_bps or 0,
            cap=contrato.cap,
            floor=contrato.floor,
            moneda=contrato.moneda,
            monto=contrato.monto_principal,
            plazo=contrato.plazo_meses,
            frecuencia=contrato.frecuencia_pago.value,
            es_bullet=contrato.es_bullet,
            gracia=contrato.periodo_gracia_meses,
            cat=resultado_fin.costo_anual_total,
            diferencia_mercado=resultado_fin.diferencia_vs_mercado
        )

        contenido.append(Paragraph(narrativa, self.styles['TextoNormal']))
        contenido.append(Spacer(1, 0.5*cm))

        # Tabla de métricas clave
        contenido.append(Paragraph("Métricas Clave", self.styles['Seccion']))

        metricas = [
            ["Métrica", "Valor", "Evaluación"],
            ["Costo Anual Total (CAT)", f"{resultado_fin.costo_anual_total}%",
             resultado_fin.evaluacion_mercado[:30]],
            ["Tasa Efectiva Anual", f"{resultado_fin.tasa_efectiva_anual}%", "-"],
            ["Cuota Mensual", f"{contrato.moneda} {resultado_fin.cuota_mensual:,.2f}", "-"],
            ["Score de Riesgo", f"{resultado_riesgo.score_total}/100",
             resultado_riesgo.nivel_riesgo.value.replace("_", " ").title()],
            ["Total Intereses", f"{contrato.moneda} {resultado_fin.total_intereses:,.2f}", "-"],
            ["Total Comisiones", f"{contrato.moneda} {resultado_fin.total_comisiones:,.2f}", "-"]
        ]

        tabla = Table(metricas, colWidths=[5*cm, 4*cm, 5*cm])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
        ]))

        contenido.append(tabla)

        return contenido

    def _generar_analisis_financiero(
        self,
        contrato: ContratoParseado,
        resultado: ResultadoCalculo
    ) -> List:
        """Genera la sección de análisis financiero detallado"""

        contenido = []

        contenido.append(Paragraph("ANÁLISIS FINANCIERO DETALLADO", self.styles['Subtitulo']))

        # Desglose de costos
        contenido.append(Paragraph("Desglose de Costos", self.styles['Seccion']))

        costo_total = resultado.costo_total_financiamiento
        costos = [
            ["Concepto", "Monto", "% del Total"],
            ["Capital", f"{contrato.moneda} {contrato.monto_principal:,.2f}",
             f"{(contrato.monto_principal/costo_total*100):.1f}%"],
            ["Intereses", f"{contrato.moneda} {resultado.total_intereses:,.2f}",
             f"{(resultado.total_intereses/costo_total*100):.1f}%"],
            ["Comisiones", f"{contrato.moneda} {resultado.total_comisiones:,.2f}",
             f"{(resultado.total_comisiones/costo_total*100):.1f}%"],
            ["TOTAL", f"{contrato.moneda} {costo_total:,.2f}", "100%"]
        ]

        tabla = Table(costos, colWidths=[5*cm, 5*cm, 4*cm])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e2e8f0'))
        ]))

        contenido.append(tabla)
        contenido.append(Spacer(1, 0.5*cm))

        # Análisis de comisiones
        if contrato.comisiones:
            contenido.append(Paragraph("Detalle de Comisiones", self.styles['Seccion']))

            comisiones_data = [["Tipo", "Valor", "Base"]]
            for com in contrato.comisiones:
                valor = f"{com.valor}%" if com.es_porcentaje else f"{contrato.moneda} {com.valor:,.2f}"
                base = com.base.replace("_", " ").title() if com.es_porcentaje else "Monto fijo"
                comisiones_data.append([com.tipo.title(), valor, base])

            tabla_com = Table(comisiones_data, colWidths=[5*cm, 4*cm, 5*cm])
            tabla_com.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))

            contenido.append(tabla_com)
            contenido.append(Spacer(1, 0.5*cm))

        # Comparación con mercado
        contenido.append(Paragraph("Comparación con Mercado", self.styles['Seccion']))

        if resultado.diferencia_vs_mercado > 1.5:
            estilo = self.styles['TextoDestacado']
            texto = (f"La tasa efectiva se encuentra {resultado.diferencia_vs_mercado:.2f}% "
                    f"por encima del promedio de mercado. Se recomienda negociar mejores condiciones.")
        elif resultado.diferencia_vs_mercado < -0.5:
            estilo = self.styles['TextoPositivo']
            texto = (f"La tasa efectiva se encuentra {abs(resultado.diferencia_vs_mercado):.2f}% "
                    f"por debajo del promedio de mercado. Condiciones favorables.")
        else:
            estilo = self.styles['TextoNormal']
            texto = "La tasa efectiva está en línea con las condiciones de mercado."

        contenido.append(Paragraph(texto, estilo))
        contenido.append(Paragraph(
            f"Percentil de mercado: {resultado.percentil_mercado}",
            self.styles['TextoNormal']
        ))

        # Análisis de garantías
        contenido.append(Spacer(1, 0.5*cm))
        contenido.append(Paragraph("Análisis de Garantías", self.styles['Seccion']))

        narrativa_garantias = self.templates['analisis_garantias'].render(
            tipo_garantia=contrato.tipo_garantia_general.value,
            garantias=contrato.garantias
        )
        contenido.append(Paragraph(narrativa_garantias, self.styles['TextoNormal']))

        return contenido

    def _generar_seccion_riesgos(self, resultado: ResultadoRiesgo) -> List:
        """Genera la sección de evaluación de riesgos"""

        contenido = []

        contenido.append(Paragraph("EVALUACIÓN DE RIESGOS", self.styles['Subtitulo']))

        # Narrativa de riesgos
        narrativa = self.templates['analisis_riesgos'].render(
            score=resultado.score_total,
            nivel=resultado.nivel_riesgo.value.replace("_", " "),
            debilidades=resultado.debilidades
        )
        contenido.append(Paragraph(narrativa, self.styles['TextoNormal']))
        contenido.append(Spacer(1, 0.5*cm))

        # Tabla de scores por categoría
        contenido.append(Paragraph("Evaluación por Categoría", self.styles['Seccion']))

        scores_data = [["Categoría", "Score", "Nivel", "Factor Principal"]]
        for sc in resultado.scores_categorias:
            factor = sc.factores[0] if sc.factores else "-"
            scores_data.append([
                sc.categoria,
                f"{sc.score}/100",
                sc.nivel.value.replace("_", " ").title(),
                factor[:40] + "..." if len(factor) > 40 else factor
            ])

        tabla = Table(scores_data, colWidths=[3*cm, 2*cm, 3*cm, 6*cm])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (1, 0), (2, -1), 'CENTER')
        ]))

        contenido.append(tabla)
        contenido.append(Spacer(1, 0.5*cm))

        # Red flags
        if resultado.red_flags:
            contenido.append(Paragraph("Alertas Identificadas", self.styles['Seccion']))

            for rf in resultado.red_flags:
                if rf.severidad == SeveridadRedFlag.ALTA:
                    estilo = self.styles['TextoDestacado']
                else:
                    estilo = self.styles['TextoNormal']

                contenido.append(Paragraph(
                    f"• [{rf.severidad.value.upper()}] {rf.descripcion}",
                    estilo
                ))

            contenido.append(Spacer(1, 0.3*cm))

        # Fortalezas
        if resultado.fortalezas:
            contenido.append(Paragraph("Fortalezas del Contrato", self.styles['Seccion']))
            for fortaleza in resultado.fortalezas[:5]:
                contenido.append(Paragraph(
                    f"✓ {fortaleza}",
                    self.styles['TextoPositivo']
                ))

        return contenido

    def _generar_recomendaciones(self, resultado: ResultadoRiesgo) -> List:
        """Genera la sección de recomendaciones"""

        contenido = []

        contenido.append(Spacer(1, 0.5*cm))
        contenido.append(Paragraph("RECOMENDACIONES", self.styles['Subtitulo']))

        # Generar narrativa de recomendaciones
        narrativa = self.templates['recomendaciones'].render(
            accion=resultado.accion_sugerida,
            puntos_negociacion=resultado.puntos_negociacion
        )

        # Colorear según acción
        if resultado.accion_sugerida == "Aceptar":
            contenido.append(Paragraph(narrativa, self.styles['TextoPositivo']))
        elif resultado.accion_sugerida == "Rechazar":
            contenido.append(Paragraph(narrativa, self.styles['TextoDestacado']))
        else:
            contenido.append(Paragraph(narrativa, self.styles['TextoNormal']))

        return contenido

    def _generar_anexo_amortizacion(self, resultado: ResultadoCalculo) -> List:
        """Genera el anexo con la tabla de amortización"""

        contenido = []

        contenido.append(Paragraph("ANEXO: TABLA DE AMORTIZACIÓN", self.styles['Subtitulo']))

        # Mostrar primeras y últimas filas
        tabla = resultado.tabla_amortizacion
        filas_mostrar = []

        # Encabezado
        filas_mostrar.append(["#", "Fecha", "Cuota", "Capital", "Interés", "Saldo"])

        # Primeras 6 filas
        for fila in tabla[:6]:
            filas_mostrar.append([
                str(fila.periodo),
                fila.fecha,
                f"{fila.cuota:,.2f}",
                f"{fila.capital:,.2f}",
                f"{fila.interes:,.2f}",
                f"{fila.saldo:,.2f}"
            ])

        # Indicador de continuación
        if len(tabla) > 12:
            filas_mostrar.append(["...", "...", "...", "...", "...", "..."])

            # Últimas 6 filas
            for fila in tabla[-6:]:
                filas_mostrar.append([
                    str(fila.periodo),
                    fila.fecha,
                    f"{fila.cuota:,.2f}",
                    f"{fila.capital:,.2f}",
                    f"{fila.interes:,.2f}",
                    f"{fila.saldo:,.2f}"
                ])

        tabla_pdf = Table(filas_mostrar, colWidths=[1.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm])
        tabla_pdf.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
        ]))

        contenido.append(tabla_pdf)
        contenido.append(Spacer(1, 0.3*cm))
        contenido.append(Paragraph(
            f"Total de períodos: {len(tabla)}",
            self.styles['NotaPie']
        ))

        return contenido

    def _generar_pie_pagina(self) -> List:
        """Genera el pie de página"""

        contenido = []
        contenido.append(Spacer(1, 1*cm))
        contenido.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
        contenido.append(Paragraph(
            f"Reporte generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} | "
            "Sistema de Análisis de Contratos de Préstamo",
            self.styles['NotaPie']
        ))

        return contenido

    def generar_visualizaciones(
        self,
        contrato: ContratoParseado,
        resultado_financiero: ResultadoCalculo,
        resultado_riesgo: ResultadoRiesgo
    ) -> Dict[str, go.Figure]:
        """Genera visualizaciones interactivas con Plotly"""

        figuras = {}

        # 1. Gráfico de amortización
        figuras['amortizacion'] = self._crear_grafico_amortizacion(resultado_financiero)

        # 2. Distribución de costos
        figuras['distribucion_costos'] = self._crear_grafico_costos(
            contrato, resultado_financiero
        )

        # 3. Radar de riesgos
        figuras['radar_riesgos'] = self._crear_radar_riesgos(resultado_riesgo)

        # 4. Sensibilidad (si aplica)
        if resultado_financiero.sensibilidad:
            figuras['sensibilidad'] = self._crear_grafico_sensibilidad(
                resultado_financiero.sensibilidad
            )

        return figuras

    def _crear_grafico_amortizacion(self, resultado: ResultadoCalculo) -> go.Figure:
        """Crea gráfico de evolución de amortización"""

        tabla = resultado.tabla_amortizacion
        periodos = [f.periodo for f in tabla]
        saldos = [f.saldo for f in tabla]
        capitales = [f.capital for f in tabla]
        intereses = [f.interes for f in tabla]

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Saldo
        fig.add_trace(
            go.Scatter(
                x=periodos, y=saldos,
                name="Saldo",
                line=dict(color="#2c5282", width=2)
            ),
            secondary_y=False
        )

        # Capital e interés como barras apiladas
        fig.add_trace(
            go.Bar(
                x=periodos, y=capitales,
                name="Capital",
                marker_color="#48bb78"
            ),
            secondary_y=True
        )

        fig.add_trace(
            go.Bar(
                x=periodos, y=intereses,
                name="Interés",
                marker_color="#f6ad55"
            ),
            secondary_y=True
        )

        fig.update_layout(
            title="Evolución de Amortización",
            xaxis_title="Período",
            barmode='stack',
            height=400
        )
        fig.update_yaxes(title_text="Saldo", secondary_y=False)
        fig.update_yaxes(title_text="Pago", secondary_y=True)

        return fig

    def _crear_grafico_costos(
        self,
        contrato: ContratoParseado,
        resultado: ResultadoCalculo
    ) -> go.Figure:
        """Crea gráfico de distribución de costos"""

        labels = ['Capital', 'Intereses', 'Comisiones']
        values = [
            contrato.monto_principal,
            resultado.total_intereses,
            resultado.total_comisiones
        ]

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker_colors=['#2c5282', '#f6ad55', '#fc8181']
        )])

        fig.update_layout(
            title="Distribución del Costo Total",
            height=400
        )

        return fig

    def _crear_radar_riesgos(self, resultado: ResultadoRiesgo) -> go.Figure:
        """Crea gráfico de radar para scores de riesgo"""

        categorias = [sc.categoria for sc in resultado.scores_categorias]
        scores = [sc.score for sc in resultado.scores_categorias]

        # Cerrar el polígono
        categorias.append(categorias[0])
        scores.append(scores[0])

        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=scores,
            theta=categorias,
            fill='toself',
            fillcolor='rgba(44, 82, 130, 0.3)',
            line_color='#2c5282',
            name='Score'
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            title="Perfil de Riesgo por Categoría",
            height=400
        )

        return fig

    def _crear_grafico_sensibilidad(self, sensibilidad: Dict) -> go.Figure:
        """Crea gráfico de análisis de sensibilidad"""

        escenarios = sensibilidad['escenarios']

        cambios = [e['cambio_tasa'] for e in escenarios]
        intereses = [e['total_intereses'] for e in escenarios]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=cambios,
            y=intereses,
            marker_color=['#48bb78' if i < len(cambios)//2 else '#f6ad55'
                         if i == len(cambios)//2 else '#fc8181'
                         for i in range(len(cambios))]
        ))

        fig.update_layout(
            title=f"Sensibilidad a Cambios en {sensibilidad.get('indice_referencia', 'Tasa')}",
            xaxis_title="Cambio en Tasa",
            yaxis_title="Total Intereses",
            height=400
        )

        return fig


# Función de conveniencia
def generar_reporte(
    contrato: ContratoParseado,
    resultado_financiero: ResultadoCalculo,
    resultado_riesgo: ResultadoRiesgo,
    ruta_salida: str
) -> str:
    """Función de conveniencia para generar reporte"""
    generator = ReportGenerator()
    return generator.generar_reporte_completo(
        contrato, resultado_financiero, resultado_riesgo, ruta_salida
    )
