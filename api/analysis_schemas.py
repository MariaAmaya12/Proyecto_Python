from __future__ import annotations  # Permite posponer la evaluación de anotaciones de tipos

from typing import Optional, List  # Tipos para campos opcionales y listas
from pydantic import BaseModel, Field, ConfigDict  # Herramientas de Pydantic para definir y validar modelos


class InmuebleInput(BaseModel):
    """
    Registro individual (dominio inmobiliario).
    """
    # Configura el modelo para no aceptar campos extra no definidos
    model_config = ConfigDict(extra="forbid")

    # Tipo de inmueble, por ejemplo: apartamento, casa, local, etc.
    # Debe tener al menos 3 caracteres
    tipo: str = Field(..., min_length=3, description="Tipo de inmueble (ej: apartamento, casa)")

    # Área del inmueble en metros cuadrados
    # Debe ser mayor que 0
    area_m2: float = Field(..., gt=0, description="Área en m^2, debe ser > 0")

    # Valor o precio del inmueble
    # Debe ser mayor que 0
    valor: float = Field(..., gt=0, description="Precio/valor del inmueble, debe ser > 0")

    # Número de habitaciones
    # Debe estar entre 0 y 20
    habitaciones: int = Field(..., ge=0, le=20, description="Número de habitaciones")

    # Número de baños
    # Debe estar entre 0 y 20
    banos: int = Field(..., ge=0, le=20, description="Número de baños")

    # Barrio donde se ubica el inmueble
    # Es opcional, pero si viene informado debe tener al menos 3 caracteres
    barrio: Optional[str] = Field(default=None, min_length=3, description="Barrio (opcional)")


class AnalisisInmobiliarioInput(BaseModel):
    """
    Request principal para POST /analizar.
    """
    # No permite campos adicionales fuera de los definidos
    model_config = ConfigDict(extra="forbid")

    # Nombre que identifica el análisis que se va a realizar
    # Debe tener al menos 3 caracteres
    nombre_analisis: str = Field(..., min_length=3)

    # Lista de inmuebles a analizar
    # Debe tener mínimo 2 elementos para poder calcular la desviación estándar muestral con ddof=1
    inmuebles: List[InmuebleInput] = Field(..., min_length=2, description="Mínimo 2 inmuebles para ddof=1")

    # Moneda en la que se expresa el valor de los inmuebles
    # Por defecto es COP
    moneda: Optional[str] = Field(default="COP", min_length=3)

    # Indica si antes del análisis se debe aplicar el módulo de limpieza
    usar_limpieza: bool = Field(default=True, description="Si True, aplica tu módulo limpieza antes de analizar")


class AnalisisInmobiliarioResult(BaseModel):
    """
    Output con 5+ campos numéricos calculados (cumple rúbrica).
    """
    # No permite agregar campos no contemplados en este resultado
    model_config = ConfigDict(extra="forbid")

    # Cantidad total de inmuebles analizados
    n: int

    # Estadísticos del valor
    precio_promedio: float   # Promedio de los valores de los inmuebles
    precio_mediana: float    # Mediana de los valores
    precio_min: float        # Valor mínimo
    precio_max: float        # Valor máximo
    precio_std: float        # Desviación estándar muestral del valor (ddof=1)

    # Estadísticos del área
    area_promedio: float     # Promedio de las áreas
    area_mediana: float      # Mediana de las áreas
    area_min: float          # Área mínima
    area_max: float          # Área máxima
    area_std: float          # Desviación estándar muestral del área (ddof=1)

    # Estadísticos del precio por m2
    precio_m2_promedio: float  # Promedio del precio por metro cuadrado
    precio_m2_mediana: float   # Mediana del precio por metro cuadrado
    precio_m2_min: float       # Precio por metro cuadrado mínimo
    precio_m2_max: float       # Precio por metro cuadrado máximo
    precio_m2_std: float       # Desviación estándar muestral del precio por metro cuadrado (ddof=1)


class AnalisisGuardado(BaseModel):
    """
    Lo que guardas en memoria (historial).
    """
    # No admite atributos extra no definidos
    model_config = ConfigDict(extra="forbid")

    # Identificador único del análisis guardado
    id: int

    # Nombre asignado al análisis
    nombre_analisis: str

    # Moneda usada en el análisis
    moneda: str

    # Resultado completo del análisis inmobiliario
    resultado: AnalisisInmobiliarioResult
