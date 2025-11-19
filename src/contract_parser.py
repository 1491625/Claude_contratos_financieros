"""
Motor de Extracción Inteligente de Contratos de Préstamo
Identifica y extrae elementos críticos de contratos PDF
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from PyPDF2 import PdfReader


class TipoTasa(Enum):
    FIJA = "fija"
    VARIABLE = "variable"


class TipoGarantia(Enum):
    REAL = "real"
    PERSONAL = "personal"
    MIXTA = "mixta"
    SIN_GARANTIA = "sin_garantia"


class FrecuenciaPago(Enum):
    MENSUAL = "mensual"
    TRIMESTRAL = "trimestral"
    SEMESTRAL = "semestral"
    ANUAL = "anual"
    BULLET = "bullet"


@dataclass
class Comision:
    tipo: str
    valor: float
    es_porcentaje: bool
    base: str = "monto_principal"
    descripcion: str = ""


@dataclass
class Garantia:
    tipo: str
    descripcion: str
    tipo_general: TipoGarantia = TipoGarantia.PERSONAL


@dataclass
class ClausulaPrepago:
    permitido: bool
    penalizacion: float
    periodo_penalizacion_meses: int
    descripcion: str = ""


@dataclass
class Covenant:
    tipo: str
    valor: float
    operador: str
    descripcion: str = ""


@dataclass
class ClausulaIncumplimiento:
    tipo: str
    descripcion: str
    tiene_aceleracion: bool = False


@dataclass
class Tramo:
    nombre: str
    monto: float
    moneda: str
    tasa: float
    tipo_tasa: TipoTasa
    plazo_meses: int
    frecuencia_pago: FrecuenciaPago
    indice_referencia: Optional[str] = None
    spread: Optional[float] = None
    cap: Optional[float] = None
    floor: Optional[float] = None
    periodo_gracia_meses: int = 0
    garantias: List[Garantia] = field(default_factory=list)
    comisiones: List[Comision] = field(default_factory=list)
    prepago: Optional[ClausulaPrepago] = None


@dataclass
class ContratoParseado:
    # Información general
    prestamista: str = ""
    prestatario: str = ""

    # Tramos (un contrato simple tiene 1 tramo)
    tramos: List[Tramo] = field(default_factory=list)

    # Información consolidada (para contratos simples)
    monto_principal: float = 0.0
    moneda: str = "USD"
    tasa_nominal: float = 0.0
    tipo_tasa: TipoTasa = TipoTasa.FIJA
    plazo_meses: int = 0
    frecuencia_pago: FrecuenciaPago = FrecuenciaPago.MENSUAL

    # Tasa variable
    indice_referencia: Optional[str] = None
    spread_bps: Optional[float] = None
    cap: Optional[float] = None
    floor: Optional[float] = None

    # Estructura especial
    periodo_gracia_meses: int = 0
    es_bullet: bool = False

    # Garantías y cláusulas
    garantias: List[Garantia] = field(default_factory=list)
    tipo_garantia_general: TipoGarantia = TipoGarantia.SIN_GARANTIA
    comisiones: List[Comision] = field(default_factory=list)
    prepago: Optional[ClausulaPrepago] = None
    covenants: List[Covenant] = field(default_factory=list)
    clausulas_incumplimiento: List[ClausulaIncumplimiento] = field(default_factory=list)

    # Cross-default y jurisdicción
    tiene_cross_default: bool = False
    jurisdiccion: str = ""

    # Metadatos de extracción
    confianza_extraccion: float = 0.0
    advertencias: List[str] = field(default_factory=list)
    texto_original: str = ""


class ContractParser:
    """Parser inteligente de contratos de préstamo"""

    def __init__(self):
        self._compilar_patrones()

    def _compilar_patrones(self):
        """Compila patrones regex para extracción"""

        # Patrones de monto y moneda
        self.patron_monto_usd = re.compile(
            r'\$\s*([\d,]+(?:\.\d{2})?)\s*(?:\(?\s*(?:USD|dólares?|dolares?)\s*)?',
            re.IGNORECASE
        )
        self.patron_monto_eur = re.compile(
            r'€\s*([\d,]+(?:\.\d{2})?)|'
            r'([\d,]+(?:\.\d{2})?)\s*(?:€|EUR|euros?)',
            re.IGNORECASE
        )
        self.patron_monto_mxn = re.compile(
            r'MXN\s*([\d,]+(?:\.\d{2})?)|'
            r'([\d,]+(?:\.\d{2})?)\s*(?:MXN|pesos?)',
            re.IGNORECASE
        )

        # Patrones de tasa
        self.patron_tasa_fija = re.compile(
            r'(\d+(?:\.\d+)?)\s*%\s*(?:fija|fijo)?\s*(?:nominal)?\s*(?:anual)?',
            re.IGNORECASE
        )
        self.patron_tasa_variable = re.compile(
            r'(EURIBOR|TIIE|LIBOR|PRIME)\s*(\d+[M]?)?\s*\+\s*(\d+(?:\.\d+)?)\s*%?'
            r'|(\d+(?:\.\d+)?)\s*(?:puntos?\s*base|bps|pb)',
            re.IGNORECASE
        )
        self.patron_cap_floor = re.compile(
            r'(?:cap|techo)\s*(?:\([^)]*\))?\s*(?:de\s*)?(\d+(?:[.,]\d+)?)\s*%|'
            r'(?:floor|piso)\s*(?:\([^)]*\))?\s*(?:de\s*)?(\d+(?:[.,]\d+)?)\s*%',
            re.IGNORECASE
        )

        # Patrones de plazo
        self.patron_plazo = re.compile(
            r'(\d+)\s*(?:meses?|mes)',
            re.IGNORECASE
        )
        self.patron_plazo_anos = re.compile(
            r'(\d+)\s*(?:años?|ano)',
            re.IGNORECASE
        )

        # Patrones de frecuencia
        self.patron_frecuencia = re.compile(
            r'pagos?\s*(mensual(?:es)?|trimestral(?:es)?|semestral(?:es)?|anual(?:es)?)',
            re.IGNORECASE
        )

        # Patrones de comisiones
        self.patron_comision_apertura = re.compile(
            r'(?:comisión\s*(?:de\s*)?)?apertura\s*(?:del?\s*)?(\d+(?:[.,]\d+)?)\s*%',
            re.IGNORECASE
        )
        self.patron_comision_mantenimiento = re.compile(
            r'mantenimiento\s*(?:mensual\s*)?(?:del?\s*)?(\d+(?:[.,]\d+)?)\s*%',
            re.IGNORECASE
        )
        self.patron_seguro = re.compile(
            r'seguro\s*(?:de\s*)?(?:vida|crédito|multirriesgo|inmueble)?\s*'
            r'(?:obligatorio\s*)?(?:por\s*)?[\$€]?\s*([\d,.]+)',
            re.IGNORECASE
        )

        # Patrones de prepago
        self.patron_prepago_penalizacion = re.compile(
            r'penaliza(?:ción|cion)\s*(?:del?\s*)?(\d+(?:\.\d+)?)\s*%',
            re.IGNORECASE
        )
        self.patron_prepago_periodo = re.compile(
            r'(?:primeros?|dentro\s*de\s*(?:los\s*)?)\s*(\d+)\s*meses?',
            re.IGNORECASE
        )

        # Patrones de garantías
        self.patron_hipoteca = re.compile(
            r'hipoteca\s*(?:de\s*)?(\d+[º°]?\s*grado)?',
            re.IGNORECASE
        )
        self.patron_prenda = re.compile(
            r'prenda\s*(?:sobre\s*)?([\w\s,]+?)(?:\.|,|y\s+aval)',
            re.IGNORECASE
        )
        self.patron_aval = re.compile(
            r'aval\s*(?:personal\s*)?(?:solidario)?',
            re.IGNORECASE
        )

        # Patrones de covenants
        self.patron_dscr = re.compile(
            r'DSCR\s*[≥>=]+\s*(\d+(?:\.\d+)?)',
            re.IGNORECASE
        )
        self.patron_deuda_ebitda = re.compile(
            r'[Dd]euda\s*[Nn]eta?\s*/\s*EBITDA\s*[≤<=]+\s*(\d+(?:\.\d+)?)',
            re.IGNORECASE
        )

        # Patrones de cláusulas
        self.patron_cross_default = re.compile(
            r'cross[\s-]*default',
            re.IGNORECASE
        )
        self.patron_aceleracion = re.compile(
            r'aceleración|vencimiento\s*anticipado',
            re.IGNORECASE
        )
        self.patron_mora = re.compile(
            r'mora\s*(?:superior\s*a\s*)?(?:>?\s*)?(\d+)\s*días?',
            re.IGNORECASE
        )

        # Patrones de partes
        self.patron_prestamista = re.compile(
            r'PRESTAMISTA:\s*([^,]+)',
            re.IGNORECASE
        )
        self.patron_prestatario = re.compile(
            r'PRESTATARIO:\s*([^,]+)',
            re.IGNORECASE
        )

        # Patrones de gracia y bullet
        self.patron_gracia = re.compile(
            r'(?:periodo|período)\s*(?:de\s*)?gracia\s*(?:de\s*(?:capital\s*)?)?(?:de\s*)?(\d+)\s*meses?',
            re.IGNORECASE
        )
        self.patron_bullet = re.compile(
            r'bullet|pago\s*único\s*(?:de\s*capital)?(?:\s*al\s*vencimiento)?',
            re.IGNORECASE
        )

        # Patrón de tramos
        self.patron_tramo = re.compile(
            r'Tramo\s*([A-Z])\s*[:\(]',
            re.IGNORECASE
        )

    def extraer_texto_pdf(self, ruta_pdf: str) -> str:
        """Extrae texto de un archivo PDF usando PyPDF2"""
        texto = ""

        try:
            with open(ruta_pdf, 'rb') as archivo:
                lector = PdfReader(archivo)
                for pagina in lector.pages:
                    texto_pagina = pagina.extract_text()
                    if texto_pagina:
                        texto += texto_pagina + "\n"
        except Exception as e:
            pass

        return texto.strip()

    def parsear_contrato(self, ruta_pdf: str) -> ContratoParseado:
        """Parsea un contrato PDF y extrae toda la información relevante"""

        texto = self.extraer_texto_pdf(ruta_pdf)
        if not texto:
            contrato = ContratoParseado()
            contrato.advertencias.append("No se pudo extraer texto del PDF")
            return contrato

        contrato = ContratoParseado()
        contrato.texto_original = texto

        # Detectar si es multitramo
        tramos_encontrados = self.patron_tramo.findall(texto)

        if len(tramos_encontrados) > 1:
            contrato = self._parsear_multitramo(texto, contrato)
        else:
            contrato = self._parsear_simple(texto, contrato)

        # Extraer información común
        contrato = self._extraer_partes(texto, contrato)
        contrato = self._extraer_covenants(texto, contrato)
        contrato = self._extraer_clausulas_incumplimiento(texto, contrato)
        contrato = self._extraer_jurisdiccion(texto, contrato)

        # Calcular confianza
        contrato.confianza_extraccion = self._calcular_confianza(contrato)

        return contrato

    def _parsear_simple(self, texto: str, contrato: ContratoParseado) -> ContratoParseado:
        """Parsea un contrato simple (un solo tramo)"""

        # Extraer monto y moneda
        monto, moneda = self._extraer_monto_principal(texto)
        contrato.monto_principal = monto
        contrato.moneda = moneda

        # Extraer tasa
        tasa_info = self._extraer_tasa(texto)
        contrato.tasa_nominal = tasa_info['tasa']
        contrato.tipo_tasa = tasa_info['tipo']
        contrato.indice_referencia = tasa_info.get('indice')
        contrato.spread_bps = tasa_info.get('spread')
        contrato.cap = tasa_info.get('cap')
        contrato.floor = tasa_info.get('floor')

        # Extraer plazo y frecuencia
        contrato.plazo_meses = self._extraer_plazo(texto)
        contrato.frecuencia_pago = self._extraer_frecuencia(texto)

        # Extraer estructura especial
        gracia = self._extraer_periodo_gracia(texto)
        contrato.periodo_gracia_meses = gracia
        contrato.es_bullet = bool(self.patron_bullet.search(texto))

        # Extraer garantías
        contrato.garantias = self._extraer_garantias(texto)
        contrato.tipo_garantia_general = self._determinar_tipo_garantia(contrato.garantias)

        # Extraer comisiones
        contrato.comisiones = self._extraer_comisiones(texto)

        # Extraer prepago
        contrato.prepago = self._extraer_prepago(texto)

        return contrato

    def _parsear_multitramo(self, texto: str, contrato: ContratoParseado) -> ContratoParseado:
        """Parsea un contrato con múltiples tramos"""

        # Dividir texto por tramos
        secciones_tramo = re.split(r'(?=\d+\.\s*Tramo\s*[A-Z])', texto, flags=re.IGNORECASE)

        for seccion in secciones_tramo:
            match_tramo = self.patron_tramo.search(seccion)
            if match_tramo:
                nombre_tramo = f"Tramo {match_tramo.group(1).upper()}"
                tramo = self._extraer_tramo(seccion, nombre_tramo)
                contrato.tramos.append(tramo)

        # Consolidar información del primer tramo como principal
        if contrato.tramos:
            primer_tramo = contrato.tramos[0]
            contrato.monto_principal = primer_tramo.monto
            contrato.moneda = primer_tramo.moneda
            contrato.tasa_nominal = primer_tramo.tasa
            contrato.tipo_tasa = primer_tramo.tipo_tasa
            contrato.plazo_meses = primer_tramo.plazo_meses
            contrato.frecuencia_pago = primer_tramo.frecuencia_pago

        # Extraer garantías del texto completo
        contrato.garantias = self._extraer_garantias(texto)

        # Si no hay garantías en el texto principal, consolidar de tramos
        if not contrato.garantias and contrato.tramos:
            garantias_vistas = set()
            for tramo in contrato.tramos:
                for g in tramo.garantias:
                    if g.descripcion not in garantias_vistas:
                        contrato.garantias.append(g)
                        garantias_vistas.add(g.descripcion)

        contrato.tipo_garantia_general = self._determinar_tipo_garantia(contrato.garantias)

        # Extraer comisiones y prepago del texto completo
        contrato.comisiones = self._extraer_comisiones(texto)
        contrato.prepago = self._extraer_prepago(texto)

        # Si no hay comisiones en el contrato principal, consolidar de tramos
        if not contrato.comisiones and contrato.tramos:
            for tramo in contrato.tramos:
                contrato.comisiones.extend(tramo.comisiones)

        return contrato

    def _extraer_tramo(self, texto_tramo: str, nombre: str) -> Tramo:
        """Extrae información de un tramo específico"""

        monto, moneda = self._extraer_monto_principal(texto_tramo)
        tasa_info = self._extraer_tasa(texto_tramo)
        plazo = self._extraer_plazo(texto_tramo)
        frecuencia = self._extraer_frecuencia(texto_tramo)
        gracia = self._extraer_periodo_gracia(texto_tramo)
        garantias = self._extraer_garantias(texto_tramo)
        comisiones = self._extraer_comisiones(texto_tramo)
        prepago = self._extraer_prepago(texto_tramo)

        return Tramo(
            nombre=nombre,
            monto=monto,
            moneda=moneda,
            tasa=tasa_info['tasa'],
            tipo_tasa=tasa_info['tipo'],
            plazo_meses=plazo,
            frecuencia_pago=frecuencia,
            indice_referencia=tasa_info.get('indice'),
            spread=tasa_info.get('spread'),
            cap=tasa_info.get('cap'),
            floor=tasa_info.get('floor'),
            periodo_gracia_meses=gracia,
            garantias=garantias,
            comisiones=comisiones,
            prepago=prepago
        )

    def _extraer_monto_principal(self, texto: str) -> Tuple[float, str]:
        """Extrae el monto principal y la moneda"""

        # Buscar en orden de prioridad
        # USD
        match = self.patron_monto_usd.search(texto)
        if match:
            monto_str = match.group(1).replace(',', '')
            return float(monto_str), "USD"

        # EUR
        match = self.patron_monto_eur.search(texto)
        if match:
            monto_str = (match.group(1) or match.group(2)).replace(',', '')
            return float(monto_str), "EUR"

        # MXN
        match = self.patron_monto_mxn.search(texto)
        if match:
            monto_str = (match.group(1) or match.group(2)).replace(',', '')
            return float(monto_str), "MXN"

        return 0.0, "USD"

    def _extraer_tasa(self, texto: str) -> Dict[str, Any]:
        """Extrae información de la tasa de interés"""

        resultado = {
            'tasa': 0.0,
            'tipo': TipoTasa.FIJA,
            'indice': None,
            'spread': None,
            'cap': None,
            'floor': None
        }

        # Determinar si es principalmente fija o variable
        # Buscar patrones que indiquen tasa fija
        es_principalmente_fija = bool(re.search(
            r'\d+(?:[.,]\d+)?\s*%?\s*fija|'
            r'tasa\s+fija|'
            r'interés\s+(?:será\s+)?\d+(?:[.,]\d+)?\s*%\s*fija',
            texto, re.IGNORECASE
        ))

        # Buscar patrones que indiquen tasa variable como principal
        es_principalmente_variable = bool(re.search(
            r'^[^.]*tasa\s*(?:de\s*interés\s*)?(?:será\s*)?variable|'
            r'2\.\s*Tasa[^.]*variable',
            texto, re.IGNORECASE | re.MULTILINE
        ))

        # Buscar tasa fija
        match_fija = self.patron_tasa_fija.search(texto)
        if match_fija:
            resultado['tasa'] = float(match_fija.group(1))

        # Si es principalmente variable, buscar índice y spread
        if es_principalmente_variable and not es_principalmente_fija:
            resultado['tipo'] = TipoTasa.VARIABLE
            match_variable = self.patron_tasa_variable.search(texto)
            if match_variable:
                if match_variable.group(1):  # EURIBOR, TIIE, etc.
                    resultado['indice'] = match_variable.group(1).upper()
                    if match_variable.group(2):
                        resultado['indice'] += f" {match_variable.group(2)}"

                    spread = match_variable.group(3)
                    if spread:
                        resultado['spread'] = float(spread)
                        # Convertir porcentaje a bps si es necesario
                        if resultado['spread'] < 10:
                            resultado['spread'] *= 100
                elif match_variable.group(4):  # Solo puntos base
                    resultado['spread'] = float(match_variable.group(4))

        # Buscar cap y floor
        for match in self.patron_cap_floor.finditer(texto):
            if match.group(1):  # cap
                valor = match.group(1).replace(',', '.')
                resultado['cap'] = float(valor)
            if match.group(2):  # floor
                valor = match.group(2).replace(',', '.')
                resultado['floor'] = float(valor)

        return resultado

    def _extraer_plazo(self, texto: str) -> int:
        """Extrae el plazo en meses"""

        # Buscar en meses primero
        match = self.patron_plazo.search(texto)
        if match:
            return int(match.group(1))

        # Buscar en años
        match = self.patron_plazo_anos.search(texto)
        if match:
            return int(match.group(1)) * 12

        return 0

    def _extraer_frecuencia(self, texto: str) -> FrecuenciaPago:
        """Extrae la frecuencia de pagos"""

        match = self.patron_frecuencia.search(texto)
        if match:
            freq = match.group(1).lower()
            if 'mensual' in freq:
                return FrecuenciaPago.MENSUAL
            elif 'trimestral' in freq:
                return FrecuenciaPago.TRIMESTRAL
            elif 'semestral' in freq:
                return FrecuenciaPago.SEMESTRAL
            elif 'anual' in freq:
                return FrecuenciaPago.ANUAL

        # Buscar bullet
        if self.patron_bullet.search(texto):
            return FrecuenciaPago.BULLET

        return FrecuenciaPago.MENSUAL

    def _extraer_periodo_gracia(self, texto: str) -> int:
        """Extrae el período de gracia en meses"""

        match = self.patron_gracia.search(texto)
        if match:
            return int(match.group(1))
        return 0

    def _extraer_garantias(self, texto: str) -> List[Garantia]:
        """Extrae las garantías del contrato"""

        garantias = []

        # Hipoteca
        match = self.patron_hipoteca.search(texto)
        if match:
            grado = match.group(1) if match.group(1) else ""
            garantias.append(Garantia(
                tipo="hipoteca",
                descripcion=f"Hipoteca {grado}".strip(),
                tipo_general=TipoGarantia.REAL
            ))

        # Prenda
        match = self.patron_prenda.search(texto)
        if match:
            objeto = match.group(1).strip()
            garantias.append(Garantia(
                tipo="prenda",
                descripcion=f"Prenda sobre {objeto}",
                tipo_general=TipoGarantia.REAL
            ))

        # Aval
        if self.patron_aval.search(texto):
            garantias.append(Garantia(
                tipo="aval",
                descripcion="Aval personal solidario",
                tipo_general=TipoGarantia.PERSONAL
            ))

        return garantias

    def _determinar_tipo_garantia(self, garantias: List[Garantia]) -> TipoGarantia:
        """Determina el tipo general de garantía"""

        if not garantias:
            return TipoGarantia.SIN_GARANTIA

        tiene_real = any(g.tipo_general == TipoGarantia.REAL for g in garantias)
        tiene_personal = any(g.tipo_general == TipoGarantia.PERSONAL for g in garantias)

        if tiene_real and tiene_personal:
            return TipoGarantia.MIXTA
        elif tiene_real:
            return TipoGarantia.REAL
        elif tiene_personal:
            return TipoGarantia.PERSONAL

        return TipoGarantia.SIN_GARANTIA

    def _extraer_comisiones(self, texto: str) -> List[Comision]:
        """Extrae las comisiones del contrato"""

        comisiones = []

        # Comisión de apertura
        match = self.patron_comision_apertura.search(texto)
        if match:
            valor_str = match.group(1).replace(',', '.')
            comisiones.append(Comision(
                tipo="apertura",
                valor=float(valor_str),
                es_porcentaje=True,
                base="monto_principal",
                descripcion="Comisión de apertura"
            ))

        # Comisión de mantenimiento
        match = self.patron_comision_mantenimiento.search(texto)
        if match:
            valor_str = match.group(1).replace(',', '.')
            comisiones.append(Comision(
                tipo="mantenimiento",
                valor=float(valor_str),
                es_porcentaje=True,
                base="saldo_insoluto",
                descripcion="Comisión de mantenimiento mensual"
            ))

        # Seguro
        match = self.patron_seguro.search(texto)
        if match:
            valor_str = match.group(1).replace(',', '')
            comisiones.append(Comision(
                tipo="seguro",
                valor=float(valor_str),
                es_porcentaje=False,
                descripcion="Seguro obligatorio"
            ))

        return comisiones

    def _extraer_prepago(self, texto: str) -> Optional[ClausulaPrepago]:
        """Extrae las condiciones de prepago"""

        # Verificar si se permite prepago
        if 'no se permite' in texto.lower() and 'prepago' in texto.lower():
            return ClausulaPrepago(
                permitido=False,
                penalizacion=0,
                periodo_penalizacion_meses=0,
                descripcion="Prepago no permitido"
            )

        penalizacion = 0
        periodo = 0

        # Buscar penalización
        match = self.patron_prepago_penalizacion.search(texto)
        if match:
            penalizacion = float(match.group(1))

        # Buscar período de penalización
        match = self.patron_prepago_periodo.search(texto)
        if match:
            periodo = int(match.group(1))

        return ClausulaPrepago(
            permitido=True,
            penalizacion=penalizacion,
            periodo_penalizacion_meses=periodo,
            descripcion=f"Penalización {penalizacion}% en primeros {periodo} meses"
        )

    def _extraer_covenants(self, texto: str, contrato: ContratoParseado) -> ContratoParseado:
        """Extrae los covenants financieros"""

        # DSCR
        match = self.patron_dscr.search(texto)
        if match:
            contrato.covenants.append(Covenant(
                tipo="DSCR",
                valor=float(match.group(1)),
                operador=">=",
                descripcion="Ratio de Cobertura del Servicio de Deuda"
            ))

        # Deuda/EBITDA
        match = self.patron_deuda_ebitda.search(texto)
        if match:
            contrato.covenants.append(Covenant(
                tipo="Deuda/EBITDA",
                valor=float(match.group(1)),
                operador="<=",
                descripcion="Ratio de apalancamiento"
            ))

        # Negative pledge
        if 'negative pledge' in texto.lower():
            contrato.covenants.append(Covenant(
                tipo="Negative Pledge",
                valor=0,
                operador="",
                descripcion="Prohibición de gravar activos clave"
            ))

        return contrato

    def _extraer_clausulas_incumplimiento(self, texto: str, contrato: ContratoParseado) -> ContratoParseado:
        """Extrae las cláusulas de incumplimiento"""

        # Cross-default
        if self.patron_cross_default.search(texto):
            contrato.tiene_cross_default = True
            contrato.clausulas_incumplimiento.append(ClausulaIncumplimiento(
                tipo="cross_default",
                descripcion="Incumplimiento cruzado con otras obligaciones",
                tiene_aceleracion=True
            ))

        # Mora
        match = self.patron_mora.search(texto)
        if match:
            dias = match.group(1)
            contrato.clausulas_incumplimiento.append(ClausulaIncumplimiento(
                tipo="mora",
                descripcion=f"Mora superior a {dias} días",
                tiene_aceleracion=True
            ))

        # Aceleración general
        if self.patron_aceleracion.search(texto):
            # Contar triggers de aceleración
            triggers = texto.lower().count('incumplimiento') + texto.lower().count('insolvencia')
            if triggers > 0 and not any(c.tipo == "aceleracion" for c in contrato.clausulas_incumplimiento):
                contrato.clausulas_incumplimiento.append(ClausulaIncumplimiento(
                    tipo="aceleracion",
                    descripcion=f"Cláusula de vencimiento anticipado ({triggers} triggers)",
                    tiene_aceleracion=True
                ))

        return contrato

    def _extraer_partes(self, texto: str, contrato: ContratoParseado) -> ContratoParseado:
        """Extrae las partes del contrato"""

        match = self.patron_prestamista.search(texto)
        if match:
            contrato.prestamista = match.group(1).strip().rstrip(',')

        match = self.patron_prestatario.search(texto)
        if match:
            contrato.prestatario = match.group(1).strip().rstrip(',')

        return contrato

    def _extraer_jurisdiccion(self, texto: str, contrato: ContratoParseado) -> ContratoParseado:
        """Extrae la jurisdicción"""

        # Buscar tribunales
        match = re.search(r'tribunales\s+de\s+([^,\.]+)', texto, re.IGNORECASE)
        if match:
            contrato.jurisdiccion = match.group(1).strip()

        return contrato

    def _calcular_confianza(self, contrato: ContratoParseado) -> float:
        """Calcula el nivel de confianza de la extracción"""

        score = 100.0

        # Penalizar por campos faltantes
        if contrato.monto_principal == 0:
            score -= 20
            contrato.advertencias.append("No se pudo extraer el monto principal")

        if contrato.tasa_nominal == 0 and contrato.tipo_tasa == TipoTasa.FIJA:
            score -= 15
            contrato.advertencias.append("No se pudo extraer la tasa de interés")

        if contrato.plazo_meses == 0:
            score -= 15
            contrato.advertencias.append("No se pudo extraer el plazo")

        if not contrato.garantias:
            score -= 5
            contrato.advertencias.append("No se identificaron garantías explícitas")

        if not contrato.comisiones:
            score -= 5
            contrato.advertencias.append("No se identificaron comisiones")

        if not contrato.prestamista:
            score -= 5

        if not contrato.prestatario:
            score -= 5

        return max(0, score)

    def obtener_resumen(self, contrato: ContratoParseado) -> Dict[str, Any]:
        """Genera un resumen estructurado del contrato"""

        resumen = {
            'partes': {
                'prestamista': contrato.prestamista,
                'prestatario': contrato.prestatario
            },
            'condiciones_principales': {
                'monto': contrato.monto_principal,
                'moneda': contrato.moneda,
                'tasa_nominal': contrato.tasa_nominal,
                'tipo_tasa': contrato.tipo_tasa.value,
                'plazo_meses': contrato.plazo_meses,
                'frecuencia_pago': contrato.frecuencia_pago.value
            },
            'estructura_especial': {
                'periodo_gracia_meses': contrato.periodo_gracia_meses,
                'es_bullet': contrato.es_bullet
            },
            'garantias': {
                'tipo_general': contrato.tipo_garantia_general.value,
                'detalle': [{'tipo': g.tipo, 'descripcion': g.descripcion} for g in contrato.garantias]
            },
            'comisiones': [
                {
                    'tipo': c.tipo,
                    'valor': c.valor,
                    'es_porcentaje': c.es_porcentaje
                } for c in contrato.comisiones
            ],
            'prepago': {
                'permitido': contrato.prepago.permitido if contrato.prepago else True,
                'penalizacion': contrato.prepago.penalizacion if contrato.prepago else 0,
                'periodo_meses': contrato.prepago.periodo_penalizacion_meses if contrato.prepago else 0
            },
            'covenants': [
                {
                    'tipo': c.tipo,
                    'valor': c.valor,
                    'operador': c.operador
                } for c in contrato.covenants
            ],
            'riesgos_identificados': {
                'tiene_cross_default': contrato.tiene_cross_default,
                'num_clausulas_incumplimiento': len(contrato.clausulas_incumplimiento)
            },
            'metadata': {
                'confianza_extraccion': contrato.confianza_extraccion,
                'advertencias': contrato.advertencias,
                'num_tramos': len(contrato.tramos) if contrato.tramos else 1
            }
        }

        # Agregar info de tasa variable si aplica
        if contrato.tipo_tasa == TipoTasa.VARIABLE:
            resumen['condiciones_principales']['indice_referencia'] = contrato.indice_referencia
            resumen['condiciones_principales']['spread_bps'] = contrato.spread_bps
            resumen['condiciones_principales']['cap'] = contrato.cap
            resumen['condiciones_principales']['floor'] = contrato.floor

        # Agregar tramos si es multitramo
        if contrato.tramos:
            resumen['tramos'] = []
            for tramo in contrato.tramos:
                resumen['tramos'].append({
                    'nombre': tramo.nombre,
                    'monto': tramo.monto,
                    'moneda': tramo.moneda,
                    'tasa': tramo.tasa,
                    'tipo_tasa': tramo.tipo_tasa.value,
                    'plazo_meses': tramo.plazo_meses,
                    'frecuencia_pago': tramo.frecuencia_pago.value
                })

        return resumen


# Función de conveniencia para uso directo
def parsear_contrato(ruta_pdf: str) -> ContratoParseado:
    """Función de conveniencia para parsear un contrato"""
    parser = ContractParser()
    return parser.parsear_contrato(ruta_pdf)
