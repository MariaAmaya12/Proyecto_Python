from __future__ import annotations

from typing import Any, Dict
import io
import uuid

import pandas as pd
from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File,
    Form,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ValidationError

from limpieza import DataCleaner, LimpiezaConfigSchema, LimpiezaReporteSchema
from api.analysis_schemas import (
    InmuebleInput,
    AnalisisInmobiliarioInput,
    AnalisisInmobiliarioResult,
    AnalisisGuardado,
    ArchivoGeneradoInfo,
    ResumenLimpiezaCSV,
    ResumenAnalisisCSV,
    ResumenPipelineCSV,
)
from analysis.stats import analizar_inmuebles


tags_metadata = [
    {
        "name": "General",
        "description": "Endpoints de verificación rápida del servicio.",
    },
    {
        "name": "Actividad aplicada JSON",
        "description": (
            "Endpoints principales del taller: validación con Pydantic, "
            "procesamiento y respuesta JSON."
        ),
    },
    {
        "name": "Flujo CSV",
        "description": (
            "Flujo extendido del proyecto con carga de archivos CSV, limpieza, "
            "análisis y descarga del archivo procesado."
        ),
    },
    {
        "name": "Historial",
        "description": "Consulta y eliminación de análisis guardados en memoria.",
    },
    {
        "name": "Descargas",
        "description": "Descarga de archivos CSV generados por la API.",
    },
]


app = FastAPI(
    title="API Inmobiliaria — Limpieza y Análisis Estadístico con CSV",
    version="2.3.0",
    description=(
        "API REST para demostración académica del procesamiento de datasets inmobiliarios. "
        "Permite recibir datos JSON validados con Pydantic, cargar archivos CSV, limpiar datos, "
        "ejecutar análisis estadístico descriptivo, consultar historial y descargar archivos procesados."
    ),
    openapi_tags=tags_metadata,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================================
# Modelos de compatibilidad para limpieza JSON
# ==========================================================
class LimpiezaRequest(BaseModel):
    config: LimpiezaConfigSchema = Field(default_factory=LimpiezaConfigSchema)
    data: list[dict[str, Any]] = Field(..., min_length=1)


# ==========================================================
# Persistencia en memoria
# ==========================================================
historial: Dict[int, AnalisisGuardado] = {}
contador_id: int = 0
archivos_generados: Dict[str, dict[str, Any]] = {}


# ==========================================================
# Funciones auxiliares
# ==========================================================
def validar_csv_subido(file: UploadFile) -> None:
    if not file.filename or not file.filename.strip():
        raise HTTPException(status_code=400, detail="No se recibió ningún archivo")

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe tener extensión .csv",
        )


async def leer_csv_a_dataframe(file: UploadFile) -> pd.DataFrame:
    try:
        contenido = await file.read()
        df = pd.read_csv(io.BytesIO(contenido))
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"No fue posible leer el archivo CSV: {str(e)}",
        )

    if df.empty:
        raise HTTPException(status_code=400, detail="El archivo CSV está vacío")

    return df


def generar_nombre_salida(nombre_original: str, sufijo: str) -> str:
    base = nombre_original.rsplit(".", 1)[0]
    return f"{base}_{sufijo}.csv"


def guardar_csv_en_memoria(df: pd.DataFrame, nombre_archivo: str) -> ArchivoGeneradoInfo:
    archivo_id = str(uuid.uuid4())

    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    contenido_csv = buffer.getvalue().encode("utf-8")

    archivos_generados[archivo_id] = {
        "filename": nombre_archivo,
        "content": contenido_csv,
        "media_type": "text/csv",
    }

    return ArchivoGeneradoInfo(
        archivo_id=archivo_id,
        nombre_archivo=nombre_archivo,
        download_url=f"/descargas/{archivo_id}",
    )


