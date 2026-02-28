
from __future__ import annotations

from typing import Any, Dict

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from limpieza import DataCleaner, LimpiezaConfigSchema, LimpiezaReporteSchema
from api.analysis_schemas import (
    AnalisisInmobiliarioInput,
    AnalisisInmobiliarioResult,
    AnalisisGuardado,
)
from analysis.stats import analizar_inmuebles


app = FastAPI(title="API Inmobiliaria - Limpieza y Análisis", version="1.0.0")


# -------------------------
# Endpoint existente: limpieza
# -------------------------
class LimpiezaRequest(BaseModel):
    config: LimpiezaConfigSchema = Field(default_factory=LimpiezaConfigSchema)
    data: list[dict[str, Any]] = Field(..., min_length=1)


@app.post("/limpiar", response_model=LimpiezaReporteSchema)
def limpiar(request: LimpiezaRequest) -> LimpiezaReporteSchema:
    df = pd.DataFrame(request.data)
    cleaner = DataCleaner(config=request.config)
    _, reporte = cleaner.run_with_report(df, preview_rows=5)
    return reporte


# -------------------------
# NUEVO: Persistencia en memoria (historial) + CRUD
# -------------------------
historial: Dict[int, AnalisisGuardado] = {}
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
    global contador_id

    # Pasar inmuebles a dicts (ya validados por Pydantic)
    inmuebles_dicts = [it.model_dump() for it in payload.inmuebles]

    # Limpieza opcional usando tu módulo (sobre columnas relevantes)
    if payload.usar_limpieza:
        df = pd.DataFrame(inmuebles_dicts)

        # Config mínima: solo asegurar tipos y limpiar NAs.
        # (Tu pipeline ya hace varias transformaciones genéricas.)
        cleaner = DataCleaner(config=LimpiezaConfigSchema())
        df_clean, _ = cleaner.run_with_report(df, preview_rows=3)

        inmuebles_dicts = df_clean.to_dict(orient="records")

    # Función pura: numpy stats
    res_dict = analizar_inmuebles(inmuebles_dicts)
    resultado = AnalisisInmobiliarioResult(**res_dict)

    contador_id += 1
    item = AnalisisGuardado(
        id=contador_id,
        nombre_analisis=payload.nombre_analisis,
        moneda=payload.moneda or "COP",
        resultado=resultado,
    )
    historial[item.id] = item
    return item


@app.get("/historial", response_model=list[AnalisisGuardado])
def listar_historial() -> list[AnalisisGuardado]:
    return list(historial.values())


@app.get("/historial/{id}", response_model=AnalisisGuardado)
def obtener_historial(id: int) -> AnalisisGuardado:
    item = historial.get(id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Análisis con id={id} no existe")
    return item


@app.delete("/historial/{id}")
def eliminar_historial(id: int) -> dict[str, Any]:
    if id not in historial:
        raise HTTPException(status_code=404, detail=f"Análisis con id={id} no existe")
    del historial[id]
    return {"deleted": id}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "API Inmobiliaria: Limpieza + Análisis"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}