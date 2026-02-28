# API Inmobiliaria — Limpieza y Análisis Estadístico

Proyecto Personal — Actividad Aplicada (Semanas 1–3)  
Tecnologías: FastAPI · Pydantic · NumPy · Pandas · Uvicorn

---

## 📌 Descripción del Proyecto

Esta API REST permite analizar estadísticamente conjuntos de inmuebles (casas, apartamentos, etc.) a partir de variables numéricas como área y valor.

El sistema:

1. Recibe datos en formato JSON.
2. Valida la estructura y restricciones usando Pydantic.
3. Opcionalmente aplica un módulo de limpieza basado en Programación Orientada a Objetos.
4. Calcula métricas estadísticas usando NumPy.
5. Retorna resultados estructurados en formato JSON.
6. Permite almacenar, consultar y eliminar análisis realizados (CRUD en memoria).

Este proyecto integra los conceptos vistos en las semanas 1, 2 y 3 del módulo.

---

## 🏘 Dominio del Proyecto

Dominio: Mercado inmobiliario (Bogotá).

Variables principales analizadas:

- Área del inmueble (m²)
- Valor del inmueble
- Número de habitaciones
- Número de baños
- Tipo de inmueble
- Barrio (opcional)

Métricas calculadas:

- Media
- Mediana
- Mínimo
- Máximo
- Desviación estándar muestral (ddof=1)
- Precio por metro cuadrado (valor / área)

Todos los resultados numéricos se redondean a 4 decimales.

---

## 🧱 Arquitectura del Proyecto


mi_proyecto/
│
├── api/
│ ├── main.py
│ ├── analysis_schemas.py
│
├── analysis/
│ ├── stats.py
│
├── limpieza/
│ ├── cleaner.py
│ ├── pipeline.py
│ ├── schemas.py
│
└── requirements.txt

### Separación de responsabilidades

- `limpieza/`  
  Módulo independiente de procesamiento tabular basado en POO.

- `analysis/stats.py`  
  Función pura que realiza cálculos estadísticos con NumPy.  
  No depende de FastAPI.

- `api/main.py`  
  Capa HTTP: routing, validación, manejo de errores y respuestas JSON.

Esta separación garantiza buena práctica de diseño y modularidad.

---

## 🔄 Flujo Completo de un Request (POST /analizar)

1. El cliente envía un JSON al endpoint `/analizar`.
2. El decorador `@app.post` enruta la solicitud.
3. Pydantic valida y convierte los datos al modelo `AnalisisInmobiliarioInput`.
4. (Opcional) Se ejecuta el módulo de limpieza.
5. Se llama a la función pura `analizar_inmuebles()` usando NumPy.
6. Se construye el modelo `AnalisisInmobiliarioResult`.
7. El resultado se guarda en memoria.
8. FastAPI retorna una respuesta JSON con status 200.

---

## 🌐 Endpoints Disponibles

| Método  | Ruta                  | Descripción |
|----------|-----------------------|-------------|
| POST     | /analizar             | Analiza un conjunto de inmuebles |
| GET      | /historial            | Lista todos los análisis |
| GET      | /historial/{id}       | Obtiene un análisis específico |
| DELETE   | /historial/{id}       | Elimina un análisis |
| POST     | /limpiar              | Aplica módulo de limpieza |
| GET      | /health               | Verifica estado del servidor |

---

## 🧮 Validaciones Implementadas

Se utilizan validaciones con Pydantic:

- `area_m2 > 0`
- `valor > 0`
- `habitaciones` entre 0 y 20
- `banos` entre 0 y 20
- `tipo` con longitud mínima
- Campo `barrio` opcional
- `extra="forbid"` para evitar campos inesperados

Si los datos violan estas reglas, la API retorna un error 422.

---

## 🧠 Manejo de Errores

- 422 → Error de validación Pydantic
- 404 → Recurso no encontrado (historial/{id})
- 200 → Operación exitosa

---

## ⚙️ Ejecución del Proyecto

Activar entorno virtual (si aplica) y ejecutar:

```bash
uvicorn api.main:app --reload