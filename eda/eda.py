import pandas as pd  # Librería para manipulación y análisis de datos en tablas
import numpy as np  # Librería para operaciones numéricas
import matplotlib.pyplot as plt  # Librería para generar gráficos


# -------------------------------------------------
# 1. Información general
# -------------------------------------------------
def info_general(df: pd.DataFrame) -> None:
    """Imprime dimensiones y tipos de datos."""
    # Encabezado de la sección de información general
    print("\n=== INFORMACIÓN GENERAL ===")

    # Muestra la cantidad de filas y columnas del DataFrame
    print("Dimensiones (filas, columnas):", df.shape)

    # Muestra un subtítulo para los tipos de datos
    print("\nTipos de datos:")

    # Imprime el tipo de dato de cada columna
    print(df.dtypes)


# -------------------------------------------------
# 2. Valores nulos
# -------------------------------------------------
def analizar_nulos(df: pd.DataFrame) -> None:
    """Muestra conteo de valores nulos (solo columnas con nulos)."""
    # Encabezado de la sección de nulos
    print("\n=== VALORES NULOS ===")

    # Cuenta cuántos valores nulos hay por columna
    nulos = df.isna().sum()

    # Filtra solo las columnas que tienen al menos un nulo
    # y las ordena de mayor a menor cantidad de nulos
    nulos = nulos[nulos > 0].sort_values(ascending=False)

    # Si no hay columnas con nulos, lo informa
    if len(nulos) == 0:
        print("No hay valores nulos.")
    else:
        # Si sí existen nulos, imprime el conteo por columna
        print(nulos)


# -------------------------------------------------
# 3. Histograma robusto (p1–p99)
# -------------------------------------------------
def histograma_robusto(
    serie: pd.Series,
    nombre: str,
    bins: int = 30,
    p_low: float = 0.01,
    p_high: float = 0.99
) -> None:
    """
    Grafica un histograma recortando extremos SOLO para visualización.
    No modifica los datos originales.
    """

    # Elimina valores nulos de la serie para evitar problemas al graficar
    s = serie.dropna()

    # Verifica que existan al menos 2 datos válidos para poder construir el histograma
    if len(s) < 2:
        print(f"{nombre}: no hay suficientes datos para graficar.")
        return

    # Percentiles para recorte visual
    # Calcula el percentil inferior definido por p_low
    low = s.quantile(p_low)

    # Calcula el percentil superior definido por p_high
    high = s.quantile(p_high)

    # Conserva solo los datos dentro del rango [low, high]
    # Esto recorta extremos únicamente para hacer la gráfica más legible
    s_plot = s[(s >= low) & (s <= high)]

    # Crea una nueva figura para el histograma
    plt.figure()

    # Dibuja el histograma con la cantidad de bins indicada
    plt.hist(s_plot, bins=bins)

    # Título del gráfico con el nombre de la variable y el rango percentil usado
    plt.title(f"Distribución de {nombre} (p{int(p_low*100)}–p{int(p_high*100)})")

    # Etiqueta del eje X
    plt.xlabel(nombre)

    # Etiqueta del eje Y
    plt.ylabel("Frecuencia")

    # Ajusta automáticamente los elementos del gráfico para que no se sobrepongan
    plt.tight_layout()

    # Muestra el gráfico en pantalla
    plt.show()


# -------------------------------------------------
# 4. Variables numéricas
# -------------------------------------------------
def analizar_numericas(df: pd.DataFrame, graficar: bool = True) -> None:
    """
    Analiza variables numéricas:
    - Estadísticas descriptivas
    - Histograma robusto (opcional)
    """

    # Encabezado de la sección de variables numéricas
    print("\n=== VARIABLES NUMÉRICAS ===")

    # Selecciona los nombres de las columnas numéricas del DataFrame
    numericas = df.select_dtypes(include=[np.number]).columns

    # Si no hay columnas numéricas, informa y termina la función
    if len(numericas) == 0:
        print("No hay variables numéricas.")
        return

    # Recorre cada columna numérica
    for col in numericas:
        # Imprime el nombre de la columna que se está analizando
        print(f"\n--- {col} ---")

        # Muestra estadísticas descriptivas básicas:
        # conteo, media, desviación estándar, mínimo, cuartiles y máximo
        print(df[col].describe())

        # Si se activó la opción de graficar, genera un histograma robusto de la columna
        if graficar:
            histograma_robusto(df[col], col)


