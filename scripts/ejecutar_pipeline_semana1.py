import pandas as pd  # Librería para leer archivos CSV y manipular datos tabulares
from limpieza import limpiar_dataframe  # Importa la función principal del pipeline de limpieza

# Leer datos crudos
# Carga el archivo CSV original en un DataFrame de pandas
# encoding="utf-8" permite manejar correctamente tildes y caracteres especiales
df = pd.read_csv("inmuebles_bogota.csv", encoding="utf-8")

# Aplicar limpieza
# Ejecuta el pipeline completo de limpieza sobre el DataFrame original
# En este caso se indica que la columna "valor" tiene formato monetario
df_limpio = limpiar_dataframe(
    df,
    columnas_monetarias=["valor"]
)

# Guardar directamente en la carpeta principal del proyecto
# Exporta el DataFrame ya limpio a un nuevo archivo CSV
# index=False evita guardar la columna de índices de pandas
df_limpio.to_csv("data_limpia.csv", index=False)

# Imprime un mensaje de confirmación en consola
print("Base limpia guardada correctamente.")
