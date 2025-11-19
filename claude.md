# Claude_contratos_financieros
# Sistema Inteligente de Análisis de Contratos de Préstamo

## Visión del Proyecto

Estamos construyendo un sistema profesional que transforma el análisis manual de contratos de préstamo en un proceso automatizado e inteligente. Imagina que eres un analista financiero senior con décadas de experiencia, capaz de revisar cualquier contrato de préstamo y identificar inmediatamente todos los elementos críticos, calcular el verdadero costo financiero, evaluar riesgos ocultos, y generar recomendaciones específicas. Esa es la inteligencia que queremos automatizar.

El sistema debe ser suficientemente sofisticado para uso profesional real, pero con una interfaz tan intuitiva que cualquier persona con conocimientos financieros básicos pueda operarlo eficazmente. Piensa en empresarios evaluando ofertas de financiamiento, analistas de crédito procesando solicitudes, o consultores financieros asesorando clientes.

## Arquitectura del Sistema

### Componente 1: Interfaz Principal (main.py)

Construye una aplicación Streamlit profesional que sirva como punto de entrada único al sistema. La interfaz debe proyectar confianza y competencia técnica desde el primer momento de interacción.

**Estructura de la página principal:**
- Header con título del sistema y breve descripción del valor que proporciona
- Sección de carga de archivos con drag-and-drop intuitivo, que acepte PDFs hasta 10MB
- Panel de configuración donde usuarios puedan seleccionar el tipo de análisis (básico, completo, o enfocado en riesgos)
- Área de resultados que muestre progress bars durante el procesamiento y resultados finales de manera clara

**Requisitos específicos de experiencia de usuario:**
- Implementa validación inmediata de archivos cargados, mostrando mensajes informativos si el formato no es compatible
- Proporciona indicadores de progreso detallados durante el procesamiento, explicando qué está sucediendo en cada etapa
- Diseña la presentación de resultados para ser escaneables visualmente, con secciones claramente diferenciadas y hallazgos clave destacados
- Incluye opciones de exportación para reportes en PDF y datos en Excel

### Componente 2: Motor de Extracción Inteligente (contract_parser.py)

Este es el cerebro analítico del sistema. Debe funcionar como un analista experto que puede identificar patrones en contratos independientemente de su formato específico o terminología particular.

**Elementos críticos que DEBE identificar automáticamente:**
- Monto principal del préstamo (manejando diferentes formatos numéricos y monedas)
- Tasa de interés (distinguiendo entre nominal, efectiva, variable, y fija)
- Plazo del préstamo (en años, meses, o días, con conversión automática)
- Frecuencia de pagos (mensual, trimestral, semestral, anual)
- Tipo de garantías (real, personal, mixta, o sin garantía)
- Comisiones y costos adicionales (apertura, manejo, seguros obligatorios)
- Cláusulas de prepago (penalizaciones, restricciones, beneficios)
- Condiciones de incumplimiento y sus consecuencias
- Cláusulas especiales (aceleración, cross-default, covenant financieros)

**Lógica de procesamiento inteligente:**
El sistema debe implementar múltiples estrategias de extracción que funcionen en paralelo. Primero, utiliza expresiones regulares para identificar patrones numéricos y de fecha obvios. Simultáneamente, aplica análisis semántico para encontrar información que no siga formatos estándar. Cuando encuentra inconsistencias o información ambigua, debe marcarla para revisión y proporcionar las interpretaciones más probables con niveles de confianza.

**Manejo de casos edge:**
- Contratos con múltiples tramos o líneas de crédito
- Tasas variables con fórmulas complejas de ajuste
- Garantías que cambian durante la vida del préstamo
- Cláusulas condicionales que afectan términos principales

### Componente 3: Calculadora Financiera Avanzada (financial_calculator.py)

Implementa la inteligencia financiera que distinguirá tu sistema de simples extractores de datos. Este componente debe demostrar comprensión profunda de matemáticas financieras y mercados de crédito.