def normalizar_dataframe_para_analisis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adapta distintos formatos de CSV al esquema esperado por InmuebleInput.
    """
    df = df.copy()

    renombres = {
        "area": "area_m2",
    }
    df = df.rename(columns=renombres)

    if "valor" in df.columns:
        df["valor"] = (
            df["valor"]
            .astype(str)
            .str.replace("$", "", regex=False)
            .str.replace(".", "", regex=False)
            .str.replace(",", "", regex=False)
            .str.strip()
        )
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")

    for col in ["area_m2", "habitaciones", "banos"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    columnas_esperadas = ["tipo", "area_m2", "valor", "habitaciones", "banos", "barrio"]
    columnas_presentes = [col for col in columnas_esperadas if col in df.columns]
    df = df[columnas_presentes]

    return df


def separar_filas_validas_inmuebles(
    df: pd.DataFrame,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Valida fila por fila, pero en vez de abortar todo el proceso,
    separa registros válidos e inválidos.
    """
    registros_validos: list[dict[str, Any]] = []
    errores: list[dict[str, Any]] = []

    for i, fila in enumerate(df.to_dict(orient="records"), start=1):
        try:
            inmueble = InmuebleInput.model_validate(fila)
            registros_validos.append(inmueble.model_dump())
        except ValidationError as e:
            errores.append(
                {
                    "fila": i,
                    "errores": e.errors(),
                }
            )

    return registros_validos, errores


def validar_minimo_registros(registros_validos: list[dict[str, Any]]) -> None:
    if len(registros_validos) < 2:
        raise HTTPException(
            status_code=422,
            detail=(
                "Después de limpiar y validar, quedaron menos de 2 registros válidos. "
                "No es posible realizar el análisis estadístico."
            ),
        )


def construir_resultado_analisis(registros: list[dict[str, Any]]) -> AnalisisInmobiliarioResult:
    """
    Ejecuta la función pura de análisis y construye el modelo de salida.
    """
    validar_minimo_registros(registros)

    try:
        res_dict = analizar_inmuebles(registros)
        return AnalisisInmobiliarioResult(**res_dict)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"No fue posible construir el análisis estadístico: {str(e)}",
        )


def guardar_analisis_en_historial(
    nombre_analisis: str,
    moneda: str,
    resultado: AnalisisInmobiliarioResult,
) -> AnalisisGuardado:
    global contador_id

    contador_id += 1
    item = AnalisisGuardado(
        id=contador_id,
        nombre_analisis=nombre_analisis,
        moneda=moneda,
        resultado=resultado,
    )
    historial[item.id] = item
    return item


# ==========================================================
# Endpoints raíz y salud
# ==========================================================
@app.get(
    "/",
    tags=["General"],
    summary="Ver mensaje de bienvenida",
    description="Endpoint raíz para verificar rápidamente el propósito de la API.",
)
def root() -> dict[str, Any]:
    return {
        "message": "API Inmobiliaria: carga CSV, limpieza, análisis e historial",
        "docs": "/docs",
        "endpoint_principal_taller": "/analizar",
        "demo_csv": "/pipeline/csv",
    }


@app.get(
    "/health",
    tags=["General"],
    summary="Verificar estado de la API",
    description="Confirma que la API está disponible y respondiendo correctamente.",
)
def health() -> dict[str, str]:
    return {"status": "ok"}


# ==========================================================
# LIMPIEZA JSON
# ==========================================================
@app.post(
    "/limpiar",
    response_model=LimpiezaReporteSchema,
    tags=["Actividad aplicada JSON"],
    summary="Limpiar dataset enviado como JSON",
    description=(
        "Recibe un dataset en formato JSON, aplica el módulo de limpieza y "
        "retorna un reporte estructurado."
    ),
)
def limpiar(request: LimpiezaRequest) -> LimpiezaReporteSchema:
    df = pd.DataFrame(request.data)
    cleaner = DataCleaner(config=request.config)
    _, reporte = cleaner.run_with_report(df, preview_rows=5)
    return reporte


# ==========================================================
# ENDPOINT PRINCIPAL DEL TALLER: ANÁLISIS JSON
# ==========================================================
@app.post(
    "/analizar",
    response_model=AnalisisGuardado,
    status_code=201,
    tags=["Actividad aplicada JSON"],
    summary="Analizar inmuebles enviados como JSON",
    description=(
        "Endpoint principal de la actividad aplicada. "
        "Recibe datos validados con Pydantic, ejecuta el análisis estadístico "
        "y guarda el resultado en memoria."
    ),
)
def analizar(payload: AnalisisInmobiliarioInput) -> AnalisisGuardado:
    inmuebles_dicts = [it.model_dump() for it in payload.inmuebles]

    if payload.usar_limpieza:
        df = pd.DataFrame(inmuebles_dicts)
        cleaner = DataCleaner(config=LimpiezaConfigSchema())
        df_clean, _ = cleaner.run_with_report(df, preview_rows=3)
        inmuebles_dicts = df_clean.to_dict(orient="records")

    resultado = construir_resultado_analisis(inmuebles_dicts)

    item = guardar_analisis_en_historial(
        nombre_analisis=payload.nombre_analisis,
        moneda=payload.moneda or "COP",
        resultado=resultado,
    )
    return item


