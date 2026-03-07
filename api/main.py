
from __future__ import annotations  # Permite usar anotaciones de tipos de manera diferida

from typing import Any, Dict  # Tipos genéricos para diccionarios y otros datos

import pandas as pd  # Se usa para convertir listas de diccionarios en DataFrame
from fastapi import FastAPI, HTTPException  # FastAPI para crear la API, HTTPException para manejar errores HTTP
from pydantic import BaseModel, Field  # BaseModel para definir esquemas y Field para validaciones/campos

from limpieza import DataCleaner, LimpiezaConfigSchema, LimpiezaReporteSchema  # Elementos del módulo de limpieza
from api.analysis_schemas import (
    AnalisisInmobiliarioInput,     # Esquema de entrada para el análisis inmobiliario
    AnalisisInmobiliarioResult,    # Esquema del resultado calculado
    AnalisisGuardado,              # Esquema del objeto que se almacena en historial
)
from analysis.stats import analizar_inmuebles  # Función pura que calcula estadísticas con NumPy


# Se crea la aplicación principal de FastAPI con título y versión
app = FastAPI(title="API Inmobiliaria - Limpieza y Análisis", version="1.0.0")


# -------------------------
# Endpoint existente: limpieza
# -------------------------
class LimpiezaRequest(BaseModel):
    # Configuración de limpieza; si no se envía, se crea una configuración por defecto
    config: LimpiezaConfigSchema = Field(default_factory=LimpiezaConfigSchema)

    # Datos de entrada a limpiar, en forma de lista de diccionarios
    # Se exige mínimo 1 registro
    data: list[dict[str, Any]] = Field(..., min_length=1)


@app.post("/limpiar", response_model=LimpiezaReporteSchema)
def limpiar(request: LimpiezaRequest) -> LimpiezaReporteSchema:
    # Convierte la lista de diccionarios recibida en un DataFrame de pandas
    df = pd.DataFrame(request.data)

    # Crea una instancia del limpiador con la configuración recibida
    cleaner = DataCleaner(config=request.config)

    # Ejecuta el proceso de limpieza y genera un reporte
    # El guion bajo (_) indica que el DataFrame limpio no se usa aquí, solo el reporte
    _, reporte = cleaner.run_with_report(df, preview_rows=5)

    # Retorna únicamente el reporte de limpieza
    return reporte


# -------------------------
# NUEVO: Persistencia en memoria (historial) + CRUD
# -------------------------
# Diccionario que almacena en memoria los análisis realizados
# La clave es el id y el valor es un objeto AnalisisGuardado
historial: Dict[int, AnalisisGuardado] = {}

# Contador global para asignar ids consecutivos a los análisis
contador_id: int = 0


@app.post("/analizar", response_model=AnalisisGuardado)
def analizar(payload: AnalisisInmobiliarioInput) -> AnalisisGuardado:
    """
    - Recibe datos validados (Pydantic)
    - (Opcional) aplica limpieza
    - Ejecuta función pura numpy
    - Guarda en memoria
    - Retorna resultado
    """
    # Se indica que se usará y modificará la variable global contador_id
    global contador_id

    # Convierte cada objeto InmuebleInput en un diccionario común
    # Los datos ya vienen validados por Pydantic
    inmuebles_dicts = [it.model_dump() for it in payload.inmuebles]

    # Limpieza opcional usando tu módulo (sobre columnas relevantes)
    if payload.usar_limpieza:
        # Convierte los inmuebles a DataFrame para aplicar el proceso de limpieza
        df = pd.DataFrame(inmuebles_dicts)

        # Config mínima: solo asegurar tipos y limpiar NAs.
        # (Tu pipeline ya hace varias transformaciones genéricas.)
        # Se crea un limpiador con configuración por defecto
        cleaner = DataCleaner(config=LimpiezaConfigSchema())

        # Se ejecuta la limpieza y se obtiene el DataFrame limpio y el reporte
        # Aquí el reporte no se usa, por eso se guarda en _
        df_clean, _ = cleaner.run_with_report(df, preview_rows=3)

        # Convierte nuevamente el DataFrame limpio a lista de diccionarios
        inmuebles_dicts = df_clean.to_dict(orient="records")

    # Función pura: numpy stats
    # Llama a la función que calcula las estadísticas sobre los inmuebles
    res_dict = analizar_inmuebles(inmuebles_dicts)

    # Convierte el diccionario de resultados en un modelo Pydantic tipado
    resultado = AnalisisInmobiliarioResult(**res_dict)

    # Incrementa el contador para asignar un nuevo id único
    contador_id += 1

    # Crea el objeto final que se guardará en historial
    item = AnalisisGuardado(
        id=contador_id,                          # Id autoincremental
        nombre_analisis=payload.nombre_analisis, # Nombre del análisis enviado por el usuario
        moneda=payload.moneda or "COP",         # Usa la moneda enviada o COP por defecto
        resultado=resultado,                    # Resultado estadístico calculado
    )

    # Guarda el análisis en memoria usando el id como clave
    historial[item.id] = item

    # Retorna el objeto recién creado y guardado
    return item


@app.get("/historial", response_model=list[AnalisisGuardado])
def listar_historial() -> list[AnalisisGuardado]:
    # Retorna todos los análisis guardados en memoria como lista
    return list(historial.values())


@app.get("/historial/{id}", response_model=AnalisisGuardado)
def obtener_historial(id: int) -> AnalisisGuardado:
    # Busca un análisis en el historial por su id
    item = historial.get(id)

    # Si no existe, lanza error 404
    if item is None:
        raise HTTPException(status_code=404, detail=f"Análisis con id={id} no existe")

    # Si existe, lo retorna
    return item


@app.delete("/historial/{id}")
def eliminar_historial(id: int) -> dict[str, Any]:
    # Verifica si el id existe en el historial
    if id not in historial:
        raise HTTPException(status_code=404, detail=f"Análisis con id={id} no existe")

    # Elimina el elemento correspondiente del historial
    del historial[id]

    # Retorna confirmación del id eliminado
    return {"deleted": id}


@app.get("/")
def root() -> dict[str, str]:
    # Endpoint raíz de la API
    return {"message": "API Inmobiliaria: Limpieza + Análisis"}


@app.get("/health")
def health() -> dict[str, str]:
    # Endpoint simple para verificar que la API está funcionando correctamente
    return {"status": "ok"}
