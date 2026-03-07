## Define los contratos (input/output) de la limpieza con Pydantic.
# En este archivo se crean los modelos que validan la configuración
# del proceso de limpieza y el formato del reporte que se devuelve.

from __future__ import annotations  # Permite usar anotaciones de tipos con evaluación diferida

from typing import Any, Optional  # Tipos auxiliares para valores opcionales y estructuras genéricas

from pydantic import BaseModel, Field, ConfigDict  # Herramientas de Pydantic para definir modelos y validaciones


## valida la configuración del pipeline
class LimpiezaConfigSchema(BaseModel):
    """
    Contrato de entrada (Input) para configurar la limpieza.

    Valida y documenta:
    - tipos
    - restricciones básicas con Field
    """

    model_config = ConfigDict(extra="forbid")  # No permite parámetros desconocidos en la configuración

    ## Campos claves

    columnas_monetarias: Optional[list[str]] = Field(
        default=None,  # Por defecto no se define ninguna columna monetaria
        description="Lista de columnas con formato monetario (ej: ['valor']).",  # Explica el propósito del campo
        examples=[["valor"]],  # Ejemplo de uso en la documentación
    )

    columnas_numericas_objetivo: Optional[list[str]] = Field(
        default=None,  # Por defecto no se obliga a convertir columnas específicas
        description="Columnas que se deben convertir a numérico sí o sí.",  # Fuerza conversión en ciertas columnas
        examples=[["area", "habitaciones"]],  # Ejemplo de columnas objetivo
    )

    estrategia_num: str = Field(
        default="median",  # Estrategia por defecto para imputar nulos numéricos
        description="Estrategia de imputación numérica.",  # Explica el campo
        pattern="^(median|mean)$",  # Solo permite "median" o "mean"
        examples=["median"],  # Ejemplo documentado
    )

    estrategia_cat: str = Field(
        default="moda",  # Estrategia por defecto para imputar variables categóricas
        description="Estrategia de imputación categórica: 'moda' o un valor constante.",  # Puede ser "moda" o un texto fijo
        examples=["moda", "desconocido"],  # Ejemplos válidos
    )

    umbral_conversion: float = Field(
        default=0.85,  # Valor por defecto: 85% de conversión exitosa para transformar una columna
        description="Proporción mínima para convertir una columna texto a numérica.",  # Explica la lógica del umbral
        ge=0.0,  # El valor mínimo permitido es 0.0
        le=1.0,  # El valor máximo permitido es 1.0
        examples=[0.85],  # Ejemplo documentado
    )


## Estructura un reporte serializable para retornarlo en una API.
class LimpiezaReporteSchema(BaseModel):
    """
    Contrato de salida (Output) para reportar el resultado de la limpieza.
    Serializable a JSON con model_dump().
    """

    n_filas_entrada: int = Field(..., ge=0, description="Número de filas antes de limpiar.")  # Filas del DataFrame original
    n_filas_salida: int = Field(..., ge=0, description="Número de filas después de limpiar.")  # Filas del DataFrame final
    columnas: list[str] = Field(..., description="Lista final de columnas en el DataFrame limpio.")  # Nombres de columnas resultantes

    # Preview opcional (sirve para APIs; evita retornar todo el DF)
    preview: list[dict[str, Any]] = Field(
        default_factory=list,  # Por defecto será una lista vacía
        description="Muestra de filas limpias en formato JSON (records).",  # Vista previa del resultado limpio
    )
