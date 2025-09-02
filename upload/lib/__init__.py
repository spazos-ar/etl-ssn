# Importar los módulos comunes
from .ssn_client import SSNClient # TODO: Actualizar a .ssn-client en v2.0
# Reexportamos la clase para mantener compatibilidad
__all__ = ['SSNClient']