**Cálculos fundamentales requeridos:**
- Costo Anual Total (CAT) considerando todos los costos explícitos e implícitos
- Tabla de amortización completa con proyecciones de saldo, intereses, y capital
- Valor presente neto del costo total de financiamiento
- Análisis de sensibilidad para cambios en tasas de interés (especialmente relevante para créditos variables)
- Comparación automática con tasas de mercado típicas por sector y monto
- Evaluación del impacto financiero de diferentes escenarios de prepago

**Funcionalidades de análisis avanzado:**
El sistema debe calcular métricas que un CFO experimentado consideraría al evaluar opciones de financiamiento. Esto incluye el costo de oportunidad del capital, el impacto en ratios financieros clave, y la flexibilidad financiera que el contrato proporciona o restringe.

**Benchmarking inteligente:**
Integra datos de referencia sobre tasas típicas por industria, tamaño de empresa, y perfil de riesgo. El sistema debe poder contextualizar si las condiciones del contrato son competitivas, estándar, o desfavorables comparado con el mercado.

### Componente 4: Evaluador de Riesgos (risk_assessor.py)

Desarrolla un sistema de evaluación de riesgos que funcione como un comité de crédito experimentado, identificando automáticamente factores que podrían generar problemas futuros.

**Categorías de riesgo a evaluar:**
- Riesgo de liquidez (basado en estructura de pagos y flujo de caja implícito)
- Riesgo de tasa de interés (especialmente para créditos con tasas variables)
- Riesgo operativo (derivado de cláusulas restrictivas o covenant financieros)
- Riesgo legal (basado en garantías, jurisdicción, y cláusulas de resolución de disputas)
- Riesgo de prepago (costos y restricciones que limiten flexibilidad financiera)

**Sistema de scoring cuantitativo:**
Implementa un algoritmo que asigne scores numéricos a diferentes aspectos del riesgo, combinándolos en un score general que sea comparable entre diferentes contratos. El sistema debe explicar claramente cómo se calcula cada score y qué factores específicos contribuyen más significativamente.

**Identificación de red flags automática:**
- Cláusulas de aceleración excesivamente amplias
- Garantías desproporcionadas al monto del préstamo
- Restricciones operativas que podrían limitar el crecimiento del negocio
- Penalizaciones por prepago que parezcan excesivas
- Tasas que cambien dramáticamente después de períodos promocionales

### Componente 5: Generador de Reportes Programático (report_generator.py)

Construye un sistema experto de generación de reportes que funcione como un analista financiero senior sistematizado, capaz de producir análisis profesionales sin dependencias externas. Este enfoque programático garantiza consistencia, auditabilidad y control total sobre la calidad del output.

**Arquitectura del Generador de Reportes:**

*Motor de Análisis Contextual:*
Implementa un sistema que evalúe el perfil completo del contrato y determine dinámicamente qué combinación de análisis, explicaciones y recomendaciones son más relevantes. Este componente funciona como un "director editorial experto" que entiende qué información priorizar para cada situación específica.

*Biblioteca de Templates Especializados:*
Desarrolla una colección estructurada de componentes narrativos especializados, organizados por dominio financiero:
- Templates para evaluación de tasas (fijas, variables, promocionales)
- Componentes para análisis de garantías (reales, personales, mixtas)
- Módulos para evaluación de riesgos por categoría
- Templates comparativos con benchmarks de mercado
- Componentes de recomendaciones basadas en perfil de riesgo

*Sistema de Reglas Financieras Formalizadas:*
Construye un motor de reglas que mapee condiciones financieras específicas a explicaciones contextualizadas. Ejemplos de reglas implementadas:
- "Si tasa > percentil 75 del sector Y garantías = personales → incluir análisis de riesgo personal elevado"
- "Si plazo < 24 meses Y monto > $500K → evaluar presión de flujo de caja"
- "Si cláusulas aceleración > 3 triggers → alertar sobre riesgo operativo"

