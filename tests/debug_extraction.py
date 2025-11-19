"""Debug de extracción de texto y patrones"""

import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.contract_parser import ContractParser

def debug_contrato(nombre: str, ruta_pdf: str):
    parser = ContractParser()

    # Extraer texto
    texto = parser.extraer_texto_pdf(ruta_pdf)

    print(f"\n{'='*60}")
    print(f"DEBUG: {nombre}")
    print(f"{'='*60}")

    # Buscar sección de comisiones
    print("\n--- Texto relacionado con comisiones ---")
    lineas = texto.split('\n')
    for i, linea in enumerate(lineas):
        if any(palabra in linea.lower() for palabra in ['comisión', 'apertura', 'mantenimiento', 'seguro']):
            print(f"{i}: {linea}")

    # Probar patrones
    print("\n--- Prueba de patrones ---")

    # Apertura
    patron_apertura = re.compile(
        r'(?:comisión\s*(?:de\s*)?)?apertura\s*(?:del?\s*)?(\d+(?:[.,]\d+)?)\s*%',
        re.IGNORECASE
    )
    matches = patron_apertura.findall(texto)
    print(f"Apertura encontradas: {matches}")

    # Mantenimiento
    patron_mant = re.compile(
        r'mantenimiento\s*(?:mensual\s*)?(?:del?\s*)?(\d+(?:[.,]\d+)?)\s*%',
        re.IGNORECASE
    )
    matches = patron_mant.findall(texto)
    print(f"Mantenimiento encontradas: {matches}")

    # Seguro
    patron_seguro = re.compile(
        r'seguro\s*(?:de\s*)?(?:vida|crédito|multirriesgo|inmueble)?\s*'
        r'(?:obligatorio\s*)?(?:por\s*)?[\$€]?\s*([\d,.]+)',
        re.IGNORECASE
    )
    matches = patron_seguro.findall(texto)
    print(f"Seguros encontrados: {matches}")

    # Buscar el texto exacto
    print("\n--- Búsqueda contextual ---")

    # Buscar "apertura" y mostrar contexto
    for match in re.finditer(r'.{0,50}apertura.{0,50}', texto, re.IGNORECASE):
        print(f"Contexto apertura: '{match.group()}'")

    for match in re.finditer(r'.{0,50}mantenimiento.{0,50}', texto, re.IGNORECASE):
        print(f"Contexto mantenimiento: '{match.group()}'")


if __name__ == "__main__":
    dir_contratos = Path(__file__).parent.parent

    debug_contrato(
        "Test Básico",
        str(dir_contratos / "Contrato_Prestamo_Sintetico_Test.pdf")
    )

    # Test directo de la función
    print("\n--- Test directo de _extraer_comisiones ---")
    parser = ContractParser()
    texto = parser.extraer_texto_pdf(str(dir_contratos / "Contrato_Prestamo_Sintetico_Test.pdf"))

    # Probar con los patrones de la instancia
    print(f"Patrón apertura: {parser.patron_comision_apertura.pattern}")
    match = parser.patron_comision_apertura.search(texto)
    if match:
        print(f"Match apertura: {match.group(0)} -> {match.group(1)}")
    else:
        print("No match apertura")

    print(f"Patrón mantenimiento: {parser.patron_comision_mantenimiento.pattern}")
    match = parser.patron_comision_mantenimiento.search(texto)
    if match:
        print(f"Match mantenimiento: {match.group(0)} -> {match.group(1)}")
    else:
        print("No match mantenimiento")

    # Llamar directamente a la función
    comisiones = parser._extraer_comisiones(texto)
    print(f"\nComisiones extraídas: {len(comisiones)}")
    for c in comisiones:
        print(f"  - {c.tipo}: {c.valor} ({'%' if c.es_porcentaje else 'fijo'})")
