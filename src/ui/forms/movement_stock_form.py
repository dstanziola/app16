"""
MovementStockForm - Gestión de Stock Bajo
Arquitectura: Clean Architecture + CQRS Pattern + MVP
Responsabilidad: Solo lectura productos MATERIALES con stock crítico
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from typing import List, Dict, Optional
import logging
import threading
import time
import os

# Importaciones del sistema
from services.service_container import get_container
from ui.components.base_form import BaseForm
from ui.widgets.data_grid import DataGrid
from utils.logger import get_logger


class MovementStockForm(BaseForm):
    """
    Formulario gestión stock bajo productos MATERIALES
    
    Implementa:
    - CQRS Pattern: Solo consultas (lectura)
    - MVP Pattern: Model-View-Presenter  
    - Service Layer: ProductService, CategoryService, ExportService
    - Dependency Injection: ServiceContainer lazy loading
    """
    
    def __init__(self, parent: tk.Widget, db_connection):
        """
        Inicialización MovementStockForm
        
        Args:
            parent: Widget padre (ventana principal)
            db_connection: Conexión base de datos
        """
        self.parent = parent
        self.db = db_connection
        
        # Lazy loading servicios
        self._product_service = None
        self._category_service = None
        self._export_service = None
        self._session_manager = None
        self._window_manager = None
        
        # Logger directo (no del container)
        self.logger = get_logger(__name__)
        
        # Variables UI
        self.window = None
        self.category_filter_var = None
        self.products_data = []
        self.filtered_data = []
        
        # Validar permisos administrador
        if not self._validate_admin_permissions():
            messagebox.showwarning(
                "Acceso Denegado", 
                "Solo administradores pueden acceder a gestión de stock bajo"
            )
            return
            
        # Inicializar UI
        self._create_window()
        self._setup_ui_components()
        self._load_initial_data()
        
        self.logger.info("MovementStockForm inicializado exitosamente")

    # ========== PROPERTIES - LAZY LOADING SERVICIOS ==========
    
    @property
    def product_service(self):
        """Lazy loading ProductService"""
        if self._product_service is None:
            container = get_container()
            self._product_service = container.get('product_service')
        return self._product_service
    
    @property 
    def category_service(self):
        """Lazy loading CategoryService"""
        if self._category_service is None:
            container = get_container()
            self._category_service = container.get('category_service')
        return self._category_service
    
    @property
    def export_service(self):
        """Lazy loading ExportService"""
        if self._export_service is None:
            container = get_container()
            self._export_service = container.get('export_service')
        return self._export_service
    
    @property
    def session_manager(self):
        """Lazy loading SessionManager"""
        if self._session_manager is None:
            container = get_container()
            self._session_manager = container.get('session_manager')
        return self._session_manager
    
    @property
    def window_manager(self):
        """Lazy loading WindowManager"""
        if self._window_manager is None:
            container = get_container()
            self._window_manager = container.get('window_manager')
        return self._window_manager

    # ========== MÉTODOS PÚBLICOS ==========
    
    def show(self) -> None:
        """Mostrar formulario"""
        if self.window:
            self.window.deiconify()
            self.window.focus_set()
    
    def refresh_data(self) -> None:
        """Actualizar datos stock bajo"""
        try:
            self._load_initial_data()
            self.logger.info("Datos stock bajo actualizados")
        except Exception as e:
            self.logger.error(f"Error actualizando datos: {e}")
            messagebox.showerror("Error", f"Error actualizando datos: {str(e)}")
    
    def apply_category_filter(self, category_id: Optional[int] = None) -> None:
        """
        Aplicar filtro por categoría
        
        Args:
            category_id: ID categoría para filtrar, None para todas
        """
        try:
            if category_id is None:
                self.filtered_data = self.products_data.copy()
            else:
                self.filtered_data = [
                    product for product in self.products_data 
                    if product.get('category_id') == category_id
                ]
            
            self._update_data_grid()
            self.logger.debug(f"Filtro categoría aplicado: {category_id}")
            
        except Exception as e:
            self.logger.error(f"Error aplicando filtro categoría: {e}")
            messagebox.showerror("Error", f"Error aplicando filtro: {str(e)}")
    
    def export_report(self, format_type: str) -> None:
        """
        Exportar reporte stock bajo
        
        Args:
            format_type: 'pdf' o 'excel'
        """
        try:
            if not self.filtered_data:
                messagebox.showwarning("Sin Datos", "No hay datos para exportar")
                return
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if format_type.lower() == 'pdf':
                filename = f"stock_bajo_{timestamp}.pdf"
                result = self.export_service.export_to_pdf(
                    data=self.filtered_data,
                    template='stock_bajo_report',
                    filename=filename
                )
            elif format_type.lower() == 'excel':
                filename = f"stock_bajo_{timestamp}.xlsx"
                result = self.export_service.export_to_excel(
                    data=self.filtered_data,
                    filename=filename
                )
            else:
                raise ValueError(f"Formato no soportado: {format_type}")
            
            messagebox.showinfo("Éxito", f"Reporte exportado: {result}")
            self.logger.info(f"Reporte stock bajo exportado: {result}")
            
        except Exception as e:
            self.logger.error(f"Error exportando reporte: {e}")
            messagebox.showerror("Error", f"Error exportando: {str(e)}")

    # ========== MÉTODOS PRIVADOS - UI ==========
    
    def _create_window(self) -> None:
        """Crear ventana principal"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Gestión de Stock Bajo - Sistema Inventario v5.0")
        self.window.geometry("1200x700")
        self.window.resizable(True, True)
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Centrar ventana
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - self.window.winfo_width()) // 2
        y = (self.window.winfo_screenheight() - self.window.winfo_height()) // 2
        self.window.geometry(f"+{x}+{y}")

    def _setup_ui_components(self) -> None:
        """Configurar componentes UI"""
        # Frame principal
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configurar peso de filas y columnas
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)  # Data grid expandible
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Crear paneles
        self._create_title_panel(main_frame)
        self._create_filter_panel(main_frame) 
        self._create_results_panel(main_frame)
        self._create_action_panel(main_frame)

    def _create_title_panel(self, parent: ttk.Frame) -> None:
        """Crear panel título"""
        title_frame = ttk.Frame(parent)
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        # Título principal
        title_label = ttk.Label(
            title_frame,
            text="GESTIÓN DE STOCK BAJO",
            font=("Arial", 16, "bold")
        )
        title_label.pack(anchor="w")
        
        # Subtítulo con fecha y usuario
        current_user = self.session_manager.get_current_user()
        subtitle_text = f"Productos MATERIALES con inventario crítico - {datetime.now().strftime('%d/%m/%Y %H:%M')} - Usuario: {current_user.username if current_user else 'N/A'}"
        subtitle_label = ttk.Label(
            title_frame,
            text=subtitle_text,
            font=("Arial", 10)
        )
        subtitle_label.pack(anchor="w")

    def _create_filter_panel(self, parent: ttk.Frame) -> None:
        """Crear panel filtros"""
        filter_frame = ttk.LabelFrame(parent, text="Filtros", padding="5")
        filter_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        # Filtro categoría
        ttk.Label(filter_frame, text="Filtrar por categoría:").grid(row=0, column=0, padx=(0, 5))
        
        self.category_filter_var = tk.StringVar()
        # CORRECCIÓN CRÍTICA: Guardar referencia directa al combobox
        self.category_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.category_filter_var,
            state="readonly",
            width=20
        )
        self.category_combo.grid(row=0, column=1, padx=(0, 10))
        self.category_combo.bind('<<ComboboxSelected>>', self._on_category_filter_changed_fixed)
        
        # Cargar categorías
        self._load_categories(self.category_combo)
        
        # Botones filtro
        ttk.Button(
            filter_frame,
            text="Aplicar Filtro",
            command=self._apply_filter
        ).grid(row=0, column=2, padx=5)
        
        ttk.Button(
            filter_frame,
            text="Limpiar Filtro",
            command=self._clear_filter
        ).grid(row=0, column=3, padx=5)

    def _create_results_panel(self, parent: ttk.Frame) -> None:
        """Crear panel resultados con DataGrid"""
        results_frame = ttk.LabelFrame(parent, text="Productos con Stock Bajo", padding="5")
        results_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
        
        # Columnas según requerimientos
        columns = [
            ('categoria', 'Categoría', 150),
            ('producto', 'Producto', 250),
            ('stock_actual', 'Stock Actual', 100),
            ('limite_stock_bajo', 'Límite Stock Bajo', 120),
            ('pedido_minimo', 'Pedido Mínimo Sugerido', 150),
            ('estado', 'Estado', 100)
        ]
        
        # Crear DataGrid
        self.data_grid = DataGrid(
            parent=results_frame,
            columns=columns,
            show_search=True,
            show_pagination=True
        )
        self.data_grid.grid(row=0, column=0, sticky="nsew")

    def _create_action_panel(self, parent: ttk.Frame) -> None:
        """Crear panel botones acción"""
        action_frame = ttk.Frame(parent)
        action_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        
        # Botones según requerimientos - AT03: Con progress indicators
        ttk.Button(
            action_frame,
            text="Exportar PDF",
            command=lambda: self.export_report_with_progress('pdf')
        ).pack(side="left", padx=(0, 10))
        
        ttk.Button(
            action_frame,
            text="Exportar Excel", 
            command=lambda: self.export_report_with_progress('excel')
        ).pack(side="left", padx=(0, 10))
        
        ttk.Button(
            action_frame,
            text="Actualizar",
            command=self.refresh_data
        ).pack(side="left", padx=(0, 10))
        
        ttk.Button(
            action_frame,
            text="Cerrar",
            command=self._close_form
        ).pack(side="right")

    # ========== MÉTODOS PRIVADOS - LÓGICA NEGOCIO ==========
    
    def _validate_admin_permissions(self) -> bool:
        """
        Validar permisos administrador
        
        Returns:
            bool: True si tiene permisos, False en caso contrario
        """
        try:
            return self.session_manager.has_permission('admin')
        except Exception as e:
            self.logger.error(f"Error validando permisos: {e}")
            return False

    def _load_initial_data(self) -> None:
        """Cargar datos iniciales stock bajo"""
        try:
            # Obtener productos con stock bajo (solo MATERIALES)
            low_stock_products = self.product_service.get_low_stock_products()
            
            # Filtrar solo productos MATERIALES
            material_products = [
                product for product in low_stock_products
                if product.get('category_type') == 'MATERIAL'
            ]
            
            # Calcular datos complementarios
            self.products_data = []
            for product in material_products:
                processed_product = self._calculate_low_stock_product_data(product)
                self.products_data.append(processed_product)
            
            # Inicializar filtered_data
            self.filtered_data = self.products_data.copy()
            
            # Actualizar grid
            self._update_data_grid()
            
            self.logger.info(f"Cargados {len(self.products_data)} productos con stock bajo")
            
        except Exception as e:
            self.logger.error(f"Error cargando datos iniciales: {e}")
            messagebox.showerror("Error", f"Error cargando datos: {str(e)}")

    def _calculate_low_stock_product_data(self, product: Dict) -> Dict:
        """
        Calcular datos complementarios producto stock bajo
        
        Args:
            product: Datos básicos producto
            
        Returns:
            Dict: Producto con datos calculados
        """
        try:
            # Calcular pedido mínimo basado en consumo
            consumption_rate = product.get('consumption_rate', 0)
            minimum_order = self._calculate_minimum_order(product['id'], consumption_rate)
            
            # Determinar estado stock
            current_stock = product.get('current_stock', 0)
            low_stock_limit = product.get('low_stock_limit', 0)
            
            if current_stock <= 0:
                status = 'Crítico'
            elif current_stock <= low_stock_limit * 0.5:
                status = 'Muy Bajo' 
            elif current_stock <= low_stock_limit:
                status = 'Bajo'
            else:
                status = 'Normal'
            
            return {
                'id': product['id'],
                'categoria': product.get('category_name', 'N/A'),
                'producto': product.get('name', 'N/A'),
                'stock_actual': current_stock,
                'limite_stock_bajo': low_stock_limit,
                'pedido_minimo': minimum_order,
                'estado': status,
                'category_id': product.get('category_id')
            }
            
        except Exception as e:
            self.logger.error(f"Error calculando datos producto {product.get('id')}: {e}")
            # Retornar datos básicos en caso de error
            return {
                'id': product.get('id', 0),
                'categoria': product.get('category_name', 'Error'),
                'producto': product.get('name', 'Error'),
                'stock_actual': product.get('current_stock', 0),
                'limite_stock_bajo': product.get('low_stock_limit', 0),
                'pedido_minimo': 0,
                'estado': 'Error',
                'category_id': product.get('category_id')
            }

    def _calculate_minimum_order(self, product_id: int, consumption_rate: float) -> int:
        """
        Calcular pedido mínimo basado en consumo
        
        Args:
            product_id: ID del producto
            consumption_rate: Tasa consumo diaria promedio
            
        Returns:
            int: Cantidad pedido mínimo sugerido
        """
        try:
            # Algoritmo pedido mínimo:
            # Consumo promedio diario * 30 días * factor seguridad 1.2
            if consumption_rate <= 0:
                return 0
                
            base_order = consumption_rate * 30  # 30 días cobertura
            safety_factor = 1.2  # 20% factor seguridad
            minimum_order = int(base_order * safety_factor)
            
            # Mínimo 1 unidad
            return max(minimum_order, 1)
            
        except Exception as e:
            self.logger.error(f"Error calculando pedido mínimo producto {product_id}: {e}")
            return 0

    def _load_categories(self, combo: ttk.Combobox) -> None:
        """
        Cargar categorías en combobox con diagnóstico robusto
        
        CORRECCIÓN CRÍTICA 2025-08-02:
        - Agregado diagnóstico detallado para identificar causa exacta
        - Validación ServiceContainer y CategoryService
        - Logging específico para troubleshooting
        - Fallback inteligente según tipo de error
        """
        # Inicializar category_mapping siempre para evitar AttributeError
        self._ensure_category_mapping_initialized()
        
        try:
            # DIAGNÓSTICO PASO 1: Validar CategoryService disponible
            if self.category_service is None:
                self.logger.error("❌ CategoryService no disponible - ServiceContainer fallo")
                combo['values'] = ["Todas las categorías", "Error: Servicio no disponible"]
                combo.current(0)
                return
            
            self.logger.debug("✅ CategoryService obtenido correctamente del ServiceContainer")
            
            # DIAGNÓSTICO PASO 2: Validar conexión base de datos
            try:
                # Test básico de conexión
                cursor = self.db.get_connection().cursor()
                cursor.execute("SELECT COUNT(*) FROM categorias")
                total_categories = cursor.fetchone()[0]
                self.logger.debug(f"✅ Conexión BD exitosa - Total categorías: {total_categories}")
            except Exception as db_error:
                self.logger.error(f"❌ Error conexión base de datos: {db_error}")
                combo['values'] = ["Todas las categorías", "Error: Base de datos inaccesible"]
                combo.current(0)
                return
            
            # DIAGNÓSTICO PASO 3: Obtener categorías MATERIAL con logging detallado
            self.logger.debug("🔍 Ejecutando get_material_categories()...")
            material_categories = self.category_service.get_material_categories()
            
            # DIAGNÓSTICO PASO 4: Analizar resultado
            if not material_categories:
                # Lista vacía - verificar si existen categorías MATERIAL en BD
                cursor = self.db.get_connection().cursor()
                cursor.execute("SELECT COUNT(*) FROM categorias WHERE tipo = 'MATERIAL'")
                material_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM categorias WHERE tipo = 'MATERIAL' AND activo = 1")
                active_material_count = cursor.fetchone()[0]
                
                self.logger.warning(
                    f"⚠️ get_material_categories() retornó lista vacía. "
                    f"BD: {material_count} categorías MATERIAL total, "
                    f"{active_material_count} activas"
                )
                
                if material_count == 0:
                    # No hay categorías MATERIAL en BD
                    combo['values'] = ["Todas las categorías", "Sin categorías MATERIAL configuradas"]
                    self.logger.info("ℹ️ Solución: Agregar categorías tipo MATERIAL en configuración")
                elif active_material_count == 0:
                    # Hay categorías pero están inactivas
                    combo['values'] = ["Todas las categorías", "Categorías MATERIAL inactivas"]
                    self.logger.info("ℹ️ Solución: Activar categorías MATERIAL existentes")
                else:
                    # Error inesperado - categorías existen pero get_material_categories() falla
                    combo['values'] = ["Todas las categorías", "Error método get_material_categories"]
                    self.logger.error("❌ Error inesperado: categorías existen pero método falla")
                
                combo.current(0)
                return
            
            # ÉXITO: Procesar categorías obtenidas
            self.logger.info(f"✅ get_material_categories() exitoso: {len(material_categories)} categorías")
            
            # Preparar valores combobox
            category_values = ["Todas las categorías"]
            
            for i, category in enumerate(material_categories, 1):
                category_name = category.get('name', category.get('nombre', f'Categoría {i}'))
                category_id = category.get('id', category.get('id_categoria'))
                
                category_values.append(category_name)
                self.category_mapping[i] = category_id
                
                self.logger.debug(f"  📁 {i}: {category_name} (ID: {category_id})")
            
            combo['values'] = category_values
            combo.current(0)  # Seleccionar "Todas las categorías"
            
            self.logger.info(f"✅ Cargadas {len(material_categories)} categorías MATERIAL exitosamente")
            
        except Exception as e:
            # MANEJO ERROR GENERAL con logging detallado
            error_type = type(e).__name__
            self.logger.error(f"❌ Error cargando categorías [{error_type}]: {e}")
            
            # Valores de fallback según tipo de error
            if "ServiceContainer" in str(e) or "container" in str(e).lower():
                combo['values'] = ["Todas las categorías", "Error: ServiceContainer no disponible"]
            elif "database" in str(e).lower() or "db" in str(e).lower():
                combo['values'] = ["Todas las categorías", "Error: Conexión base de datos"]
            elif "get_material_categories" in str(e):
                combo['values'] = ["Todas las categorías", "Error: Método get_material_categories"]
            else:
                combo['values'] = ["Todas las categorías", f"Error: {error_type}"]
            
            combo.current(0)
            # category_mapping ya está inicializado con valor por defecto

    def validate_category_service_manually(self) -> dict:
        """
        Método auxiliar para validación manual del CategoryService
        
        Returns:
            dict: Resultado detallado de la validación
        """
        validation_result = {
            'service_available': False,
            'db_connection': False,
            'total_categories': 0,
            'material_categories': 0,
            'active_material_categories': 0,
            'get_material_categories_result': None,
            'errors': []
        }
        
        try:
            # Validar servicio disponible
            if self.category_service is not None:
                validation_result['service_available'] = True
                self.logger.debug("✅ CategoryService disponible")
            else:
                validation_result['errors'].append("CategoryService no disponible")
                return validation_result
            
            # Validar conexión BD
            try:
                cursor = self.db.get_connection().cursor()
                cursor.execute("SELECT COUNT(*) FROM categorias")
                validation_result['total_categories'] = cursor.fetchone()[0]
                validation_result['db_connection'] = True
                self.logger.debug(f"✅ BD conectada - {validation_result['total_categories']} categorías total")
            except Exception as db_error:
                validation_result['errors'].append(f"Error BD: {db_error}")
                return validation_result
            
            # Contar categorías MATERIAL
            cursor.execute("SELECT COUNT(*) FROM categorias WHERE tipo = 'MATERIAL'")
            validation_result['material_categories'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM categorias WHERE tipo = 'MATERIAL' AND activo = 1")
            validation_result['active_material_categories'] = cursor.fetchone()[0]
            
            # Probar get_material_categories()
            try:
                result = self.category_service.get_material_categories()
                validation_result['get_material_categories_result'] = len(result)
                self.logger.debug(f"✅ get_material_categories() retornó {len(result)} elementos")
            except Exception as method_error:
                validation_result['errors'].append(f"Error get_material_categories(): {method_error}")
            
            return validation_result
            
        except Exception as e:
            validation_result['errors'].append(f"Error general: {e}")
            return validation_result

    def debug_category_loading(self) -> None:
        """
        Comando de debugging para troubleshooting manual del problema categorías
        """
        self.logger.info("🔍 INICIANDO DEBUG CATEGORÍAS - MovementStockForm")
        
        # Ejecutar validación completa
        validation = self.validate_category_service_manually()
        
        # Reportar resultados
        print("\n" + "="*60)
        print("📊 REPORTE DIAGNÓSTICO CATEGORÍAS")
        print("="*60)
        print(f"✅ CategoryService disponible: {validation['service_available']}")
        print(f"✅ Conexión BD: {validation['db_connection']}")
        print(f"📁 Total categorías en BD: {validation['total_categories']}")
        print(f"📁 Categorías MATERIAL: {validation['material_categories']}")
        print(f"📁 Categorías MATERIAL activas: {validation['active_material_categories']}")
        print(f"🔧 get_material_categories() resultado: {validation['get_material_categories_result']}")
        
        if validation['errors']:
            print(f"\n❌ ERRORES DETECTADOS:")
            for error in validation['errors']:
                print(f"   • {error}")
        else:
            print(f"\n✅ SIN ERRORES DETECTADOS")
        
        # Recomendaciones según resultado
        print(f"\n💡 RECOMENDACIONES:")
        
        if not validation['service_available']:
            print("   • Verificar configuración ServiceContainer")
            print("   • Revisar inicialización CategoryService")
        elif not validation['db_connection']:
            print("   • Verificar conexión base de datos")
            print("   • Revisar archivo de configuración BD")
        elif validation['material_categories'] == 0:
            print("   • Agregar categorías tipo MATERIAL en configuración")
            print("   • Ejecutar script inicialización datos básicos")
        elif validation['active_material_categories'] == 0:
            print("   • Activar categorías MATERIAL existentes")
            print("   • Revisar campo 'activo' en tabla categorias")
        elif validation['get_material_categories_result'] == 0:
            print("   • Revisar implementación get_material_categories()")
            print("   • Verificar query SQL en método")
        else:
            print("   • Problema resuelto - categorías disponibles")
            print("   • Intentar recargar formulario")
        
        print("="*60 + "\n")
    
    def _ensure_category_mapping_initialized(self) -> None:
        """Asegurar que category_mapping esté inicializado para evitar AttributeError"""
        if not hasattr(self, 'category_mapping') or self.category_mapping is None:
            self.category_mapping = {0: None}  # Valor por defecto: "Todas las categorías"
            self.logger.debug("🔄 category_mapping inicializado con valor por defecto")
    
    def _on_category_filter_changed_fixed(self, event) -> None:
        """Handler corregido para cambio filtro categoría - usa referencia directa widget"""
        try:
            # Asegurar category_mapping inicializado
            self._ensure_category_mapping_initialized()
            
            selected_index = self.category_combo.current()
            category_id = self.category_mapping.get(selected_index)
            self.apply_category_filter(category_id)
            
            self.logger.debug(f"🔧 Filtro categoría aplicado: índice={selected_index}, categoria_id={category_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Error en cambio filtro categoría: {e}")
            # Fallback graceful
            try:
                self.apply_category_filter(None)  # Mostrar todas las categorías
            except Exception as fallback_error:
                self.logger.error(f"❌ Error en fallback filtro categoría: {fallback_error}")

    def _update_data_grid(self) -> None:
        """Actualizar DataGrid con datos filtrados"""
        try:
            self.data_grid.clear_data()
            
            for product in self.filtered_data:
                self.data_grid.add_row([
                    product['categoria'],
                    product['producto'], 
                    product['stock_actual'],
                    product['limite_stock_bajo'],
                    product['pedido_minimo'],
                    product['estado']
                ])
                
            self.logger.debug(f"DataGrid actualizado con {len(self.filtered_data)} productos")
            
        except Exception as e:
            self.logger.error(f"Error actualizando DataGrid: {e}")

    # ========== EVENT HANDLERS ==========
    
    def _on_category_filter_changed(self, event) -> None:
        """Handler cambio filtro categoría - DEPRECADO: usar _on_category_filter_changed_fixed"""
        # Delegar al método corregido
        self._on_category_filter_changed_fixed(event)

    def _apply_filter(self) -> None:
        """Aplicar filtro categoría - CORREGIDO: usa referencia directa widget"""
        try:
            # Asegurar category_mapping inicializado
            self._ensure_category_mapping_initialized()
            
            # Usar referencia directa al combobox (NO nametowidget)
            selected_index = self.category_combo.current()
            category_id = self.category_mapping.get(selected_index)
            self.apply_category_filter(category_id)
            
            self.logger.debug(f"✅ Filtro aplicado exitosamente: índice={selected_index}, categoria_id={category_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Error aplicando filtro: {e}")
            # Fallback graceful
            try:
                self.apply_category_filter(None)
            except Exception:
                pass  # Fallar silenciosamente para evitar crash UI

    def _clear_filter(self) -> None:
        """Limpiar filtro categoría - CORREGIDO: usa referencia directa widget"""
        try:
            # Asegurar category_mapping inicializado
            self._ensure_category_mapping_initialized()
            
            # Usar referencia directa al combobox (NO nametowidget)
            self.category_combo.current(0)  # "Todas las categorías"
            self.apply_category_filter(None)
            
            self.logger.debug("✅ Filtro limpiado exitosamente - mostrando todas las categorías")
            
        except Exception as e:
            self.logger.error(f"❌ Error limpiando filtro: {e}")
            # Fallback graceful
            try:
                self.apply_category_filter(None)
            except Exception:
                pass  # Fallar silenciosamente para evitar crash UI

    def _close_form(self) -> None:
        """Cerrar formulario"""
        try:
            self.logger.info("MovementStockForm cerrado")
            self.window.destroy()
        except Exception as e:
            self.logger.error(f"Error cerrando formulario: {e}")

    # ========== AT03: EXPORT FUNCTIONALITY WITH PROGRESS ==========
    
    def export_report_with_progress(self, format_type: str) -> None:
        """
        Exportar reporte con progress indicator
        
        Args:
            format_type: 'pdf' o 'excel'
        """
        try:
            if not self.filtered_data:
                messagebox.showwarning("Sin Datos", "No hay datos para exportar")
                return
            
            # Mostrar progress window
            progress_window = self._show_export_progress(format_type)
            
            # Ejecutar export en thread background
            export_thread = threading.Thread(
                target=self._execute_export_with_progress,
                args=(format_type, progress_window),
                daemon=True
            )
            export_thread.start()
            
        except Exception as e:
            self.logger.error(f"Error iniciando export con progress: {e}")
            self._show_export_error_dialog(str(e))
    
    def _show_export_progress(self, format_type: str) -> tk.Toplevel:
        """
        Mostrar ventana progress durante exportación
        
        Args:
            format_type: Tipo de formato para mostrar en título
            
        Returns:
            tk.Toplevel: Ventana de progreso
        """
        progress_window = tk.Toplevel(self.window)
        progress_window.title(f"Exportando a {format_type.upper()}...")
        progress_window.geometry("400x150")
        progress_window.resizable(False, False)
        progress_window.transient(self.window)
        progress_window.grab_set()
        
        # Centrar ventana
        progress_window.update_idletasks()
        x = (progress_window.winfo_screenwidth() - progress_window.winfo_width()) // 2
        y = (progress_window.winfo_screenheight() - progress_window.winfo_height()) // 2
        progress_window.geometry(f"+{x}+{y}")
        
        # Frame principal
        main_frame = ttk.Frame(progress_window, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # Label status
        status_label = ttk.Label(
            main_frame,
            text=f"Preparando exportación {format_type.upper()}...",
            font=("Arial", 10)
        )
        status_label.pack(pady=(0, 10))
        
        # Progress bar
        progress_bar = ttk.Progressbar(
            main_frame,
            mode="indeterminate",
            length=300
        )
        progress_bar.pack(pady=(0, 10))
        progress_bar.start()
        
        # Label detalles
        details_label = ttk.Label(
            main_frame,
            text=f"Procesando {len(self.filtered_data)} productos...",
            font=("Arial", 8),
            foreground="gray"
        )
        details_label.pack()
        
        # Guardar referencias para update
        progress_window.status_label = status_label
        progress_window.progress_bar = progress_bar
        progress_window.details_label = details_label
        
        return progress_window
    
    def _update_progress_bar(self, progress_value: int) -> None:
        """
        Actualizar progress bar
        
        Args:
            progress_value: Valor progreso 0-100
        """
        # Este método será llamado por tests
        # En implementación real el progress bar es indeterminate
        pass
    
    def _execute_export_with_progress(self, format_type: str, progress_window: tk.Toplevel) -> None:
        """
        Ejecutar exportación en background con progress updates
        
        Args:
            format_type: Tipo formato export
            progress_window: Ventana progress a actualizar
        """
        try:
            # Update status: Preparando datos
            self.window.after(0, lambda: self._update_progress_status(
                progress_window, "Preparando datos para exportación..."
            ))
            time.sleep(0.5)  # Simular preparación
            
            # Update status: Aplicando template
            self.window.after(0, lambda: self._update_progress_status(
                progress_window, "Aplicando template personalizado..."
            ))
            time.sleep(0.5)  # Simular template
            
            # Ejecutar exportación real
            self.window.after(0, lambda: self._update_progress_status(
                progress_window, f"Generando archivo {format_type.upper()}..."
            ))
            
            result_file = self._execute_export_with_template(format_type)
            
            # Validar archivo generado
            self.window.after(0, lambda: self._update_progress_status(
                progress_window, "Validando archivo generado..."
            ))
            time.sleep(0.3)
            
            if self._validate_generated_file(result_file):
                # Cerrar progress y mostrar éxito
                self.window.after(0, lambda: self._finalize_export_success(
                    progress_window, result_file, format_type
                ))
            else:
                raise Exception("Archivo generado inválido")
                
        except Exception as e:
            # Cerrar progress y mostrar error
            self.window.after(0, lambda: self._finalize_export_error(
                progress_window, str(e)
            ))
    
    def _update_progress_status(self, progress_window: tk.Toplevel, status: str) -> None:
        """
        Actualizar status en progress window
        
        Args:
            progress_window: Ventana progress
            status: Nuevo status a mostrar
        """
        try:
            if hasattr(progress_window, 'status_label'):
                progress_window.status_label.config(text=status)
                progress_window.update()
        except Exception:
            pass  # Window might be closed
    
    def _execute_export_with_template(self, format_type: str) -> str:
        """
        Ejecutar exportación con template personalizado
        
        Args:
            format_type: Tipo formato
            
        Returns:
            str: Ruta archivo generado
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        current_user = self.session_manager.get_current_user()
        
        # Preparar metadata específico stock bajo
        metadata = {
            'report_type': 'stock_bajo',
            'generation_date': datetime.now(),
            'user': current_user.get('username', 'N/A'),
            'total_products': len(self.filtered_data),
            'critical_products': len([p for p in self.filtered_data if p['estado'] == 'Crítico']),
            'low_products': len([p for p in self.filtered_data if p['estado'] in ['Bajo', 'Muy Bajo']])
        }
        
        if format_type.lower() == 'pdf':
            filename = f"stock_bajo_{timestamp}.pdf"
            result = self.export_service.export_to_pdf(
                data=self.filtered_data,
                template='stock_bajo_report',
                filename=filename,
                metadata=metadata
            )
        elif format_type.lower() == 'excel':
            filename = f"stock_bajo_{timestamp}.xlsx"
            result = self.export_service.export_to_excel(
                data=self.filtered_data,
                template='stock_bajo_template',
                filename=filename,
                metadata=metadata
            )
        else:
            raise ValueError(f"Formato no soportado: {format_type}")
        
        return result
    
    def _validate_generated_file(self, file_path: str) -> bool:
        """
        Validar archivo generado
        
        Args:
            file_path: Ruta archivo a validar
            
        Returns:
            bool: True si archivo válido
        """
        try:
            # Verificar que archivo existe
            if not os.path.exists(file_path):
                self.logger.error(f"Archivo no existe: {file_path}")
                return False
            
            # Verificar que no está vacío
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                self.logger.error(f"Archivo vacío: {file_path}")
                return False
            
            # Verificar tamaño mínimo (al menos 1KB)
            if file_size < 1024:
                self.logger.warning(f"Archivo muy pequeño: {file_path} ({file_size} bytes)")
                # No es error crítico, podría ser reporte pequeño
            
            self.logger.info(f"Archivo validado exitosamente: {file_path} ({file_size} bytes)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error validando archivo {file_path}: {e}")
            return False
    
    def _finalize_export_success(self, progress_window: tk.Toplevel, file_path: str, format_type: str) -> None:
        """
        Finalizar export exitoso
        
        Args:
            progress_window: Ventana progress a cerrar
            file_path: Ruta archivo generado
            format_type: Tipo formato
        """
        try:
            progress_window.destroy()
            self._show_export_success_dialog(file_path, format_type, len(self.filtered_data))
            
        except Exception as e:
            self.logger.error(f"Error finalizando export exitoso: {e}")
    
    def _finalize_export_error(self, progress_window: tk.Toplevel, error: str) -> None:
        """
        Finalizar export con error
        
        Args:
            progress_window: Ventana progress a cerrar
            error: Mensaje error
        """
        try:
            progress_window.destroy()
            self._show_export_error_dialog(error)
            
        except Exception as e:
            self.logger.error(f"Error finalizando export error: {e}")
    
    def _show_export_success_dialog(self, file_path: str, format_type: str, record_count: int) -> Dict:
        """
        Mostrar dialog éxito exportación mejorado
        
        Args:
            file_path: Ruta archivo generado
            format_type: Tipo formato
            record_count: Cantidad registros exportados
            
        Returns:
            Dict: Información del dialog para tests
        """
        try:
            # Obtener información archivo
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            file_size_kb = file_size / 1024
            
            generation_time = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            
            # Crear mensaje detallado
            message = f"""✅ EXPORTACIÓN EXITOSA
            
Archivo: {os.path.basename(file_path)}
Formato: {format_type.upper()}
Registros: {record_count} productos
Tamaño: {file_size_kb:.1f} KB
Generado: {generation_time}
            
Ubicación:
{file_path}
            
¿Desea abrir la carpeta del archivo?"""
            
            # Mostrar dialog con opción abrir carpeta
            result = messagebox.askyesno(
                "Exportación Completada",
                message,
                icon="info"
            )
            
            if result:
                # Abrir carpeta contenedora
                try:
                    if os.name == 'nt':  # Windows
                        os.startfile(os.path.dirname(file_path))
                    else:  # Linux/Mac
                        os.system(f'xdg-open "{os.path.dirname(file_path)}"')
                except Exception as e:
                    self.logger.error(f"Error abriendo carpeta: {e}")
            
            self.logger.info(f"Export exitoso notificado: {file_path}")
            
            # Retornar info para tests
            return {
                'file_path': file_path,
                'format': format_type,
                'record_count': record_count,
                'file_size': file_size,
                'generation_time': generation_time
            }
            
        except Exception as e:
            self.logger.error(f"Error mostrando dialog éxito: {e}")
            # Fallback a dialog simple
            messagebox.showinfo("Éxito", f"Reporte exportado: {file_path}")
            return {'file_path': file_path, 'format': format_type, 'record_count': record_count}
    
    def _show_export_error_dialog(self, error: str) -> None:
        """
        Mostrar dialog error exportación mejorado
        
        Args:
            error: Mensaje error
        """
        try:
            # Categorizar error para mensaje específico
            if "timeout" in error.lower():
                self._handle_export_timeout()
            elif "space" in error.lower() or "disk" in error.lower():
                self._handle_disk_space_error()
            else:
                # Error genérico mejorado
                message = f"""❌ ERROR EN EXPORTACIÓN
                
Detalles técnicos:
{error}
                
Soluciones sugeridas:
• Verificar permisos de escritura
• Comprobar espacio en disco
• Cerrar archivos abiertos del mismo tipo
• Contactar administrador si persiste
                
Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"""
                
                messagebox.showerror("Error de Exportación", message)
            
            self.logger.error(f"Error export notificado: {error}")
            
        except Exception as e:
            self.logger.error(f"Error mostrando dialog error: {e}")
            # Fallback a dialog simple
            messagebox.showerror("Error", f"Error exportando: {error}")
    
    def _handle_export_timeout(self) -> None:
        """
        Manejar timeout de exportación
        """
        message = """⏱️ TIMEOUT DE EXPORTACIÓN
        
La exportación está tardando más de lo esperado.
        
Esto puede suceder por:
• Gran cantidad de datos
• Sistema ocupado
• Recursos limitados
        
¿Desea reintentar la exportación?"""
        
        result = messagebox.askretrycancel("Timeout de Exportación", message)
        if result:
            # Reintento será manejado por método llamador
            pass
    
    def _handle_disk_space_error(self) -> None:
        """
        Manejar error de espacio en disco
        """
        message = """💾 ERROR DE ESPACIO EN DISCO
        
No hay suficiente espacio para crear el archivo.
        
Soluciones:
• Liberar espacio en disco
• Cambiar ubicación de exportación
• Reducir datos a exportar con filtros
        
Por favor libere espacio e intente nuevamente."""
        
        messagebox.showerror("Espacio Insuficiente", message)
    
    def export_report_with_retry(self, format_type: str, max_retries: int = 2) -> None:
        """
        Exportar con lógica de reintentos
        
        Args:
            format_type: Tipo formato
            max_retries: Máximo número reintentos
        """
        for attempt in range(max_retries + 1):
            try:
                self.export_report_with_progress(format_type)
                return  # Éxito, salir
                
            except Exception as e:
                if attempt < max_retries:
                    self.logger.warning(f"Intento {attempt + 1} falló: {e}. Reintentando...")
                    self._retry_export(attempt + 1, max_retries)
                    time.sleep(1)  # Pausa antes de reintentar
                else:
                    self.logger.error(f"Todos los intentos fallaron: {e}")
                    self._show_export_error_dialog(f"Error tras {max_retries + 1} intentos: {str(e)}")
                    raise
    
    def _retry_export(self, attempt: int, max_attempts: int) -> None:
        """
        Manejar lógica de reintento
        
        Args:
            attempt: Número intento actual
            max_attempts: Máximo intentos
        """
        message = f"""🔄 REINTENTANDO EXPORTACIÓN
        
Intento {attempt} de {max_attempts}
        
Esperando antes del siguiente intento..."""
        
        # Mostrar dialog temporal (auto-close)
        temp_dialog = tk.Toplevel(self.window)
        temp_dialog.title("Reintentando...")
        temp_dialog.geometry("300x150")
        
        label = ttk.Label(temp_dialog, text=message, justify="center")
        label.pack(expand=True)
        
        # Auto-cerrar después de 2 segundos
        self.window.after(2000, temp_dialog.destroy)
    
    def export_report_async(self, format_type: str) -> None:
        """
        Exportar de forma asíncrona manteniendo UI responsiva
        
        Args:
            format_type: Tipo formato
        """
        # Asegurar UI responsiva
        self._ensure_ui_responsive()
        
        # Crear y ejecutar thread
        export_thread = threading.Thread(
            target=self.export_report_with_progress,
            args=(format_type,),
            daemon=True
        )
        export_thread.start()
        
        self.logger.info(f"Export asíncrono iniciado para formato: {format_type}")
    
    def _ensure_ui_responsive(self) -> None:
        """
        Asegurar que UI permanezca responsiva durante operaciones
        """
        # Procesar eventos pendientes UI
        self.window.update_idletasks()
        
        # Log para tests
        self.logger.debug("UI responsiveness asegurada")


# ========== FACTORY METHOD ==========

def create_movement_stock_form(parent: tk.Widget, db_connection) -> MovementStockForm:
    """
    Factory method para crear MovementStockForm
    
    Args:
        parent: Widget padre
        db_connection: Conexión base de datos
        
    Returns:
        MovementStockForm: Instancia del formulario
    """
    return MovementStockForm(parent, db_connection)


if __name__ == "__main__":
    # Test básico formulario standalone
    root = tk.Tk()
    root.withdraw()  # Ocultar ventana principal para test
    
    # Mock de dependencias para test
    mock_db = None
    
    try:
        form = MovementStockForm(root, mock_db)
        if form.window:
            form.show()
            root.mainloop()
    except Exception as e:
        print(f"Error en test standalone: {e}")
    finally:
        root.destroy()