**Estructura del Reporte Generado:**

*Resumen Ejecutivo Dinámico:*
Genera automáticamente las 3-5 conclusiones más críticas basándose en el análisis cuantitativo realizado. Prioriza hallazgos por impacto financiero y nivel de riesgo identificado.

*Análisis Financiero Detallado:*
- Explicación contextualizada del costo efectivo total con comparaciones sectoriales
- Análisis de la estructura de pagos con identificación de períodos de mayor presión de flujo de caja
- Evaluación del impacto de diferentes escenarios de prepago con recomendaciones específicas

*Evaluación de Riesgos Sistematizada:*
- Categorización automática de riesgos identificados por nivel de criticidad
- Explicación detallada de cada factor de riesgo con contexto específico del contrato
- Recomendaciones concretas de mitigación para cada riesgo identificado

*Recomendaciones Estratégicas:*
Sistema de decisión programática que genera una de tres recomendaciones principales (Aceptar/Rechazar/Negociar) con justificación detallada y, en caso de "Negociar", términos específicos a mejorar.

**Generación de Narrativas Contextuales:**
El sistema debe producir explicaciones que demuestren comprensión profunda de implicaciones financieras. Por ejemplo, en lugar de decir "La tasa es alta", generar "La tasa del 18% representa un costo 240 puntos base superior al promedio sectorial del 15.6%, lo cual podría reflejar la evaluación del prestamista sobre factores de riesgo específicos como [factores identificados en el análisis]."

**Integración de Visualizaciones con Narrativas:**
- Gráfico de amortización con explicación de patrones críticos identificados
- Dashboard de costos comparativos con interpretación de diferencias significativas
- Matriz de riesgos visual con explicación de cada cuadrante
- Timeline de pagos con highlighting de períodos críticos y explicación de implicaciones

## Datos de Referencia y Calibración

### Tasas de Mercado (market_rates.json)

Incluye datos de referencia que permitan al sistema contextualizar si las condiciones de un contrato son competitivas. Organiza por:
- Tipo de empresa (PYME, mediana, grande)
- Sector económico (manufacturero, servicios, tecnología, comercial)
- Monto del préstamo (menos de $1M, $1M-$10M, más de $10M)
- Plazo (corto, mediano, largo plazo)

### Factores de Riesgo (risk_factors.json)

Define los parámetros que el sistema utilizará para evaluar riesgos:
- Weights para diferentes tipos de garantías
- Benchmarks para ratios de cobertura típicos
- Definiciones de cláusulas que constituyen red flags
- Scoring matrices para evaluación cuantitativa de riesgo

## Estándares de Calidad y Validación

### Precisión de Extracción

El sistema debe lograr al menos 95% de precisión en identificar elementos críticos en contratos estándar. Cuando la confianza sea menor al 90% en cualquier elemento crítico, debe marcar específicamente esa información para revisión manual.

### Robustez de Cálculos

Todos los cálculos financieros deben ser auditables y replicables. El sistema debe generar logs detallados de todos los cálculos realizados, permitiendo que usuarios avanzados verifiquen metodologías y supuestos.

### Experiencia de Usuario

La interfaz debe ser suficientemente intuitiva que un usuario nuevo pueda generar su primer análisis completo en menos de 5 minutos. Simultáneamente, debe proporcionar suficiente profundidad analítica para satisfacer usuarios expertos.

## Casos de Uso Principales

### Caso 1: Empresario Evaluando Ofertas de Financiamiento
Un empresario recibe múltiples propuestas de financiamiento para expansión de su negocio. Necesita comparar no solo las tasas de interés, sino entender el costo total real, identificar restricciones operativas, y evaluar cuál opción le proporciona mayor flexibilidad estratégica.

