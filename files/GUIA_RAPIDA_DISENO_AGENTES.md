# GUÍA RÁPIDA: DISEÑO DE AGENTES ANTI-ALUCINACIÓN

**Basada en:** Análisis comparativo del sistema de búsqueda ArXiv  
**Última actualización:** 18 de noviembre de 2025  
**Propósito:** Referencia rápida para diseñar agentes confiables

---

## 🎯 LOS 12 MANDAMIENTOS DEL DISEÑO DE AGENTES

### 1. ESPECÍFICO > GENÉRICO
```yaml
❌ MAL: role: "Investigador Universal"
✅ BIEN: role: "Especialista en Búsqueda ArXiv"
```

### 2. CALIDAD > VELOCIDAD
```yaml
❌ MAL: goal: "Encontrar 5 papers en <2 minutos"
✅ BIEN: goal: "Encontrar papers verificables con ArXiv IDs válidos"
```

### 3. EJEMPLOS > INSTRUCCIONES
```yaml
❌ MAL: "Cita fuentes apropiadamente"
✅ BIEN: 
"Cita fuentes:
✅ CORRECTO: [Smith et al., 2401.12345]
❌ INCORRECTO: 'Varios estudios...'"
```

### 4. PREVENCIÓN > DETECCIÓN
```yaml
❌ MAL: "No inventes información"
✅ BIEN: 
"NUNCA inventes títulos, autores, o IDs.
Si no encuentras datos, di: 'No encontré información verificable sobre X'"
```

### 5. TRANSPARENCIA FORZADA
```yaml
❌ MAL: expected_output: "Lista de papers"
✅ BIEN: 
expected_output: "Lista de papers + estrategia de búsqueda usada
                  + justificación de relevancia por paper"
```

### 6. VALIDACIÓN JERÁRQUICA
```yaml
❌ MAL: "Evalúa si el output es correcto"
✅ BIEN: 
"Evalúa en 3 niveles:
NIVEL 1 - Formato correcto
NIVEL 2 - Contenido verificable  
NIVEL 3 - Señales de alucinación"
```

### 7. HONESTIDAD EXPLÍCITA
```yaml
❌ MAL: [sin guía para admitir ignorancia]
✅ BIEN: 
"Si no encuentras resultados, responde:
'No encontré [X] sobre [Y] en [fuente Z]'"
```

### 8. CONSECUENCIAS CLARAS
```yaml
❌ MAL: "No inventes información"
✅ BIEN: "Si inventas información: FALLO CRÍTICO"
```

### 9. SIMPLICIDAD ARQUITECTÓNICA
```yaml
❌ MAL: 5 agentes con responsabilidades superpuestas
✅ BIEN: 3 agentes con roles claros y separados
```

### 10. FORMATO SOBRE FREESTYLE
```yaml
❌ MAL: expected_output: "Un reporte sobre los papers"
✅ BIEN: 
expected_output: "JSON con campos:
{
  'papers_found': [...],
  'search_strategy': {...}
}"
```

### 11. LENGUAJE REGULADO
```yaml
❌ MAL: [sin regulación de lenguaje]
✅ BIEN: 
"Lenguaje permitido: 'encontré', 'según el paper'
Lenguaje prohibido: 'probablemente', 'tal vez'"
```

### 12. ITERACIÓN CON DOCUMENTACIÓN
```yaml
❌ MAL: Cambios sin documentar razón
✅ BIEN: 
"v1.1 → v1.2: Agregado formato ArXiv ID explícito
Problema resuelto: 40% de IDs inválidos"
```

---

## 🏗️ TEMPLATE DE AGENTE PRINCIPAL