# ==========================================================
# LIMPIEZA POR CSV
# ==========================================================
@app.post(
    "/limpieza/csv",
    response_model=ResumenLimpiezaCSV,
    tags=["Flujo CSV"],
    summary="Subir CSV y obtener dataset limpio",
    description=(
        "Recibe un archivo CSV, aplica el pipeline de limpieza, devuelve un resumen "
        "y genera una URL para descargar el CSV limpio."
    ),
)
async def limpiar_csv(
    file: UploadFile = File(..., description="Archivo CSV a procesar"),
) -> ResumenLimpiezaCSV:
    validar_csv_subido(file)
    df = await leer_csv_a_dataframe(file)

    cleaner = DataCleaner(config=LimpiezaConfigSchema())
    df_limpio, reporte = cleaner.run_with_report(df, preview_rows=5)

    archivo_info = guardar_csv_en_memoria(
        df_limpio,
        generar_nombre_salida(file.filename, "limpio"),
    )

    return ResumenLimpiezaCSV(
        mensaje="Archivo procesado correctamente con el módulo de limpieza",
        n_registros_entrada=reporte.n_filas_entrada,
        n_registros_salida=reporte.n_filas_salida,
        columnas_resultantes=reporte.columnas,
        diagnostico=reporte.diagnostico,
        preview=reporte.preview,
        archivo_generado=archivo_info,
    )


# ==========================================================
# ANÁLISIS POR CSV
# ==========================================================
@app.post(
    "/analisis/csv",
    response_model=ResumenAnalisisCSV,
    status_code=201,
    tags=["Flujo CSV"],
    summary="Subir CSV, limpiar opcionalmente y analizar inmuebles",
    description=(
        "Recibe un archivo CSV con datos inmobiliarios, adapta columnas al esquema esperado, "
        "descarta filas inválidas, ejecuta el análisis estadístico descriptivo y guarda el resultado."
    ),
)
async def analizar_csv(
    file: UploadFile = File(..., description="Archivo CSV con inmuebles"),
    nombre_analisis: str = Form(..., description="Nombre identificador del análisis"),
    moneda: str = Form("COP", description="Moneda del análisis"),
    usar_limpieza: bool = Form(True, description="Indica si se aplica limpieza antes del análisis"),
) -> ResumenAnalisisCSV:
    validar_csv_subido(file)
    df = await leer_csv_a_dataframe(file)

    df = normalizar_dataframe_para_analisis(df)

    registros_validos, errores_validacion = separar_filas_validas_inmuebles(df)
    validar_minimo_registros(registros_validos)

    df_procesado = pd.DataFrame(registros_validos)

    if usar_limpieza:
        cleaner = DataCleaner(config=LimpiezaConfigSchema())
        df_procesado, _ = cleaner.run_with_report(df_procesado, preview_rows=3)

    registros_finales = df_procesado.to_dict(orient="records")
    resultado = construir_resultado_analisis(registros_finales)

    item = guardar_analisis_en_historial(
        nombre_analisis=nombre_analisis,
        moneda=moneda,
        resultado=resultado,
    )

    archivo_info = guardar_csv_en_memoria(
        df_procesado,
        generar_nombre_salida(file.filename, "procesado"),
    )

    return ResumenAnalisisCSV(
        mensaje="Análisis ejecutado correctamente sobre archivo CSV",
        analisis_id=item.id,
        nombre_analisis=item.nombre_analisis,
        moneda=item.moneda,
        n_registros_procesados=resultado.n,
        limpieza_aplicada=usar_limpieza,
        filas_invalidas_descartadas=len(errores_validacion),
        preview_errores_validacion=errores_validacion[:5],
        resultado=resultado,
        archivo_generado=archivo_info,
    )


