## Contiene todas las funciones de limpieza y el pipeline principal.
# Este archivo reúne las funciones que transforman y preparan un DataFrame
# para dejarlo más consistente antes de analizarlo.


from __future__ import annotations ## Permite usar anotaciones de tipos con evaluación diferida

import unicodedata ## Se usa para normalizar texto y quitar acentos
from typing import Iterable, Optional  ## Tipos para colecciones iterables y valores opcionales

import numpy as np  ## Operaciones numéricas y uso de NaN
import pandas as pd  ## Manipulación de DataFrames


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
    # Convierte los nombres de columnas a texto, quita espacios laterales,
    # pasa a minúsculas y reemplaza espacios internos por guiones bajos
    columnas = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )

    # Recorre cada nombre de columna y elimina acentos o caracteres especiales
    # usando normalización Unicode
    columnas = columnas.map(
        lambda col: unicodedata.normalize("NFKD", col)
        .encode("ascii", errors="ignore")
        .decode("utf-8")
    )

    # Asigna los nombres ya estandarizados al DataFrame
    df.columns = columnas


# -------------------------------------------------
# 2) Conversión de vacíos a NaN
# -------------------------------------------------
def convertir_vacios_a_nan(df: pd.DataFrame) -> None:
    """
    Convierte strings vacíos o con solo espacios en NaN.
    """
    # Reemplaza cadenas vacías o compuestas solo por espacios por np.nan
    # Se hace en el mismo DataFrame (inplace=True)
    df.replace(r"^\s*$", np.nan, regex=True, inplace=True)


# -------------------------------------------------
# 3) Eliminación de duplicados
# -------------------------------------------------
def eliminar_duplicados(df: pd.DataFrame) -> None:
    """
    Elimina filas duplicadas conservando la primera aparición.
    """
    # Elimina filas repetidas y conserva solo la primera ocurrencia
    # El cambio se aplica directamente sobre el DataFrame
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
    # Recorre cada columna indicada como monetaria
    for col in columnas:
        # Si la columna no existe en el DataFrame, la omite
        if col not in df.columns:
            continue

        # Convierte la columna a texto para poder aplicar limpieza de caracteres
        s = df[col].astype(str)

        # Quitar todo lo que no sea dígito, signo negativo o separadores comunes
        # Elimina símbolos como $, espacios y otros caracteres no numéricos
        s = s.str.replace(r"[^\d\-\.,]", "", regex=True)

        # Quitar separador de miles
        # Elimina el carácter usado como separador de miles
        if miles:
            s = s.str.replace(miles, "", regex=False)

        # Normalizar separador decimal a "."
        # Convierte el separador decimal definido a punto, para que pandas lo entienda
        if decimal and decimal != ".":
            s = s.str.replace(decimal, ".", regex=False)

        # Intenta convertir la serie ya limpia a tipo numérico
        # Los valores que no se puedan convertir se vuelven NaN
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
    # Si se especificaron columnas objetivo, solo se intenta convertir esas
    if columnas_objetivo is not None:
        for col in columnas_objetivo:
            # Solo convierte si la columna existe en el DataFrame
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return

    # Si no se especificaron columnas, se buscan candidatas de tipo texto
    candidatos = df.select_dtypes(include=["object", "string"]).columns

    # Se revisa cada columna candidata
    for col in candidatos:
        # Intenta convertir la columna a numérica
        convertido = pd.to_numeric(df[col], errors="coerce")

        # Calcula la proporción de valores que sí lograron convertirse
        ratio_ok = convertido.notna().mean()

        # Si la proporción supera el umbral, reemplaza la columna original
        # por la versión numérica convertida
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
    # Obtiene las columnas numéricas del DataFrame
    num_cols = df.select_dtypes(include=[np.number]).columns

    # Recorre cada columna numérica para rellenar sus nulos
    for col in num_cols:
        # Si la estrategia es "mean", usa la media; en caso contrario usa la mediana
        valor = df[col].mean() if estrategia_num == "mean" else df[col].median()

        # Rellena los valores nulos con el valor calculado
        df[col] = df[col].fillna(valor)

    # Categóricas
    # Obtiene las columnas de texto o categóricas
    cat_cols = df.select_dtypes(include=["object", "string", "category"]).columns

    # Recorre cada columna categórica para rellenar faltantes
    for col in cat_cols:
        # Si la estrategia categórica es "moda", usa el valor más frecuente
        if estrategia_cat == "moda":
            # Calcula la moda excluyendo nulos
            moda = df[col].mode(dropna=True)

            # Si existe al menos una moda, usa la primera;
            # si no hay moda disponible, usa "desconocido"
            relleno = moda.iloc[0] if len(moda) > 0 else "desconocido"

            # Rellena los nulos con ese valor
            df[col] = df[col].fillna(relleno)
        else:
            # Si no se usa "moda", rellena con el valor constante indicado
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
    # Crea una copia del DataFrame original para no alterarlo directamente
    df_work = df.copy()

    # Estandariza nombres de columnas
    estandarizar_nombres_columnas(df_work)

    # Convierte vacíos o cadenas en blanco a NaN
    convertir_vacios_a_nan(df_work)

    # Elimina filas duplicadas
    eliminar_duplicados(df_work)

    # Si se indicaron columnas monetarias, las limpia primero
    if columnas_monetarias:
        limpiar_columnas_monetarias(df_work, columnas_monetarias)

    # Intenta convertir columnas a numéricas de forma segura
    convertir_a_numerico_seguro(
        df_work,
        columnas_objetivo=columnas_numericas_objetivo,
        umbral_conversion=umbral_conversion,
    )

    # Imputa valores faltantes en columnas numéricas y categóricas
    imputar_nulos(
        df_work,
        estrategia_num=estrategia_num,
        estrategia_cat=estrategia_cat,
    )

    # Retorna el DataFrame limpio
    return df_work
