from __future__ import annotations  # Permite usar anotaciones de tipos de forma más flexible/pospuesta

from typing import Any, Dict, List  # Tipos para describir mejor entradas y salidas
import numpy as np  # Librería para cálculos numéricos eficientes


def _r4(x: float) -> float:
    # Convierte el valor a float y lo redondea a 4 decimales
    return round(float(x), 4)


def analizar_inmuebles(inmuebles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Función PURA (sin FastAPI).
    Recibe lista de dicts validados (inmuebles) y retorna dict con resultados.

    Reglas rúbrica:
    - numpy para 5+ cálculos
    - redondeo a 4 decimales
    - ddof=1 para var/std muestral
    """
    # Extraer arrays
    # Se construye un arreglo de NumPy con los valores de los inmuebles
    valor = np.array([it["valor"] for it in inmuebles], dtype=float)

    # Se construye un arreglo de NumPy con las áreas en metros cuadrados
    area = np.array([it["area_m2"] for it in inmuebles], dtype=float)

    # Precio por m2 (dominio)
    # Se calcula el precio por metro cuadrado dividiendo valor entre área
    precio_m2 = valor / area

    # Cantidad total de inmuebles analizados
    n = int(valor.size)

    # ddof=1 (muestral); n>=2 garantizado por Pydantic (min_length=2)
    # Función interna para calcular estadísticas básicas de cualquier arreglo numérico
    def stats(arr: np.ndarray) -> Dict[str, float]:
        return {
            "promedio": _r4(np.mean(arr)),          # Media aritmética
            "mediana": _r4(np.median(arr)),         # Valor central
            "min": _r4(np.min(arr)),                # Valor mínimo
            "max": _r4(np.max(arr)),                # Valor máximo
            "std": _r4(np.std(arr, ddof=1)),        # Desviación estándar muestral
        }

    # Estadísticas del valor total de los inmuebles
    p = stats(valor)

    # Estadísticas del área de los inmuebles
    a = stats(area)

    # Estadísticas del precio por metro cuadrado
    pm2 = stats(precio_m2)

    # Se retorna un diccionario consolidado con todos los resultados
    return {
        "n": n,  # Número de inmuebles procesados

        "precio_promedio": p["promedio"],   # Promedio del valor de los inmuebles
        "precio_mediana": p["mediana"],     # Mediana del valor de los inmuebles
        "precio_min": p["min"],             # Valor mínimo
        "precio_max": p["max"],             # Valor máximo
        "precio_std": p["std"],             # Desviación estándar del valor

        "area_promedio": a["promedio"],     # Promedio de área
        "area_mediana": a["mediana"],       # Mediana de área
        "area_min": a["min"],               # Área mínima
        "area_max": a["max"],               # Área máxima
        "area_std": a["std"],               # Desviación estándar del área

        "precio_m2_promedio": pm2["promedio"],  # Promedio del precio por m²
        "precio_m2_mediana": pm2["mediana"],    # Mediana del precio por m²
        "precio_m2_min": pm2["min"],            # Precio por m² mínimo
        "precio_m2_max": pm2["max"],            # Precio por m² máximo
        "precio_m2_std": pm2["std"],            # Desviación estándar del precio por m²
    }
