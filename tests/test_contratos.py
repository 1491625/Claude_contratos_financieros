"""
Tests de validación del sistema con contratos sintéticos
"""

import sys
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.contract_parser import ContractParser
from src.financial_calculator import FinancialCalculator
from src.risk_assessor import RiskAssessor
from src.report_generator import ReportGenerator


def test_contrato(nombre: str, ruta_pdf: str):
    """Ejecuta test completo sobre un contrato"""

    print(f"\n{'='*60}")
    print(f"ANALIZANDO: {nombre}")
    print(f"{'='*60}\n")

    # Inicializar componentes
    parser = ContractParser()
    calculator = FinancialCalculator()
    assessor = RiskAssessor()

    # 1. Parsear contrato
    print("1. Extrayendo información...")
    contrato = parser.parsear_contrato(ruta_pdf)

    print(f"   - Prestamista: {contrato.prestamista}")
    print(f"   - Prestatario: {contrato.prestatario}")
    print(f"   - Monto: {contrato.moneda} {contrato.monto_principal:,.2f}")
    print(f"   - Tasa: {contrato.tasa_nominal}% ({contrato.tipo_tasa.value})")
    print(f"   - Plazo: {contrato.plazo_meses} meses")
    print(f"   - Frecuencia: {contrato.frecuencia_pago.value}")
    print(f"   - Garantías: {len(contrato.garantias)}")
    print(f"   - Comisiones: {len(contrato.comisiones)}")
    print(f"   - Confianza extracción: {contrato.confianza_extraccion}%")

    if contrato.advertencias:
        print(f"   - Advertencias: {', '.join(contrato.advertencias)}")

    # Verificar extracción mínima
    assert contrato.monto_principal > 0, "Monto no extraído"
    assert contrato.plazo_meses > 0, "Plazo no extraído"

    # 2. Calcular financiero
    print("\n2. Calculando métricas financieras...")
    resultado_fin = calculator.calcular(contrato)

    print(f"   - TEA: {resultado_fin.tasa_efectiva_anual}%")
    print(f"   - CAT: {resultado_fin.costo_anual_total}%")
    print(f"   - Cuota mensual: {contrato.moneda} {resultado_fin.cuota_mensual:,.2f}")
    print(f"   - Total intereses: {contrato.moneda} {resultado_fin.total_intereses:,.2f}")
    print(f"   - Total comisiones: {contrato.moneda} {resultado_fin.total_comisiones:,.2f}")
    print(f"   - Costo total: {contrato.moneda} {resultado_fin.costo_total_financiamiento:,.2f}")
    print(f"   - Diferencia vs mercado: {resultado_fin.diferencia_vs_mercado:+.2f}%")
    print(f"   - Períodos en tabla: {len(resultado_fin.tabla_amortizacion)}")

    # Verificar cálculos
    assert resultado_fin.tabla_amortizacion, "Tabla de amortización vacía"
    assert resultado_fin.costo_anual_total > 0, "CAT no calculado"

    # 3. Evaluar riesgos
    print("\n3. Evaluando riesgos...")
    resultado_riesgo = assessor.evaluar(contrato, resultado_fin)

    print(f"   - Score total: {resultado_riesgo.score_total}/100")
    print(f"   - Nivel: {resultado_riesgo.nivel_riesgo.value}")
    print(f"   - Acción sugerida: {resultado_riesgo.accion_sugerida}")
    print(f"   - Red flags: {len(resultado_riesgo.red_flags)}")

    for sc in resultado_riesgo.scores_categorias:
        print(f"   - {sc.categoria}: {sc.score}/100 ({sc.nivel.value})")

    if resultado_riesgo.red_flags:
        print("\n   Red flags identificados:")
        for rf in resultado_riesgo.red_flags:
            print(f"   - [{rf.severidad.value}] {rf.descripcion}")

    print(f"\n   Fortalezas: {len(resultado_riesgo.fortalezas)}")
    print(f"   Debilidades: {len(resultado_riesgo.debilidades)}")
    print(f"   Puntos negociación: {len(resultado_riesgo.puntos_negociacion)}")

    # Verificar evaluación
    assert 0 <= resultado_riesgo.score_total <= 100, "Score fuera de rango"
    assert resultado_riesgo.accion_sugerida in ["Aceptar", "Negociar", "Rechazar"]

    print("\n✅ Test completado exitosamente")

    return {
        'nombre': nombre,
        'monto': contrato.monto_principal,
        'moneda': contrato.moneda,
        'tasa': contrato.tasa_nominal,
        'cat': resultado_fin.costo_anual_total,
        'score_riesgo': resultado_riesgo.score_total,
        'accion': resultado_riesgo.accion_sugerida,
        'confianza': contrato.confianza_extraccion
    }


def main():
    """Ejecuta tests sobre todos los contratos de prueba"""

    # Directorio de contratos
    dir_contratos = Path(__file__).parent.parent

    # Contratos de prueba
    contratos = [
        ("Test Básico", dir_contratos / "Contrato_Prestamo_Sintetico_Test.pdf"),
        ("Tasa Variable", dir_contratos / "Contrato_Prestamo_Sintetico_Variable.pdf"),
        ("Bullet + Gracia", dir_contratos / "Contrato_Prestamo_Sintetico_Bullet_Gracia.pdf"),
        ("MultiTramos", dir_contratos / "Contrato_Prestamo_Sintetico_MultiTramos.pdf")
    ]

    resultados = []
    errores = []

    for nombre, ruta in contratos:
        if not ruta.exists():
            print(f"⚠️ Archivo no encontrado: {ruta}")
            continue

        try:
            resultado = test_contrato(nombre, str(ruta))
            resultados.append(resultado)
        except Exception as e:
            print(f"\n❌ Error en {nombre}: {str(e)}")
            errores.append((nombre, str(e)))

    # Resumen final
    print(f"\n{'='*60}")
    print("RESUMEN DE TESTS")
    print(f"{'='*60}\n")

    print(f"Contratos analizados: {len(resultados)}/{len(contratos)}")
    print(f"Errores: {len(errores)}")

    if resultados:
        print("\n| Contrato | Monto | CAT | Score | Acción | Confianza |")
        print("|----------|-------|-----|-------|--------|-----------|")
        for r in resultados:
            print(f"| {r['nombre'][:15]} | {r['moneda']} {r['monto']:,.0f} | "
                  f"{r['cat']:.1f}% | {r['score_riesgo']} | {r['accion']} | {r['confianza']:.0f}% |")

    if errores:
        print("\nErrores encontrados:")
        for nombre, error in errores:
            print(f"  - {nombre}: {error}")

    # Resultado final
    if len(errores) == 0:
        print("\n✅ TODOS LOS TESTS PASARON")
        return 0
    else:
        print(f"\n❌ {len(errores)} TESTS FALLARON")
        return 1


if __name__ == "__main__":
    sys.exit(main())
