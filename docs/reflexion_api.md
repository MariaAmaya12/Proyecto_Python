
# API Inmobiliaria — Limpieza y Análisis Estadístico

## Descripción del Proyecto

Esta API REST permite analizar conjuntos de datos de inmuebles (casas, apartamentos, etc.) mediante métricas estadísticas como precio promedio, mediana, desviación estándar y precio por metro cuadrado.

El sistema recibe datos en formato JSON, valida su estructura usando **Pydantic**, opcionalmente aplica un módulo de **limpieza de datos**, y luego calcula estadísticas utilizando **NumPy**.  
Los resultados pueden almacenarse en memoria y consultarse posteriormente mediante endpoints CRUD.

Tecnologías principales utilizadas:

- **FastAPI** — Creación de la API REST
- **Pydantic** — Validación de datos
- **NumPy** — Cálculos estadísticos
- **Pandas** — Manipulación de datos
- **Uvicorn** — Servidor ASGI

Dominio del proyecto: **mercado inmobiliario**.

---

# Preguntas de Reflexión

## Pregunta 1 — Dominio y Validaciones

Elegí el dominio inmobiliario porque los datos de propiedades (precio, área, habitaciones y baños) permiten realizar análisis estadísticos reales y útiles. En esta API se analizan conjuntos de inmuebles para calcular métricas como precio promedio, mediana y precio por metro cuadrado.

Para garantizar la integridad de los datos utilicé validaciones con **Pydantic** en el modelo `InmuebleInput`. Por ejemplo, los campos `area_m2` y `valor` deben ser mayores que cero (`gt=0`), lo que evita propiedades con valores negativos o inválidos. Además, `habitaciones` y `banos` están restringidos entre 0 y 20 (`ge=0`, `le=20`) para evitar valores irreales. El campo `tipo` tiene `min_length=3` para evitar cadenas vacías, mientras que `barrio` es opcional para permitir registros incompletos.

Estas validaciones garantizan que los cálculos estadísticos se realicen sobre datos plausibles y consistentes.

---

## Pregunta 2 — Sin Validación

Si se eliminaran las validaciones de Pydantic, la API podría recibir datos inconsistentes que afectarían el procesamiento estadístico. Por ejemplo, el siguiente JSON contiene varios errores:

```json
{
  "nombre_analisis": "test",
  "inmuebles": [
    {
      "tipo": "apt",
      "area_m2": -50,
      "valor": "caro",
      "habitaciones": 200,
      "banos": -3
    }
  ]
}
````

En este ejemplo, `area_m2` es negativa, `valor` no es numérico y `habitaciones` tiene un valor irreal. Sin Pydantic, estos datos llegarían directamente a la función `analizar_inmuebles`. Cuando **NumPy** intente realizar operaciones estadísticas con valores no numéricos o inválidos, se producirían errores de tipo o resultados incorrectos.

Por lo tanto, las validaciones de Pydantic son esenciales para evitar errores en la lógica de análisis.

---

## Pregunta 3 — Escalabilidad

Actualmente la API guarda los resultados de los análisis en un diccionario en memoria llamado `historial`. Si la API recibiera **10,000 requests por minuto**, aparecerían dos problemas principales.

Primero, el consumo de memoria aumentaría continuamente, ya que cada nuevo análisis se almacenaría en RAM. Con el tiempo esto podría saturar la memoria del servidor. Segundo, la información no es persistente: si el servidor se reinicia, todos los análisis almacenados se perderían.

Una alternativa más escalable sería usar una base de datos externa, como **PostgreSQL o MongoDB**, para almacenar los resultados de los análisis. De esta forma, los endpoints `/historial` y `/historial/{id}` consultarían los datos directamente desde la base de datos, lo que permitiría manejar grandes volúmenes de solicitudes y mantener persistencia incluso si el servidor se reinicia.

---

## Pregunta 4 — Flujo Completo

El flujo comienza cuando el cliente envía un **request POST** al endpoint `/analizar` con un JSON que contiene los inmuebles a analizar.

El decorador `@app.post("/analizar")` de FastAPI recibe la solicitud y automáticamente **Pydantic valida los datos** usando los modelos `AnalisisInmobiliarioInput` e `InmuebleInput`. Si los datos no cumplen las validaciones, FastAPI devuelve un error **HTTP 422**.

Si la validación es exitosa, el endpoint convierte los registros a una lista de diccionarios y opcionalmente ejecuta el módulo de limpieza (`DataCleaner`). Luego se llama a la función de lógica `analizar_inmuebles`, que utiliza **NumPy** para calcular estadísticas como promedio, mediana, mínimo, máximo y desviación estándar.

El resultado se transforma en un objeto `AnalisisInmobiliarioResult` y se guarda en memoria en el diccionario `historial`. Finalmente, FastAPI devuelve la respuesta HTTP en formato **JSON** con los resultados del análisis.

---

# Conclusiones

Este proyecto demuestra la integración de **FastAPI, Pydantic y NumPy** para construir una API capaz de recibir datos estructurados, validarlos y generar análisis estadísticos. Además, se implementó un módulo adicional de limpieza de datos para mejorar la calidad de los registros antes del análisis.

El uso de validaciones con Pydantic permite asegurar la integridad de los datos, mientras que la separación entre la capa de API y la lógica de análisis mejora la organización del código. Aunque actualmente el almacenamiento se realiza en memoria, la arquitectura permite extender fácilmente el sistema para utilizar bases de datos externas y mejorar la escalabilidad.

