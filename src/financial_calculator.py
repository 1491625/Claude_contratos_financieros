"""
Calculadora Financiera Avanzada
Cálculos de CAT, amortización, sensibilidad y benchmarking
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from .contract_parser import ContratoParseado, TipoTasa, FrecuenciaPago


@dataclass
class FilaAmortizacion:
    periodo: int
    fecha: str
    cuota: float
    capital: float
    interes: float
    saldo: float
    comision_mantenimiento: float = 0.0


@dataclass
class ResultadoCalculo:
    # Tasas efectivas
    tasa_efectiva_anual: float
    costo_anual_total: float

    # Totales
    total_intereses: float
    total_comisiones: float
    costo_total_financiamiento: float
    cuota_mensual: float

    # Tabla de amortización
    tabla_amortizacion: List[FilaAmortizacion]

    # Análisis adicional
    valor_presente_neto: float
    tir: float

    # Comparación con mercado
    diferencia_vs_mercado: float
    percentil_mercado: int
    evaluacion_mercado: str

    # Análisis de sensibilidad (para tasa variable)
    sensibilidad: Optional[Dict[str, Any]] = None


class FinancialCalculator:
    """Calculadora financiera avanzada para análisis de contratos"""

    def __init__(self, ruta_market_rates: str = None):
        """Inicializa la calculadora con datos de mercado"""

        if ruta_market_rates is None:
            ruta_market_rates = Path(__file__).parent.parent / 'data' / 'market_rates.json'

        self.market_rates = self._cargar_market_rates(ruta_market_rates)

    def _cargar_market_rates(self, ruta: str) -> Dict:
        """Carga las tasas de mercado desde JSON"""
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def calcular(self, contrato: ContratoParseado) -> ResultadoCalculo:
        """Realiza todos los cálculos financieros para un contrato"""

        # Calcular tabla de amortización
        tabla = self._generar_tabla_amortizacion(contrato)

        # Calcular totales
        total_intereses = sum(fila.interes for fila in tabla)
        total_comisiones = self._calcular_total_comisiones(contrato, tabla)

        # Calcular tasas efectivas
        tea = self._calcular_tea(contrato)
        cat = self._calcular_cat(contrato, total_intereses, total_comisiones)

        # Calcular cuota
        cuota = tabla[0].cuota if tabla else 0

        # Costo total
        costo_total = contrato.monto_principal + total_intereses + total_comisiones

        # VPN y TIR
        vpn = self._calcular_vpn(contrato, tabla, total_comisiones)
        tir = self._calcular_tir(contrato, tabla, total_comisiones)

        # Comparación con mercado
        comparacion = self._comparar_con_mercado(contrato, tea)

        # Análisis de sensibilidad (solo para tasa variable)
        sensibilidad = None
        if contrato.tipo_tasa == TipoTasa.VARIABLE:
            sensibilidad = self._analisis_sensibilidad(contrato)

        return ResultadoCalculo(
            tasa_efectiva_anual=tea,
            costo_anual_total=cat,
            total_intereses=total_intereses,
            total_comisiones=total_comisiones,
            costo_total_financiamiento=costo_total,
            cuota_mensual=cuota,
            tabla_amortizacion=tabla,
            valor_presente_neto=vpn,
            tir=tir,
            diferencia_vs_mercado=comparacion['diferencia'],
            percentil_mercado=comparacion['percentil'],
            evaluacion_mercado=comparacion['evaluacion'],
            sensibilidad=sensibilidad
        )

    def _generar_tabla_amortizacion(self, contrato: ContratoParseado) -> List[FilaAmortizacion]:
        """Genera la tabla de amortización según el tipo de préstamo"""

        if contrato.es_bullet:
            return self._amortizacion_bullet(contrato)
        elif contrato.periodo_gracia_meses > 0:
            return self._amortizacion_con_gracia(contrato)
        else:
            return self._amortizacion_francesa(contrato)

    def _amortizacion_francesa(self, contrato: ContratoParseado) -> List[FilaAmortizacion]:
        """Genera tabla de amortización método francés"""

        monto = contrato.monto_principal
        tasa_mensual = contrato.tasa_nominal / 100 / 12
        n = contrato.plazo_meses

        # Calcular cuota fija
        if tasa_mensual > 0:
            cuota = monto * (tasa_mensual * (1 + tasa_mensual)**n) / ((1 + tasa_mensual)**n - 1)
        else:
            cuota = monto / n

        # Comisión de mantenimiento mensual
        comision_mant = 0
        for com in contrato.comisiones:
            if com.tipo == "mantenimiento":
                comision_mant = com.valor / 100

        tabla = []
        saldo = monto
        fecha_base = datetime.now()

        for i in range(1, n + 1):
            interes = saldo * tasa_mensual
            capital = cuota - interes
            mantenimiento = saldo * comision_mant

            saldo_nuevo = max(0, saldo - capital)

            fecha = fecha_base + timedelta(days=30 * i)

            tabla.append(FilaAmortizacion(
                periodo=i,
                fecha=fecha.strftime('%Y-%m-%d'),
                cuota=round(cuota, 2),
                capital=round(capital, 2),
                interes=round(interes, 2),
                saldo=round(saldo_nuevo, 2),
                comision_mantenimiento=round(mantenimiento, 2)
            ))

            saldo = saldo_nuevo

        return tabla

    def _amortizacion_bullet(self, contrato: ContratoParseado) -> List[FilaAmortizacion]:
        """Genera tabla para préstamo bullet (capital al final)"""

        monto = contrato.monto_principal
        tasa_mensual = contrato.tasa_nominal / 100 / 12
        n = contrato.plazo_meses

        # Comisión de mantenimiento mensual
        comision_mant = 0
        for com in contrato.comisiones:
            if com.tipo == "mantenimiento":
                comision_mant = com.valor / 100

        tabla = []
        saldo = monto
        fecha_base = datetime.now()

        for i in range(1, n + 1):
            interes = saldo * tasa_mensual
            mantenimiento = saldo * comision_mant

            # Solo pagar capital en el último mes
            if i == n:
                capital = saldo
                cuota = capital + interes
                saldo_nuevo = 0
            else:
                capital = 0
                cuota = interes
                saldo_nuevo = saldo

            fecha = fecha_base + timedelta(days=30 * i)

            tabla.append(FilaAmortizacion(
                periodo=i,
                fecha=fecha.strftime('%Y-%m-%d'),
                cuota=round(cuota, 2),
                capital=round(capital, 2),
                interes=round(interes, 2),
                saldo=round(saldo_nuevo, 2),
                comision_mantenimiento=round(mantenimiento, 2)
            ))

            saldo = saldo_nuevo

        return tabla

    def _amortizacion_con_gracia(self, contrato: ContratoParseado) -> List[FilaAmortizacion]:
        """Genera tabla con período de gracia"""

        monto = contrato.monto_principal
        tasa_mensual = contrato.tasa_nominal / 100 / 12
        n_total = contrato.plazo_meses
        n_gracia = contrato.periodo_gracia_meses
        n_amortizacion = n_total - n_gracia

        # Comisión de mantenimiento mensual
        comision_mant = 0
        for com in contrato.comisiones:
            if com.tipo == "mantenimiento":
                comision_mant = com.valor / 100

        tabla = []
        saldo = monto
        fecha_base = datetime.now()

        # Período de gracia (solo intereses)
        for i in range(1, n_gracia + 1):
            interes = saldo * tasa_mensual
            mantenimiento = saldo * comision_mant

            fecha = fecha_base + timedelta(days=30 * i)

            tabla.append(FilaAmortizacion(
                periodo=i,
                fecha=fecha.strftime('%Y-%m-%d'),
                cuota=round(interes, 2),
                capital=0,
                interes=round(interes, 2),
                saldo=round(saldo, 2),
                comision_mantenimiento=round(mantenimiento, 2)
            ))

        # Después de gracia: amortización o bullet
        if contrato.es_bullet:
            # Bullet después de gracia
            for i in range(n_gracia + 1, n_total + 1):
                interes = saldo * tasa_mensual
                mantenimiento = saldo * comision_mant

                if i == n_total:
                    capital = saldo
                    cuota = capital + interes
                    saldo_nuevo = 0
                else:
                    capital = 0
                    cuota = interes
                    saldo_nuevo = saldo

                fecha = fecha_base + timedelta(days=30 * i)

                tabla.append(FilaAmortizacion(
                    periodo=i,
                    fecha=fecha.strftime('%Y-%m-%d'),
                    cuota=round(cuota, 2),
                    capital=round(capital, 2),
                    interes=round(interes, 2),
                    saldo=round(saldo_nuevo, 2),
                    comision_mantenimiento=round(mantenimiento, 2)
                ))

                saldo = saldo_nuevo
        else:
            # Amortización francesa después de gracia
            if tasa_mensual > 0:
                cuota = saldo * (tasa_mensual * (1 + tasa_mensual)**n_amortizacion) / \
                        ((1 + tasa_mensual)**n_amortizacion - 1)
            else:
                cuota = saldo / n_amortizacion

            for i in range(n_gracia + 1, n_total + 1):
                interes = saldo * tasa_mensual
                capital = cuota - interes
                mantenimiento = saldo * comision_mant
                saldo_nuevo = max(0, saldo - capital)

                fecha = fecha_base + timedelta(days=30 * i)

                tabla.append(FilaAmortizacion(
                    periodo=i,
                    fecha=fecha.strftime('%Y-%m-%d'),
                    cuota=round(cuota, 2),
                    capital=round(capital, 2),
                    interes=round(interes, 2),
                    saldo=round(saldo_nuevo, 2),
                    comision_mantenimiento=round(mantenimiento, 2)
                ))

                saldo = saldo_nuevo

        return tabla

    def _calcular_total_comisiones(self, contrato: ContratoParseado,
                                    tabla: List[FilaAmortizacion]) -> float:
        """Calcula el total de comisiones del préstamo"""

        total = 0.0

        for comision in contrato.comisiones:
            if comision.tipo == "apertura":
                if comision.es_porcentaje:
                    total += contrato.monto_principal * comision.valor / 100
                else:
                    total += comision.valor

            elif comision.tipo == "seguro":
                total += comision.valor

            elif comision.tipo == "mantenimiento":
                # Ya calculado en la tabla
                total += sum(fila.comision_mantenimiento for fila in tabla)

        return round(total, 2)

    def _calcular_tea(self, contrato: ContratoParseado) -> float:
        """Calcula la Tasa Efectiva Anual"""

        tasa_nominal = contrato.tasa_nominal / 100

        # Determinar número de períodos por año
        periodos_por_ano = {
            FrecuenciaPago.MENSUAL: 12,
            FrecuenciaPago.TRIMESTRAL: 4,
            FrecuenciaPago.SEMESTRAL: 2,
            FrecuenciaPago.ANUAL: 1,
            FrecuenciaPago.BULLET: 1
        }

        n = periodos_por_ano.get(contrato.frecuencia_pago, 12)

        # TEA = (1 + r/n)^n - 1
        tea = ((1 + tasa_nominal / n) ** n - 1) * 100

        return round(tea, 2)

    def _calcular_cat(self, contrato: ContratoParseado, total_intereses: float,
                       total_comisiones: float) -> float:
        """Calcula el Costo Anual Total (CAT)"""

        monto = contrato.monto_principal
        plazo_anos = contrato.plazo_meses / 12

        if plazo_anos == 0 or monto == 0:
            return 0.0

        # CAT simplificado: (total pagado / monto - 1) / años
        total_pagado = monto + total_intereses + total_comisiones
        cat = ((total_pagado / monto - 1) / plazo_anos) * 100

        return round(cat, 2)

    def _calcular_vpn(self, contrato: ContratoParseado, tabla: List[FilaAmortizacion],
                       total_comisiones: float) -> float:
        """Calcula el Valor Presente Neto del costo de financiamiento"""

        # Tasa de descuento (usar tasa del contrato o una de referencia)
        tasa_descuento = contrato.tasa_nominal / 100 / 12

        # Flujos negativos (pagos del prestatario)
        flujos = [-contrato.monto_principal]  # Recibe el préstamo (positivo sería recibir)

        # Pagos mensuales
        for fila in tabla:
            pago = fila.cuota + fila.comision_mantenimiento
            flujos.append(-pago)

        # Agregar comisiones iniciales
        comision_inicial = 0
        for com in contrato.comisiones:
            if com.tipo in ["apertura", "seguro"]:
                if com.es_porcentaje:
                    comision_inicial += contrato.monto_principal * com.valor / 100
                else:
                    comision_inicial += com.valor

        flujos[0] -= comision_inicial

        # Calcular VPN
        vpn = 0
        for i, flujo in enumerate(flujos):
            vpn += flujo / ((1 + tasa_descuento) ** i)

        return round(vpn, 2)

    def _calcular_tir(self, contrato: ContratoParseado, tabla: List[FilaAmortizacion],
                       total_comisiones: float) -> float:
        """Calcula la Tasa Interna de Retorno"""

        # Flujos de caja
        flujos = [contrato.monto_principal]  # Desembolso inicial (desde perspectiva del prestamista)

        # Comisiones iniciales
        comision_inicial = 0
        for com in contrato.comisiones:
            if com.tipo in ["apertura", "seguro"]:
                if com.es_porcentaje:
                    comision_inicial += contrato.monto_principal * com.valor / 100
                else:
                    comision_inicial += com.valor

        flujos[0] = -(contrato.monto_principal - comision_inicial)  # Lo que realmente recibe

        # Pagos
        for fila in tabla:
            pago = fila.cuota + fila.comision_mantenimiento
            flujos.append(pago)

        # Calcular TIR usando numpy
        try:
            tir_mensual = np.irr(flujos)
            tir_anual = ((1 + tir_mensual) ** 12 - 1) * 100
            return round(tir_anual, 2)
        except Exception:
            # Si no se puede calcular, estimar
            return self._calcular_tea(contrato)

    def _comparar_con_mercado(self, contrato: ContratoParseado, tea: float) -> Dict[str, Any]:
        """Compara las condiciones con tasas de mercado"""

        if not self.market_rates:
            return {
                'diferencia': 0,
                'percentil': 50,
                'evaluacion': 'Sin datos de mercado disponibles'
            }

        # Determinar tipo de empresa por monto
        monto = contrato.monto_principal
        if monto < 500000:
            tipo_empresa = 'pyme'
        elif monto < 5000000:
            tipo_empresa = 'mediana'
        else:
            tipo_empresa = 'grande'

        # Determinar plazo
        plazo = contrato.plazo_meses
        if plazo <= 12:
            tipo_plazo = 'corto_plazo'
        elif plazo <= 36:
            tipo_plazo = 'mediano_plazo'
        else:
            tipo_plazo = 'largo_plazo'

        # Obtener tasa de referencia
        try:
            tasas_ref = self.market_rates['tasas_referencia']['por_tipo_empresa'][tipo_empresa][tipo_plazo]
            tasa_promedio = tasas_ref['promedio']
            tasa_max = tasas_ref['max']
            tasa_min = tasas_ref['min']
        except KeyError:
            return {
                'diferencia': 0,
                'percentil': 50,
                'evaluacion': 'Sin datos de mercado para este perfil'
            }

        # Calcular diferencia
        diferencia = tea - tasa_promedio

        # Calcular percentil aproximado
        if tea <= tasa_min:
            percentil = 10
        elif tea >= tasa_max:
            percentil = 90
        else:
            rango = tasa_max - tasa_min
            posicion = tea - tasa_min
            percentil = int(10 + (posicion / rango) * 80)

        # Evaluación
        if diferencia < -1:
            evaluacion = "Muy competitivo - Condiciones favorables"
        elif diferencia < 0.5:
            evaluacion = "Competitivo - En línea con el mercado"
        elif diferencia < 2:
            evaluacion = "Ligeramente elevado - Considerar negociar"
        else:
            evaluacion = "Elevado - Revisar alternativas de financiamiento"

        return {
            'diferencia': round(diferencia, 2),
            'percentil': percentil,
            'evaluacion': evaluacion,
            'tasa_promedio_mercado': tasa_promedio,
            'rango_mercado': f"{tasa_min}% - {tasa_max}%"
        }

    def _analisis_sensibilidad(self, contrato: ContratoParseado) -> Dict[str, Any]:
        """Análisis de sensibilidad para préstamos con tasa variable"""

        if contrato.tipo_tasa != TipoTasa.VARIABLE:
            return None

        # Escenarios de cambio en el índice de referencia
        escenarios = [-1.0, -0.5, 0, 0.5, 1.0, 2.0]

        resultados = []
        tasa_base = contrato.tasa_nominal

        for cambio in escenarios:
            # Aplicar cambio considerando cap y floor
            nueva_tasa = tasa_base + cambio

            if contrato.cap:
                nueva_tasa = min(nueva_tasa, contrato.cap)
            if contrato.floor:
                nueva_tasa = max(nueva_tasa, contrato.floor)

            # Crear copia del contrato con nueva tasa
            contrato_modificado = ContratoParseado()
            contrato_modificado.monto_principal = contrato.monto_principal
            contrato_modificado.tasa_nominal = nueva_tasa
            contrato_modificado.plazo_meses = contrato.plazo_meses
            contrato_modificado.frecuencia_pago = contrato.frecuencia_pago
            contrato_modificado.periodo_gracia_meses = contrato.periodo_gracia_meses
            contrato_modificado.es_bullet = contrato.es_bullet
            contrato_modificado.comisiones = contrato.comisiones

            # Calcular para este escenario
            tabla = self._generar_tabla_amortizacion(contrato_modificado)
            total_intereses = sum(fila.interes for fila in tabla)

            cuota_promedio = sum(fila.cuota for fila in tabla) / len(tabla) if tabla else 0

            resultados.append({
                'cambio_tasa': f"{'+' if cambio >= 0 else ''}{cambio}%",
                'tasa_resultante': round(nueva_tasa, 2),
                'cuota_promedio': round(cuota_promedio, 2),
                'total_intereses': round(total_intereses, 2),
                'impacto_vs_base': round(total_intereses - sum(fila.interes for fila in
                    self._generar_tabla_amortizacion(contrato)), 2)
            })

        return {
            'escenarios': resultados,
            'tiene_cap': contrato.cap is not None,
            'tiene_floor': contrato.floor is not None,
            'cap': contrato.cap,
            'floor': contrato.floor,
            'indice_referencia': contrato.indice_referencia
        }

    def calcular_escenario_prepago(self, contrato: ContratoParseado, mes_prepago: int,
                                    monto_prepago: float) -> Dict[str, Any]:
        """Calcula el impacto de un prepago"""

        # Generar tabla original
        tabla_original = self._generar_tabla_amortizacion(contrato)
        total_original = sum(fila.interes for fila in tabla_original)

        # Simular prepago
        tabla_prepago = []
        saldo = contrato.monto_principal
        tasa_mensual = contrato.tasa_nominal / 100 / 12
        ahorro_intereses = 0

        for i, fila in enumerate(tabla_original):
            if i + 1 == mes_prepago:
                # Aplicar prepago
                saldo = fila.saldo - monto_prepago
                if saldo < 0:
                    saldo = 0

            # Recalcular cuota si es necesario
            if i + 1 >= mes_prepago and saldo > 0:
                periodos_restantes = len(tabla_original) - i - 1
                if periodos_restantes > 0 and tasa_mensual > 0:
                    nueva_cuota = saldo * (tasa_mensual * (1 + tasa_mensual)**periodos_restantes) / \
                                  ((1 + tasa_mensual)**periodos_restantes - 1)
                else:
                    nueva_cuota = saldo

                tabla_prepago.append({
                    'periodo': i + 1,
                    'saldo': round(saldo, 2),
                    'cuota': round(nueva_cuota, 2)
                })

        # Calcular penalización
        penalizacion = 0
        if contrato.prepago and mes_prepago <= contrato.prepago.periodo_penalizacion_meses:
            penalizacion = monto_prepago * contrato.prepago.penalizacion / 100

        # Calcular ahorro
        total_con_prepago = sum(fila.interes for fila in tabla_original[:mes_prepago-1])
        # Estimar intereses restantes sobre saldo reducido
        saldo_reducido = tabla_original[mes_prepago-1].saldo - monto_prepago if mes_prepago <= len(tabla_original) else 0
        periodos_restantes = contrato.plazo_meses - mes_prepago
        intereses_restantes = saldo_reducido * tasa_mensual * periodos_restantes * 0.5  # Aproximación

        ahorro_intereses = total_original - total_con_prepago - intereses_restantes

        return {
            'ahorro_intereses': round(ahorro_intereses, 2),
            'penalizacion': round(penalizacion, 2),
            'beneficio_neto': round(ahorro_intereses - penalizacion, 2),
            'recomendacion': 'Prepago recomendado' if ahorro_intereses > penalizacion else 'Evaluar conveniencia'
        }

    def generar_resumen_financiero(self, resultado: ResultadoCalculo,
                                    contrato: ContratoParseado) -> Dict[str, Any]:
        """Genera un resumen financiero completo"""

        return {
            'resumen_ejecutivo': {
                'monto_financiado': contrato.monto_principal,
                'moneda': contrato.moneda,
                'costo_total': resultado.costo_total_financiamiento,
                'costo_por_cada_100': round((resultado.costo_total_financiamiento /
                                             contrato.monto_principal - 1) * 100, 2)
            },
            'tasas': {
                'tasa_nominal': contrato.tasa_nominal,
                'tasa_efectiva_anual': resultado.tasa_efectiva_anual,
                'costo_anual_total': resultado.costo_anual_total
            },
            'estructura_pagos': {
                'cuota_mensual': resultado.cuota_mensual,
                'numero_cuotas': len(resultado.tabla_amortizacion),
                'total_intereses': resultado.total_intereses,
                'total_comisiones': resultado.total_comisiones
            },
            'metricas_avanzadas': {
                'valor_presente_neto': resultado.valor_presente_neto,
                'tir': resultado.tir
            },
            'comparacion_mercado': {
                'diferencia_vs_promedio': resultado.diferencia_vs_mercado,
                'percentil': resultado.percentil_mercado,
                'evaluacion': resultado.evaluacion_mercado
            },
            'periodos_criticos': self._identificar_periodos_criticos(resultado.tabla_amortizacion)
        }

    def _identificar_periodos_criticos(self, tabla: List[FilaAmortizacion]) -> List[Dict]:
        """Identifica períodos con pagos elevados"""

        if not tabla:
            return []

        cuotas = [fila.cuota for fila in tabla]
        promedio = sum(cuotas) / len(cuotas)

        periodos_criticos = []
        for fila in tabla:
            if fila.cuota > promedio * 1.5:  # Cuotas 50% sobre el promedio
                periodos_criticos.append({
                    'periodo': fila.periodo,
                    'cuota': fila.cuota,
                    'razon': 'Cuota significativamente superior al promedio'
                })

        return periodos_criticos

    def tabla_amortizacion_a_dataframe(self, tabla: List[FilaAmortizacion]) -> pd.DataFrame:
        """Convierte la tabla de amortización a DataFrame de pandas"""

        data = []
        for fila in tabla:
            data.append({
                'Período': fila.periodo,
                'Fecha': fila.fecha,
                'Cuota': fila.cuota,
                'Capital': fila.capital,
                'Interés': fila.interes,
                'Saldo': fila.saldo,
                'Comisión Mant.': fila.comision_mantenimiento
            })

        return pd.DataFrame(data)


# Función de conveniencia
def calcular_financiero(contrato: ContratoParseado) -> ResultadoCalculo:
    """Función de conveniencia para cálculos financieros"""
    calculator = FinancialCalculator()
    return calculator.calcular(contrato)
