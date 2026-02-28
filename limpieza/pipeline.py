## Contiene todas las funciones de limpieza y el pipeline principal.


from __future__ import annotations ## 

import unicodedata ## limpieza de texto (acentos)
from typing import Iterable, Optional 

import numpy as np
import pandas as pd


# -------------------------------------------------
# 1) Estandarización de nombres de columnas
# -------------------------------------------------
def estandarizar_nombres_columnas(df: pd.DataFrame) -> None:
    """
    Normaliza nombres de columnas:
    - elimina espacios laterales
    - convierte a minúsculas
    - reemplaza espacios por "_"
    - elimina acentos
    """
    columnas = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )

    columnas = columnas.map(
        lambda col: unicodedata.normalize("NFKD", col)
        .encode("ascii", errors="ignore")
        .decode("utf-8")
    )

    df.columns = columnas


# -------------------------------------------------
# 2) Conversión de vacíos a NaN
# -------------------------------------------------
def convertir_vacios_a_nan(df: pd.DataFrame) -> None:
    """
    Convierte strings vacíos o con solo espacios en NaN.
    """
    df.replace(r"^\s*$", np.nan, regex=True, inplace=True)


# -------------------------------------------------
# 3) Eliminación de duplicados
# -------------------------------------------------
def eliminar_duplicados(df: pd.DataFrame) -> None:
    """
    Elimina filas duplicadas conservando la primera aparición.
    """
    df.drop_duplicates(keep="first", inplace=True)


# -------------------------------------------------
# 4) Limpieza de columnas monetarias (in-place)
# -------------------------------------------------
def limpiar_columnas_monetarias(
    df: pd.DataFrame,
    columnas: Iterable[str],
    miles: str = ".",
    decimal: str = ",",
) -> None:
    """
    Limpia columnas monetarias / numéricas con símbolos.
    Ej: "$ 360.000.000" -> 360000000

    Supuestos:
    - 'miles' indica separador de miles (por defecto ".")
    - 'decimal' indica separador decimal (por defecto ",")
    """
    for col in columnas:
        if col not in df.columns:
            continue

        s = df[col].astype(str)

        # Quitar todo lo que no sea dígito, signo negativo o separadores comunes
        s = s.str.replace(r"[^\d\-\.,]", "", regex=True)

        # Quitar separador de miles
        if miles:
            s = s.str.replace(miles, "", regex=False)

        # Normalizar separador decimal a "."
        if decimal and decimal != ".":
            s = s.str.replace(decimal, ".", regex=False)

        df[col] = pd.to_numeric(s, errors="coerce")


# -------------------------------------------------
# 5) Conversión segura a numérico
# -------------------------------------------------
def convertir_a_numerico_seguro(
    df: pd.DataFrame,
    columnas_objetivo: Optional[Iterable[str]] = None,
    umbral_conversion: float = 0.85,
) -> None:
    """
    Convierte columnas a numérico sin afectar categóricas.

    Caso 1: columnas_objetivo especificadas → convierte solo esas.
    Caso 2: None → convierte columnas tipo texto si al menos
             el 85% de los valores se convierten correctamente.
    """
    if columnas_objetivo is not None:
        for col in columnas_objetivo:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return

    candidatos = df.select_dtypes(include=["object", "string"]).columns

    for col in candidatos:
        convertido = pd.to_numeric(df[col], errors="coerce")
        ratio_ok = convertido.notna().mean()

        if ratio_ok >= umbral_conversion:
            df[col] = convertido


# -------------------------------------------------
# 6) Imputación simple de nulos
# -------------------------------------------------
def imputar_nulos(
    df: pd.DataFrame,
    estrategia_num: str = "median",  # "median" o "mean"
    estrategia_cat: str = "moda",    # "moda" o valor constante
) -> None:
    """
    Imputa valores faltantes:
    - Numéricas: median o mean
    - Categóricas: moda o valor constante
    """
    # Numéricas
    num_cols = df.select_dtypes(include=[np.number]).columns

    for col in num_cols:
        valor = df[col].mean() if estrategia_num == "mean" else df[col].median()
        df[col] = df[col].fillna(valor)

    # Categóricas
    cat_cols = df.select_dtypes(include=["object", "string", "category"]).columns

    for col in cat_cols:
        if estrategia_cat == "moda":
            moda = df[col].mode(dropna=True)
            relleno = moda.iloc[0] if len(moda) > 0 else "desconocido"
            df[col] = df[col].fillna(relleno)
        else:
            df[col] = df[col].fillna(estrategia_cat)


# -------------------------------------------------
# 7) Pipeline principal
# -------------------------------------------------
def limpiar_dataframe(
    df: pd.DataFrame,
    columnas_monetarias: Optional[Iterable[str]] = None,
    columnas_numericas_objetivo: Optional[Iterable[str]] = None,
    estrategia_num: str = "median",
    estrategia_cat: str = "moda",
    umbral_conversion: float = 0.85,
) -> pd.DataFrame:
    """
    Pipeline completo de limpieza (Semana 1).

    - No modifica el DataFrame original.
    - Usa una única copia para eficiencia.
    """
    df_work = df.copy()

    estandarizar_nombres_columnas(df_work)
    convertir_vacios_a_nan(df_work)
    eliminar_duplicados(df_work)

    if columnas_monetarias:
        limpiar_columnas_monetarias(df_work, columnas_monetarias)

    convertir_a_numerico_seguro(
        df_work,
        columnas_objetivo=columnas_numericas_objetivo,
        umbral_conversion=umbral_conversion,
    )

    imputar_nulos(
        df_work,
        estrategia_num=estrategia_num,
        estrategia_cat=estrategia_cat,
    )

    return df_work