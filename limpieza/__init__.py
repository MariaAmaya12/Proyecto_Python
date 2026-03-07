### Se define la API pública del paquete.
# Este archivo indica qué elementos del paquete `limpieza`
# estarán disponibles para importarse fácilmente desde fuera.

from .pipeline import limpiar_dataframe  ## Importa la función principal del pipeline funcional de limpieza
from .cleaner import DataCleaner         ## Importa la clase que encapsula la lógica de limpieza
from .schemas import LimpiezaConfigSchema, LimpiezaReporteSchema  ## Importa los esquemas Pydantic de configuración y reporte


## Con __all__ se define, mediante una lista,
# qué nombres públicos del módulo se importan con from ... import *.
# Es decir, controla cuáles son los elementos "oficialmente públicos"
# del paquete cuando otro archivo hace una importación global.
__all__ = [
    "limpiar_dataframe",      # Función pública para limpiar un DataFrame
    "DataCleaner",            # Clase pública para ejecutar limpieza con configuración
    "LimpiezaConfigSchema",   # Esquema público de configuración de limpieza
    "LimpiezaReporteSchema",  # Esquema público del reporte generado por la limpieza
]