### Caso 2: Analista de Crédito Procesando Solicitudes
Un analista en una institución financiera necesita evaluar rápidamente si los términos de un contrato propuesto están alineados con las políticas internas de riesgo y son competitivos con el mercado.

### Caso 3: Consultor Financiero Asesorando Clientes
Un consultor debe proporcionar a sus clientes análisis objetivos de propuestas de financiamiento, explicando implicaciones complejas en términos comprensibles y ofreciendo recomendaciones específicas.

## Implementación Técnica

### Tecnologías Específicas
- **Streamlit**: Para crear una interfaz web profesional sin complejidad de desarrollo web
- **PyPDF2 y pdfplumber**: Para extracción robusta de texto de PDFs con diferentes formatos
- **pandas**: Para manipulación eficiente de datos financieros y cálculos
- **plotly**: Para visualizaciones interactivas de calidad profesional
- **reportlab**: Para generación programática de reportes PDF profesionales
- **Jinja2**: Para sistema avanzado de templates que permita generación de narrativas dinámicas

### Sistema de Templates y Generación de Contenido
El sistema utilizará un enfoque híbrido de templates inteligentes que combinen:
- **Templates base estructurales** para mantener formato profesional consistente
- **Componentes narrativos modulares** que se seleccionen dinámicamente basado en el análisis
- **Motor de reglas financieras** que determine qué explicaciones y recomendaciones incluir
- **Sistema de coherencia textual** que asegure transiciones fluidas entre secciones generadas

### Ventajas del Enfoque Programático
- **Auditabilidad completa**: Cada conclusión y recomendación es trazable a reglas específicas
- **Consistencia garantizada**: Contratos similares recibirán análisis comparables
- **Independencia operacional**: No requiere conectividad externa ni servicios de terceros
- **Control de calidad**: Permite validación exhaustiva de cada componente narrativo
- **Escalabilidad**: Nuevas reglas y templates pueden agregarse sistemáticamente

### Estructura de Testing
Desarrolla casos de prueba que incluyan:
- Contratos con formatos típicos de diferentes instituciones financieras
- Contratos con información faltante o ambigua
- Contratos con estructuras complejas (múltiples tramos, tasas variables)
- Validación de precisión de cálculos contra hojas de Excel manuales

### Manejo de Errores
Implementa manejo elegante de errores que:
- Identifique específicamente qué información no pudo extraerse
- Proporcione sugerencias para mejorar la calidad del análisis
- Permita a usuarios corregir o completar información manualmente
- Mantenga funcionalidad parcial incluso cuando algunos elementos no se puedan procesar

## Objetivos de Aprendizaje y Valor Académico

Este proyecto te proporcionará dominio práctico en:
- **Formalización de Conocimiento Financiero**: Convertir intuición analítica en reglas programáticas auditables
- **Procesamiento inteligente de documentos financieros complejos**: Manejo robusto de información no estructurada
- **Implementación de modelos financieros avanzados en código**: Traducción de teoría económica a sistemas funcionales
- **Construcción de sistemas expertos**: Desarrollo de motores de reglas que repliquen razonamiento profesional
- **Arquitectura de software empresarial**: Diseño de sistemas autónomos, escalables y auditables
- **Generación programática de análisis narrativos**: Combinación de datos cuantitativos con interpretación estructurada

**Valor Académico Diferencial:**
El enfoque programático puro distingue tu proyecto porque requiere formalizar completamente el conocimiento financiero experto en reglas explícitas y algoritmos determinísticos. Esta formalización demuestra comprensión profunda que trasciende la aplicación mecánica de herramientas, mostrando capacidad para sistematizar y estructurar conocimiento complejo de manera que pueda ser replicado y auditado.

El resultado final debe ser un sistema que genuinamente agregue valor en entornos profesionales reales, mientras proporciona transparencia completa sobre cómo se toma cada decisión analítica, combinando rigor académico con aplicabilidad práctica inmediata.
