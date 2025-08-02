"""
Servicio de gestión de configuración de empresa.
Implementa la lógica de negocio para configuración corporativa y cálculos de impuestos.

Este servicio maneja:
- CRUD de configuración de empresa (Singleton)
- Validaciones de datos corporativos
- Cálculos de impuestos centralizados
- Formateo de información corporativa

CORRECCIÓN APLICADA: Constructor corregido para usar inyección de dependencias
Fecha corrección: 2025-07-10
Problema resuelto: 'name Database is not defined' error

Autor: Sistema TDD - FASE 3
Fecha: 2025-06-25
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from decimal import Decimal
import threading

from db.database import get_database_connection

from models.company_config import CompanyConfig

class CompanyService:
    """
    Servicio para gestión de configuración de empresa.
    
    Implementa patrón Singleton para garantizar una única configuración
    de empresa en el sistema.
    
    CORRECCIÓN APLICADA: Constructor ahora acepta db_connection como parámetro
    para seguir patrón de inyección de dependencias consistente.
    """
    
    _instance = None
    _lock = threading.Lock()
    _config_cache = None
    
    def __new__(cls, db_connection=None):
        """
        Implementar patrón Singleton thread-safe.
        
        Args:
            db_connection: Conexión de base de datos (requerida para nueva instancia)
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, db_connection=None):
        """
        Inicializar el servicio de configuración de empresa.
        
        CORRECCIÓN CRÍTICA: Constructor ahora acepta db_connection como parámetro
        para seguir patrón de inyección de dependencias.
        
        Args:
            db_connection: Conexión a base de datos (requerida)
        """
        if not hasattr(self, '_initialized'):
            # CORRECCIÓN: Usar conexión proporcionada o obtener una nueva
            self.db = db_connection or get_database_connection()
            self._initialized = True
    
    def _limpiar_cache(self) -> None:
        """
        Limpiar el cache de configuración.
        Se ejecuta cuando se actualiza la configuración.
        """
        with self._lock:
            CompanyService._config_cache = None
    
    def _crear_configuracion_defecto(self) -> CompanyConfig:
        """
        Crear y guardar configuración por defecto en la base de datos.
        
        Returns:
            Configuración por defecto creada
        """
        config_defecto = CompanyConfig.crear_configuracion_defecto()
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            insert_query = """
                INSERT INTO company_config (
                    id, nombre, ruc, direccion, telefono, email,
                    itbms_rate, moneda, logo_path, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            values = (
                1,  # config_id siempre es 1 (Singleton)
                config_defecto.nombre,
                config_defecto.ruc,
                config_defecto.direccion,
                config_defecto.telefono,
                config_defecto.email,
                float(config_defecto.itbms_rate),
                config_defecto.moneda,
                config_defecto.logo_path,
                config_defecto.updated_at
            )
            
            cursor.execute(insert_query, values)
            conn.commit()
            
            return config_defecto
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def _row_to_company_config(self, row: tuple) -> CompanyConfig:
        """
        Convertir fila de base de datos a objeto CompanyConfig.
        
        Args:
            row: Tupla con datos de la base de datos
            
        Returns:
            Instancia de CompanyConfig
        """
        updated_at = None
        if row[9]:  # updated_at
            if isinstance(row[9], str):
                updated_at = datetime.fromisoformat(row[9].replace(' ', 'T'))
            else:
                updated_at = row[9]
        
        return CompanyConfig(
            config_id=row[0],
            nombre=row[1],
            ruc=row[2],
            direccion=row[3],
            telefono=row[4],
            email=row[5],
            itbms_rate=float(row[6]),
            moneda=row[7],
            logo_path=row[8],
            updated_at=updated_at
        )
    
    def obtener_configuracion(self) -> CompanyConfig:
        """
        Obtener la configuración de empresa actual.
        
        Si no existe configuración, crea una por defecto.
        Utiliza cache para mejorar rendimiento.
        
        Returns:
            Configuración de empresa
        """
        # Verificar cache primero
        if CompanyService._config_cache is not None:
            return CompanyService._config_cache
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Buscar configuración existente (siempre config_id = 1)
            query = """
                SELECT id, nombre, ruc, direccion, telefono, email,
                       itbms_rate, moneda, logo_path, updated_at
                FROM company_config WHERE id = 1
            """

            cursor.execute(query)
            row = cursor.fetchone()
            
            if row is None:
                # No existe configuración, crear por defecto
                config = self._crear_configuracion_defecto()
            else:
                # Convertir fila a objeto
                config = self._row_to_company_config(row)
            
            # Guardar en cache
            with self._lock:
                CompanyService._config_cache = config
            
            return config
            
        finally:
            cursor.close()
    
    def actualizar_configuracion(
        self,
        nombre: Optional[str] = None,
        ruc: Optional[str] = None,
        direccion: Optional[str] = None,
        telefono: Optional[str] = None,
        email: Optional[str] = None,
        itbms_rate: Optional[float] = None,
        moneda: Optional[str] = None,
        logo_path: Optional[str] = None
    ) -> CompanyConfig:
        """
        Actualizar la configuración de empresa.
        
        Args:
            nombre: Nuevo nombre (opcional)
            ruc: Nuevo RUC (opcional)
            direccion: Nueva dirección (opcional)
            telefono: Nuevo teléfono (opcional)
            email: Nuevo email (opcional)
            itbms_rate: Nueva tasa de ITBMS (opcional)
            moneda: Nueva moneda (opcional)
            logo_path: Nueva ruta de logo (opcional)
            
        Returns:
            Configuración actualizada
            
        Raises:
            ValueError: Si los datos actualizados no son válidos
        """
        # Obtener configuración actual
        config_actual = self.obtener_configuracion()
        
        # Crear nueva configuración con datos actualizados
        config_actualizada = CompanyConfig(
            config_id=1,
            nombre=nombre if nombre is not None else config_actual.nombre,
            ruc=ruc if ruc is not None else config_actual.ruc,
            direccion=direccion if direccion is not None else config_actual.direccion,
            telefono=telefono if telefono is not None else config_actual.telefono,
            email=email if email is not None else config_actual.email,
            itbms_rate=itbms_rate if itbms_rate is not None else float(config_actual.itbms_rate),
            moneda=moneda if moneda is not None else config_actual.moneda,
            logo_path=logo_path if logo_path is not None else config_actual.logo_path,
            updated_at=datetime.now()
        )
        
        # Validar nueva configuración
        errores = config_actualizada.validar_datos()
        if errores:
            raise ValueError(f"Los datos actualizados no son válidos: {', '.join(errores)}")
        
        # Actualizar en base de datos
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            update_query = """
                UPDATE company_config 
                SET nombre = ?, ruc = ?, direccion = ?, telefono = ?, email = ?,
                    itbms_rate = ?, moneda = ?, logo_path = ?, updated_at = ?
                WHERE id = 1
            """
            
            values = (
                config_actualizada.nombre,
                config_actualizada.ruc,
                config_actualizada.direccion,
                config_actualizada.telefono,
                config_actualizada.email,
                float(config_actualizada.itbms_rate),
                config_actualizada.moneda,
                config_actualizada.logo_path,
                config_actualizada.updated_at
            )
            
            cursor.execute(update_query, values)
            conn.commit()
            
            # Limpiar cache para forzar recarga
            self._limpiar_cache()
            
            return config_actualizada
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def calcular_itbms(self, subtotal: Decimal) -> Decimal:
        """
        Calcular ITBMS usando la tasa configurada.
        
        Args:
            subtotal: Monto base para calcular impuesto
            
        Returns:
            Monto del ITBMS calculado
        """
        config = self.obtener_configuracion()
        return config.calcular_itbms(subtotal)
    
    def calcular_total_con_itbms(self, subtotal: Decimal) -> Decimal:
        """
        Calcular total incluyendo ITBMS usando la tasa configurada.
        
        Args:
            subtotal: Monto base
            
        Returns:
            Total con ITBMS incluido
        """
        config = self.obtener_configuracion()
        return config.calcular_total_con_itbms(subtotal)
    
    def obtener_tasa_itbms(self) -> Decimal:
        """
        Obtener la tasa de ITBMS configurada.
        
        Returns:
            Tasa de ITBMS como Decimal
        """
        config = self.obtener_configuracion()
        return config.itbms_rate
    
    def formatear_monto(self, monto: Decimal) -> str:
        """
        Formatear un monto con la moneda configurada.
        
        Args:
            monto: Monto a formatear
            
        Returns:
            Monto formateado con símbolo de moneda
        """
        config = self.obtener_configuracion()
        return config.formatear_monto(monto)
    
    def obtener_simbolo_moneda(self) -> str:
        """
        Obtener el símbolo de la moneda configurada.
        
        Returns:
            Símbolo de moneda
        """
        config = self.obtener_configuracion()
        return config.obtener_simbolo_moneda()
    
    def obtener_encabezado_documentos(self) -> Dict[str, str]:
        """
        Obtener encabezado completo para documentos.
        
        Returns:
            Diccionario con datos de encabezado formateados
        """
        config = self.obtener_configuracion()
        return config.obtener_encabezado_completo()
    
    def obtener_datos_facturacion(self) -> Dict[str, Any]:
        """
        Obtener datos específicos para facturación.
        
        Returns:
            Diccionario con datos necesarios para facturación
        """
        config = self.obtener_configuracion()
        
        return {
            'nombre_empresa': config.nombre,
            'ruc': config.ruc,
            'direccion': config.direccion,
            'telefono': config.telefono,
            'email': config.email,
            'tasa_itbms': config.itbms_rate,
            'simbolo_moneda': config.obtener_simbolo_moneda(),
            'moneda': config.moneda
        }
    
    def validar_configuracion_actual(self) -> Tuple[bool, List[str]]:
        """
        Validar la configuración actual.
        
        Returns:
            Tupla con (es_valida, lista_de_errores)
        """
        config = self.obtener_configuracion()
        errores = config.validar_datos()
        es_valida = len(errores) == 0
        
        return es_valida, errores
    
    def actualizar_logo_path(self, logo_path: str) -> bool:
        """
        Actualizar solo la ruta del logo.
        
        Args:
            logo_path: Nueva ruta del logo
            
        Returns:
            True si se actualizó correctamente
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            update_query = """
                UPDATE company_config 
                SET logo_path = ?, updated_at = ?
                WHERE id = 1
            """
            
            cursor.execute(update_query, (logo_path, datetime.now()))
            conn.commit()
            
            # Limpiar cache
            self._limpiar_cache()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def eliminar_logo(self) -> bool:
        """
        Eliminar el logo configurado.
        
        Returns:
            True si se eliminó correctamente
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            update_query = """
                UPDATE company_config 
                SET logo_path = NULL, updated_at = ?
                WHERE id = 1
            """
            
            cursor.execute(update_query, (datetime.now(),))
            conn.commit()
            
            # Limpiar cache
            self._limpiar_cache()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def tiene_logo_configurado(self) -> bool:
        """
        Verificar si tiene logo configurado.
        
        Returns:
            True si hay logo configurado
        """
        config = self.obtener_configuracion()
        return config.tiene_logo()
    
    def restablecer_configuracion_defecto(self) -> CompanyConfig:
        """
        Restablecer la configuración a valores por defecto.
        
        Returns:
            Configuración restablecida
        """
        config_defecto = CompanyConfig.crear_configuracion_defecto()
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            update_query = """
                UPDATE company_config 
                SET nombre = ?, ruc = ?, direccion = ?, telefono = ?, email = ?,
                    itbms_rate = ?, moneda = ?, logo_path = ?, updated_at = ?
                WHERE id = 1
            """
            
            values = (
                config_defecto.nombre,
                config_defecto.ruc,
                config_defecto.direccion,
                config_defecto.telefono,
                config_defecto.email,
                float(config_defecto.itbms_rate),
                config_defecto.moneda,
                config_defecto.logo_path,
                datetime.now()
            )
            
            cursor.execute(update_query, values)
            conn.commit()
            
            # Limpiar cache
            self._limpiar_cache()
            
            return config_defecto
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def exportar_configuracion(self) -> Dict[str, Any]:
        """
        Exportar configuración actual a diccionario.
        
        Returns:
            Diccionario con la configuración completa
        """
        config = self.obtener_configuracion()
        return config.to_dict()
    
    def importar_configuracion(self, config_data: Dict[str, Any]) -> CompanyConfig:
        """
        Importar configuración desde diccionario.
        
        Args:
            config_data: Diccionario con datos de configuración
            
        Returns:
            Configuración importada
            
        Raises:
            ValueError: Si la configuración importada no es válida
        """
        # Crear configuración desde diccionario
        try:
            config_importada = CompanyConfig.from_dict(config_data)
            config_importada.id = 1  # Forzar ID = 1 (Singleton)
            config_importada.updated_at = datetime.now()
        except Exception as e:
            raise ValueError(f"Error al procesar configuración importada: {e}")
        
        # Validar configuración
        errores = config_importada.validar_datos()
        if errores:
            raise ValueError(f"La configuración importada no es válida: {', '.join(errores)}")
        
        # Actualizar en base de datos
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            update_query = """
                UPDATE company_config 
                SET nombre = ?, ruc = ?, direccion = ?, telefono = ?, email = ?,
                    itbms_rate = ?, moneda = ?, logo_path = ?, updated_at = ?
                WHERE id = 1
            """
            
            values = (
                config_importada.nombre,
                config_importada.ruc,
                config_importada.direccion,
                config_importada.telefono,
                config_importada.email,
                float(config_importada.itbms_rate),
                config_importada.moneda,
                config_importada.logo_path,
                config_importada.updated_at
            )
            
            cursor.execute(update_query, values)
            conn.commit()
            
            # Limpiar cache
            self._limpiar_cache()
            
            return config_importada
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def obtener_historial_cambios(self) -> Dict[str, Any]:
        """
        Obtener información sobre el último cambio de configuración.
        
        Returns:
            Diccionario con información del último cambio
        """
        config = self.obtener_configuracion()
        
        return {
            'ultima_actualizacion': config.updated_at,
            'fecha_formateada': config.updated_at.strftime("%d/%m/%Y %H:%M:%S"),
            'configuracion_actual': {
                'nombre': config.nombre,
                'ruc': config.ruc,
                'moneda': config.moneda,
                'tasa_itbms': float(config.itbms_rate)
            }
        }
    
    def verificar_configuracion_completa(self) -> Dict[str, Any]:
        """
        Verificar completitud de la configuración.
        
        Returns:
            Diccionario con estado de completitud
        """
        config = self.obtener_configuracion()
        
        campos_completos = {
            'nombre': bool(config.nombre and config.nombre.strip()),
            'ruc': bool(config.ruc and config.ruc.strip()),
            'direccion': bool(config.direccion and config.direccion.strip()),
            'telefono': bool(config.telefono and config.telefono.strip()),
            'email': bool(config.email and config.email.strip()),
            'logo': config.tiene_logo()
        }
        
        total_campos = len(campos_completos)
        campos_completos_count = sum(1 for completo in campos_completos.values() if completo)
        porcentaje_completitud = (campos_completos_count / total_campos) * 100
        
        return {
            'campos_completos': campos_completos,
            'total_campos': total_campos,
            'campos_completos_count': campos_completos_count,
            'porcentaje_completitud': round(porcentaje_completitud, 1),
            'configuracion_completa': porcentaje_completitud == 100
        }
