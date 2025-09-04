#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Utilidades para la gestión de certificados SSL.

Este módulo proporciona funcionalidades para:
1. Detectar automáticamente certificados en el directorio configurado
2. Validar y cargar certificados SSL para conexiones seguras
3. Manejar múltiples ambientes (prod, test)

Uso:
    from cert_utils import cert_manager
    
    # Obtener certificado para ambiente actual
    cert_path = cert_manager.get_latest_cert_for_environment('prod')
    
    # Obtener ruta completa del certificado
    full_path = cert_manager.get_full_cert_path(cert_path)

Variables de entorno (.env):
    SSL_CERT_DIR: Directorio donde buscar certificados (default: upload/certs)
    SSL_CERT_AUTO_DETECT: Habilita detección automática (default: true)

Autor: G. Casanova
Fecha: Septiembre 2025
"""

import os
import logging
from pathlib import Path
from typing import Optional, List
import re
from datetime import datetime

class CertificateManager:
    """Gestor de certificados SSL para el cliente SSN."""
    
    def __init__(self):
        self.logger = logging.getLogger('cert_utils')
        self.base_path = Path(__file__).resolve().parents[2]  # Ir dos niveles arriba desde upload/lib/
        
    def get_cert_directory(self) -> Path:
        """Obtiene el directorio de certificados desde la configuración."""
        cert_dir = os.getenv('SSL_CERT_DIR', 'upload/certs')
        return self.base_path / cert_dir
    
    def is_auto_detect_enabled(self) -> bool:
        """Verifica si la detección automática está habilitada."""
        return os.getenv('SSL_CERT_AUTO_DETECT', 'true').lower() == 'true'
    
    def find_cert_files(self) -> List[Path]:
        """Busca archivos de certificado en el directorio configurado."""
        cert_dir = self.get_cert_directory()
        
        if not cert_dir.exists():
            self.logger.warning(f"Directorio de certificados no existe: {cert_dir}")
            return []
        
        # Patrones comunes para archivos de certificado
        patterns = ['*.pem', '*.crt', '*.cert']
        cert_files = []
        
        for pattern in patterns:
            cert_files.extend(cert_dir.glob(pattern))
        
        # Filtrar archivos que contengan "ssn" en el nombre
        ssn_certs = [f for f in cert_files if 'ssn' in f.name.lower()]
        
        if ssn_certs:
            return ssn_certs
        
        return cert_files
    
    def parse_cert_date(self, filename: str) -> Optional[datetime]:
        """Extrae fecha del nombre del archivo de certificado."""
        # Buscar patrones como ssn_cert_20250904.pem
        date_match = re.search(r'(\d{8})', filename)
        if date_match:
            try:
                date_str = date_match.group(1)
                return datetime.strptime(date_str, '%Y%m%d')
            except ValueError:
                pass
        
        # Buscar patrones como ssn_cert_2025-09-04.pem
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if date_match:
            try:
                date_str = date_match.group(1)
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                pass
        
        return None
    
    def get_latest_cert_for_environment(self, environment: str = 'prod') -> Optional[str]:
        """Obtiene el certificado más reciente para el ambiente especificado."""
        if not self.is_auto_detect_enabled():
            self.logger.debug("Detección automática de certificados deshabilitada")
            return None
        
        cert_files = self.find_cert_files()
        if not cert_files:
            self.logger.warning("No se encontraron archivos de certificado")
            return None
        
        # Filtrar por ambiente si es necesario
        env_certs = []
        for cert_file in cert_files:
            filename = cert_file.name.lower()
            # Si el archivo contiene el ambiente específico, priorizarlo
            if environment.lower() in filename:
                env_certs.append(cert_file)
        
        # Si no hay certificados específicos del ambiente, usar todos
        if not env_certs:
            env_certs = cert_files
        
        # Ordenar por fecha si es posible, sino por nombre
        cert_with_dates = []
        cert_without_dates = []
        
        for cert_file in env_certs:
            cert_date = self.parse_cert_date(cert_file.name)
            if cert_date:
                cert_with_dates.append((cert_file, cert_date))
            else:
                cert_without_dates.append(cert_file)
        
        # Ordenar certificados con fecha por fecha descendente (más reciente primero)
        cert_with_dates.sort(key=lambda x: x[1], reverse=True)
        
        # Ordenar certificados sin fecha por nombre descendente
        cert_without_dates.sort(key=lambda x: x.name, reverse=True)
        
        # Priorizar certificados con fecha
        if cert_with_dates:
            selected_cert = cert_with_dates[0][0]
            self.logger.debug(f"Certificado seleccionado (con fecha): {selected_cert.name}")
            return selected_cert.name
        elif cert_without_dates:
            selected_cert = cert_without_dates[0]
            self.logger.debug(f"Certificado seleccionado (sin fecha): {selected_cert.name}")
            return selected_cert.name
        
        return None
    
    def get_full_cert_path(self, cert_filename: str) -> str:
        """Convierte un nombre de archivo de certificado a ruta completa."""
        cert_dir = self.get_cert_directory()
        return str(cert_dir / cert_filename)
    
    def validate_cert_file(self, cert_path: str) -> bool:
        """Valida que un archivo de certificado sea válido."""
        try:
            if not os.path.exists(cert_path):
                return False
            
            # Leer el archivo y verificar que tenga el formato básico de certificado
            with open(cert_path, 'r') as f:
                content = f.read()
                return '-----BEGIN CERTIFICATE-----' in content and '-----END CERTIFICATE-----' in content
        except Exception as e:
            self.logger.error(f"Error validando certificado {cert_path}: {e}")
            return False
    
    def get_cert_info(self, cert_path: str) -> dict:
        """Obtiene información básica de un certificado."""
        info = {
            'path': cert_path,
            'exists': False,
            'valid_format': False,
            'size': 0
        }
        
        try:
            if os.path.exists(cert_path):
                info['exists'] = True
                info['size'] = os.path.getsize(cert_path)
                info['valid_format'] = self.validate_cert_file(cert_path)
        except Exception as e:
            self.logger.error(f"Error obteniendo información del certificado: {e}")
        
        return info

# Instancia global del gestor de certificados
cert_manager = CertificateManager()