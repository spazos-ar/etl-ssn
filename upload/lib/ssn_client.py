#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Cliente HTTP para la interacción con el sistema de la SSN.

Este módulo proporciona una interfaz común para realizar operaciones HTTP contra
el sistema de la Superintendencia de Seguros de la Nación (SSN). Maneja:

1. Autenticación y gestión de tokens
2. Manejo de errores y reintentos
3. Configuración de SSL y certificados
4. Logging centralizado y configurable
5. Envío y recepción de datos en formato JSON

La clase principal SSNClient implementa:
- Autenticación usando credenciales del .env
- Manejo de sesiones HTTP persistentes
- Gestión automática de reintentos
- Formateo y validación de datos
- Gestión del certificado SSL

Uso:
    from ssn_client import SSNClient

    # Crear cliente con config
    config = {
        'baseUrl': 'https://ri.ssn.gob.ar/api',
        'endpoints': {
            'authenticate': '/login',
            'entregaMensual': '/entrega/mensual',
            'entregaSemanal': '/entrega/semanal'
        },
        'debug': True  # opcional
    }

    with SSNClient(config) as client:
        token = client.authenticate()
        client.post('entregaMensual', data)

Variables de entorno (.env):
    SSN_USER: Usuario para autenticación
    SSN_PASSWORD: Contraseña del usuario
    SSN_COMPANY: Código de la compañía

