from __future__ import annotations

from typing import Any, Dict, List
import numpy as np


def _r4(x: float) -> float:
    return round(float(x), 4)


def analizar_inmuebles(inmuebles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Función pura de análisis estadístico para inmuebles.

    Recibe una lista de registros ya validados y retorna un diccionario
    con métricas descriptivas del valor, área y precio por metro cuadrado.

    Supuestos:
    - ya existe una validación previa que garantiza al menos 2 registros válidos;
    - area_m2 y valor son numéricos y mayores que cero.
    """
    valor = np.array([it["valor"] for it in inmuebles], dtype=float)
    area = np.array([it["area_m2"] for it in inmuebles], dtype=float)

    precio_m2 = valor / area
    n = int(valor.size)

    def stats(arr: np.ndarray) -> Dict[str, float]:
        return {
            "promedio": _r4(np.mean(arr)),
            "mediana": _r4(np.median(arr)),
            "min": _r4(np.min(arr)),
            "max": _r4(np.max(arr)),
            "std": _r4(np.std(arr, ddof=1)),
            "var": _r4(np.var(arr, ddof=1)),
        }

    p = stats(valor)
    a = stats(area)
    pm2 = stats(precio_m2)

    return {
        "n": n,

        "precio_promedio": p["promedio"],
        "precio_mediana": p["mediana"],
        "precio_min": p["min"],
        "precio_max": p["max"],
        "precio_std": p["std"],
        "precio_var": p["var"],

        "area_promedio": a["promedio"],
        "area_mediana": a["mediana"],
        "area_min": a["min"],
        "area_max": a["max"],
        "area_std": a["std"],
        "area_var": a["var"],

        "precio_m2_promedio": pm2["promedio"],
        "precio_m2_mediana": pm2["mediana"],
        "precio_m2_min": pm2["min"],
        "precio_m2_max": pm2["max"],
        "precio_m2_std": pm2["std"],
        "precio_m2_var": pm2["var"],
    }