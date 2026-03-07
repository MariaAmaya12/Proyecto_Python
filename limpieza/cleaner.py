## Proveer una interfaz orientada a objetos para
# ejecutar la limpieza con config validada.
# Este archivo define una clase que organiza el proceso de limpieza
# usando una configuración validada previamente con Pydantic.


from __future__ import annotations  # Permite usar anotaciones de tipos con evaluación diferida
from typing import Any, Mapping, Optional  # Tipos auxiliares para configuración flexible
import pandas as pd  # Librería para manipular DataFrames


from .pipeline import (
    convertir_a_numerico_seguro,    # Convierte columnas a tipo numérico cuando sea posible
    convertir_vacios_a_nan,         # Reemplaza vacíos por valores NaN
    eliminar_duplicados,            # Elimina filas duplicadas
    estandarizar_nombres_columnas,  # Normaliza nombres de columnas
    imputar_nulos,                  # Rellena valores faltantes según estrategia
    limpiar_columnas_monetarias,    # Limpia columnas con formato monetario
)
from .schemas import LimpiezaConfigSchema, LimpiezaReporteSchema  # Esquemas de configuración y reporte


class DataCleaner:
    """
    Encapsula el pipeline de limpieza en una clase con configuración validada por Pydantic.
    """
    # Esta clase permite ejecutar el flujo de limpieza de forma organizada,
    # guardando una configuración validada en el atributo self.config.

    def __init__(self, config: Optional[LimpiezaConfigSchema | Mapping[str, Any]] = None) -> None:
        # Si no se pasa configuración, se crea una configuración por defecto
        if config is None:
            self.config = LimpiezaConfigSchema()

        # Si ya se pasó un objeto del tipo correcto, se usa directamente
        elif isinstance(config, LimpiezaConfigSchema):
            self.config = config

        # Si se pasó un diccionario u otra estructura tipo mapping,
        # se valida y convierte al esquema Pydantic correspondiente
        else:
            self.config = LimpiezaConfigSchema.model_validate(config)

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        # Se crea una copia del DataFrame original para no modificar el original directamente
        df_work = df.copy()

        # Estandariza los nombres de las columnas
        estandarizar_nombres_columnas(df_work)

        # Convierte cadenas vacías o equivalentes a NaN
        convertir_vacios_a_nan(df_work)

        # Elimina filas duplicadas
        eliminar_duplicados(df_work)

        # Si en la configuración se definieron columnas monetarias,
        # se limpian antes de intentar conversiones numéricas
        if self.config.columnas_monetarias:
            limpiar_columnas_monetarias(df_work, self.config.columnas_monetarias)

        # Intenta convertir columnas objetivo a tipo numérico
        # usando el umbral de conversión definido en la configuración
        convertir_a_numerico_seguro(
            df_work,
            columnas_objetivo=self.config.columnas_numericas_objetivo,
            umbral_conversion=self.config.umbral_conversion,
        )

        # Imputa valores nulos usando las estrategias configuradas
        # para variables numéricas y categóricas
        imputar_nulos(
            df_work,
            estrategia_num=self.config.estrategia_num,
            estrategia_cat=self.config.estrategia_cat,
        )

        # Retorna el DataFrame ya procesado
        return df_work

    def run_with_report(
        self, df: pd.DataFrame, preview_rows: int = 5
    ) -> tuple[pd.DataFrame, LimpiezaReporteSchema]:
        # Guarda la cantidad de filas de entrada antes de la limpieza
        n_in = len(df)

        # Ejecuta la limpieza principal
        df_out = self.run(df)

        # Guarda la cantidad de filas resultantes después de la limpieza
        n_out = len(df_out)

        # Genera una vista previa de las primeras filas del DataFrame limpio
        # en formato lista de diccionarios, solo si preview_rows > 0
        preview = df_out.head(preview_rows).to_dict(orient="records") if preview_rows > 0 else []

        # Construye el reporte de limpieza con información resumida
        reporte = LimpiezaReporteSchema(
            n_filas_entrada=n_in,         # Número de filas antes de limpiar
            n_filas_salida=n_out,         # Número de filas después de limpiar
            columnas=list(df_out.columns),# Lista final de columnas del DataFrame limpio
            preview=preview,              # Muestra de las primeras filas limpias
        )

        # Retorna tanto el DataFrame limpio como el reporte estructurado
        return df_out, reporte
