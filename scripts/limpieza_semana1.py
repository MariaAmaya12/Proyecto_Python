from __future__ import annotations  # Permite usar anotaciones de tipos con evaluación diferida

import unicodedata  # Se usa para normalizar texto y eliminar acentos
from typing import Iterable, Optional  # Tipos para parámetros iterables y opcionales

import numpy as np  # Librería para operaciones numéricas y uso de NaN
import pandas as pd  # Librería principal para manejo de DataFrames


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
    # Convierte los nombres de las columnas a texto, elimina espacios al inicio y al final,
    # pasa todo a minúsculas y reemplaza espacios internos por guiones bajos
    columnas = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )

    # Elimina acentos y otros signos diacríticos de los nombres de columnas
    columnas = columnas.map(
        lambda col: unicodedata.normalize("NFKD", col)
        .encode("ascii", errors="ignore")
        .decode("utf-8")
    )

    # Reemplaza los nombres originales por los nombres ya estandarizados
    df.columns = columnas


# -------------------------------------------------
# 2) Conversión de vacíos a NaN
# -------------------------------------------------
def convertir_vacios_a_nan(df: pd.DataFrame) -> None:
    """
    Convierte strings vacíos o con solo espacios en NaN.
    """
    # Reemplaza cadenas vacías o formadas solo por espacios por np.nan
    # inplace=True aplica el cambio directamente sobre el DataFrame
    df.replace(r"^\s*$", np.nan, regex=True, inplace=True)


# -------------------------------------------------
# 3) Eliminación de duplicados
# -------------------------------------------------
def eliminar_duplicados(df: pd.DataFrame) -> None:
    """
    Elimina filas duplicadas conservando la primera aparición.
    """
    # Elimina filas repetidas y conserva solo la primera vez que aparece cada una
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
    # Recorre cada columna indicada por el usuario
    for col in columnas:
        # Si la columna no existe en el DataFrame, se omite
        if col not in df.columns:
            continue

        # Convierte la columna a texto para poder limpiar símbolos y separadores
        s = df[col].astype(str)

        # Quitar todo lo que no sea dígito, signo negativo o separadores comunes
        # Elimina símbolos como $, letras, espacios y otros caracteres no numéricos
        s = s.str.replace(r"[^\d\-\.,]", "", regex=True)

        # Quitar separador de miles
        # Elimina el carácter usado para separar miles
        if miles:
            s = s.str.replace(miles, "", regex=False)

        # Normalizar separador decimal a "."
        # Convierte el separador decimal a punto, que es el formato esperado por pandas
        if decimal and decimal != ".":
            s = s.str.replace(decimal, ".", regex=False)

        # Convierte la serie resultante a valores numéricos
        # Si algún valor no puede convertirse, se asigna NaN
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
    # Si el usuario especificó columnas objetivo, solo intenta convertir esas
    if columnas_objetivo is not None:
        for col in columnas_objetivo:
            # Verifica que la columna exista antes de convertirla
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return

    # Si no se especifican columnas, busca automáticamente columnas de texto candidatas
    candidatos = df.select_dtypes(include=["object", "string"]).columns

    # Recorre cada columna candidata
    for col in candidatos:
        # Intenta convertir la columna a numérica
        convertido = pd.to_numeric(df[col], errors="coerce")

        # Calcula la proporción de valores que sí se pudieron convertir
        ratio_ok = convertido.notna().mean()

        # Si la proporción supera el umbral, reemplaza la columna original por la convertida
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
    # Selecciona las columnas numéricas del DataFrame
    num_cols = df.select_dtypes(include=[np.number]).columns

    # Recorre cada columna numérica
    for col in num_cols:
        # Si la estrategia es "mean", usa la media; en otro caso usa la mediana
        valor = df[col].mean() if estrategia_num == "mean" else df[col].median()

        # Rellena los valores faltantes con el valor calculado
        df[col] = df[col].fillna(valor)

    # Categóricas
    # Selecciona columnas de texto o categóricas
    cat_cols = df.select_dtypes(include=["object", "string", "category"]).columns

    # Recorre cada columna categórica
    for col in cat_cols:
        # Si la estrategia es "moda", rellena con el valor más frecuente
        if estrategia_cat == "moda":
            moda = df[col].mode(dropna=True)  # Calcula la moda ignorando nulos
            relleno = moda.iloc[0] if len(moda) > 0 else "desconocido"  # Si no hay moda, usa un valor por defecto
            df[col] = df[col].fillna(relleno)  # Rellena los nulos con la moda o "desconocido"
        else:
            # Si la estrategia no es "moda", usa directamente el valor constante indicado
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

    # Estandariza los nombres de columnas
    estandarizar_nombres_columnas(df_work)

    # Convierte vacíos y espacios en NaN
    convertir_vacios_a_nan(df_work)

    # Elimina filas duplicadas
    eliminar_duplicados(df_work)

    # Si se definieron columnas monetarias, las limpia antes de convertir a numérico
    if columnas_monetarias:
        limpiar_columnas_monetarias(df_work, columnas_monetarias)

    # Convierte columnas a numéricas de forma segura
    convertir_a_numerico_seguro(
        df_work,
        columnas_objetivo=columnas_numericas_objetivo,
        umbral_conversion=umbral_conversion,
    )

    # Imputa valores nulos según la estrategia configurada
    imputar_nulos(
        df_work,
        estrategia_num=estrategia_num,
        estrategia_cat=estrategia_cat,
    )

    # Retorna el DataFrame ya limpio
    return df_work