```yaml
nombre_del_agente:
  role: >
    [Rol específico en 1 línea]
  
  goal: >
    [Objetivo enfocado en CALIDAD de output, NO métricas de proceso]
  
  backstory: >
    Eres un [rol] especializado en [dominio].
    
    PRINCIPIOS FUNDAMENTALES:
    - [Principio 1: prioridad de valores]
    - [Principio 2: qué hacer cuando falla]
    - [Principio 3: honestidad sobre limitaciones]
    - [Principio 4: prevención de alucinaciones]
    
    METODOLOGÍA:
    1. [Paso 1 del proceso]
    2. [Paso 2 con decisión IF/THEN]
    3. [Paso 3 con documentación obligatoria]
    
    EJEMPLOS DE EJECUCIÓN:
    
    Ejemplo 1 - CASO TÍPICO:
    Input: [input concreto]
    Proceso: [qué haces]
    Output: [resultado esperado]
    
    Ejemplo 2 - CASO DIFÍCIL:
    Input: [input problemático]
    Proceso: [cómo lo manejas]
    Output: [incluso admitiendo limitación si necesario]
    
    REGLAS NO NEGOCIABLES:
    - [Regla 1] → Si violas: [consecuencia]
    - [Regla 2] → Si violas: [consecuencia]
    - [Regla 3 sobre lenguaje]
    
    FORMATO DE DATOS CRÍTICOS:
    [Si hay datos estructurados como IDs, fechas, etc.]
    Formato: [especificación exacta]
    Ejemplos válidos: [2-3 ejemplos]
    Ejemplos inválidos: [2-3 ejemplos con razón]
    
    CAPACIDADES:
    - [Qué puedes hacer 1]
    - [Qué puedes hacer 2]
    
    LIMITACIONES:
    - [Qué NO puedes hacer 1]
    - [Qué NO puedes hacer 2]
    
    TEMPLATE DE HONESTIDAD:
    Si no puedes [X], di: "[frase específica]"
    NO inventes información para compensar.
  
  llm: claude-sonnet-4-5-20250929
  
  tools:
    - [herramienta MÁS ESPECÍFICA disponible para este dominio]
  
  allow_delegation: false  # empezar simple
  verbose: true  # para debugging
```

---

## 🔍 TEMPLATE DE VALIDADOR (TEMPORAL)

```yaml
inspector_de_[aspecto]:
  role: >
    Inspector de [Aspecto Específico]
  
  goal: >
    Evaluar [aspecto] contra criterios rigurosos, detectando problemas
    críticos como alucinaciones y datos inventados.
  
  backstory: >
    Eres un evaluador experto especializado en validación de [aspecto].
    
    PROCESO DE VALIDACIÓN EN [N] NIVELES:
    
    NIVEL 1 - [ASPECTO MÁS BÁSICO]:
    ¿[Pregunta de validación básica]?
    - [Criterio verificable 1]
    - [Criterio verificable 2]
    
    NIVEL 2 - [ASPECTO INTERMEDIO]:
    ¿[Pregunta de validación intermedia]?
    - [Criterio verificable 1]
    - [Criterio verificable 2]
    
    NIVEL [N] - SEÑALES DE ALERTA CRÍTICAS:
    ¿Hay indicios de [problema crítico como alucinaciones]?
    
    SEÑALES DE ALERTA:
    - [Señal específica 1: descripción y por qué es problemática]
    - [Señal específica 2: descripción y por qué es problemática]
    - [Señal específica 3: descripción y por qué es problemática]
    
    EJEMPLOS DE VALIDACIÓN:
    
    ✅ OUTPUT VÁLIDO:
    [Ejemplo concreto de output que pasa validación]
    Por qué es válido: [razón específica]
    
    ❌ OUTPUT INVÁLIDO:
    [Ejemplo concreto con problema]
    Problema detectado: [qué está mal]
    Severidad: [CRÍTICA/ALTA/MEDIA]
    
    FORMATO DE REPORTE:
    
    ## RESUMEN EJECUTIVO
    Estado: APROBADO / REVISAR / RECHAZADO
    Puntuación: X/N niveles PASS
    Confianza: [0.0-1.0]
    
    ## VALIDACIÓN NIVEL 1 - [NOMBRE]
    Estado: PASS / FAIL
    [Análisis específico]
    Problemas: [lista si hay]
    
    [... repetir para cada nivel ...]
    
    ## PROBLEMAS CRÍTICOS
    [Lista numerada con severidad]
    1. [Problema] - Severidad: [X] - Afecta: [Y]
    
    ## RECOMENDACIONES
    [Acciones específicas para corregir]
    
    ## DECISIÓN FINAL
    [APROBADO: razones / REVISAR: qué verificar / RECHAZADO: por qué]
  
  llm: claude-sonnet-4-5-20250929
  allow_delegation: false
  verbose: true
```

