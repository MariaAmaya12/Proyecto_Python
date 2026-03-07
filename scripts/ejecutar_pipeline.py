import pandas as pd  # Librería para leer, manipular y guardar datos tabulares
from limpieza import DataCleaner  # Importa la clase encargada de ejecutar el proceso de limpieza

# Lee el archivo CSV original con la base de datos de inmuebles
# Se especifica codificación utf-8 para manejar correctamente caracteres especiales
df = pd.read_csv("inmuebles_bogota.csv", encoding="utf-8")

# Crea una instancia del limpiador de datos
# La configuración se pasa como diccionario y luego será validada internamente
cleaner = DataCleaner(
    config={
        "columnas_monetarias": ["valor"],  # Indica que la columna "valor" tiene formato monetario y debe limpiarse
        "estrategia_num": "median",        # Para nulos en variables numéricas usa la mediana
        "estrategia_cat": "moda",          # Para nulos en variables categóricas usa la moda
        "umbral_conversion": 0.85,         # Convierte columnas a numéricas si al menos 85% de sus valores son convertibles
    }
)

# Ejecuta el pipeline de limpieza y además genera un reporte
# preview_rows=3 indica que el reporte incluirá una vista previa de 3 filas limpias
df_limpio, reporte = cleaner.run_with_report(df, preview_rows=3)

# Guarda el DataFrame limpio en un nuevo archivo CSV
# index=False evita guardar la columna de índices de pandas
df_limpio.to_csv("data_limpia.csv", index=False)

# Imprime mensaje de confirmación al usuario
print("Base limpia guardada correctamente.")

# Convierte el reporte Pydantic a diccionario y lo muestra en consola
print("Reporte (dict):", reporte.model_dump())
