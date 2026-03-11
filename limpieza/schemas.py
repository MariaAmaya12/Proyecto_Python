from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, ConfigDict


class LimpiezaConfigSchema(BaseModel):
    """
    Contrato de entrada (Input) para configurar la limpieza.
    """

    model_config = ConfigDict(extra="forbid")

    columnas_monetarias: Optional[list[str]] = Field(
        default=None,
        description="Lista de columnas con formato monetario (ej: ['valor']).",
        examples=[["valor"]],
    )

    columnas_numericas_objetivo: Optional[list[str]] = Field(
        default=None,
        description="Columnas que se deben convertir a numérico sí o sí.",
        examples=[["area", "habitaciones"]],
    )

    estrategia_num: str = Field(
        default="median",
        description="Estrategia de imputación numérica.",
        pattern="^(median|mean)$",
        examples=["median"],
    )

    estrategia_cat: str = Field(
        default="moda",
        description="Estrategia de imputación categórica: 'moda' o un valor constante.",
        examples=["moda", "desconocido"],
    )

    umbral_conversion: float = Field(
        default=0.85,
        description="Proporción mínima para convertir una columna texto a numérica.",
        ge=0.0,
        le=1.0,
        examples=[0.85],
    )


class ColumnaResumenSchema(BaseModel):
    """
    Perfil resumido por columna antes y después de limpiar.
    """
    model_config = ConfigDict(extra="forbid")

    columna: str
    dtype_antes: str
    dtype_despues: str
    nulos_antes: int = Field(..., ge=0)
    nulos_despues: int = Field(..., ge=0)
    pct_nulos_antes: float = Field(..., ge=0.0, le=100.0)
    pct_nulos_despues: float = Field(..., ge=0.0, le=100.0)


class LimpiezaDiagnosticoSchema(BaseModel):
    """
    Diagnóstico general del dataset.
    """
    model_config = ConfigDict(extra="forbid")

    n_filas_entrada: int = Field(..., ge=0)
    n_filas_salida: int = Field(..., ge=0)
    n_columnas_entrada: int = Field(..., ge=0)
    n_columnas_salida: int = Field(..., ge=0)

    nulos_totales_antes: int = Field(..., ge=0)
    nulos_totales_despues: int = Field(..., ge=0)
    pct_nulos_antes: float = Field(..., ge=0.0, le=100.0)
    pct_nulos_despues: float = Field(..., ge=0.0, le=100.0)

    duplicados_exactos_detectados: int = Field(..., ge=0)
    duplicados_exactos_restantes: int = Field(..., ge=0)

    columnas_originales: list[str] = Field(default_factory=list)
    columnas_resultantes: list[str] = Field(default_factory=list)
    columnas_renombradas: list[str] = Field(default_factory=list)

    columnas_monetarias_limpiadas: list[str] = Field(default_factory=list)
    columnas_convertidas_a_numerico: list[str] = Field(default_factory=list)

    detalle_columnas: list[ColumnaResumenSchema] = Field(default_factory=list)


class LimpiezaReporteSchema(BaseModel):
    """
    Contrato de salida (Output) enriquecido para reportar el resultado de la limpieza.
    """
    model_config = ConfigDict(extra="forbid")

    n_filas_entrada: int = Field(..., ge=0, description="Número de filas antes de limpiar.")
    n_filas_salida: int = Field(..., ge=0, description="Número de filas después de limpiar.")
    columnas: list[str] = Field(..., description="Lista final de columnas en el DataFrame limpio.")

    diagnostico: LimpiezaDiagnosticoSchema

    preview: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Muestra de filas limpias en formato JSON (records).",
    )