---

## 📝 TEMPLATE DE TAREA

```yaml
nombre_de_tarea:
  description: >
    [Descripción clara de QUÉ debe hacer]
    
    INPUT:
    {variable_input}
    
    PROCESO DETALLADO:
    
    1. [PASO 1]:
       - [Sub-paso específico]
       - [Sub-paso específico]
       - [Qué documentar]
    
    2. [PASO 2 CON DECISIÓN]:
       SI [condición]:
         - [Acción A]
       SI NO:
         - [Acción B]
       DOCUMENTAR: [qué documentar]
    
    3. [PASO 3]:
       Para cada [elemento]:
       - [Qué hacer con el elemento]
       - [Qué validar]
       - [Qué documentar]
    
    VALIDACIÓN CRÍTICA ANTES DE RESPONDER:
    - Verificar que [requisito 1]
    - Verificar que [requisito 2]
    - Verificar que [requisito 3]
    
    PROHIBIDO:
    - NO [comportamiento prohibido 1]
    - NO [comportamiento prohibido 2]
    - NO [comportamiento prohibido 3]
  
  expected_output: >
    [Formato específico del output esperado]
    
    [Si es JSON, incluir schema completo]
    {
      "campo_1": "tipo y descripción",
      "campo_2": "tipo y descripción",
      "campo_3": {
        "sub_campo": "tipo y descripción"
      }
    }
    
    [Si es markdown, especificar estructura]
    ## SECCIÓN 1
    [Qué debe contener]
    
    ## SECCIÓN 2
    [Qué debe contener]
    
    Requisitos de formato:
    - [Requisito 1: ej. citaciones en formato [X]]
    - [Requisito 2: ej. cada afirmación con fuente]
  
  agent: [nombre_del_agente]
  
  context:  # Si depende de otra tarea
    - [tarea_previa]
```

---

## 🧪 TEMPLATE DE TEST SUITE

```yaml
# test_suite.yaml

suite_name: "Tests para [Sistema/Agente]"

# BASIC TESTS (Happy Path)
basic_tests:
  test_001:
    id: "BASIC-001"
    name: "[Nombre descriptivo del test]"
    input:
      campo1: "[valor concreto]"
      campo2: "[valor concreto]"
    
    expected_behavior:
      - "[Comportamiento esperado 1]"
      - "[Comportamiento esperado 2]"
    
    success_criteria:
      - "[Criterio verificable 1]"
      - "[Criterio verificable 2]"
      - "[Criterio verificable 3]"

# ADVERSARIAL TESTS (Edge Cases)
adversarial_tests:
  test_001:
    id: "ADV-001"
    name: "[Caso problemático específico]"
    input:
      campo1: "[valor que típicamente causa problemas]"
    
    expected_behavior:
      - "[Debe manejar apropiadamente, no inventar]"
      - "[Debe admitir limitación si aplica]"
      - "[NO debe especular]"
    
    success_criteria:
      - "[Criterio que confirma manejo correcto]"
      - "[Criterio anti-alucinación]"

# CONSISTENCY TESTS
consistency_tests:
  test_001:
    id: "CONS-001"
    name: "[Mismo input, múltiples ejecuciones]"
    input:
      campo1: "[valor a repetir]"
    
    executions: 3  # Ejecutar N veces
    
    expected_behavior:
      - "[Resultados consistentes]"
      - "[Overlap esperado >X%]"
    
    success_criteria:
      - "[Criterio de consistencia]"
```

---

## ⚠️ RED FLAGS A EVITAR

### Checklist Anti-Problemas

#### ❌ Red Flag #1: Over-Promise, Under-Deliver
```yaml
# Promesas rígidas en goal
goal: "Garantizar ejecución <3 minutos con 5-8 papers"
```
**Solución:** Enfocarse en calidad de output, no métricas de proceso.

#### ❌ Red Flag #2: Categorización Pre-Matura
```yaml
# Categorías rígidas
"Si es TÉCNICO → añadir 'algorithm'
 Si es MATEMÁTICO → añadir 'theory'"
```
**Solución:** Dar principios de análisis, no categorías fijas.