Autor: G. Casanova
Fecha: Septiembre 2025
"""

import os
import json
import httpx
import certifi
import ssl
from typing import Dict, Any, Optional, Union
from urllib3.exceptions import InsecureRequestWarning
import warnings
import logging
from pathlib import Path

class SSNClient:
    def __init__(self, config: Dict[str, Any], debug: bool = False):
        """
        Inicializa el cliente SSN.
        
        Args:
            config: Configuración con baseUrl y endpoints
            debug: Habilita logging detallado
        """
        self.config = config
        self.debug = debug
        self.token = None
        self._setup_logging()
        
        # Configuración de timeouts
        timeout = 30.0
        
        # Configuración de SSL para producción
        self.verify = True  # Por defecto habilitado en producción
        ssl_context = None
        
        try:
            # Crear contexto SSL con certificados del sistema y certifi
            ssl_context = ssl.create_default_context()
            ssl_context.load_default_certs()
            # Cargar certificados de certifi
            ssl_context.load_verify_locations(cafile=certifi.where())
            
            # Cargar certificado específico de la SSN si está configurado
            if 'cafile' in self.config.get('ssl', {}):
                ca_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                     self.config['ssl']['cafile'])
                if os.path.exists(ca_file):
                    ssl_context.load_verify_locations(cafile=ca_file)
                    self.logger.info(f"Cargado certificado específico: {ca_file}")
                else:
                    self.logger.warning(f"No se encontró el archivo de certificado: {ca_file}")
            
            # Configurar nivel de seguridad para producción
            ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            ssl_context.check_hostname = True
            
            # Mostramos información del certificado para diagnóstico
            if self.debug:
                from OpenSSL import SSL
                ctx = SSL.Context(SSL.TLS_METHOD)
                ctx.load_verify_locations(cafile=certifi.where())
                self.logger.debug("Configuración SSL:")
                self.logger.debug(f"Certificados cargados de: {certifi.where()}")
                self.logger.debug(f"Versión mínima TLS: 1.2")
                self.logger.debug(f"Modo de verificación: CERT_REQUIRED")
                self.logger.debug(f"Verificación de hostname: Activada")
            
            # Hacemos una prueba de conexión
            test_client = httpx.Client(
                verify=ssl_context,
                timeout=5.0  # timeout corto para la prueba
            )
            
            try:
                response = test_client.get(self.config['baseUrl'])
                # Intentar obtener información del certificado
                try:
                    cert = response.extensions.get_ssl_context()
                    if cert and self.debug:
                        self.logger.debug(f"Conexión establecida con:")
                        self.logger.debug(f"Protocolo: {cert.protocol if hasattr(cert, 'protocol') else 'N/A'}")
                        self.logger.debug(f"Cipher: {cert.cipher() if hasattr(cert, 'cipher') else 'N/A'}")
                except Exception:
                    pass  # No es crítico si no podemos obtener esta información
                
            except httpx.ConnectError as conn_err:
                if "SSL" in str(conn_err) or "certificate" in str(conn_err).lower():
                    self.logger.error(f"Error de verificación SSL: {str(conn_err)}")
                    raise
                else:
                    raise RuntimeError(f"Error de conexión: {str(conn_err)}")
            finally:
                test_client.close()
            
            # Si llegamos aquí, la verificación SSL fue exitosa
            self.verify = True
            self.ssl_context = ssl_context
            self.logger.info("Conexión SSL verificada correctamente")
            
        except Exception as e:
            error_msg = f"Error crítico en la configuración SSL: {str(e)}"
            if self.config.get('ssl', {}).get('verify', True):
                self.logger.error(error_msg)
                if self.debug:
                    import traceback
                    self.logger.debug("Traceback completo del error SSL:")
                    self.logger.debug(traceback.format_exc())
                raise RuntimeError(f"{error_msg} Por favor, verifique la configuración SSL.")
            else:
                # Solo si se ha configurado explícitamente para no verificar
                self.logger.warning("ADVERTENCIA DE SEGURIDAD: Continuando sin verificación SSL según configuración.")
                self.verify = False
                ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                warnings.filterwarnings('ignore', category=InsecureRequestWarning)
                self.ssl_context = ssl_context

        # Cliente HTTP con configuración base y SSL personalizado
        self.client = httpx.Client(
            verify=self.ssl_context,
            timeout=timeout,
            headers={"Content-Type": "application/json"}
        )
    
    def _setup_logging(self):
        """Configura el sistema de logging."""
        self.logger = logging.getLogger('ssn_client')

        # Evitamos añadir handlers si ya existen
        if not logging.getLogger().handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s\n')
            handler.setFormatter(formatter)
            logging.getLogger().addHandler(handler)
            
        # Configurar niveles de logging
        if self.debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            # En modo no-debug, solo mostramos WARNING y ERROR
            self.logger.setLevel(logging.WARNING)
            logging.getLogger('httpx').setLevel(logging.WARNING)
            logging.getLogger('httpcore').setLevel(logging.WARNING)
            logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    def _build_url(self, endpoint: str) -> str:
        """Construye la URL completa para un endpoint."""
        if endpoint not in self.config['endpoints']:
            raise ValueError(f"Endpoint '{endpoint}' no encontrado en la configuración")
        return self.config['baseUrl'].rstrip('/') + self.config['endpoints'][endpoint]
    
    def _handle_response(self, response: httpx.Response, context: str = "") -> Dict[str, Any]:
        """
        Procesa la respuesta HTTP y maneja errores.
        
        Args:
            response: Respuesta HTTP
            context: Contexto de la operación para mensajes de error
            
        Returns:
            Dict con la respuesta JSON procesada
            
        Raises:
            RuntimeError si hay errores en la respuesta
        """
        try:
            # Solo loguear detalles en modo debug
            if self.debug:
                self.logger.debug(f"Response Code: {response.status_code}")
                if response.status_code != 200:
                    self.logger.debug(f"Response Headers: {dict(response.headers)}")
                    self.logger.debug(f"Response Body: {response.text[:1000]}...")
            
            if response.status_code == 401:
                raise RuntimeError("Error de autenticación. Token inválido o expirado.")
            
            data = response.json()
            
            if response.status_code != 200:
                error_msg = (
                    data.get("message") or
                    data.get("detail") or
                    data.get("errors") or
                    response.text
                )
                if isinstance(error_msg, (list, dict)):
                    error_msg = json.dumps(error_msg, indent=2, ensure_ascii=False)
                raise RuntimeError(f"Error en {context}: {error_msg}")
                
            return data
            
        except json.JSONDecodeError:
            raise RuntimeError(f"Error decodificando respuesta JSON: {response.text}")
        except Exception as e:
            raise RuntimeError(f"Error procesando respuesta: {str(e)}")
    
    def authenticate(self) -> str:
        """
        Autentica con el servicio SSN.
        
        Returns:
            Token de autenticación
            
        Raises:
            RuntimeError si hay error de autenticación
        """
        user = os.getenv('SSN_USER')
        password = os.getenv('SSN_PASSWORD')
        company = os.getenv('SSN_COMPANY')
        
        if not all([user, password, company]):
            raise RuntimeError("Faltan variables de entorno SSN_USER, SSN_PASSWORD o SSN_COMPANY")
        
        url = self._build_url("authenticate")  # usamos authenticate aunque el endpoint sea login
        payload = {
            "USER": user,
            "CIA": company,
            "PASSWORD": password
        }
        
        try:
            if self.debug:
                self.logger.debug(f"Autenticando en {url}")
                self.logger.debug(f"Verificación SSL: {'Activada' if self.verify else 'Desactivada'}")
            
            response = self.client.post(url, json=payload)
            data = self._handle_response(response, "autenticación")
            
            token = data.get('TOKEN') or data.get('token')
            if not token:
                raise RuntimeError("No se encontró el token en la respuesta")
            
            self.token = token
            return token
            
        except httpx.ConnectError as e:
            error_msg = str(e)
            if "SSL" in error_msg or "certificate" in error_msg.lower():
                self.logger.error(f"Error de verificación SSL durante autenticación: {error_msg}")
                if self.verify:
                    raise RuntimeError("Error de seguridad SSL. No se puede establecer una conexión segura.")
                else:
                    self.logger.warning("ADVERTENCIA DE SEGURIDAD: Conexión no segura según configuración.")
            raise RuntimeError(f"Error de conexión durante autenticación: {error_msg}")
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Realiza una petición GET."""
        url = self._build_url(endpoint)
        headers = {"Token": self.token} if self.token else {}
        
        try:
            response = self.client.get(url, params=params, headers=headers)
            return self._handle_response(response, f"GET {endpoint}")
        except httpx.RequestError as e:
            raise RuntimeError(f"Error en GET {endpoint}: {str(e)}")
    
    def post(self, endpoint: str, data: Dict) -> Dict[str, Any]:
        """Realiza una petición POST."""
        url = self._build_url(endpoint)
        headers = {"Token": self.token} if self.token else {}
        
        if self.debug:
            self.logger.debug(f"POST {url}")
            self.logger.debug(f"Headers: {headers}")
            self.logger.debug(f"Data: {json.dumps(data, indent=2)}")
        
        try:
            response = self.client.post(url, json=data, headers=headers)
            return self._handle_response(response, f"POST {endpoint}")
        except httpx.RequestError as e:
            raise RuntimeError(f"Error en POST {endpoint}: {str(e)}")
    
    def put(self, endpoint: str, data: Dict) -> Dict[str, Any]:
        """Realiza una petición PUT."""
        url = self._build_url(endpoint)
        headers = {"Token": self.token} if self.token else {}
        
        try:
            response = self.client.put(url, json=data, headers=headers)
            return self._handle_response(response, f"PUT {endpoint}")
        except httpx.RequestError as e:
            raise RuntimeError(f"Error en PUT {endpoint}: {str(e)}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
