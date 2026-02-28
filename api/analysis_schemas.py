from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class InmuebleInput(BaseModel):
    """
    Registro individual (dominio inmobiliario).
    """
    model_config = ConfigDict(extra="forbid")

    tipo: str = Field(..., min_length=3, description="Tipo de inmueble (ej: apartamento, casa)")
    area_m2: float = Field(..., gt=0, description="Área en m^2, debe ser > 0")
    valor: float = Field(..., gt=0, description="Precio/valor del inmueble, debe ser > 0")
    habitaciones: int = Field(..., ge=0, le=20, description="Número de habitaciones")
    banos: int = Field(..., ge=0, le=20, description="Número de baños")
    barrio: Optional[str] = Field(default=None, min_length=3, description="Barrio (opcional)")


class AnalisisInmobiliarioInput(BaseModel):
    """
    Request principal para POST /analizar.
    """
    model_config = ConfigDict(extra="forbid")

    nombre_analisis: str = Field(..., min_length=3)
    inmuebles: List[InmuebleInput] = Field(..., min_length=2, description="Mínimo 2 inmuebles para ddof=1")
    moneda: Optional[str] = Field(default="COP", min_length=3)
    usar_limpieza: bool = Field(default=True, description="Si True, aplica tu módulo limpieza antes de analizar")


class AnalisisInmobiliarioResult(BaseModel):
    """
    Output con 5+ campos numéricos calculados (cumple rúbrica).
    """
    model_config = ConfigDict(extra="forbid")

    n: int

    # Estadísticos del valor
    precio_promedio: float
    precio_mediana: float
    precio_min: float
    precio_max: float
    precio_std: float  # ddof=1

    # Estadísticos del área
    area_promedio: float
    area_mediana: float
    area_min: float
    area_max: float
    area_std: float  # ddof=1

    # Estadísticos del precio por m2
    precio_m2_promedio: float
    precio_m2_mediana: float
    precio_m2_min: float
    precio_m2_max: float
    precio_m2_std: float  # ddof=1


class AnalisisGuardado(BaseModel):
    """
    Lo que guardas en memoria (historial).
    """
    model_config = ConfigDict(extra="forbid")

    id: int
    nombre_analisis: str
    moneda: str
    resultado: AnalisisInmobiliarioResult