#### ❌ Red Flag #3: Validador Frankensteins
```yaml
# Múltiples validadores con overlap
agents:
  - quality_validator_1
  - quality_validator_2  
  - quality_checker
```
**Solución:** Un agente por responsabilidad clara.

#### ❌ Red Flag #4: Instrucciones Abstractas Sin Ejemplos
```yaml
"Cita fuentes apropiadamente"
"Evalúa relevancia objetivamente"
```
**Solución:** Cada instrucción debe tener 1+ ejemplo concreto.

#### ❌ Red Flag #5: Herramienta Genérica para Tarea Específica
```yaml
tools:
  - web_search  # con hacks para dominio específico
```
**Solución:** Usar herramienta MÁS específica disponible.

#### ❌ Red Flag #6: Consecuencias Implícitas
```yaml
"NUNCA más de 3 queries"
# ¿Qué pasa si viola? No especificado.
```
**Solución:** Toda regla crítica debe especificar consecuencia.

#### ❌ Red Flag #7: Formato Implícito
```yaml
"ArXiv ID formato básico"
# ¿Qué es "básico"? No especificado.
```
**Solución:** Especificar formato EXACTO con ejemplos válidos/inválidos.

---

## ✅ CHECKLIST DE CALIDAD PRE-DEPLOYMENT

### Arquitectura
- [ ] Cada agente tiene responsabilidad clara y no superpuesta
- [ ] Usa herramienta MÁS ESPECÍFICA para el dominio
- [ ] Número de agentes justificado (menos es más)
- [ ] Nombres <50 caracteres

### Goals y Roles
- [ ] Goal enfocado en CALIDAD, no proceso
- [ ] Sin promesas de velocidad/cantidad rígidas
- [ ] Success criteria verificables
- [ ] Role específico (no genérico)

### Backstory y Prompts
- [ ] Backstory estructurado con secciones claras
- [ ] PRINCIPIOS FUNDAMENTALES (3-5 bullets)
- [ ] METODOLOGÍA (pasos numerados)
- [ ] EJEMPLOS (2+: típico + difícil)
- [ ] REGLAS NO NEGOCIABLES (con consecuencias)
- [ ] CAPACIDADES explícitas
- [ ] LIMITACIONES explícitas
- [ ] TEMPLATE DE HONESTIDAD

### Prevención de Alucinaciones
- [ ] Formato de datos estructurados especificado
- [ ] Ejemplos válidos E inválidos
- [ ] Lenguaje regulado
- [ ] Instrucción de documentar proceso
- [ ] Template "no encontré nada"
- [ ] Regla "NUNCA inventes [X]" con consecuencia

### Validación
- [ ] 1+ validador temporal activo
- [ ] Validación en 3-5 niveles jerárquicos
- [ ] Cada nivel con PASS/FAIL
- [ ] Señales de alerta documentadas
- [ ] Reporte estructurado

### Expected Outputs
- [ ] Outputs estructurados con formato exacto
- [ ] JSON schemas cuando aplica
- [ ] Estructura de reportes definida
- [ ] Formato de citaciones especificado

### Testing
- [ ] Test suite definido PRE-implementación
- [ ] 3+ basic tests
- [ ] 3+ adversarial tests
- [ ] 2+ consistency tests
- [ ] Criterios de éxito claros

---

## 📊 MATRIZ DE DECISIÓN: ¿CUÁNTOS VALIDADORES?

| Complejidad del Sistema | Criticidad | Validadores Recomendados |
|-------------------------|------------|-------------------------|
| Simple (1 agente) | Baja | 1 validador básico |
| Simple (1 agente) | Alta | 1 validador exhaustivo |
| Media (2-3 agentes) | Media | 1-2 validadores |
| Media (2-3 agentes) | Alta | 2-3 validadores especializados |
| Compleja (4+ agentes) | Media-Alta | 2-3 validadores + 1 integrador |

**Regla de oro:** Empezar con 1 validador bien diseñado. Agregar más solo si hay aspectos claramente separables.

---

## 🎯 PROCESO DE IMPLEMENTACIÓN (GUÍA RÁPIDA)

### Día 1-2: Diseño
1. Definir dominio específico
2. Identificar herramienta más específica
3. Definir success criteria (calidad, no proceso)
4. **Crear test suite ANTES de implementar**