# ==========================================================
# PIPELINE COMPLETO: LIMPIEZA + ANÁLISIS
# ==========================================================
@app.post(
    "/pipeline/csv",
    response_model=ResumenPipelineCSV,
    status_code=201,
    tags=["Flujo CSV"],
    summary="Subir un CSV, limpiarlo y analizarlo en una sola ejecución",
    description=(
        "Recibe un único archivo CSV, ejecuta primero el pipeline de limpieza, "
        "después adapta el dataset limpio al esquema esperado por el análisis estadístico, "
        "descarta filas inválidas, guarda el resultado en historial y devuelve un resumen "
        "completo del flujo junto con la URL de descarga del CSV procesado."
    ),
)
async def pipeline_csv(
    file: UploadFile = File(..., description="Archivo CSV a procesar de extremo a extremo"),
    nombre_analisis: str = Form(..., description="Nombre identificador del análisis"),
    moneda: str = Form("COP", description="Moneda del análisis"),
) -> ResumenPipelineCSV:
    validar_csv_subido(file)
    df_original = await leer_csv_a_dataframe(file)

    cleaner = DataCleaner(config=LimpiezaConfigSchema())
    df_limpio, reporte_limpieza = cleaner.run_with_report(df_original, preview_rows=5)

    df_para_analisis = normalizar_dataframe_para_analisis(df_limpio)

    registros_validos, errores_validacion = separar_filas_validas_inmuebles(df_para_analisis)
    validar_minimo_registros(registros_validos)

    df_procesado = pd.DataFrame(registros_validos)

    registros_finales = df_procesado.to_dict(orient="records")
    resultado = construir_resultado_analisis(registros_finales)

    item = guardar_analisis_en_historial(
        nombre_analisis=nombre_analisis,
        moneda=moneda,
        resultado=resultado,
    )

    archivo_info = guardar_csv_en_memoria(
        df_procesado,
        generar_nombre_salida(file.filename, "procesado"),
    )

    resumen_limpieza = ResumenLimpiezaCSV(
        mensaje="Archivo procesado correctamente con el módulo de limpieza",
        n_registros_entrada=reporte_limpieza.n_filas_entrada,
        n_registros_salida=reporte_limpieza.n_filas_salida,
        columnas_resultantes=reporte_limpieza.columnas,
        diagnostico=reporte_limpieza.diagnostico,
        preview=reporte_limpieza.preview,
        archivo_generado=archivo_info,
    )

    return ResumenPipelineCSV(
        mensaje="Pipeline completo ejecutado correctamente",
        analisis_id=item.id,
        nombre_analisis=item.nombre_analisis,
        moneda=item.moneda,
        filas_invalidas_descartadas=len(errores_validacion),
        preview_errores_validacion=errores_validacion[:5],
        limpieza=resumen_limpieza,
        analisis=resultado,
        archivo_generado=archivo_info,
    )


# ==========================================================
# DESCARGA DE ARCHIVOS GENERADOS
# ==========================================================
@app.get(
    "/descargas/{archivo_id}",
    tags=["Descargas"],
    summary="Descargar CSV generado por la API",
    description="Permite descargar el archivo CSV limpio o procesado generado en una operación anterior.",
)
def descargar_archivo(archivo_id: str):
    archivo = archivos_generados.get(archivo_id)

    if archivo is None:
        raise HTTPException(status_code=404, detail="El archivo solicitado no existe")

    return StreamingResponse(
        io.BytesIO(archivo["content"]),
        media_type=archivo["media_type"],
        headers={
            "Content-Disposition": f'attachment; filename="{archivo["filename"]}"'
        },
    )


# ==========================================================
# HISTORIAL
# ==========================================================
@app.get(
    "/historial",
    response_model=list[AnalisisGuardado],
    tags=["Historial"],
    summary="Listar historial de análisis",
    description="Retorna todos los análisis guardados en memoria durante la ejecución de la API.",
)
def listar_historial() -> list[AnalisisGuardado]:
    return list(historial.values())


@app.get(
    "/historial/{analisis_id}",
    response_model=AnalisisGuardado,
    tags=["Historial"],
    summary="Consultar un análisis por ID",
    description="Retorna el detalle de un análisis específico guardado en memoria.",
)
def obtener_historial(analisis_id: int) -> AnalisisGuardado:
    item = historial.get(analisis_id)

    if item is None:
        raise HTTPException(
            status_code=404,
            detail=f"Análisis con id={analisis_id} no existe",
        )

    return item


@app.delete(
    "/historial/{analisis_id}",
    tags=["Historial"],
    summary="Eliminar análisis del historial",
    description="Elimina un análisis almacenado en memoria usando su identificador.",
)
def eliminar_historial(analisis_id: int) -> dict[str, Any]:
    if analisis_id not in historial:
        raise HTTPException(
            status_code=404,
            detail=f"Análisis con id={analisis_id} no existe",
        )

    del historial[analisis_id]
    return {"deleted": analisis_id}