# -------------------------------------------------
# 5. Variables categóricas
# -------------------------------------------------
def analizar_categoricas(df: pd.DataFrame, top: int = 10) -> None:
    """
    Muestra las categorías más frecuentes.
    Detecta object, string y category.
    """

    # Encabezado de la sección de variables categóricas
    print("\n=== VARIABLES CATEGÓRICAS ===")

    # Selecciona columnas de tipo categórico o texto
    categoricas = df.select_dtypes(include=["object", "string", "category"]).columns

    # Si no hay variables categóricas, informa y termina
    if len(categoricas) == 0:
        print("No hay variables categóricas.")
        return

    # Recorre cada columna categórica
    for col in categoricas:
        # Imprime el nombre de la variable categórica analizada
        print(f"\n--- {col} ---")

        # Muestra las categorías más frecuentes, incluyendo valores nulos si existen
        # head(top) limita la salida a las primeras 'top' categorías
        print(df[col].value_counts(dropna=False).head(top))


# -------------------------------------------------
# 6. Matriz de correlación
# -------------------------------------------------
def matriz_correlacion(df: pd.DataFrame, max_cols: int = 12) -> None:
    """
    Calcula correlación de Pearson entre variables numéricas.
    No grafica si hay demasiadas columnas (para evitar ilegibilidad).
    """

    # Encabezado de la sección de correlación
    print("\n=== MATRIZ DE CORRELACIÓN ===")

    # Extrae únicamente las columnas numéricas del DataFrame
    numericas = df.select_dtypes(include=[np.number])

    # Si hay menos de 2 variables numéricas, no se puede calcular correlación
    if numericas.shape[1] < 2:
        print("No hay suficientes variables numéricas para correlación.")
        return

    # Calcula la matriz de correlación de Pearson
    corr = numericas.corr()

    # Imprime la matriz de correlación en formato tabular
    print(corr)

    # Si la cantidad de variables no supera el límite permitido, se grafica
    if corr.shape[0] <= max_cols:
        # Crea una nueva figura para la matriz
        plt.figure()

        # Muestra la matriz como imagen
        plt.imshow(corr, aspect="auto")

        # Agrega barra de color para interpretar la intensidad de la correlación
        plt.colorbar()

        # Etiquetas del eje X con rotación para mejorar legibilidad
        plt.xticks(range(corr.shape[1]), corr.columns, rotation=45, ha="right")

        # Etiquetas del eje Y con los nombres de las variables
        plt.yticks(range(corr.shape[0]), corr.index)

        # Título del gráfico
        plt.title("Matriz de correlación (Pearson)")

        # Ajusta automáticamente el diseño
        plt.tight_layout()

        # Muestra la figura
        plt.show()
    else:
        # Si hay demasiadas variables, evita graficar porque sería difícil de leer
        print("Demasiadas variables para graficar matriz de correlación.")


# -------------------------------------------------
# 7. Ejecutar EDA completo
# -------------------------------------------------
def ejecutar_eda(df: pd.DataFrame, graficar: bool = True) -> None:
    """Ejecuta análisis exploratorio completo."""
    # Ejecuta la revisión general del DataFrame
    info_general(df)

    # Analiza los valores nulos
    analizar_nulos(df)

    # Analiza variables numéricas y, si corresponde, las grafica
    analizar_numericas(df, graficar=graficar)

    # Analiza variables categóricas
    analizar_categoricas(df)

    # Calcula e imprime/grafica la matriz de correlación
    matriz_correlacion(df)
