"""
Evaluador de Riesgos de Contratos de Préstamo
Sistema de scoring y detección de red flags
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

from .contract_parser import ContratoParseado, TipoTasa, TipoGarantia, FrecuenciaPago
from .financial_calculator import ResultadoCalculo


class NivelRiesgo(Enum):
    MUY_BAJO = "muy_bajo"
    BAJO = "bajo"
    MODERADO = "moderado"
    ALTO = "alto"
    MUY_ALTO = "muy_alto"


class SeveridadRedFlag(Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


@dataclass
class RedFlag:
    tipo: str
    descripcion: str
    severidad: SeveridadRedFlag
    recomendacion: str
    impacto_score: int


@dataclass
class ScoreCategoria:
    categoria: str
    score: int  # 0-100
    nivel: NivelRiesgo
    factores: List[str]
    peso: float


@dataclass
class ResultadoRiesgo:
    # Score consolidado
    score_total: int  # 0-100 (mayor = menor riesgo)
    nivel_riesgo: NivelRiesgo

    # Scores por categoría
    scores_categorias: List[ScoreCategoria]

    # Red flags identificados
    red_flags: List[RedFlag]

    # Recomendación general
    recomendacion_general: str
    accion_sugerida: str  # "Aceptar", "Negociar", "Rechazar"

    # Detalle de evaluación
    fortalezas: List[str]
    debilidades: List[str]
    puntos_negociacion: List[str]


class RiskAssessor:
    """Evaluador de riesgos para contratos de préstamo"""

    def __init__(self, ruta_risk_factors: str = None):
        """Inicializa el evaluador con factores de riesgo"""

        if ruta_risk_factors is None:
            ruta_risk_factors = Path(__file__).parent.parent / 'data' / 'risk_factors.json'

        self.risk_factors = self._cargar_risk_factors(ruta_risk_factors)

    def _cargar_risk_factors(self, ruta: str) -> Dict:
        """Carga los factores de riesgo desde JSON"""
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def evaluar(self, contrato: ContratoParseado,
                resultado_financiero: ResultadoCalculo) -> ResultadoRiesgo:
        """Realiza evaluación completa de riesgos"""

        # Evaluar cada categoría
        scores_categorias = [
            self._evaluar_riesgo_liquidez(contrato, resultado_financiero),
            self._evaluar_riesgo_tasa(contrato, resultado_financiero),
            self._evaluar_riesgo_operativo(contrato),
            self._evaluar_riesgo_legal(contrato),
            self._evaluar_riesgo_prepago(contrato)
        ]

        # Identificar red flags
        red_flags = self._identificar_red_flags(contrato, resultado_financiero)

        # Calcular score total ponderado
        score_total = self._calcular_score_total(scores_categorias, red_flags)

        # Determinar nivel de riesgo
        nivel_riesgo = self._determinar_nivel_riesgo(score_total)

        # Generar análisis cualitativo
        fortalezas = self._identificar_fortalezas(contrato, resultado_financiero, scores_categorias)
        debilidades = self._identificar_debilidades(contrato, resultado_financiero, red_flags)
        puntos_negociacion = self._sugerir_puntos_negociacion(contrato, red_flags, debilidades)

        # Generar recomendación
        recomendacion, accion = self._generar_recomendacion(score_total, red_flags, resultado_financiero)

        return ResultadoRiesgo(
            score_total=score_total,
            nivel_riesgo=nivel_riesgo,
            scores_categorias=scores_categorias,
            red_flags=red_flags,
            recomendacion_general=recomendacion,
            accion_sugerida=accion,
            fortalezas=fortalezas,
            debilidades=debilidades,
            puntos_negociacion=puntos_negociacion
        )

    def _evaluar_riesgo_liquidez(self, contrato: ContratoParseado,
                                  resultado: ResultadoCalculo) -> ScoreCategoria:
        """Evalúa el riesgo de liquidez basado en estructura de pagos"""

        score = 100
        factores = []

        # Factor 1: Relación cuota/monto
        if contrato.monto_principal > 0:
            ratio_cuota = (resultado.cuota_mensual * 12) / contrato.monto_principal
            if ratio_cuota > 0.6:
                score -= 30
                factores.append("Cuota anual representa más del 60% del monto")
            elif ratio_cuota > 0.4:
                score -= 15
                factores.append("Cuota anual representa más del 40% del monto")

        # Factor 2: Estructura bullet
        if contrato.es_bullet:
            score -= 20
            factores.append("Pago bullet concentra riesgo al vencimiento")

        # Factor 3: Período de gracia
        if contrato.periodo_gracia_meses > 0:
            if contrato.periodo_gracia_meses >= 12:
                score -= 10
                factores.append("Período de gracia largo puede ocultar problemas de flujo")
            else:
                score += 5
                factores.append("Período de gracia moderado mejora liquidez inicial")

        # Factor 4: Frecuencia de pagos
        if contrato.frecuencia_pago == FrecuenciaPago.ANUAL:
            score -= 10
            factores.append("Pagos anuales concentran presión de liquidez")
        elif contrato.frecuencia_pago == FrecuenciaPago.MENSUAL:
            score += 5
            factores.append("Pagos mensuales distribuyen mejor el flujo")

        # Factor 5: Plazo
        if contrato.plazo_meses > 60:
            score += 10
            factores.append("Plazo largo reduce presión de pagos")
        elif contrato.plazo_meses < 12:
            score -= 15
            factores.append("Plazo corto genera alta presión de pagos")

        score = max(0, min(100, score))
        nivel = self._score_a_nivel(score)

        return ScoreCategoria(
            categoria="Liquidez",
            score=score,
            nivel=nivel,
            factores=factores,
            peso=0.25
        )

    def _evaluar_riesgo_tasa(self, contrato: ContratoParseado,
                             resultado: ResultadoCalculo) -> ScoreCategoria:
        """Evalúa el riesgo de tasa de interés"""

        score = 100
        factores = []

        # Factor 1: Tipo de tasa
        if contrato.tipo_tasa == TipoTasa.VARIABLE:
            score -= 20
            factores.append("Tasa variable expone a cambios de mercado")

            # Mitigantes
            if contrato.cap:
                score += 10
                factores.append(f"Cap de {contrato.cap}% limita exposición al alza")
            if contrato.floor:
                score -= 5
                factores.append(f"Floor de {contrato.floor}% limita beneficio de bajadas")
        else:
            score += 10
            factores.append("Tasa fija proporciona certidumbre de costos")

        # Factor 2: Nivel de tasa vs mercado
        diferencia = resultado.diferencia_vs_mercado
        if diferencia > 3:
            score -= 25
            factores.append(f"Tasa {diferencia:.1f}% sobre mercado - muy elevada")
        elif diferencia > 1.5:
            score -= 15
            factores.append(f"Tasa {diferencia:.1f}% sobre mercado")
        elif diferencia < -1:
            score += 10
            factores.append(f"Tasa {abs(diferencia):.1f}% bajo mercado - favorable")

        # Factor 3: Spread para tasas variables
        if contrato.tipo_tasa == TipoTasa.VARIABLE and contrato.spread_bps:
            if contrato.spread_bps > 400:
                score -= 15
                factores.append(f"Spread de {contrato.spread_bps} bps es elevado")
            elif contrato.spread_bps < 200:
                score += 5
                factores.append(f"Spread de {contrato.spread_bps} bps es competitivo")

        score = max(0, min(100, score))
        nivel = self._score_a_nivel(score)

        return ScoreCategoria(
            categoria="Tasa de Interés",
            score=score,
            nivel=nivel,
            factores=factores,
            peso=0.20
        )

    def _evaluar_riesgo_operativo(self, contrato: ContratoParseado) -> ScoreCategoria:
        """Evalúa el riesgo operativo derivado de covenants y restricciones"""

        score = 100
        factores = []

        # Factor 1: Número de covenants
        num_covenants = len(contrato.covenants)
        if num_covenants > 4:
            score -= 20
            factores.append(f"{num_covenants} covenants generan alta carga de cumplimiento")
        elif num_covenants > 2:
            score -= 10
            factores.append(f"{num_covenants} covenants requieren monitoreo constante")
        elif num_covenants == 0:
            score += 5
            factores.append("Sin covenants restrictivos")

        # Factor 2: Severidad de covenants
        for covenant in contrato.covenants:
            if covenant.tipo == "DSCR":
                if covenant.valor >= 1.5:
                    score -= 15
                    factores.append(f"DSCR ≥ {covenant.valor} es exigente")
                elif covenant.valor >= 1.25:
                    score -= 5
                    factores.append(f"DSCR ≥ {covenant.valor} es estándar")

            elif covenant.tipo == "Deuda/EBITDA":
                if covenant.valor <= 2.5:
                    score -= 15
                    factores.append(f"Deuda/EBITDA ≤ {covenant.valor} es restrictivo")
                elif covenant.valor <= 3.5:
                    score -= 5
                    factores.append(f"Deuda/EBITDA ≤ {covenant.valor} es estándar")

            elif covenant.tipo == "Negative Pledge":
                score -= 10
                factores.append("Negative pledge limita opciones de financiamiento futuro")

        # Factor 3: Cláusulas de incumplimiento
        num_clausulas = len(contrato.clausulas_incumplimiento)
        if num_clausulas > 5:
            score -= 15
            factores.append(f"{num_clausulas} triggers de incumplimiento - alto riesgo")
        elif num_clausulas > 3:
            score -= 5
            factores.append(f"{num_clausulas} triggers de incumplimiento")

        # Factor 4: Cross-default
        if contrato.tiene_cross_default:
            score -= 15
            factores.append("Cross-default aumenta riesgo sistémico")

        score = max(0, min(100, score))
        nivel = self._score_a_nivel(score)

        return ScoreCategoria(
            categoria="Operativo",
            score=score,
            nivel=nivel,
            factores=factores,
            peso=0.20
        )

    def _evaluar_riesgo_legal(self, contrato: ContratoParseado) -> ScoreCategoria:
        """Evalúa el riesgo legal basado en garantías y jurisdicción"""

        score = 100
        factores = []

        # Factor 1: Tipo de garantía (desde perspectiva del prestatario)
        tipo_garantia = contrato.tipo_garantia_general

        if tipo_garantia == TipoGarantia.REAL:
            score -= 20
            factores.append("Garantía real expone activos del negocio")
        elif tipo_garantia == TipoGarantia.MIXTA:
            score -= 25
            factores.append("Garantía mixta expone activos y patrimonio personal")
        elif tipo_garantia == TipoGarantia.PERSONAL:
            score -= 10
            factores.append("Aval personal compromete patrimonio del avalista")
        else:
            score += 10
            factores.append("Sin garantías específicas")

        # Factor 2: Grado de hipoteca
        for garantia in contrato.garantias:
            if "1er grado" in garantia.descripcion or "primer grado" in garantia.descripcion.lower():
                score -= 10
                factores.append("Hipoteca de primer grado da máxima prelación al acreedor")
            elif "2º grado" in garantia.descripcion or "segundo grado" in garantia.descripcion.lower():
                score -= 5
                factores.append("Hipoteca de segundo grado")

        # Factor 3: Cantidad de garantías
        num_garantias = len(contrato.garantias)
        if num_garantias > 3:
            score -= 15
            factores.append(f"{num_garantias} garantías - posible sobrecolateralización")
        elif num_garantias == 0:
            score += 5
            factores.append("Sin garantías requeridas")

        # Factor 4: Jurisdicción
        if contrato.jurisdiccion:
            if "España" in contrato.jurisdiccion or "Madrid" in contrato.jurisdiccion:
                score += 5
                factores.append("Jurisdicción española - marco legal conocido")
            # Podría penalizar jurisdicciones menos favorables

        score = max(0, min(100, score))
        nivel = self._score_a_nivel(score)

        return ScoreCategoria(
            categoria="Legal",
            score=score,
            nivel=nivel,
            factores=factores,
            peso=0.15
        )

    def _evaluar_riesgo_prepago(self, contrato: ContratoParseado) -> ScoreCategoria:
        """Evalúa el riesgo y flexibilidad de prepago"""

        score = 100
        factores = []

        if contrato.prepago:
            # Factor 1: Prepago permitido
            if not contrato.prepago.permitido:
                score -= 40
                factores.append("Prepago no permitido - sin flexibilidad")
            else:
                # Factor 2: Penalización
                penalizacion = contrato.prepago.penalizacion
                if penalizacion > 2.5:
                    score -= 25
                    factores.append(f"Penalización de {penalizacion}% es muy elevada")
                elif penalizacion > 1.5:
                    score -= 15
                    factores.append(f"Penalización de {penalizacion}% limita flexibilidad")
                elif penalizacion > 0:
                    score -= 5
                    factores.append(f"Penalización de {penalizacion}% es moderada")
                else:
                    score += 10
                    factores.append("Sin penalización por prepago")

                # Factor 3: Período de penalización
                periodo = contrato.prepago.periodo_penalizacion_meses
                if periodo > 18:
                    score -= 10
                    factores.append(f"Penalización aplica {periodo} meses - período largo")
                elif periodo > 12:
                    score -= 5
                    factores.append(f"Penalización aplica {periodo} meses")

        score = max(0, min(100, score))
        nivel = self._score_a_nivel(score)

        return ScoreCategoria(
            categoria="Prepago",
            score=score,
            nivel=nivel,
            factores=factores,
            peso=0.20
        )

    def _identificar_red_flags(self, contrato: ContratoParseado,
                                resultado: ResultadoCalculo) -> List[RedFlag]:
        """Identifica señales de alerta en el contrato"""

        red_flags = []

        # Red flag 1: Tasa muy elevada
        if resultado.diferencia_vs_mercado > 3:
            red_flags.append(RedFlag(
                tipo="tasa_elevada",
                descripcion=f"Tasa {resultado.diferencia_vs_mercado:.1f}% superior al promedio de mercado",
                severidad=SeveridadRedFlag.ALTA,
                recomendacion="Solicitar revisión de tasa o buscar alternativas de financiamiento",
                impacto_score=-15
            ))

        # Red flag 2: Muchos triggers de aceleración
        num_triggers = len(contrato.clausulas_incumplimiento)
        if num_triggers > 5:
            red_flags.append(RedFlag(
                tipo="triggers_excesivos",
                descripcion=f"{num_triggers} triggers de aceleración identificados",
                severidad=SeveridadRedFlag.ALTA,
                recomendacion="Negociar reducción de causales de vencimiento anticipado",
                impacto_score=-10
            ))

        # Red flag 3: Penalización prepago elevada
        if contrato.prepago and contrato.prepago.penalizacion > 2.5:
            red_flags.append(RedFlag(
                tipo="penalizacion_excesiva",
                descripcion=f"Penalización por prepago de {contrato.prepago.penalizacion}%",
                severidad=SeveridadRedFlag.MEDIA,
                recomendacion="Negociar reducción o eliminación de penalización",
                impacto_score=-8
            ))

        # Red flag 4: Tasa variable sin cap
        if contrato.tipo_tasa == TipoTasa.VARIABLE and not contrato.cap:
            red_flags.append(RedFlag(
                tipo="sin_cap",
                descripcion="Tasa variable sin límite máximo (cap)",
                severidad=SeveridadRedFlag.ALTA,
                recomendacion="Exigir inclusión de cap para limitar exposición",
                impacto_score=-12
            ))

        # Red flag 5: Garantías excesivas
        tiene_hipoteca = any("hipoteca" in g.tipo.lower() for g in contrato.garantias)
        tiene_prenda = any("prenda" in g.tipo.lower() for g in contrato.garantias)
        tiene_aval = any("aval" in g.tipo.lower() for g in contrato.garantias)

        if tiene_hipoteca and tiene_prenda and tiene_aval:
            red_flags.append(RedFlag(
                tipo="sobrecolateralizacion",
                descripcion="Múltiples tipos de garantía (hipoteca + prenda + aval)",
                severidad=SeveridadRedFlag.MEDIA,
                recomendacion="Evaluar si el nivel de garantías es proporcional al riesgo",
                impacto_score=-8
            ))

        # Red flag 6: Cross-default
        if contrato.tiene_cross_default:
            red_flags.append(RedFlag(
                tipo="cross_default",
                descripcion="Cláusula de cross-default con otras obligaciones",
                severidad=SeveridadRedFlag.MEDIA,
                recomendacion="Evaluar impacto en caso de dificultades con otros acreedores",
                impacto_score=-6
            ))

        # Red flag 7: CAT muy elevado
        if resultado.costo_anual_total > 30:
            red_flags.append(RedFlag(
                tipo="cat_elevado",
                descripcion=f"Costo Anual Total de {resultado.costo_anual_total:.1f}%",
                severidad=SeveridadRedFlag.ALTA,
                recomendacion="Revisar estructura de comisiones y buscar alternativas",
                impacto_score=-12
            ))

        # Red flag 8: Comisiones excesivas
        comision_apertura = 0
        for com in contrato.comisiones:
            if com.tipo == "apertura":
                comision_apertura = com.valor

        if comision_apertura > 2.5:
            red_flags.append(RedFlag(
                tipo="comision_apertura_alta",
                descripcion=f"Comisión de apertura de {comision_apertura}%",
                severidad=SeveridadRedFlag.MEDIA,
                recomendacion="Negociar reducción de comisión de apertura",
                impacto_score=-5
            ))

        return red_flags

    def _calcular_score_total(self, scores_categorias: List[ScoreCategoria],
                               red_flags: List[RedFlag]) -> int:
        """Calcula el score total ponderado"""

        # Score ponderado de categorías
        score_ponderado = 0
        total_peso = 0

        for sc in scores_categorias:
            score_ponderado += sc.score * sc.peso
            total_peso += sc.peso

        if total_peso > 0:
            score_base = score_ponderado / total_peso
        else:
            score_base = 50

        # Aplicar impacto de red flags
        impacto_flags = sum(rf.impacto_score for rf in red_flags)
        score_final = score_base + impacto_flags

        return max(0, min(100, int(score_final)))

    def _score_a_nivel(self, score: int) -> NivelRiesgo:
        """Convierte un score numérico a nivel de riesgo"""

        if score >= 80:
            return NivelRiesgo.MUY_BAJO
        elif score >= 60:
            return NivelRiesgo.BAJO
        elif score >= 40:
            return NivelRiesgo.MODERADO
        elif score >= 20:
            return NivelRiesgo.ALTO
        else:
            return NivelRiesgo.MUY_ALTO

    def _determinar_nivel_riesgo(self, score: int) -> NivelRiesgo:
        """Determina el nivel de riesgo basado en el score total"""
        return self._score_a_nivel(score)

    def _identificar_fortalezas(self, contrato: ContratoParseado,
                                 resultado: ResultadoCalculo,
                                 scores: List[ScoreCategoria]) -> List[str]:
        """Identifica los puntos fuertes del contrato"""

        fortalezas = []

        # Tasa competitiva
        if resultado.diferencia_vs_mercado < 0:
            fortalezas.append(f"Tasa {abs(resultado.diferencia_vs_mercado):.1f}% inferior al promedio de mercado")

        # Tasa fija
        if contrato.tipo_tasa == TipoTasa.FIJA:
            fortalezas.append("Tasa fija proporciona predictibilidad de costos")

        # Prepago sin penalización
        if contrato.prepago and contrato.prepago.penalizacion == 0:
            fortalezas.append("Prepago permitido sin penalización")

        # Período de gracia
        if contrato.periodo_gracia_meses > 0:
            fortalezas.append(f"Período de gracia de {contrato.periodo_gracia_meses} meses")

        # Plazo adecuado
        if contrato.plazo_meses >= 36:
            fortalezas.append("Plazo largo permite mejor distribución del flujo de caja")

        # Cap en tasa variable
        if contrato.tipo_tasa == TipoTasa.VARIABLE and contrato.cap:
            fortalezas.append(f"Cap de {contrato.cap}% protege contra subidas de tasa")

        # Scores altos por categoría
        for sc in scores:
            if sc.score >= 80:
                fortalezas.append(f"Bajo riesgo de {sc.categoria.lower()}")

        return fortalezas

    def _identificar_debilidades(self, contrato: ContratoParseado,
                                  resultado: ResultadoCalculo,
                                  red_flags: List[RedFlag]) -> List[str]:
        """Identifica los puntos débiles del contrato"""

        debilidades = []

        # Debilidades basadas en red flags
        for rf in red_flags:
            debilidades.append(rf.descripcion)

        # Garantías exigentes
        if contrato.tipo_garantia_general == TipoGarantia.MIXTA:
            debilidades.append("Requiere tanto garantías reales como personales")

        # Covenants estrictos
        for covenant in contrato.covenants:
            if covenant.tipo == "DSCR" and covenant.valor >= 1.5:
                debilidades.append(f"Covenant DSCR ≥ {covenant.valor} es exigente")

        # Múltiples tramos
        if len(contrato.tramos) > 2:
            debilidades.append(f"Estructura compleja con {len(contrato.tramos)} tramos")

        return debilidades

    def _sugerir_puntos_negociacion(self, contrato: ContratoParseado,
                                     red_flags: List[RedFlag],
                                     debilidades: List[str]) -> List[str]:
        """Sugiere puntos específicos para negociar"""

        puntos = []

        # Basado en red flags
        for rf in red_flags:
            if rf.severidad in [SeveridadRedFlag.ALTA, SeveridadRedFlag.CRITICA]:
                puntos.append(rf.recomendacion)

        # Puntos adicionales
        if contrato.prepago and contrato.prepago.penalizacion > 1:
            puntos.append(f"Reducir penalización de prepago del {contrato.prepago.penalizacion}% al 1% o menos")

        if contrato.tiene_cross_default:
            puntos.append("Eliminar o limitar alcance de cláusula cross-default")

        # Garantías
        if len(contrato.garantias) > 2:
            puntos.append("Reducir número de garantías requeridas")

        # Comisiones
        for com in contrato.comisiones:
            if com.tipo == "apertura" and com.valor > 2:
                puntos.append(f"Reducir comisión de apertura del {com.valor}% al 1.5%")
            if com.tipo == "mantenimiento" and com.valor > 0.2:
                puntos.append(f"Reducir comisión de mantenimiento del {com.valor}% al 0.15%")

        # Tasa variable sin protección
        if contrato.tipo_tasa == TipoTasa.VARIABLE and not contrato.cap:
            puntos.append("Incluir cap (techo) para limitar tasa máxima")

        return list(set(puntos))[:5]  # Limitar a 5 puntos más importantes

    def _generar_recomendacion(self, score: int, red_flags: List[RedFlag],
                                resultado: ResultadoCalculo) -> tuple:
        """Genera la recomendación general y acción sugerida"""

        num_flags_criticos = sum(1 for rf in red_flags
                                  if rf.severidad in [SeveridadRedFlag.ALTA, SeveridadRedFlag.CRITICA])

        # Determinar acción
        if score >= 70 and num_flags_criticos == 0:
            accion = "Aceptar"
            recomendacion = (
                "El contrato presenta condiciones generalmente favorables. "
                "Se recomienda proceder con la firma tras revisión legal estándar."
            )
        elif score >= 50 or (score >= 40 and num_flags_criticos <= 1):
            accion = "Negociar"
            recomendacion = (
                "El contrato presenta áreas de mejora significativas. "
                "Se recomienda negociar los puntos identificados antes de proceder."
            )
        else:
            accion = "Rechazar"
            recomendacion = (
                "El contrato presenta condiciones desfavorables o riesgos elevados. "
                "Se recomienda buscar alternativas de financiamiento o renegociar sustancialmente."
            )

        return recomendacion, accion

    def generar_resumen_riesgos(self, resultado: ResultadoRiesgo) -> Dict[str, Any]:
        """Genera un resumen estructurado de la evaluación de riesgos"""

        return {
            'score_general': {
                'valor': resultado.score_total,
                'nivel': resultado.nivel_riesgo.value,
                'interpretacion': self._interpretar_score(resultado.score_total)
            },
            'evaluacion_por_categoria': [
                {
                    'categoria': sc.categoria,
                    'score': sc.score,
                    'nivel': sc.nivel.value,
                    'factores_principales': sc.factores[:3]
                } for sc in resultado.scores_categorias
            ],
            'alertas': [
                {
                    'tipo': rf.tipo,
                    'descripcion': rf.descripcion,
                    'severidad': rf.severidad.value,
                    'accion_recomendada': rf.recomendacion
                } for rf in resultado.red_flags
            ],
            'sintesis': {
                'fortalezas': resultado.fortalezas,
                'debilidades': resultado.debilidades,
                'puntos_negociacion': resultado.puntos_negociacion
            },
            'decision': {
                'recomendacion': resultado.recomendacion_general,
                'accion': resultado.accion_sugerida
            }
        }

    def _interpretar_score(self, score: int) -> str:
        """Interpreta el score en lenguaje natural"""

        if score >= 80:
            return "Riesgo muy bajo - Condiciones muy favorables"
        elif score >= 60:
            return "Riesgo bajo - Condiciones generalmente aceptables"
        elif score >= 40:
            return "Riesgo moderado - Requiere atención en algunos aspectos"
        elif score >= 20:
            return "Riesgo alto - Múltiples aspectos preocupantes"
        else:
            return "Riesgo muy alto - Condiciones significativamente desfavorables"


# Función de conveniencia
def evaluar_riesgo(contrato: ContratoParseado,
                   resultado_financiero: ResultadoCalculo) -> ResultadoRiesgo:
    """Función de conveniencia para evaluación de riesgos"""
    assessor = RiskAssessor()
    return assessor.evaluar(contrato, resultado_financiero)
