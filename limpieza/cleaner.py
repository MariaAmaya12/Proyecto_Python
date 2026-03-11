from __future__ import annotations

from typing import Any, Mapping, Optional

import pandas as pd

from .pipeline import (
    convertir_a_numerico_seguro,
    convertir_vacios_a_nan,
    eliminar_duplicados,
    estandarizar_nombres_columnas,
    imputar_nulos,
    limpiar_columnas_monetarias,
)
from .schemas import (
    LimpiezaConfigSchema,
    LimpiezaReporteSchema,
    LimpiezaDiagnosticoSchema,
    ColumnaResumenSchema,
)


class DataCleaner:
    """
    Encapsula el pipeline de limpieza en una clase con configuración validada por Pydantic.
    """

    def __init__(self, config: Optional[LimpiezaConfigSchema | Mapping[str, Any]] = None) -> None:
        if config is None:
            self.config = LimpiezaConfigSchema()
        elif isinstance(config, LimpiezaConfigSchema):
            self.config = config
        else:
            self.config = LimpiezaConfigSchema.model_validate(config)

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        df_work = df.copy()

        estandarizar_nombres_columnas(df_work)
        convertir_vacios_a_nan(df_work)
        eliminar_duplicados(df_work)

        if self.config.columnas_monetarias:
            limpiar_columnas_monetarias(df_work, self.config.columnas_monetarias)

        convertir_a_numerico_seguro(
            df_work,
            columnas_objetivo=self.config.columnas_numericas_objetivo,
            umbral_conversion=self.config.umbral_conversion,
        )

        imputar_nulos(
            df_work,
            estrategia_num=self.config.estrategia_num,
            estrategia_cat=self.config.estrategia_cat,
        )

        return df_work

    @staticmethod
    def _pct(parte: int, total: int) -> float:
        return 0.0 if total == 0 else round((parte / total) * 100, 2)

    def run_with_report(
        self, df: pd.DataFrame, preview_rows: int = 5
    ) -> tuple[pd.DataFrame, LimpiezaReporteSchema]:
        df_in = df.copy()

        # Estado inicial
        columnas_originales = [str(c) for c in df_in.columns]
        dtypes_antes = {str(col): str(dtype) for col, dtype in df_in.dtypes.items()}
        nulos_antes_por_col = df_in.isna().sum().to_dict()
        nulos_totales_antes = int(df_in.isna().sum().sum())
        celdas_antes = int(df_in.shape[0] * df_in.shape[1])
        duplicados_detectados = int(df_in.duplicated().sum())

        # Limpieza
        df_out = self.run(df_in)

        # Estado final
        dtypes_despues = {str(col): str(dtype) for col, dtype in df_out.dtypes.items()}
        nulos_despues_por_col = df_out.isna().sum().to_dict()
        nulos_totales_despues = int(df_out.isna().sum().sum())
        celdas_despues = int(df_out.shape[0] * df_out.shape[1])
        duplicados_restantes = int(df_out.duplicated().sum())

        columnas_resultantes = list(df_out.columns)

        # Renombres detectados: posición a posición sobre intersección de longitudes
        columnas_renombradas: list[str] = []
        n_cols_comunes = min(len(columnas_originales), len(columnas_resultantes))
        for i in range(n_cols_comunes):
            if columnas_originales[i] != columnas_resultantes[i]:
                columnas_renombradas.append(
                    f"{columnas_originales[i]} -> {columnas_resultantes[i]}"
                )

        # Columnas convertidas a numérico
        columnas_convertidas_a_numerico: list[str] = []
        for col in df_out.columns:
            col_str = str(col)
            if col_str in dtypes_antes and col_str in dtypes_despues:
                if dtypes_antes[col_str] != dtypes_despues[col_str]:
                    if "int" in dtypes_despues[col_str] or "float" in dtypes_despues[col_str]:
                        columnas_convertidas_a_numerico.append(col_str)

        # Detalle por columna
        detalle_columnas: list[ColumnaResumenSchema] = []
        for col in df_out.columns:
            col_str = str(col)
            nulos_antes = int(nulos_antes_por_col.get(col_str, 0))
            nulos_despues = int(nulos_despues_por_col.get(col_str, 0))

            detalle_columnas.append(
                ColumnaResumenSchema(
                    columna=col_str,
                    dtype_antes=dtypes_antes.get(col_str, "no_disponible"),
                    dtype_despues=dtypes_despues.get(col_str, "no_disponible"),
                    nulos_antes=nulos_antes,
                    nulos_despues=nulos_despues,
                    pct_nulos_antes=self._pct(nulos_antes, len(df_in)),
                    pct_nulos_despues=self._pct(nulos_despues, len(df_out)),
                )
            )

        diagnostico = LimpiezaDiagnosticoSchema(
            n_filas_entrada=len(df_in),
            n_filas_salida=len(df_out),
            n_columnas_entrada=df_in.shape[1],
            n_columnas_salida=df_out.shape[1],
            nulos_totales_antes=nulos_totales_antes,
            nulos_totales_despues=nulos_totales_despues,
            pct_nulos_antes=self._pct(nulos_totales_antes, celdas_antes),
            pct_nulos_despues=self._pct(nulos_totales_despues, celdas_despues),
            duplicados_exactos_detectados=duplicados_detectados,
            duplicados_exactos_restantes=duplicados_restantes,
            columnas_originales=columnas_originales,
            columnas_resultantes=columnas_resultantes,
            columnas_renombradas=columnas_renombradas,
            columnas_monetarias_limpiadas=self.config.columnas_monetarias or [],
            columnas_convertidas_a_numerico=columnas_convertidas_a_numerico,
            detalle_columnas=detalle_columnas,
        )

        preview = df_out.head(preview_rows).to_dict(orient="records") if preview_rows > 0 else []

        reporte = LimpiezaReporteSchema(
            n_filas_entrada=len(df_in),
            n_filas_salida=len(df_out),
            columnas=columnas_resultantes,
            diagnostico=diagnostico,
            preview=preview,
        )

        return df_out, reporte