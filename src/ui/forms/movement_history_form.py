# src/ui/forms/movement_history_form.py
"""
MovementHistoryForm - Formulario de Historial de Movimientos
Implementación Clean Architecture + MVP Pattern + CQRS

Propósito: Consulta y visualización de movimientos históricos
Restricción: Solo lectura, no modificación de registros
Acceso: Solo administradores

Autor: Sistema de Gestión de Inventario v5.0
Fecha: 2025-07-16
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import re
import shutil  # NUEVO: Para manejo de archivos cross-drive
from typing import List, Dict, Optional, Any
import logging

# Configurar logger
logger = logging.getLogger(__name__)

class MovementHistoryForm:
    """
    Formulario de historial de movimientos
    
    Implementa:
    - Clean Architecture: Capa Presentación
    - MVP Pattern: Presenter
    - CQRS: Solo consultas (lectura)
    - Service Layer: Lazy loading de servicios
    - Observer Pattern: Callbacks para eventos
    """
    
    def __init__(self, parent: tk.Tk, db_connection: Any):
        """
        Inicializar formulario de historial de movimientos
        
        Args:
            parent: Ventana padre
            db_connection: Conexión a base de datos
        """
        self.parent = parent
        self.db = db_connection
        self.window = None
        
        # Servicios (lazy loading)
        self._movement_service = None
        self._product_service = None
        self._export_service = None
        self._session_manager = None
        self._container = None
        
        # Estado del formulario
        self.current_movements = []
        self.selected_movement = None
        
        # Configurar ventana y UI primero
        self._setup_window()
        self._create_ui_components()
        self._setup_bindings()
        self._setup_styles()
        
        # CORRECCIÓN CRÍTICA: Validar permisos DESPUÉS de que UI esté configurada
        # Esto permite que lazy loading esté disponible antes de validar permisos
        try:
            if not self._validate_permissions():
                self._close_form()
                return
        except Exception as perm_error:
            logger.error(f"Error crítico validando permisos durante inicialización: {perm_error}")
            messagebox.showerror(
                "Error de Inicialización",
                f"No se pudo inicializar el formulario: {perm_error}"
            )
            self._close_form()
            return
        
        logger.info("MovementHistoryForm inicializado correctamente")
    
    def _validate_permissions(self) -> bool:
        """
        CORRECCIÓN CRÍTICA: Validar permisos con lazy loading robusto.
        
        Problema original: session_manager no estaba disponible durante __init__
        Solución: Validación robusta con lazy loading y manejo de errores
        
        Returns:
            bool: True si tiene permisos, False caso contrario
        """
        try:
            # PASO 1: Asegurar que ServiceContainer esté disponible
            try:
                container = self.container
                if not container:
                    raise RuntimeError("ServiceContainer no disponible")
            except Exception as container_error:
                logger.error(f"Error accediendo ServiceContainer: {container_error}")
                messagebox.showerror(
                    "Error de Sistema", 
                    "Sistema de servicios no disponible. No se puede validar permisos."
                )
                return False
            
            # PASO 2: Cargar session_manager via lazy loading property
            try:
                session_mgr = self.session_manager
                if not session_mgr:
                    raise RuntimeError("SessionManager no disponible después de lazy loading")
            except Exception as sm_error:
                logger.error(f"Error cargando SessionManager via lazy loading: {sm_error}")
                messagebox.showerror(
                    "Error de Autenticación",
                    "No se pudo acceder al sistema de autenticación. Verifique que esté logueado correctamente."
                )
                return False
            
            # PASO 3: Validar permisos de administrador
            try:
                has_admin_permission = session_mgr.has_permission('admin')
                if not has_admin_permission:
                    messagebox.showerror(
                        "Acceso Denegado",
                        "Solo los administradores pueden acceder al historial de movimientos."
                    )
                    return False
                
                logger.info("Validación de permisos exitosa: usuario administrador confirmado")
                return True
                
            except Exception as perm_error:
                logger.error(f"Error validando permisos administrativos: {perm_error}")
                messagebox.showerror(
                    "Error de Permisos",
                    f"No se pudo validar permisos administrativos: {perm_error}"
                )
                return False
            
        except Exception as e:
            logger.error(f"Error general en validación de permisos: {e}")
            messagebox.showerror(
                "Error Crítico", 
                f"Error validando permisos de usuario: {str(e)}"
            )
            return False
    
    def _setup_window(self):
        """Configurar ventana principal"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Historial de Movimientos - Copy Point S.A.")
        self.window.geometry("1200x700")
        self.window.resizable(True, True)
        self.window.grab_set()  # Modal
        
        # Centrar ventana
        self.window.transient(self.parent)
        self.window.protocol("WM_DELETE_WINDOW", self._close_form)
    
    def _create_ui_components(self):
        """Crear todos los componentes de la interfaz"""
        
        # Frame principal
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar peso de filas y columnas
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # 1. Panel de título
        self._create_title_panel(main_frame)
        
        # 2. Panel de búsqueda y filtros
        self._create_search_panel(main_frame)
        
        # 3. Panel de botones de acción
        self._create_action_panel(main_frame)
        
        # 4. Panel de resultados
        self._create_results_panel(main_frame)
        
        # 5. Panel de detalles (inferior)
        self._create_details_panel(main_frame)
    
    def _create_title_panel(self, parent):
        """Crear panel de título"""
        title_frame = ttk.LabelFrame(parent, text="", padding="5")
        title_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        title_label = ttk.Label(
            title_frame,
            text="HISTORIAL DE MOVIMIENTOS",
            font=('Arial', 14, 'bold')
        )
        title_label.pack()
    
    def _create_search_panel(self, parent):
        """Crear panel de búsqueda y filtros"""
        search_frame = ttk.LabelFrame(parent, text="Filtros de Búsqueda", padding="10")
        search_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)
        search_frame.columnconfigure(3, weight=1)
        
        # Fila 1: Rango de fechas
        ttk.Label(search_frame, text="Fecha Inicio:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.date_start_entry = ttk.Entry(search_frame, width=12)
        self.date_start_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 20))
        self.date_start_entry.insert(0, (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        
        ttk.Label(search_frame, text="Fecha Fin:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.date_end_entry = ttk.Entry(search_frame, width=12)
        self.date_end_entry.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=(0, 20))
        self.date_end_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        # Fila 2: Tipo de transacción y ticket
        ttk.Label(search_frame, text="Tipo Transacción:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        self.transaction_type_combo = ttk.Combobox(
            search_frame, 
            values=['TODOS', 'ENTRADA', 'AJUSTE', 'VENTA'],
            state='readonly',
            width=15
        )
        self.transaction_type_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 20), pady=(10, 0))
        self.transaction_type_combo.set('TODOS')
        
        ttk.Label(search_frame, text="Número Ticket:").grid(row=1, column=2, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        self.ticket_search_entry = ttk.Entry(search_frame, width=15)
        self.ticket_search_entry.grid(row=1, column=3, sticky=(tk.W, tk.E), padx=(0, 20), pady=(10, 0))
    
    def _create_action_panel(self, parent):
        """Crear panel de botones de acción"""
        action_frame = ttk.Frame(parent, padding="5")
        action_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Botones principales
        ttk.Button(
            action_frame,
            text="BUSCAR",
            command=self._search_movements,
            width=12
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            action_frame,
            text="LIMPIAR",
            command=self._clear_form,
            width=12
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            action_frame,
            text="EXPORTAR PDF",
            command=self._export_to_pdf,
            width=15
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            action_frame,
            text="EXPORTAR EXCEL",
            command=self._export_to_excel,
            width=15
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # Botón cerrar a la derecha
        ttk.Button(
            action_frame,
            text="CERRAR",
            command=self._close_form,
            width=12
        ).pack(side=tk.RIGHT)
    
    def _create_results_panel(self, parent):
        """Crear panel de resultados con tabla"""
        results_frame = ttk.LabelFrame(parent, text="Resultados de Búsqueda", padding="10")
        results_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Crear Treeview con scrollbars
        tree_frame = ttk.Frame(results_frame)
        tree_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Configurar columnas
        columns = ('ID', 'Fecha/Hora', 'Tipo', 'Ticket', 'Producto', 'Cantidad', 'Responsable', 'Observaciones')
        self.results_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        # Configurar encabezados
        self.results_tree.heading('ID', text='ID')
        self.results_tree.heading('Fecha/Hora', text='Fecha/Hora')
        self.results_tree.heading('Tipo', text='Tipo')
        self.results_tree.heading('Ticket', text='Ticket')
        self.results_tree.heading('Producto', text='Producto')
        self.results_tree.heading('Cantidad', text='Cantidad')
        self.results_tree.heading('Responsable', text='Responsable')
        self.results_tree.heading('Observaciones', text='Observaciones')
        
        # Configurar anchos de columna
        self.results_tree.column('ID', width=60, minwidth=50)
        self.results_tree.column('Fecha/Hora', width=130, minwidth=100)
        self.results_tree.column('Tipo', width=80, minwidth=70)
        self.results_tree.column('Ticket', width=100, minwidth=80)
        self.results_tree.column('Producto', width=200, minwidth=150)
        self.results_tree.column('Cantidad', width=80, minwidth=70)
        self.results_tree.column('Responsable', width=100, minwidth=80)
        self.results_tree.column('Observaciones', width=200, minwidth=150)
        
        # Posicionar Treeview
        self.results_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.results_tree.configure(yscrollcommand=v_scrollbar.set)
        
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        self.results_tree.configure(xscrollcommand=h_scrollbar.set)
    
    def _create_details_panel(self, parent):
        """Crear panel de detalles del movimiento seleccionado"""
        details_frame = ttk.LabelFrame(parent, text="Detalles del Movimiento Seleccionado", padding="10")
        details_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        details_frame.columnconfigure(1, weight=1)
        details_frame.columnconfigure(3, weight=1)
        
        # Campos de detalles (readonly)
        ttk.Label(details_frame, text="ID Movimiento:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.detail_id_var = tk.StringVar()
        ttk.Entry(details_frame, textvariable=self.detail_id_var, state='readonly', width=15).grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 20))
        
        ttk.Label(details_frame, text="Producto ID:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.detail_product_id_var = tk.StringVar()
        ttk.Entry(details_frame, textvariable=self.detail_product_id_var, state='readonly', width=15).grid(
            row=0, column=3, sticky=(tk.W, tk.E))
        
        ttk.Label(details_frame, text="Observaciones:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        self.detail_obs_var = tk.StringVar()
        ttk.Entry(details_frame, textvariable=self.detail_obs_var, state='readonly').grid(
            row=1, column=1, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def _setup_bindings(self):
        """Configurar eventos y bindings"""
        # Evento selección en Treeview
        self.results_tree.bind('<<TreeviewSelect>>', self._on_tree_select)
        
        # Eventos de teclado para búsqueda rápida
        self.ticket_search_entry.bind('<Return>', lambda e: self._search_movements())
        
        # Bind para cerrar con Escape
        self.window.bind('<Escape>', lambda e: self._close_form())
    
    def _setup_styles(self):
        """Configurar estilos visuales"""
        style = ttk.Style()
        
        # Estilo para Treeview alternado
        style.configure('Treeview', rowheight=25)
        style.configure('Treeview.Heading', font=('Arial', 9, 'bold'))
    
    # ===============================
    # LAZY LOADING DE SERVICIOS
    # ===============================
    
    @property
    def container(self):
        """Lazy loading ServiceContainer"""
        if self._container is None:
            try:
                from services.service_container import get_container
                self._container = get_container()
            except Exception as e:
                logger.error(f"Error cargando ServiceContainer: {e}")
                raise
        return self._container
    
    @property
    def session_manager(self):
        """Lazy loading SessionManager"""
        if self._session_manager is None:
            try:
                self._session_manager = self.container.get('session_manager')
            except Exception as e:
                logger.error(f"Error cargando SessionManager: {e}")
                raise
        return self._session_manager
    
    @property
    def movement_service(self):
        """Lazy loading MovementService"""
        if self._movement_service is None:
            try:
                self._movement_service = self.container.get('movement_service')
            except Exception as e:
                logger.error(f"Error cargando MovementService: {e}")
                raise
        return self._movement_service
    
    @property
    def product_service(self):
        """Lazy loading ProductService"""
        if self._product_service is None:
            try:
                self._product_service = self.container.get('product_service')
            except Exception as e:
                logger.error(f"Error cargando ProductService: {e}")
                raise
        return self._product_service
    
    @property
    def export_service(self):
        """Lazy loading ExportService"""
        if self._export_service is None:
            try:
                self._export_service = self.container.get('export_service')
            except Exception as e:
                logger.error(f"Error cargando ExportService: {e}")
                raise
        return self._export_service
    
    # ===============================
    # MÉTODOS UTILITARIOS
    # ===============================
    
    def _get_movement_field(self, movement: Any, field_names: List[str]) -> Any:
        """
        Obtener campo de movimiento con soporte para múltiples nombres.
        
        Problema: MovementService puede devolver objetos con diferentes nombres de campos:
        - Formato A: {'id', 'movement_date', 'product_name', ...}
        - Formato B: {'id_movimiento', 'fecha_movimiento', 'producto_nombre', ...}
        
        Esta función intenta obtener el valor usando los nombres alternativos
        hasta encontrar uno que exista.
        
        Args:
            movement: Objeto o diccionario con datos del movimiento
            field_names: Lista de nombres posibles para el campo (en orden de preferencia)
            
        Returns:
            Any: Valor del campo encontrado, o None si ningún nombre funciona
            
        Example:
            >>> movement = {'id_movimiento': 123, 'fecha_movimiento': '2025-08-01'}
            >>> self._get_movement_field(movement, ['id', 'id_movimiento'])
            123
        """
        try:
            # Si movement es None, retornar None inmediatamente
            if movement is None:
                return None
            
            # Intentar acceso como diccionario primero
            if isinstance(movement, dict):
                for field_name in field_names:
                    if field_name in movement:
                        return movement[field_name]
            
            # Intentar acceso como objeto con atributos
            else:
                for field_name in field_names:
                    if hasattr(movement, field_name):
                        return getattr(movement, field_name)
            
            # Si no se encontró ningún campo, loggear para debugging
            logger.debug(
                f"Campo no encontrado en movimiento. "
                f"Nombres intentados: {field_names}, "
                f"Tipo objeto: {type(movement)}, "
                f"Campos disponibles: {self._get_available_fields(movement)}"
            )
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo campo de movimiento: {e}")
            return None
    
    def _get_available_fields(self, movement: Any) -> List[str]:
        """
        Obtener lista de campos disponibles en objeto movimiento para debugging.
        
        Args:
            movement: Objeto movimiento
            
        Returns:
            List[str]: Lista de nombres de campos disponibles
        """
        try:
            if movement is None:
                return []
            
            if isinstance(movement, dict):
                return list(movement.keys())
            else:
                # Obtener atributos que no empiecen con _ (privados)
                return [attr for attr in dir(movement) 
                       if not attr.startswith('_') and not callable(getattr(movement, attr))]
        except Exception:
            return []
    
    # ===============================
    # MÉTODOS DE BÚSQUEDA Y FILTROS
    # ===============================
    
    def _search_movements(self):
        """Ejecutar búsqueda de movimientos con filtros aplicados"""
        try:
            # Limpiar resultados anteriores
            self._clear_results()
            
            # Obtener filtros
            filters = self._get_search_filters()
            
            # Validar filtros
            self._validate_filters(filters)
            
            # Ejecutar búsqueda
            if filters.get('ticket_number'):
                # Búsqueda específica por ticket
                movements = self._search_by_ticket(filters['ticket_number'])
            else:
                # Búsqueda general por filtros
                movements = self._search_by_filters(filters)
            
            # Mostrar resultados
            self._display_search_results(movements)
            
            logger.info(f"Búsqueda ejecutada: {len(movements)} movimientos encontrados")
            
        except ValueError as e:
            messagebox.showerror("Error de Validación", str(e))
        except Exception as e:
            logger.error(f"Error en búsqueda de movimientos: {e}")
            messagebox.showerror("Error", f"Error ejecutando búsqueda: {str(e)}")
    
    def _get_search_filters(self) -> Dict[str, Any]:
        """Obtener filtros de búsqueda desde la UI"""
        filters = {}
        
        # Fechas
        start_date_str = self.date_start_entry.get().strip()
        end_date_str = self.date_end_entry.get().strip()
        
        if start_date_str:
            filters['start_date'] = datetime.strptime(start_date_str, '%Y-%m-%d')
        if end_date_str:
            filters['end_date'] = datetime.strptime(end_date_str + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
        
        # Tipo de transacción
        transaction_type = self.transaction_type_combo.get()
        if transaction_type and transaction_type != 'TODOS':
            filters['transaction_type'] = transaction_type
        
        # Número de ticket
        ticket_number = self.ticket_search_entry.get().strip()
        if ticket_number:
            filters['ticket_number'] = self._sanitize_ticket_input(ticket_number)
        
        return filters
    
    def _validate_filters(self, filters: Dict[str, Any]):
        """Validar filtros de búsqueda"""
        # Validar rango de fechas
        if 'start_date' in filters and 'end_date' in filters:
            self._validate_date_range(filters['start_date'], filters['end_date'])
    
    def _validate_date_range(self, start_date: datetime, end_date: datetime):
        """Validar rango de fechas"""
        if start_date > end_date:
            raise ValueError("La fecha de inicio debe ser menor o igual a la fecha fin")
        
        # Validar rango máximo (1 año)
        if (end_date - start_date).days > 365:
            raise ValueError("El rango de fechas no puede exceder 1 año")
    
    def _sanitize_ticket_input(self, ticket_input: str) -> str:
        """Sanitizar entrada de búsqueda de ticket"""
        # Remover caracteres especiales, solo alfanuméricos
        return re.sub(r'[^a-zA-Z0-9]', '', ticket_input.upper())
    
    def _search_by_filters(self, filters: Dict[str, Any]) -> List[Any]:
        """Buscar movimientos por filtros generales"""
        try:
            return self.movement_service.get_movements_by_filters(filters)
        except Exception as e:
            logger.error(f"Error buscando por filtros: {e}")
            raise
    
    def _search_by_ticket(self, ticket_number: str) -> List[Any]:
        """Buscar movimiento por número de ticket específico"""
        try:
            movement = self.movement_service.get_movement_by_ticket(ticket_number)
            return [movement] if movement else []
        except Exception as e:
            logger.error(f"Error buscando por ticket: {e}")
            raise
    
    def _search_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Any]:
        """Buscar movimientos por rango de fechas"""
        filters = {'start_date': start_date, 'end_date': end_date}
        return self._search_by_filters(filters)
    
    def _search_by_transaction_type(self, transaction_type: str) -> List[Any]:
        """Buscar movimientos por tipo de transacción"""
        filters = {'transaction_type': transaction_type}
        return self._search_by_filters(filters)
    
    def _apply_combined_filters(self, filters: Dict[str, Any]) -> List[Any]:
        """Aplicar filtros combinados"""
        return self._search_by_filters(filters)
    
    # ===============================
    # MÉTODOS DE VISUALIZACIÓN
    # ===============================
    
    def _display_search_results(self, movements: List[Any]):
        """Mostrar resultados de búsqueda en la tabla"""
        # Limpiar tabla
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Guardar movimientos actuales
        self.current_movements = movements
        
        if not movements:
            # Mostrar mensaje de no resultados
            self.results_tree.insert('', 'end', values=(
                '', '', '', 'No se encontraron movimientos', '', '', '', ''
            ))
            return
        
        # Insertar movimientos con mapeo correcto de campos
        for movement in movements:
            # CORRECCIÓN CRÍTICA: Mapear nombres de campos MovementService → UI
            movement_id = self._get_movement_field(movement, ['id', 'id_movimiento'])
            movement_date = self._get_movement_field(movement, ['movement_date', 'fecha_movimiento'])
            movement_type = self._get_movement_field(movement, ['movement_type', 'tipo_movimiento'])
            ticket_number = self._get_movement_field(movement, ['ticket_number', 'id_venta'])
            product_name = self._get_movement_field(movement, ['product_name', 'producto_nombre'])
            quantity = self._get_movement_field(movement, ['quantity', 'cantidad'])
            responsible = self._get_movement_field(movement, ['responsible', 'responsable'])
            observations = self._get_movement_field(movement, ['observations', 'observaciones'])
            
            # Truncar observaciones si son muy largas
            if observations and len(str(observations)) > 50:
                observations = str(observations)[:50] + '...'
            
            self.results_tree.insert('', 'end', values=(
                movement_id or '',
                movement_date or '',
                movement_type or '', 
                ticket_number or '',
                product_name or '',
                quantity or '',
                responsible or '',
                observations or ''
            ))
        
        # Mostrar contador de resultados
        self.window.title(f"Historial de Movimientos - {len(movements)} resultados encontrados")
    
    def _clear_results(self):
        """Limpiar resultados de búsqueda"""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.current_movements = []
        self._clear_details()
    
    def _clear_details(self):
        """Limpiar panel de detalles"""
        self.detail_id_var.set('')
        self.detail_product_id_var.set('')
        self.detail_obs_var.set('')
        self.selected_movement = None
    
    def _on_tree_select(self, event):
        """Manejar selección en Treeview"""
        selection = self.results_tree.selection()
        if not selection:
            return
        
        # Obtener item seleccionado
        item = self.results_tree.item(selection[0])
        values = item['values']
        
        if not values or not values[0]:  # No hay datos válidos
            return
        
        # Buscar movimiento correspondiente
        movement_id = values[0]
        movement = self._find_movement_by_id(movement_id)
        
        if movement:
            self._on_movement_selected(movement)
    
    def _find_movement_by_id(self, movement_id: Any) -> Optional[Any]:
        """Buscar movimiento por ID en resultados actuales"""
        for movement in self.current_movements:
            # CORRECCIÓN: Buscar por ambos nombres de campo posibles
            current_id = self._get_movement_field(movement, ['id', 'id_movimiento'])
            if str(current_id) == str(movement_id):
                return movement
        return None
    
    def _on_movement_selected(self, movement: Any):
        """Mostrar detalles del movimiento seleccionado"""
        self.selected_movement = movement
        
        # CORRECCIÓN: Mapear campos para detalles
        movement_id = self._get_movement_field(movement, ['id', 'id_movimiento'])
        product_id = self._get_movement_field(movement, ['product_id', 'id_producto'])
        observations = self._get_movement_field(movement, ['observations', 'observaciones'])
        
        # Actualizar panel de detalles
        self.detail_id_var.set(movement_id or '')
        self.detail_product_id_var.set(product_id or '')
        self.detail_obs_var.set(observations or '')
        
        logger.info(f"Movimiento seleccionado: ID {movement_id}")
    
    # ===============================
    # MÉTODOS DE EXPORTACIÓN
    # ===============================
    
    def _export_to_pdf(self):
        """Exportar resultados actuales a PDF"""
        if not self.current_movements:
            messagebox.showwarning("Sin Datos", "No hay movimientos para exportar")
            return
        
        try:
            # Generar nombre de archivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"historial_movimientos_{timestamp}.pdf"
            
            # Solicitar ubicación de guardado
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=filename,
                title="Guardar reporte PDF"
            )
            
            if not file_path:
                return
            
            # CORRECCIÓN CRÍTICA: Obtener filtros y pasarlos al export_service
            filters = self._get_search_filters()
            
            # Exportar usando servicio con filtros requeridos
            generated_pdf_path = self.export_service.export_movements_to_pdf(self.current_movements, filters)
            
            # CORRECCIÓN CRÍTICA: Usar shutil.move() para manejo cross-drive
            # shutil.move() maneja movimientos entre unidades diferentes
            try:
                shutil.move(generated_pdf_path, file_path)
                logger.info(f"Archivo PDF movido exitosamente: {generated_pdf_path} -> {file_path}")
                
            except (OSError, shutil.Error) as move_error:
                logger.warning(f"shutil.move() falló: {move_error}. Intentando método alternativo...")
                
                # FALLBACK: Método alternativo con copy + remove
                try:
                    # Copiar archivo a destino
                    shutil.copy2(generated_pdf_path, file_path)
                    logger.info(f"Archivo copiado exitosamente: {file_path}")
                    
                    # Eliminar archivo temporal original
                    import os
                    if os.path.exists(generated_pdf_path):
                        os.remove(generated_pdf_path)
                        logger.info(f"Archivo temporal eliminado: {generated_pdf_path}")
                        
                except Exception as fallback_error:
                    logger.error(f"Método fallback falló: {fallback_error}")
                    raise Exception(f"No se pudo mover archivo PDF. Error principal: {move_error}, Error fallback: {fallback_error}")
            
            messagebox.showinfo("Exportación Exitosa", f"Reporte PDF guardado en:\n{file_path}")
            logger.info(f"Exportación PDF exitosa: {file_path}")
            
        except Exception as e:
            logger.error(f"Error exportando PDF: {e}")
            messagebox.showerror("Error de Exportación", f"Error exportando PDF: {str(e)}")
    
    def _export_to_excel(self):
        """Exportar resultados actuales a Excel"""
        if not self.current_movements:
            messagebox.showwarning("Sin Datos", "No hay movimientos para exportar")
            return
        
        try:
            # Generar nombre de archivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"historial_movimientos_{timestamp}.xlsx"
            
            # Solicitar ubicación de guardado
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                initialfile=filename,
                title="Guardar reporte Excel"
            )
            
            if not file_path:
                return
            
            # CORRECCIÓN: Obtener filtros y pasarlos al export_service
            filters = self._get_search_filters()
            
            # Exportar usando servicio con filtros requeridos
            generated_excel_path = self.export_service.export_movements_to_excel(self.current_movements, filters)
            
            # CORRECCIÓN CRÍTICA: Usar shutil.move() para manejo cross-drive
            # shutil.move() maneja movimientos entre unidades diferentes
            try:
                shutil.move(generated_excel_path, file_path)
                logger.info(f"Archivo Excel movido exitosamente: {generated_excel_path} -> {file_path}")
                
            except (OSError, shutil.Error) as move_error:
                logger.warning(f"shutil.move() falló: {move_error}. Intentando método alternativo...")
                
                # FALLBACK: Método alternativo con copy + remove
                try:
                    # Copiar archivo a destino
                    shutil.copy2(generated_excel_path, file_path)
                    logger.info(f"Archivo copiado exitosamente: {file_path}")
                    
                    # Eliminar archivo temporal original
                    import os
                    if os.path.exists(generated_excel_path):
                        os.remove(generated_excel_path)
                        logger.info(f"Archivo temporal eliminado: {generated_excel_path}")
                        
                except Exception as fallback_error:
                    logger.error(f"Método fallback falló: {fallback_error}")
                    raise Exception(f"No se pudo mover archivo Excel. Error principal: {move_error}, Error fallback: {fallback_error}")
            
            messagebox.showinfo("Exportación Exitosa", f"Reporte Excel guardado en:\n{file_path}")
            logger.info(f"Exportación Excel exitosa: {file_path}")
            
        except Exception as e:
            logger.error(f"Error exportando Excel: {e}")
            messagebox.showerror("Error de Exportación", f"Error exportando Excel: {str(e)}")
    
    # ===============================
    # MÉTODOS DE FORMULARIO
    # ===============================
    
    def _clear_form(self):
        """Limpiar todos los campos del formulario"""
        # Limpiar filtros
        self.date_start_entry.delete(0, tk.END)
        self.date_start_entry.insert(0, (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        
        self.date_end_entry.delete(0, tk.END)
        self.date_end_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        self.transaction_type_combo.set('TODOS')
        self.ticket_search_entry.delete(0, tk.END)
        
        # Limpiar resultados y detalles
        self._clear_results()
        
        # Restaurar título
        self.window.title("Historial de Movimientos - Copy Point S.A.")
        
        logger.info("Formulario limpiado")
    
    def _close_form(self):
        """Cerrar formulario con limpieza"""
        try:
            # Limpiar estado
            self.current_movements = None
            self.selected_movement = None
            
            # Cerrar ventana
            if self.window:
                self.window.destroy()
                
            logger.info("MovementHistoryForm cerrado correctamente")
            
        except Exception as e:
            logger.error(f"Error cerrando formulario: {e}")
    
    def show(self):
        """Mostrar el formulario"""
        if self.window:
            self.window.deiconify()
            self.window.lift()
            self.window.focus_set()
    
    def destroy(self):
        """Destruir el formulario"""
        self._close_form()


# Funciones de utilidad para compatibilidad con tests
def create_movement_history_form(parent, db_connection):
    """Factory function para crear MovementHistoryForm"""
    return MovementHistoryForm(parent, db_connection)


if __name__ == "__main__":
    # Test básico del formulario
    root = tk.Tk()
    root.withdraw()
    
    # Mock database connection
    mock_db = type('MockDB', (), {})()
    
    try:
        form = MovementHistoryForm(root, mock_db)
        if form.window:
            form.show()
            root.mainloop()
    except Exception as e:
        print(f"Error en test: {e}")
    finally:
        root.destroy()
