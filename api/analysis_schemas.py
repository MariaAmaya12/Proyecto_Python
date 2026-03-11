from __future__ import annotations

from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict

from limpieza.schemas import LimpiezaDiagnosticoSchema


class InmuebleInput(BaseModel):
    """
    Registro individual de un inmueble para análisis estadístico.
    """
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "tipo": "apartamento",
                "area_m2": 78.5,
                "valor": 325000000,
                "habitaciones": 3,
                "banos": 2,
                "barrio": "Chapinero"
            }
        }
    )

    tipo: str = Field(
        ...,
        min_length=3,
        max_length=40,
        description="Tipo de inmueble, por ejemplo: apartamento, casa, lote o local."
    )
    area_m2: float = Field(
        ...,
        gt=0,
        description="Área del inmueble en metros cuadrados."
    )
    valor: float = Field(
        ...,
        gt=0,
        description="Valor comercial del inmueble en la moneda seleccionada."
    )
    habitaciones: int = Field(
        ...,
        ge=0,
        le=20,
        description="Número de habitaciones. Puede ser 0 en inmuebles no residenciales."
    )
    banos: int = Field(
        ...,
        ge=0,
        le=20,
        description="Número de baños. Puede ser 0 en algunos tipos de inmueble."
    )
    barrio: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=60,
        description="Barrio o sector del inmueble. Campo opcional."
    )


class AnalisisInmobiliarioInput(BaseModel):
    """
    Entrada principal del endpoint /analizar.
    """
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "nombre_analisis": "Analisis apartamentos zona norte",
                "moneda": "COP",
                "usar_limpieza": True,
                "inmuebles": [
                    {
                        "tipo": "apartamento",
                        "area_m2": 78.5,
                        "valor": 325000000,
                        "habitaciones": 3,
                        "banos": 2,
                        "barrio": "Chapinero"
                    },
                    {
                        "tipo": "apartamento",
                        "area_m2": 64.0,
                        "valor": 280000000,
                        "habitaciones": 2,
                        "banos": 2,
                        "barrio": "Cedritos"
                    }
                ]
            }
        }
    )

    nombre_analisis: str = Field(
        ...,
        min_length=3,
        max_length=80,
        description="Nombre identificador del análisis estadístico."
    )
    inmuebles: List[InmuebleInput] = Field(
        ...,
        min_length=2,
        description="Lista de inmuebles a procesar. Se requieren al menos 2 registros."
    )
    moneda: Optional[str] = Field(
        default="COP",
        min_length=3,
        max_length=5,
        description="Moneda de referencia del análisis, por ejemplo COP o USD."
    )
    usar_limpieza: bool = Field(
        default=True,
        description="Indica si se debe ejecutar el módulo de limpieza antes del análisis."
    )


class AnalisisInmobiliarioResult(BaseModel):
    """
    Resultado estadístico del conjunto de inmuebles analizados.
    """
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "n": 25,
                "precio_promedio": 352400000.1234,
                "precio_mediana": 340000000.0,
                "precio_min": 210000000.0,
                "precio_max": 510000000.0,
                "precio_std": 78500231.4567,
                "precio_var": 6162286347366.3457,
                "area_promedio": 81.3456,
                "area_mediana": 79.0,
                "area_min": 45.0,
                "area_max": 120.0,
                "area_std": 18.2211,
                "area_var": 331.0085,
                "precio_m2_promedio": 4350000.7788,
                "precio_m2_mediana": 4280000.0,
                "precio_m2_min": 3200000.0,
                "precio_m2_max": 5900000.0,
                "precio_m2_std": 602100.3344,
                "precio_m2_var": 362524812345.1122
            }
        }
    )

    n: int = Field(..., description="Número total de inmuebles analizados.")

    precio_promedio: float = Field(..., description="Promedio del valor de los inmuebles.")
    precio_mediana: float = Field(..., description="Mediana del valor de los inmuebles.")
    precio_min: float = Field(..., description="Valor mínimo observado.")
    precio_max: float = Field(..., description="Valor máximo observado.")
    precio_std: float = Field(..., description="Desviación estándar muestral del valor.")
    precio_var: float = Field(..., description="Varianza muestral del valor.")

    area_promedio: float = Field(..., description="Promedio del área en m².")
    area_mediana: float = Field(..., description="Mediana del área en m².")
    area_min: float = Field(..., description="Área mínima observada.")
    area_max: float = Field(..., description="Área máxima observada.")
    area_std: float = Field(..., description="Desviación estándar muestral del área.")
    area_var: float = Field(..., description="Varianza muestral del área.")

    precio_m2_promedio: float = Field(..., description="Promedio del precio por metro cuadrado.")
    precio_m2_mediana: float = Field(..., description="Mediana del precio por metro cuadrado.")
    precio_m2_min: float = Field(..., description="Precio por m² mínimo observado.")
    precio_m2_max: float = Field(..., description="Precio por m² máximo observado.")
    precio_m2_std: float = Field(..., description="Desviación estándar muestral del precio por m².")
    precio_m2_var: float = Field(..., description="Varianza muestral del precio por m².")


class AnalisisGuardado(BaseModel):
    """
    Estructura almacenada en memoria para el historial de análisis.
    """
    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Identificador único del análisis en memoria.")
    nombre_analisis: str = Field(..., description="Nombre del análisis guardado.")
    moneda: str = Field(..., description="Moneda asociada al análisis.")
    resultado: AnalisisInmobiliarioResult = Field(..., description="Resultado estadístico calculado.")


class ArchivoGeneradoInfo(BaseModel):
    """
    Metadatos del archivo CSV generado por la API.
    """
    model_config = ConfigDict(extra="forbid")

    archivo_id: str = Field(..., description="Identificador único del archivo generado.")
    nombre_archivo: str = Field(..., description="Nombre del archivo descargable.")
    download_url: str = Field(..., description="Ruta para descargar el archivo generado.")


class ResumenLimpiezaCSV(BaseModel):
    """
    Resumen del proceso de limpieza sobre un archivo CSV.
    """
    model_config = ConfigDict(extra="forbid")

    mensaje: str
    n_registros_entrada: int
    n_registros_salida: int
    columnas_resultantes: list[str]
    diagnostico: LimpiezaDiagnosticoSchema
    preview: list[dict[str, Any]]
    archivo_generado: ArchivoGeneradoInfo


class ResumenAnalisisCSV(BaseModel):
    """
    Resumen del análisis ejecutado a partir de un CSV.
    """
    model_config = ConfigDict(extra="forbid")

    mensaje: str
    analisis_id: int
    nombre_analisis: str
    moneda: str
    n_registros_procesados: int
    limpieza_aplicada: bool
    filas_invalidas_descartadas: int = 0
    preview_errores_validacion: list[dict[str, Any]] = Field(default_factory=list)
    resultado: AnalisisInmobiliarioResult
    archivo_generado: ArchivoGeneradoInfo


class ResumenPipelineCSV(BaseModel):
    """
    Resumen integral del pipeline: limpieza + validación + análisis + descarga.
    """
    model_config = ConfigDict(extra="forbid")

    mensaje: str
    analisis_id: int
    nombre_analisis: str
    moneda: str
    filas_invalidas_descartadas: int = 0
    preview_errores_validacion: list[dict[str, Any]] = Field(default_factory=list)
    limpieza: ResumenLimpiezaCSV
    analisis: AnalisisInmobiliarioResult
    archivo_generado: ArchivoGeneradoInfo