### Día 3-4: Agente Principal
1. Escribir role + goal
2. Estructurar backstory (usar template)
3. Especificar formato de output
4. Agregar ejemplos concretos

### Día 5: Validadores
1. Diseñar inspector (3-5 niveles)
2. Especificar señales de alerta
3. Definir formato de reporte

### Día 6-7: Testing Inicial
1. Ejecutar basic tests
2. Ejecutar adversarial tests
3. Ejecutar consistency tests
4. Documentar todos los fallos

### Día 8-10: Refinamiento
1. Analizar patrones de error
2. Refinar prompts
3. Agregar ejemplos de casos que fallaron
4. Re-ejecutar tests hasta pass rate >80%

---

## 🔗 PATRONES ÚTILES

### Patrón 1: "Ejemplos Bipolares"
Para cada comportamiento, proporcionar ejemplo correcto E incorrecto.

```yaml
COMPORTAMIENTO: [descripción]

✅ CORRECTO:
[ejemplo] 
Por qué: [razón]

❌ INCORRECTO:
[ejemplo]
Por qué: [razón]
```

### Patrón 2: "Escalera de Validación"
Validación del más básico al más complejo.

```yaml
NIVEL 1 - ESTRUCTURA
NIVEL 2 - SEMÁNTICA
NIVEL 3 - CONSISTENCIA
NIVEL 4 - CALIDAD
NIVEL 5 - SEÑALES DE ALERTA
```

### Patrón 3: "Template de Honestidad"
Fraseo específico para admitir limitaciones.

```yaml
Si no puedes [X], di: "[template específico]"
NO inventes información para compensar.
```

### Patrón 4: "Checklist Pre-Respuesta"
Lista de verificación antes de generar output.

```yaml
ANTES DE RESPONDER, VERIFICA:
☐ [Criterio 1]
☐ [Criterio 2]
☐ [Criterio 3]
```

### Patrón 5: "Adaptación Documentada"
Cuando adaptas estrategia, documenta por qué.

```yaml
expected_output:
{
  "strategy_used": {
    "initial": "[qué intentaste]",
    "adaptations": ["cambios hechos"],
    "reasoning": "[por qué adaptaste]"
  }
}
```

---

## 💡 TIPS RÁPIDOS

### Para Prevenir Alucinaciones
1. Especifica formato EXACTO de datos estructurados
2. Proporciona template para "no encontré nada"
3. Regula lenguaje (qué usar, qué evitar)
4. Obliga a citar fuente para cada afirmación
5. Pide documentar estrategia/proceso

### Para Mejorar Claridad
1. Usa ejemplos concretos > instrucciones abstractas
2. Estructura backstory en secciones claras
3. Numera pasos del proceso
4. Especifica consecuencias de violación de reglas
5. Define success criteria verificables

### Para Debugging Efectivo
1. Valida en niveles jerárquicos
2. Documenta cada cambio con razón
3. Usa validadores temporales en desarrollo
4. Mantén test suite actualizado
5. Analiza patrones de error, no casos individuales

---

## 📚 RECURSOS COMPLEMENTARIOS

**Documento principal:** `ANALISIS_COMPARATIVO_Y_CONCLUSIONES.md`  
Análisis exhaustivo con:
- Comparación detallada V1 vs V2
- 12 principios fundamentales explicados
- Patrones y anti-patrones
- Casos de estudio

**Metodología completa:** `__METODOLOGÍA_DE_8_FASES_PARA_AGENT.txt`  
Proceso completo desde diseño hasta producción.

---

## 🚀 QUICK START PARA NUEVO PROYECTO

```bash
1. Copiar template de agente principal
2. Rellenar dominio específico
3. Identificar herramienta más específica
4. Crear test suite (3 basic + 3 adversarial + 2 consistency)
5. Implementar agente + 1 validador
6. Ejecutar tests
7. Refinar basado en fallos
8. Iterar hasta pass rate >80%
9. Deploy con monitoring
```

**Tiempo estimado:** 10-16 días para sistema robusto.

---

**FIN DE LA GUÍA RÁPIDA**

*Versión: 1.0 - Fecha: 18 de noviembre de 2025*
*Mantener actualizada conforme se identifiquen nuevos principios.*
