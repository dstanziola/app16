"""
ReportService - FASE 2: Sistema de Reportes

Servicio principal para generación de reportes del sistema de inventario.
Implementa 4 tipos de reportes principales:
1. Reporte de Inventario Actual
2. Reporte de Movimientos por período  
3. Reporte de Ventas con filtros
4. Reporte de Rentabilidad

Autor: Sistema de Inventario Copy Point S.A.
Metodología: TDD - Implementación basada en tests unitarios
"""

import sqlite3
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from src.db.database import DatabaseConnection


@dataclass
class ReportData:
    """Estructura estándar para datos de reportes"""
    data: List[Dict[str, Any]]
    summary: Dict[str, Any]
    generated_at: datetime
    filters_applied: Optional[Dict[str, Any]] = None
    totals: Optional[Dict[str, Any]] = None


class ReportService:
    """Servicio para generación de reportes del sistema de inventario"""
    
    def __init__(self, db_connection: DatabaseConnection):
        """
        Inicializa el servicio de reportes
        
        Args:
            db_connection: Instancia de DatabaseConnection
        """
        self.db_connection = db_connection
        self.logger = logging.getLogger(__name__)
        
    def _get_connection(self) -> sqlite3.Connection:
        """Obtiene conexión a la base de datos"""
        return self.db_connection.get_connection()
    
    def _validate_date_range(self, fecha_inicio: date, fecha_fin: date) -> None:
        """
        Valida que el rango de fechas sea válido
        
        Args:
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
            
        Raises:
            ValueError: Si el rango de fechas es inválido
        """
        if fecha_fin < fecha_inicio:
            raise ValueError("fecha_fin debe ser posterior a fecha_inicio")
    
    def generate_inventory_report(
        self, 
        categoria_id: Optional[int] = None,
        fecha_corte: Optional[date] = None,
        solo_con_stock: bool = False
    ) -> Dict[str, Any]:
        """
        Genera reporte de inventario actual
        
        Args:
            categoria_id: Filtrar por categoría específica
            fecha_corte: Fecha de corte para el inventario (default: hoy)
            solo_con_stock: Solo mostrar productos con stock > 0
            
        Returns:
            Dict con datos del reporte de inventario
        """
        if fecha_corte is None:
            fecha_corte = date.today()
            
        try:
            with self._get_connection() as conn:
                # Query base para inventario actual
                query = """
                SELECT 
                    p.id_producto,
                    p.nombre,
                    c.nombre as categoria,
                    p.stock,
                    p.costo,
                    (p.stock * p.costo) as valor_total,
                    p.activo
                FROM productos p
                JOIN categorias c ON p.id_categoria = c.id_categoria
                WHERE c.tipo = 'MATERIAL'
                """
                
                params = []
                filters_applied = {}
                
                # Aplicar filtros
                if categoria_id:
                    query += " AND p.id_categoria = ?"
                    params.append(categoria_id)
                    filters_applied['categoria_id'] = categoria_id
                
                if solo_con_stock:
                    query += " AND p.stock > 0"
                    filters_applied['solo_con_stock'] = True
                    
                query += " ORDER BY c.nombre, p.nombre"
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                # Convertir a lista de diccionarios
                data = []
                total_productos = 0
                total_valor = Decimal('0')
                productos_con_stock = 0
                
                for row in rows:
                    item = {
                        'id_producto': row['id_producto'],
                        'nombre': row['nombre'],
                        'categoria': row['categoria'],
                        'stock_actual': row['stock'],
                        'costo_unitario': float(row['costo']),
                        'valor_total': float(row['valor_total']),
                        'stock_minimo': 5  # TODO: Implementar stock mínimo configurable
                    }
                    data.append(item)
                    
                    total_productos += 1
                    total_valor += Decimal(str(row['valor_total']))
                    if row['stock'] > 0:
                        productos_con_stock += 1
                
                # Preparar resumen
                summary = {
                    'total_productos': total_productos,
                    'productos_con_stock': productos_con_stock,
                    'productos_sin_stock': total_productos - productos_con_stock,
                    'valor_total_inventario': float(total_valor),
                    'fecha_corte': fecha_corte.isoformat()
                }
                
                return {
                    'data': data,
                    'summary': summary,
                    'generated_at': datetime.now(),
                    'filters_applied': filters_applied
                }
                
        except Exception as e:
            self.logger.error(f"Error generando reporte de inventario: {e}")
            raise
    
    def generate_movements_report(
        self,
        fecha_inicio: date,
        fecha_fin: date,
        tipo_movimiento: Optional[str] = None,
        categoria_id: Optional[int] = None,
        producto_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Genera reporte de movimientos por período
        
        Args:
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
            tipo_movimiento: Filtrar por tipo ('ENTRADA', 'VENTA', 'AJUSTE')
            categoria_id: Filtrar por categoría
            producto_id: Filtrar por producto específico
            
        Returns:
            Dict con datos del reporte de movimientos
        """
        self._validate_date_range(fecha_inicio, fecha_fin)
        
        try:
            with self._get_connection() as conn:
                # Query base para movimientos
                query = """
                SELECT 
                    m.id_movimiento,
                    m.fecha_movimiento,
                    m.tipo_movimiento,
                    p.nombre as producto_nombre,
                    c.nombre as categoria_nombre,
                    m.cantidad,
                    m.responsable,
                    m.observaciones,
                    p.costo,
                    (ABS(m.cantidad) * p.costo) as valor_movimiento
                FROM movimientos m
                JOIN productos p ON m.id_producto = p.id_producto
                JOIN categorias c ON p.id_categoria = c.id_categoria
                WHERE DATE(m.fecha_movimiento) >= ? AND DATE(m.fecha_movimiento) <= ?
                """
                
                params = [fecha_inicio.isoformat(), fecha_fin.isoformat()]
                filters_applied = {
                    'fecha_inicio': fecha_inicio.isoformat(),
                    'fecha_fin': fecha_fin.isoformat()
                }
                
                # Aplicar filtros adicionales
                if tipo_movimiento:
                    query += " AND m.tipo_movimiento = ?"
                    params.append(tipo_movimiento)
                    filters_applied['tipo_movimiento'] = tipo_movimiento
                
                if categoria_id:
                    query += " AND p.id_categoria = ?"
                    params.append(categoria_id)
                    filters_applied['categoria_id'] = categoria_id
                
                if producto_id:
                    query += " AND p.id_producto = ?"
                    params.append(producto_id)
                    filters_applied['producto_id'] = producto_id
                    
                query += " ORDER BY m.fecha_movimiento DESC"
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                # Convertir a lista de diccionarios
                data = []
                total_movimientos = 0
                entradas = 0
                salidas = 0
                valor_total_movimientos = Decimal('0')
                
                for row in rows:
                    item = {
                        'id_movimiento': row['id_movimiento'],
                        'fecha_movimiento': row['fecha_movimiento'],
                        'tipo_movimiento': row['tipo_movimiento'],
                        'producto_nombre': row['producto_nombre'],
                        'categoria_nombre': row['categoria_nombre'],
                        'cantidad': row['cantidad'],
                        'responsable': row['responsable'],
                        'observaciones': row['observaciones'] or '',
                        'valor_movimiento': float(row['valor_movimiento'])
                    }
                    data.append(item)
                    
                    total_movimientos += 1
                    valor_total_movimientos += Decimal(str(row['valor_movimiento']))
                    
                    if row['cantidad'] > 0:
                        entradas += abs(row['cantidad'])
                    else:
                        salidas += abs(row['cantidad'])
                
                # Preparar resumen
                summary = {
                    'total_movimientos': total_movimientos,
                    'total_entradas': entradas,
                    'total_salidas': salidas,
                    'valor_total_movimientos': float(valor_total_movimientos),
                    'periodo': f"{fecha_inicio.isoformat()} - {fecha_fin.isoformat()}"
                }
                
                return {
                    'data': data,
                    'summary': summary,
                    'generated_at': datetime.now(),
                    'period': summary['periodo'],
                    'filters_applied': filters_applied
                }
                
        except Exception as e:
            self.logger.error(f"Error generando reporte de movimientos: {e}")
            raise
    
    def generate_sales_report(
        self,
        fecha_inicio: date,
        fecha_fin: date,
        group_by: Optional[str] = None,
        include_details: bool = True,
        cliente_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Genera reporte de ventas con filtros
        
        Args:
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
            group_by: Agrupar por período ('day', 'month', 'year')
            include_details: Incluir detalles de productos vendidos
            cliente_id: Filtrar por cliente específico
            
        Returns:
            Dict con datos del reporte de ventas
        """
        self._validate_date_range(fecha_inicio, fecha_fin)
        
        try:
            with self._get_connection() as conn:
                # Query base para ventas
                query = """
                SELECT 
                    v.id_venta,
                    v.fecha_venta,
                    COALESCE(c.nombre, 'Cliente General') as cliente_nombre,
                    v.subtotal,
                    v.impuestos,
                    v.total,
                    v.responsable
                FROM ventas v
                LEFT JOIN clientes c ON v.id_cliente = c.id_cliente
                WHERE DATE(v.fecha_venta) >= ? AND DATE(v.fecha_venta) <= ?
                """
                
                params = [fecha_inicio.isoformat(), fecha_fin.isoformat()]
                filters_applied = {
                    'fecha_inicio': fecha_inicio.isoformat(),
                    'fecha_fin': fecha_fin.isoformat()
                }
                
                if cliente_id:
                    query += " AND v.id_cliente = ?"
                    params.append(cliente_id)
                    filters_applied['cliente_id'] = cliente_id
                    
                query += " ORDER BY v.fecha_venta DESC"
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                # Convertir a lista de diccionarios
                
                data = []
                total_ventas = 0
                subtotal_acumulado = Decimal('0')
                impuestos_acumulados = Decimal('0')
                total_acumulado = Decimal('0')
                
                for row in rows:
                    item = {
                        'id_venta': row['id_venta'],
                        'fecha_venta': row['fecha_venta'],
                        'cliente_nombre': row['cliente_nombre'],
                        'subtotal': float(row['subtotal']),
                        'impuestos': float(row['impuestos']),
                        'total': float(row['total']),
                        'responsable': row['responsable']
                    }
                    data.append(item)
                    
                    total_ventas += 1
                    # subtotal_acumulado += row['subtotal']
                    # impuestos_acumulados += row['impuestos']
                    # total_acumulado += row['total']

                    subtotal_acumulado   += Decimal(str(row['subtotal']))
                    impuestos_acumulados += Decimal(str(row['impuestos']))
                    total_acumulado      += Decimal(str(row['total']))

                # Preparar totales y resumen
                totals = {
                    'subtotal_total': float(subtotal_acumulado),
                    'impuestos_total': float(impuestos_acumulados),
                    'gran_total': float(total_acumulado)
                }
                
                summary = {
                    'total_ventas': total_ventas,
                    'promedio_venta': float(total_acumulado / total_ventas) if total_ventas > 0 else 0,
                    'periodo': f"{fecha_inicio.isoformat()} - {fecha_fin.isoformat()}"
                }
                
                result = {
                    'data': data,
                    'summary': summary,
                    'totals': totals,
                    'generated_at': datetime.now(),
                    'filters_applied': filters_applied
                }
                
                # Agregar agrupación si se solicita
                if group_by and not include_details:
                    result['grouped_data'] = self._group_sales_data(data, group_by)
                
                return result
                
        except Exception as e:
            self.logger.error(f"Error generando reporte de ventas: {e}")
            raise
    
    def _group_sales_data(self, data: List[Dict], group_by: str) -> Dict[str, Any]:
        """Agrupa datos de ventas por período especificado"""
        # Implementación básica de agrupación
        grouped = {}
        
        for sale in data:
            # Extraer fecha y agrupar según criterio
            fecha_venta = datetime.fromisoformat(sale['fecha_venta'].replace('Z', '+00:00'))
            
            if group_by == 'day':
                key = fecha_venta.date().isoformat()
            elif group_by == 'month':
                key = f"{fecha_venta.year}-{fecha_venta.month:02d}"
            elif group_by == 'year':
                key = str(fecha_venta.year)
            else:
                key = fecha_venta.date().isoformat()
            
            if key not in grouped:
                grouped[key] = {
                    'periodo': key,
                    'total_ventas': 0,
                    'subtotal': 0,
                    'impuestos': 0,
                    'total': 0
                }
            
            grouped[key]['total_ventas'] += 1
            grouped[key]['subtotal'] += sale['subtotal']
            grouped[key]['impuestos'] += sale['impuestos']
            grouped[key]['total'] += sale['total']
        
        return grouped
    
    def generate_profitability_report(
        self,
        fecha_inicio: date,
        fecha_fin: date,
        categoria_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Genera reporte de rentabilidad por período
        
        Args:
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
            categoria_id: Filtrar por categoría específica
            
        Returns:
            Dict con datos del reporte de rentabilidad
        """
        self._validate_date_range(fecha_inicio, fecha_fin)
        
        try:
            with self._get_connection() as conn:
                # Query para calcular rentabilidad por producto
                query = """
                SELECT 
                    p.id_producto,
                    p.nombre as producto_nombre,
                    c.nombre as categoria_nombre,
                    SUM(ABS(m.cantidad)) as cantidad_vendida,
                    SUM(ABS(m.cantidad) * p.precio) as ingresos_brutos,
                    SUM(ABS(m.cantidad) * p.costo) as costo_total,
                    (SUM(ABS(m.cantidad) * p.precio) - SUM(ABS(m.cantidad) * p.costo)) as ganancia_bruta,
                    p.precio,
                    p.costo
                FROM movimientos m
                JOIN productos p ON m.id_producto = p.id_producto
                JOIN categorias c ON p.id_categoria = c.id_categoria
                WHERE m.tipo_movimiento = 'VENTA'
                AND DATE(m.fecha_movimiento) >= ? AND DATE(m.fecha_movimiento) <= ?
                """
                
                params = [fecha_inicio.isoformat(), fecha_fin.isoformat()]
                filters_applied = {
                    'fecha_inicio': fecha_inicio.isoformat(),
                    'fecha_fin': fecha_fin.isoformat()
                }
                
                if categoria_id:
                    query += " AND p.id_categoria = ?"
                    params.append(categoria_id)
                    filters_applied['categoria_id'] = categoria_id
                
                query += " GROUP BY p.id_producto ORDER BY ganancia_bruta DESC"
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                # Convertir a lista de diccionarios
                data = []
                total_ingresos = Decimal('0')
                total_costos = Decimal('0')
                total_ganancia = Decimal('0')
                
                for row in rows:
                    ingresos = Decimal(str(row['ingresos_brutos']))
                    costos = Decimal(str(row['costo_total']))
                    ganancia = Decimal(str(row['ganancia_bruta']))
                    
                    # Calcular margen de ganancia
                    margen_porcentaje = 0
                    if ingresos > 0:
                        margen_porcentaje = float((ganancia / ingresos) * 100)
                    
                    item = {
                        'producto_id': row['id_producto'],
                        'producto_nombre': row['producto_nombre'],
                        'categoria_nombre': row['categoria_nombre'],
                        'cantidad_vendida': row['cantidad_vendida'],
                        'ingresos_brutos': float(ingresos),
                        'costo_total': float(costos),
                        'ganancia_bruta': float(ganancia),
                        'margen_porcentaje': round(margen_porcentaje, 2)
                    }
                    data.append(item)
                    
                    total_ingresos += ingresos
                    total_costos += costos
                    total_ganancia += ganancia
                
                # Calcular margen total
                margen_total_porcentaje = 0
                if total_ingresos > 0:
                    margen_total_porcentaje = float((total_ganancia / total_ingresos) * 100)
                
                # Preparar totales y resumen
                totals = {
                    'total_ingresos': float(total_ingresos),
                    'total_costos': float(total_costos),
                    'total_ganancia': float(total_ganancia),
                    'margen_total_porcentaje': round(margen_total_porcentaje, 2)
                }
                
                summary = {
                    'productos_analizados': len(data),
                    'periodo': f"{fecha_inicio.isoformat()} - {fecha_fin.isoformat()}"
                }
                
                return {
                    'data': data,
                    'summary': summary,
                    'totals': totals,
                    'generated_at': datetime.now(),
                    'filters_applied': filters_applied
                }
                
        except Exception as e:
            self.logger.error(f"Error generando reporte de rentabilidad: {e}")
            raise
    
    def generate_low_stock_report(
        self,
        categoria_id: Optional[int] = None,
        threshold_multiplier: float = 1.0,
        include_zero_stock: bool = True
    ) -> Dict[str, Any]:
        """
        Genera reporte de productos con stock bajo configurable
        
        Args:
            categoria_id: Filtrar por categoría específica
            threshold_multiplier: Multiplicador del stock mínimo (ej: 1.5 = 150% del mínimo)
            include_zero_stock: Incluir productos agotados
            
        Returns:
            Dict con productos que requieren reposición
        """
        try:
            with self._get_connection() as conn:
                query = """
                SELECT 
                    p.id_producto,
                    p.nombre as producto_nombre,
                    c.nombre as categoria_nombre,
                    p.stock as stock_actual,
                    p.stock_minimo,
                    p.costo,
                    p.precio,
                    CASE 
                        WHEN p.stock_minimo > 0 THEN (p.stock_minimo * 2) - p.stock
                        ELSE 10 - p.stock
                    END as cantidad_sugerida,
                    CASE 
                        WHEN p.stock = 0 THEN 'AGOTADO'
                        WHEN p.stock < (p.stock_minimo * 0.5) THEN 'CRÍTICO'
                        ELSE 'BAJO'
                    END as criticidad
                FROM productos p
                JOIN categorias c ON p.id_categoria = c.id_categoria
                WHERE p.activo = 1 
                AND p.stock < (p.stock_minimo * ?)
                """
                
                params = [threshold_multiplier]
                filters_applied = {'threshold_multiplier': threshold_multiplier}
                
                if not include_zero_stock:
                    query += " AND p.stock > 0"
                    filters_applied['include_zero_stock'] = False
                
                if categoria_id:
                    query += " AND p.id_categoria = ?"
                    params.append(categoria_id)
                    filters_applied['categoria_id'] = categoria_id
                
                query += " ORDER BY criticidad DESC, p.stock ASC"
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                # Procesar datos
                data = []
                productos_agotados = 0
                valor_reposicion_total = Decimal('0')
                
                for row in rows:
                    cantidad_sugerida = max(0, row['cantidad_sugerida']) if row['cantidad_sugerida'] else 10
                    valor_reposicion = cantidad_sugerida * Decimal(str(row['costo']))
                    
                    item = {
                        'producto_id': row['id_producto'],
                        'producto_nombre': row['producto_nombre'],
                        'categoria_nombre': row['categoria_nombre'],
                        'stock_actual': row['stock_actual'],
                        'stock_minimo': row['stock_minimo'],
                        'cantidad_sugerida': cantidad_sugerida,
                        'costo_unitario': float(row['costo']),
                        'valor_reposicion': float(valor_reposicion),
                        'criticidad': row['criticidad']
                    }
                    data.append(item)
                    
                    if row['stock_actual'] == 0:
                        productos_agotados += 1
                    
                    valor_reposicion_total += valor_reposicion
                
                summary = {
                    'productos_bajo_minimo': len(data),
                    'productos_agotados': productos_agotados,
                    'valor_reposicion_sugerida': float(valor_reposicion_total),
                    'threshold_aplicado': threshold_multiplier
                }
                
                return {
                    'data': data,
                    'summary': summary,
                    'generated_at': datetime.now(),
                    'filters_applied': filters_applied
                }
                
        except Exception as e:
            self.logger.error(f"Error generando reporte de stock bajo: {e}")
            raise
    
    def generate_top_selling_products_report(
        self,
        fecha_inicio: date,
        fecha_fin: date,
        top_n: int = 10,
        order_by: str = 'quantity',
        categoria_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Genera reporte de productos más vendidos
        
        Args:
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
            top_n: Número de productos a incluir
            order_by: Criterio de ordenamiento ('quantity' o 'revenue')
            categoria_id: Filtrar por categoría específica
            
        Returns:
            Dict con productos más vendidos
        """
        self._validate_date_range(fecha_inicio, fecha_fin)
        
        try:
            with self._get_connection() as conn:
                # Ordenamiento dinámico
                order_field = "cantidad_vendida" if order_by == 'quantity' else "ingresos_generados"
                
                query = f"""
                SELECT 
                    p.id_producto,
                    p.nombre as producto_nombre,
                    c.nombre as categoria_nombre,
                    SUM(ABS(m.cantidad)) as cantidad_vendida,
                    SUM(ABS(m.cantidad) * p.precio) as ingresos_generados,
                    SUM(ABS(m.cantidad) * p.costo) as costo_total,
                    (SUM(ABS(m.cantidad) * p.precio) - SUM(ABS(m.cantidad) * p.costo)) as ganancia_bruta,
                    p.precio as precio_unitario,
                    COUNT(DISTINCT DATE(m.fecha_movimiento)) as dias_con_ventas
                FROM movimientos m
                JOIN productos p ON m.id_producto = p.id_producto
                JOIN categorias c ON p.id_categoria = c.id_categoria
                WHERE m.tipo_movimiento = 'VENTA'
                AND DATE(m.fecha_movimiento) >= ? AND DATE(m.fecha_movimiento) <= ?
                """
                
                params = [fecha_inicio.isoformat(), fecha_fin.isoformat()]
                filters_applied = {
                    'fecha_inicio': fecha_inicio.isoformat(),
                    'fecha_fin': fecha_fin.isoformat(),
                    'order_by': order_by,
                    'top_n': top_n
                }
                
                if categoria_id:
                    query += " AND p.id_categoria = ?"
                    params.append(categoria_id)
                    filters_applied['categoria_id'] = categoria_id
                
                query += f" GROUP BY p.id_producto ORDER BY {order_field} DESC LIMIT ?"
                params.append(top_n)
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                # Procesar datos
                data = []
                total_ingresos = Decimal('0')
                total_cantidad = 0
                
                for row in rows:
                    ingresos = Decimal(str(row['ingresos_generados']))
                    ganancia = Decimal(str(row['ganancia_bruta']))
                    
                    # Calcular margen de ganancia
                    margen_porcentaje = 0
                    if ingresos > 0:
                        margen_porcentaje = float((ganancia / ingresos) * 100)
                    
                    item = {
                        'producto_id': row['id_producto'],
                        'producto_nombre': row['producto_nombre'],
                        'categoria_nombre': row['categoria_nombre'],
                        'cantidad_vendida': row['cantidad_vendida'],
                        'ingresos_generados': float(ingresos),
                        'costo_total': float(row['costo_total']),
                        'ganancia_bruta': float(ganancia),
                        'margen_porcentaje': round(margen_porcentaje, 2),
                        'precio_unitario': float(row['precio_unitario']),
                        'dias_con_ventas': row['dias_con_ventas'],
                        'promedio_diario': round(row['cantidad_vendida'] / max(1, row['dias_con_ventas']), 2)
                    }
                    data.append(item)
                    
                    total_ingresos += ingresos
                    total_cantidad += row['cantidad_vendida']
                
                summary = {
                    'productos_analizados': len(data),
                    'total_cantidad_vendida': total_cantidad,
                    'total_ingresos_generados': float(total_ingresos),
                    'periodo': f"{fecha_inicio.isoformat()} - {fecha_fin.isoformat()}"
                }
                
                return {
                    'data': data,
                    'summary': summary,
                    'period': summary['periodo'],
                    'generated_at': datetime.now(),
                    'filters_applied': filters_applied
                }
                
        except Exception as e:
            self.logger.error(f"Error generando reporte productos más vendidos: {e}")
            raise
    
    def generate_trends_analysis_report(
        self,
        fecha_inicio: date,
        fecha_fin: date,
        period_type: str = 'month',
        producto_id: Optional[int] = None,
        categoria_id: Optional[int] = None,
        predict_periods: int = 0
    ) -> Dict[str, Any]:
        """
        Genera análisis de tendencias de ventas
        
        Args:
            fecha_inicio: Fecha de inicio del análisis
            fecha_fin: Fecha de fin del análisis
            period_type: Tipo de período ('day', 'week', 'month', 'year')
            producto_id: Analizar producto específico
            categoria_id: Analizar categoría específica
            predict_periods: Número de períodos futuros a predecir
            
        Returns:
            Dict con análisis de tendencias y predicciones
        """
        self._validate_date_range(fecha_inicio, fecha_fin)
        
        try:
            with self._get_connection() as conn:
                # Formateo de fecha según tipo de período
                if period_type == 'day':
                    date_format = "DATE(m.fecha_movimiento)"
                    date_group = "DATE(m.fecha_movimiento)"
                elif period_type == 'week':
                    date_format = "strftime('%Y-W%W', m.fecha_movimiento)"
                    date_group = "strftime('%Y-W%W', m.fecha_movimiento)"
                elif period_type == 'month':
                    date_format = "strftime('%Y-%m', m.fecha_movimiento)"
                    date_group = "strftime('%Y-%m', m.fecha_movimiento)"
                elif period_type == 'year':
                    date_format = "strftime('%Y', m.fecha_movimiento)"
                    date_group = "strftime('%Y', m.fecha_movimiento)"
                else:
                    raise ValueError(f"Tipo de período no válido: {period_type}")
                
                query = f"""
                SELECT 
                    {date_format} as periodo,
                    SUM(ABS(m.cantidad)) as cantidad_vendida,
                    SUM(ABS(m.cantidad) * p.precio) as ingresos_generados,
                    COUNT(DISTINCT m.id_movimiento) as numero_transacciones,
                    AVG(ABS(m.cantidad)) as promedio_cantidad_por_transaccion
                FROM movimientos m
                JOIN productos p ON m.id_producto = p.id_producto
                WHERE m.tipo_movimiento = 'VENTA'
                AND DATE(m.fecha_movimiento) >= ? AND DATE(m.fecha_movimiento) <= ?
                """
                
                params = [fecha_inicio.isoformat(), fecha_fin.isoformat()]
                filters_applied = {
                    'fecha_inicio': fecha_inicio.isoformat(),
                    'fecha_fin': fecha_fin.isoformat(),
                    'period_type': period_type
                }
                
                if producto_id:
                    query += " AND m.id_producto = ?"
                    params.append(producto_id)
                    filters_applied['producto_id'] = producto_id
                
                if categoria_id:
                    query += " AND p.id_categoria = ?"
                    params.append(categoria_id)
                    filters_applied['categoria_id'] = categoria_id
                
                query += f" GROUP BY {date_group} ORDER BY periodo"
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                # Procesar datos temporales
                data = []
                valores_cantidad = []
                
                for i, row in enumerate(rows):
                    item = {
                        'periodo': row['periodo'],
                        'cantidad_vendida': row['cantidad_vendida'],
                        'ingresos_generados': float(row['ingresos_generados']),
                        'numero_transacciones': row['numero_transacciones'],
                        'promedio_cantidad_transaccion': round(row['promedio_cantidad_por_transaccion'], 2),
                        'index': i
                    }
                    data.append(item)
                    valores_cantidad.append(row['cantidad_vendida'])
                
                # Análisis de tendencias
                trends = self._analyze_trend(valores_cantidad)
                
                # Predicciones si se solicitan
                predictions = []
                if predict_periods > 0 and len(data) >= 2:
                    predictions = self._generate_predictions(data, predict_periods, period_type)
                
                summary = {
                    'periodos_analizados': len(data),
                    'total_cantidad_vendida': sum(valores_cantidad),
                    'promedio_por_periodo': round(sum(valores_cantidad) / len(valores_cantidad), 2) if valores_cantidad else 0
                }
                
                return {
                    'data': data,
                    'trends': trends,
                    'predictions': predictions,
                    'summary': summary,
                    'generated_at': datetime.now(),
                    'filters_applied': filters_applied
                }
                
        except Exception as e:
            self.logger.error(f"Error generando análisis de tendencias: {e}")
            raise
    
    def _analyze_trend(self, values: List[int]) -> Dict[str, Any]:
        """Analiza tendencia de una serie de valores"""
        if len(values) < 2:
            return {'direction': 'INSUFICIENTE_DATA', 'growth_rate': 0, 'correlation_coefficient': 0}
        
        # Cálculo simple de tendencia
        n = len(values)
        x_values = list(range(n))
        
        # Correlación simple
        mean_x = sum(x_values) / n
        mean_y = sum(values) / n
        
        numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, values))
        denominator_x = sum((x - mean_x) ** 2 for x in x_values)
        denominator_y = sum((y - mean_y) ** 2 for y in values)
        
        if denominator_x == 0 or denominator_y == 0:
            correlation = 0
        else:
            correlation = numerator / (denominator_x * denominator_y) ** 0.5
        
        # Tasa de crecimiento promedio
        if values[0] != 0:
            growth_rate = ((values[-1] / values[0]) ** (1 / (n - 1)) - 1) * 100
        else:
            growth_rate = 0
        
        # Dirección de tendencia
        if correlation > 0.3:
            direction = 'CRECIENTE'
        elif correlation < -0.3:
            direction = 'DECRECIENTE'
        else:
            direction = 'ESTABLE'
        
        return {
            'direction': direction,
            'growth_rate': round(growth_rate, 2),
            'correlation_coefficient': round(correlation, 3)
        }
    
    def _generate_predictions(self, data: List[Dict], periods: int, period_type: str) -> List[Dict]:
        """Genera predicciones basadas en tendencia histórica"""
        predictions = []
        
        if len(data) < 2:
            return predictions
        
        # Predicción lineal simple
        values = [item['cantidad_vendida'] for item in data]
        n = len(values)
        
        # Calcular pendiente promedio
        if n >= 2:
            slope = (values[-1] - values[0]) / (n - 1)
        else:
            slope = 0
        
        # Generar predicciones
        last_value = values[-1]
        last_period = data[-1]['periodo']
        
        for i in range(1, periods + 1):
            predicted_value = max(0, last_value + (slope * i))
            
            # Calcular próximo período
            next_period = self._get_next_period(last_period, i, period_type)
            
            predictions.append({
                'periodo': next_period,
                'cantidad_predicha': round(predicted_value),
                'confianza': 'MEDIA' if i <= 2 else 'BAJA'
            })
        
        return predictions
    
    def _get_next_period(self, last_period: str, increment: int, period_type: str) -> str:
        """Calcula el siguiente período basado en el tipo"""
        if period_type == 'month':
            # Formato: YYYY-MM
            year, month = map(int, last_period.split('-'))
            for _ in range(increment):
                month += 1
                if month > 12:
                    month = 1
                    year += 1
            return f"{year}-{month:02d}"
        
        # Para otros tipos, implementación básica
        return f"{last_period}+{increment}"
    
    def generate_detailed_movements_report(
        self,
        fecha_inicio: date,
        fecha_fin: date,
        include_sales_details: bool = True,
        include_lot_tracking: bool = False,
        tipo_movimiento: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Genera reporte detallado de movimientos con información expandida
        
        Args:
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
            include_sales_details: Incluir detalles de ventas relacionadas
            include_lot_tracking: Incluir seguimiento de lotes
            tipo_movimiento: Filtrar por tipo específico
            
        Returns:
            Dict con movimientos detallados y análisis
        """
        self._validate_date_range(fecha_inicio, fecha_fin)
        
        try:
            with self._get_connection() as conn:
                # Query base expandida (ajustada al schema real)
                query = """
                SELECT 
                    m.id_movimiento,
                    m.fecha_movimiento,
                    m.tipo_movimiento,
                    m.cantidad,
                    m.responsable,
                    m.observaciones,
                    COALESCE(m.id_venta, '') as id_venta_relacionada,
                    p.id_producto,
                    p.nombre as producto_nombre,
                    c.nombre as categoria_nombre,
                    p.precio,
                    p.costo,
                    (ABS(m.cantidad) * COALESCE(m.costo_unitario, p.costo)) as valor_costo,
                    (ABS(m.cantidad) * p.precio) as valor_precio
                FROM movimientos m
                JOIN productos p ON m.id_producto = p.id_producto
                JOIN categorias c ON p.id_categoria = c.id_categoria
                WHERE DATE(m.fecha_movimiento) >= ? AND DATE(m.fecha_movimiento) <= ?
                """
                
                params = [fecha_inicio.isoformat(), fecha_fin.isoformat()]
                filters_applied = {
                    'fecha_inicio': fecha_inicio.isoformat(),
                    'fecha_fin': fecha_fin.isoformat(),
                    'include_sales_details': include_sales_details,
                    'include_lot_tracking': include_lot_tracking
                }
                
                if tipo_movimiento:
                    query += " AND m.tipo_movimiento = ?"
                    params.append(tipo_movimiento)
                    filters_applied['tipo_movimiento'] = tipo_movimiento
                
                query += " ORDER BY m.fecha_movimiento DESC"
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                # Procesar movimientos detallados
                data = []
                balance_entradas = 0
                balance_salidas = 0
                lot_tracking = {}
                
                for row in rows:
                    # Información básica del movimiento (ajustada al schema real)
                    item = {
                        'id_movimiento': row['id_movimiento'],
                        'fecha_movimiento': row['fecha_movimiento'],
                        'tipo_movimiento': row['tipo_movimiento'],
                        'producto_id': row['id_producto'],
                        'producto_nombre': row['producto_nombre'],
                        'categoria_nombre': row['categoria_nombre'],
                        'cantidad': row['cantidad'],
                        'responsable': row['responsable'],
                        'observaciones': row['observaciones'] or '',
                        'id_venta_relacionada': row['id_venta_relacionada'] or '',
                        'valor_costo': float(row['valor_costo']),
                        'valor_precio': float(row['valor_precio'])
                    }
                    
                    # Detalles de venta si se solicita
                    if include_sales_details and row['tipo_movimiento'] == 'VENTA' and row['id_venta_relacionada']:
                        item['venta_detalle'] = self._get_sale_details(conn, str(row['id_venta_relacionada']))
                    
                    data.append(item)
                    
                    # Calcular balance
                    if row['cantidad'] > 0:
                        balance_entradas += row['cantidad']
                    else:
                        balance_salidas += abs(row['cantidad'])
                    
                    # Tracking por tipo de movimiento (en lugar de lotes)
                    if include_lot_tracking:
                        mov_type = row['tipo_movimiento']
                        if mov_type not in lot_tracking:
                            lot_tracking[mov_type] = {
                                'total_entrada': 0,
                                'total_salida': 0,
                                'balance': 0,
                                'movimientos': []
                            }
                        
                        if row['cantidad'] > 0:
                            lot_tracking[mov_type]['total_entrada'] += row['cantidad']
                        else:
                            lot_tracking[mov_type]['total_salida'] += abs(row['cantidad'])
                        
                        lot_tracking[mov_type]['balance'] = lot_tracking[mov_type]['total_entrada'] - lot_tracking[mov_type]['total_salida']
                        lot_tracking[mov_type]['movimientos'].append(row['id_movimiento'])
                
                # Resumen de balance
                balance_summary = {
                    'total_entradas': balance_entradas,
                    'total_salidas': balance_salidas,
                    'balance_neto': balance_entradas - balance_salidas,
                    'total_movimientos': len(data)
                }
                
                summary = {
                    'movimientos_analizados': len(data),
                    'periodo': f"{fecha_inicio.isoformat()} - {fecha_fin.isoformat()}"
                }
                
                result = {
                    'data': data,
                    'balance_summary': balance_summary,
                    'summary': summary,
                    'generated_at': datetime.now(),
                    'filters_applied': filters_applied
                }
                
                if include_lot_tracking:
                    result['lot_tracking'] = lot_tracking
                
                return result
                
        except Exception as e:
            self.logger.error(f"Error generando reporte movimientos detallados: {e}")
            raise
    
    def _get_sale_details(self, conn: sqlite3.Connection, id_venta: str) -> Optional[Dict[str, Any]]:
        """Obtiene detalles de venta por ID de venta"""
        try:
            # Buscar venta por ID
            cursor = conn.execute("""
                SELECT id_venta, numero_factura, fecha_venta, total, responsable
                FROM ventas 
                WHERE id_venta = ?
            """, [id_venta])
            
            row = cursor.fetchone()
            if row:
                return {
                    'id_venta': row['id_venta'],
                    'numero_factura': row['numero_factura'],
                    'fecha_venta': row['fecha_venta'],
                    'total_factura': float(row['total']),
                    'responsable_venta': row['responsable']
                }
            
            return None
            
        except Exception:
            # Si hay error, retornar None
            return None
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas resumen generales del sistema
        
        Returns:
            Dict con estadísticas principales
        """
        try:
            with self._get_connection() as conn:
                stats = {}
                
                # Total de productos
                cursor = conn.execute("SELECT COUNT(*) as total FROM productos WHERE activo = 1")
                stats['total_productos'] = cursor.fetchone()['total']
                
                # Productos con stock
                cursor = conn.execute("SELECT COUNT(*) as total FROM productos WHERE activo = 1 AND stock > 0")
                stats['productos_con_stock'] = cursor.fetchone()['total']
                
                # Valor total del inventario
                cursor = conn.execute("""
                    SELECT SUM(stock * costo) as valor_total 
                    FROM productos p
                    JOIN categorias c ON p.id_categoria = c.id_categoria
                    WHERE p.activo = 1 AND c.tipo = 'MATERIAL'
                """)
                valor_total = cursor.fetchone()['valor_total']
                stats['valor_total_inventario'] = float(valor_total) if valor_total else 0
                
                # Ventas del mes actual
                primer_dia_mes = date.today().replace(day=1)
                cursor = conn.execute("""
                    SELECT COUNT(*) as total, SUM(total) as suma
                    FROM ventas 
                    WHERE DATE(fecha_venta) >= ?
                """, [primer_dia_mes.isoformat()])
                row = cursor.fetchone()
                stats['ventas_mes_actual'] = row['total']
                stats['ingresos_mes_actual'] = float(row['suma']) if row['suma'] else 0
                
                # Productos más vendidos (usando nuevo método)
                try:
                    top_products = self.generate_top_selling_products_report(
                        fecha_inicio=primer_dia_mes,
                        fecha_fin=date.today(),
                        top_n=5
                    )
                    stats['productos_mas_vendidos'] = top_products['data']
                except:
                    stats['productos_mas_vendidos'] = []
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas resumen: {e}")
            raise
    
    def export_to_pdf(
        self, 
        report_data: Dict[str, Any], 
        pdf_path: str, 
        report_type: str,
        company_info: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Exporta reporte a PDF usando reportlab
        
        Args:
            report_data: Datos del reporte
            pdf_path: Ruta donde guardar el PDF
            report_type: Tipo de reporte ('inventory', 'movements', 'sales', 'profitability')
            company_info: Información de la empresa para el encabezado
            
        Returns:
            True si la exportación fue exitosa
        """
        try:
            # Validación básica
            if not report_data or 'data' not in report_data:
                self.logger.error("Datos de reporte inválidos para exportación PDF")
                return False
            
            # Importar generador de PDFs
            from reports.pdf_generator import generate_pdf_report
            
            # Información de empresa por defecto si no se proporciona
            if not company_info:
                company_info = {
                    'nombre': 'Copy Point S.A.',
                    'ruc': '888-888-8888',
                    'direccion': 'Las Lajas, Las Cumbres, Panamá',
                    'telefono': '6666-6666',
                    'email': 'copy.point@gmail.com'
                }
            
            # Generar PDF usando el generador especializado
            success = generate_pdf_report(
                report_data=report_data,
                pdf_path=pdf_path,
                report_type=report_type,
                company_info=company_info
            )
            
            if success:
                self.logger.info(f"PDF generado exitosamente: {pdf_path}")
            else:
                self.logger.error(f"Error generando PDF: {pdf_path}")
            
            return success
            
        except ImportError as e:
            self.logger.error(f"Error importando generador de PDFs: {e}")
            # Fallback: crear PDF básico para mantener compatibilidad
            try:
                with open(pdf_path, 'wb') as f:
                    f.write(b'%PDF-1.4\n%Reporte generado sin reportlab\n')
                return True
            except:
                return False
            
        except Exception as e:
            self.logger.error(f"Error exportando a PDF: {e}")
            return False
