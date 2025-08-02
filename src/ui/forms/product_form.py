"""
Corrección para product_form.py - Solución al problema de inicialización de CategoryService
Garantiza que todos los servicios reciban correctamente la conexión a la base de datos.
CORRECCIÓN CRÍTICA: Variable global BARCODE_SUPPORT manejada correctamente.
"""

import shutil
import datetime
from decimal import Decimal
import logging
import os
import tempfile
from datetime import datetime

import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename

from typing import Optional, List

import openpyxl

# Imports con Service Container Integration
try:
    from services.service_container import get_container
    from models.producto import Producto
    
    # Imports opcionales para códigos de barras (MODO TECLADO)
    try:
        from utils.barcode_utils import validate_barcode, BarcodeUtils, generate_product_code
        from ui.widgets.barcode_entry import BarcodeEntry
        BARCODE_SUPPORT = True
    except ImportError as e:
        print(f"Advertencia: Funcionalidades de códigos de barras no disponibles: {e}")
        BARCODE_SUPPORT = False
        
except ImportError as e:
    print(f"Error crítico importando dependencias: {e}")
    raise


class ProductWindow:
    """
    Ventana de gestión de productos con inicialización de servicios corregida.
    
    CORRECCIONES APLICADAS:
    - Inicialización robusta de servicios con manejo de errores
    - Validación de conexión de base de datos antes de crear servicios
    - Fallback para funcionalidades opcionales
    - CRÍTICO: Manejo correcto de variable global BARCODE_SUPPORT
    """
    
    def __init__(self, parent: tk.Tk):
        """Inicializa la ventana de productos con servicios correctamente configurados."""
        self.parent = parent
        
        # Configurar logging
        self.logger = logging.getLogger(f"ProductWindow.{id(self)}")
        self.logger.setLevel(logging.DEBUG)
        
        if not self.logger.handlers:
            file_handler = logging.FileHandler('product_form_debug.log')
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        self.logger.info("=== INICIANDO ProductWindow con inicialización corregida ===")
        
        # Variable de instancia para códigos de barras (evita problemas con variable global)
        self.barcode_support = BARCODE_SUPPORT
        
        # Inicializar servicios con manejo de errores robusto
        self._initialize_services()
        
        # Continuar solo si los servicios se inicializaron correctamente
        if not self._validate_services():
            messagebox.showerror("Error Fatal", "No se pudieron inicializar los servicios necesarios")
            return
        
        # Crear ventana
        self.root = tk.Toplevel(parent)
        self.root.title("Gestión de Productos")
        window_width = 900 if self.barcode_support else 750
        self.root.geometry(f"{window_width}x500")
        self.root.transient(parent)
        self.root.grab_set()
        
        # Inicializar variables de formulario
        self._initialize_form_variables()
        
        # Estado del formulario
        self.editing_product: Optional[Producto] = None
        self.is_creating_new = False
        self.products: List[Producto] = []
        self.categories: List = []
        
        # Crear interfaz
        self._create_user_interface()
        self._setup_event_handlers()
        self._load_initial_data()
        
        self.logger.info("ProductWindow inicializado correctamente")
    
    # === PROPIEDADES LAZY PARA SERVICIOS DEL CONTAINER ===
    
    @property
    def product_service(self):
        """Obtiene ProductService del container (lazy)."""
        return self.container.get('product_service')
    
    @property
    def category_service(self):
        """Obtiene CategoryService del container (lazy)."""
        return self.container.get('category_service')
    
    @property
    def label_service(self):
        """Obtiene LabelService del container si está disponible (lazy)."""
        if self.barcode_support and self.container.is_registered('label_service'):
            return self.container.get('label_service')
        return None
    
    @property
    def barcode_service(self):
        """Obtiene BarcodeService del container si está disponible (lazy)."""
        if self.barcode_support and self.container.is_registered('barcode_service'):
            return self.container.get('barcode_service')
        return None
        
    def _initialize_services(self):
        """Inicializa servicios usando Service Container."""
        self.logger.info("Inicializando servicios con Service Container...")
        
        try:
            # Obtener Service Container configurado
            self.container = get_container()
            
            # Validar servicios principales requeridos
            required_services = ['product_service', 'category_service']
            for service in required_services:
                if not self.container.is_registered(service):
                    raise Exception(f"Servicio principal '{service}' no está registrado en el container")
            
            self.logger.info("Servicios principales validados en container")
            
            # Verificar servicios opcionales de códigos de barras
            if self.barcode_support:
                barcode_services = ['label_service', 'barcode_service']
                missing_services = []
                
                for service in barcode_services:
                    if not self.container.is_registered(service):
                        missing_services.append(service)
                
                if missing_services:
                    self.logger.warning(f"Servicios de barcode no disponibles: {missing_services}")
                    self.barcode_support = False
                else:
                    self.logger.info("Servicios de códigos de barras disponibles en container")
            
            self.logger.info(f"Servicios inicializados: barcode_support={self.barcode_support}")
            
        except Exception as e:
            self.logger.error(f"Error inicializando servicios: {e}")
            self._show_service_error(e)
            
    def _validate_services(self) -> bool:
        """Valida que los servicios críticos estén disponibles en el container."""
        try:
            # Intentar obtener servicios principales del container
            product_service = self.container.get('product_service')
            category_service = self.container.get('category_service')
            
            if product_service is None or category_service is None:
                self.logger.error("Servicios principales no disponibles en container")
                return False
                
            self.logger.info("Validación de servicios exitosa")
            return True
            
        except Exception as e:
            self.logger.error(f"Error validando servicios: {e}")
            return False
        
    def _show_service_error(self, error: Exception):
        """Muestra error de inicialización de servicios al usuario."""
        error_msg = f"No se pudo conectar a la base de datos: {error}"
        self.logger.error(error_msg)
        messagebox.showerror("Error de Conexión", error_msg)
        
    def _initialize_form_variables(self):
        """Inicializa todas las variables del formulario."""
        # Variables básicas
        self.product_name_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.stock_var = tk.StringVar()
        self.cost_var = tk.StringVar()
        self.price_var = tk.StringVar()
        self.tax_var = tk.StringVar()
        
        # === NUEVAS VARIABLES SISTEMA FILTROS ===
        self.filter_var = tk.StringVar()
        self.filter_var.set("Activos")  # Filtro por defecto
        
        # Estado interno para filtros
        self.current_filter_status = "active"  # active, inactive, all
        self.displayed_products = []  # Productos actualmente mostrados
        
        # SIMPLIFICADO: Variables de barcode UI eliminadas (innecesarias)
        # Solo mantener funcionalidad de escaneo si está disponible
        
    def _create_user_interface(self):
        """Crea la interfaz de usuario adaptativa."""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configurar grid
        main_frame.columnconfigure(0, weight=0)
        main_frame.columnconfigure(1, weight=1)  # Botones
        main_frame.rowconfigure(1, weight=1)  # Formulario
        main_frame.rowconfigure(2, weight=2)  # Lista de productos
        
        # Título SIMPLIFICADO (sin referencia a códigos de barras)
        title_label = ttk.Label(
            main_frame,
            text="Gestión de Productos",  # Título simple
            font=("Arial", 16, "bold"),
            foreground="darkblue"
        )
        title_label.grid(row=0, column=0, pady=(0, 10))
        
        # Panel de Botones
        self._create_button_panel(main_frame)
        
        # Panel Formulario
        self._create_form_panel(main_frame)

        # Panel Lista de productos
        self._create_product_list_panel(main_frame)

    def _create_button_panel(self, parent):
        """Crea el panel de botones en 2 columnas."""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=1, column=1, sticky=(tk.N, tk.W), padx=(10, 10), pady=(4, 0))

        # Botones principales en 2 columnas (3 filas)
        self.new_button = ttk.Button(button_frame, text="Nuevo", command=self._new_product)
        self.new_button.grid(row=0, column=0, padx=5, pady=3, sticky="ew")

        self.save_button = ttk.Button(button_frame, text="Guardar", command=self._save_product, state='disabled')
        self.save_button.grid(row=0, column=1, padx=5, pady=3, sticky="ew")

        self.edit_button = ttk.Button(button_frame, text="Editar", command=self._edit_product, state='disabled')
        self.edit_button.grid(row=1, column=0, padx=5, pady=3, sticky="ew")

        self.delete_button = ttk.Button(button_frame, text="Eliminar", command=self._delete_product, state='disabled')
        self.delete_button.grid(row=1, column=1, padx=5, pady=3, sticky="ew")

        # === NUEVO: BOTÓN REACTIVAR ===
        self.reactivate_button = ttk.Button(
            button_frame, 
            text="Reactivar", 
            command=self._reactivate_product, 
            state='disabled'
        )
        self.reactivate_button.grid(row=2, column=0, padx=5, pady=3, sticky="ew")

        self.cancel_button = ttk.Button(button_frame, text="Cancelar", command=self._cancel_edit, state='disabled')
        self.cancel_button.grid(row=2, column=1, padx=5, pady=3, sticky="ew")

        close_button = ttk.Button(button_frame, text="Cerrar", command=self._close_window)
        close_button.grid(row=3, column=0, columnspan=2, padx=5, pady=3, sticky="ew")

        # Botón de Importar Excel
        self.import_button = ttk.Button(button_frame, text="Importar Productos x Excel", command=self._import_from_excel)
        self.import_button.grid(row=5, column=0, columnspan=2, padx=5, pady=3, sticky="ew")

        # Botón para descargar archivo de ejemplo
        self.download_sample_button = ttk.Button(button_frame, text="Descargar Ejemplo Excel", command=self._download_sample_excel)
        self.download_sample_button.grid(row=6, column=0, columnspan=2, padx=5, pady=3, sticky="ew")

        # Botón de escanear (solo si hay soporte)
        if self.barcode_support:
            scan_button = ttk.Button(button_frame, text="Buscar por Código", command=self._scan_barcode)
            scan_button.grid(row=4, column=0, columnspan=2, padx=5, pady=(4, 5), sticky="ew")

        # Expansión uniforme por columna
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)


    def _create_product_list_panel(self, parent):
        """Crea el panel de lista de productos con sistema de filtros."""
        list_frame = ttk.LabelFrame(parent, text="Lista de Productos", padding=10)
        list_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5), pady=(15, 0))
        
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(2, weight=1)  # Cambiar a fila 2 para TreeView
        
        # === NUEVO: FRAME DE FILTROS Y BÚSQUEDA ===
        controls_frame = ttk.Frame(list_frame)
        controls_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        controls_frame.columnconfigure(3, weight=1)  # Búsqueda se expande
        
        # Widget de filtro
        ttk.Label(controls_frame, text="Filtro:").grid(row=0, column=0, padx=(0, 5))
        
        self.filter_combobox = ttk.Combobox(
            controls_frame, 
            textvariable=self.filter_var,
            values=["Activos", "Inactivos", "Todos"],
            state='readonly',
            width=12
        )
        self.filter_combobox.grid(row=0, column=1, padx=(0, 10))
        
        # Campo de búsqueda (movido a la misma fila)
        ttk.Label(controls_frame, text="Buscar por nombre:").grid(row=0, column=2, padx=(10, 5))
        search_entry = ttk.Entry(controls_frame, textvariable=self.search_var)
        search_entry.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=(0, 5))
        
        # === NUEVO: FRAME DE ESTADÍSTICAS ===
        stats_frame = ttk.Frame(list_frame)
        stats_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.stats_label = ttk.Label(
            stats_frame, 
            text="Cargando productos...",
            font=("Arial", 9),
            foreground="gray"
        )
        self.stats_label.grid(row=0, column=0, sticky=tk.W)
        
        # SIMPLIFICADO: TreeView sin columna "Código" redundante
        columns = ('ID', 'Nombre', 'Categoría', 'Stock', 'Precio', 'Estado')
        self.product_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        # Configurar columnas
        for col in columns:
            self.product_tree.heading(col, text=col)
        
        # Ancho de columnas optimizado
        self.product_tree.column('ID', width=50)   # ID visible (que es el código)
        self.product_tree.column('Nombre', width=180)
        self.product_tree.column('Categoría', width=100)
        self.product_tree.column('Stock', width=70, anchor='e')
        self.product_tree.column('Precio', width=80, anchor='e')
        self.product_tree.column('Estado', width=70, anchor='center')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.product_tree.yview)
        self.product_tree.configure(yscrollcommand=scrollbar.set)
        
        self.product_tree.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=2, column=1, sticky=(tk.N, tk.S))
        
    def _create_form_panel(self, parent):
        """Crea el panel del formulario SIMPLIFICADO sin pestaña de códigos."""
        form_frame = ttk.LabelFrame(parent, text="Datos del Producto: Seleccione Nuevo para crear o haga click en un producto para editar", padding=10)
        form_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0), pady=(15, 0))
        
        form_frame.columnconfigure(1, weight=1)
        
        # SIMPLIFICADO: Siempre usar formulario básico (sin notebook/pestañas)
        self._create_basic_form_fields(form_frame)
            
    # ELIMINADO: _create_basic_info_tab() - Ya no es necesario (sin notebook)
        
    def _create_basic_form_fields(self, parent):
        """Crea los campos básicos del formulario."""
        parent.columnconfigure(1, weight=1)
        
        row = 0
        
        # Nombre
        ttk.Label(parent, text="Nombre:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.name_entry = ttk.Entry(parent, textvariable=self.product_name_var, width=30)
        self.name_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Categoría
        ttk.Label(parent, text="Categoría:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.category_combo = ttk.Combobox(parent, textvariable=self.category_var, state='readonly', width=27)
        self.category_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Stock
        ttk.Label(parent, text="Stock:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.stock_entry = ttk.Entry(parent, textvariable=self.stock_var, width=30, justify='right')
        self.stock_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Costo
        ttk.Label(parent, text="Costo:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.cost_entry = ttk.Entry(parent, textvariable=self.cost_var, width=30, justify='right')
        self.cost_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Precio
        ttk.Label(parent, text="Precio:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.price_entry = ttk.Entry(parent, textvariable=self.price_var, width=30, justify='right')
        self.price_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Impuesto
        ttk.Label(parent, text="Impuesto (%):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.tax_entry = ttk.Entry(parent, textvariable=self.tax_var, width=30, justify='right')
        self.tax_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        
    # ELIMINADO: _create_barcode_tab() - Ya no es necesario
        
        
    def _setup_event_handlers(self):
        """Configura los manejadores de eventos con filtros."""
        self.product_tree.bind('<<TreeviewSelect>>', self._on_product_select)
        self.search_var.trace('w', self._on_search)
        self.product_name_var.trace('w', self._validate_form)
        self.category_var.trace('w', self._validate_form)
        
        # === NUEVO: HANDLER DE FILTRO ===
        self.filter_var.trace('w', self._on_filter_change)
        
        # SIMPLIFICADO: Ya no hay handlers de código de barras
            
        self.root.protocol("WM_DELETE_WINDOW", self._close_window)
        
    def _load_initial_data(self):
        """Carga los datos iniciales con filtro por defecto."""
        try:
            self.logger.info("Cargando datos iniciales con sistema de filtros...")
            
            # Cargar categorías
            self.categories = self.category_service.get_all_categories()
            category_names = [f"{cat.nombre} ({cat.tipo})" for cat in self.categories]
            self.category_combo['values'] = category_names
            self.logger.info(f"Cargadas {len(self.categories)} categorías")
            
            # === NUEVO: CARGAR PRODUCTOS CON FILTRO POR DEFECTO ===
            self._load_products_by_filter()
            
            self.logger.info(f"Cargados {len(self.displayed_products)} productos con filtro '{self.filter_var.get()}'")
            self._update_product_list()
            self._update_stats_label()
            
        except Exception as e:
            self.logger.error(f"Error cargando datos: {e}")
            messagebox.showerror("Error", f"Error cargando datos: {e}")
            
    def _update_product_list(self, search_filter: str = ""):
        """Actualiza la lista de productos con filtros y búsqueda."""
        # Limpiar TreeView
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
        
        # Aplicar filtro de búsqueda adicional si existe
        products_to_show = self.displayed_products
        if search_filter:
            products_to_show = [
                p for p in self.displayed_products 
                if search_filter.lower() in p.nombre.lower()
            ]
        
        # Agregar productos al TreeView
        for product in products_to_show:
            # Buscar nombre de categoría
            category_name = "N/A"
            for cat in self.categories:
                if cat.id_categoria == product.id_categoria:
                    category_name = cat.nombre
                    break
            
            # Estado del producto
            estado = "Activo" if product.activo else "Inactivo"
            
            # SIMPLIFICADO: Sin columna "Código" redundante
            # El ID ya representa el código automáticamente
            values = (
                product.id_producto,      # ID (que sirve como código)
                product.nombre,
                category_name,
                product.stock,
                f"B/. {float(product.precio):.2f}",
                estado
            )
            
            # Insertar en TreeView
            item_id = self.product_tree.insert('', tk.END, values=values)
                
    # === MÉTODOS DE CÓDIGOS DE BARRAS (SOLO SI ESTÁN DISPONIBLES) ===
    
    # ELIMINADOS: Métodos innecesarios de barcode UI
    # - _generate_barcode()
    # - _validate_barcode() 
    # - _clear_barcode()
        
    def _scan_barcode(self):
        """Abre ventana de escaneo SIMPLIFICADA."""
        if not self.barcode_support:
            return
        
        # Crear ventana de escaneo
        scan_window = tk.Toplevel(self.root)
        scan_window.title("Escanear Código de Barras")
        scan_window.geometry("400x200")
        scan_window.transient(self.root)
        scan_window.grab_set()
        
        # Frame principal
        main_frame = ttk.Frame(scan_window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Instrucciones
        ttk.Label(
            main_frame, 
            text="Introduzca el código del producto:\nPor teclado o use scanner",
            justify=tk.CENTER
        ).pack(pady=(0, 15))
        
        # Campo de escaneo simplificado
        scan_var = tk.StringVar()
        scan_entry = ttk.Entry(main_frame, textvariable=scan_var, width=20, font=('Consolas', 12))
        scan_entry.pack(pady=(0, 15))
        scan_entry.focus()
        
        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack()
        
        ttk.Button(
            button_frame, 
            text="Buscar", 
            command=lambda: self._search_product_by_id(scan_var.get(), scan_window)
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Cerrar", 
            command=scan_window.destroy
        ).pack(side=tk.LEFT, padx=5)

    def _search_product_by_id(self, product_id_str: str, scan_window: tk.Toplevel):
        """Busca producto por ID (código) SIMPLIFICADO."""
        if not product_id_str.strip():
            return
        
        try:
            product_id = int(product_id_str.strip())
            
            # Buscar en la lista de productos actuales
            found_product = None
            for product in self.displayed_products:
                if product.id_producto == product_id:
                    found_product = product
                    break
            
            if found_product:
                # Mostrar producto encontrado
                self._show_product_in_form(found_product)
                
                # Seleccionar en TreeView
                for item in self.product_tree.get_children():
                    values = self.product_tree.item(item)['values']
                    if values[0] == product_id:
                        self.product_tree.selection_set(item)
                        self.product_tree.see(item)
                        break
                
                # Habilitar botones de edición
                self.edit_button.config(state='normal')
                self.delete_button.config(state='normal')
                
                messagebox.showinfo(
                    "Producto Encontrado", 
                    f"Producto: {found_product.nombre}\nCódigo: {product_id}"
                )
                scan_window.destroy()
            else:
                messagebox.showinfo(
                    "Producto No Encontrado", 
                    f"No se encontró un producto con el código '{product_id}'"
                )
                
        except ValueError:
            messagebox.showerror("Error", "El código debe ser un número válido")
    
    def _handle_scanned_code(self, code: str, is_valid: bool, scan_window: tk.Toplevel):
        """Maneja código escaneado desde la ventana de escaneo."""
        if not code.strip():
            return
        
        if not is_valid:
            messagebox.showwarning("Código Inválido", "El código escaneado no es válido")
            return
        
        # Buscar producto
        try:
            product = self.barcode_service.search_product_by_code(code)
            
            if product:
                # Mostrar producto encontrado
                self._show_product_in_form(product)
                self._on_product_found_by_barcode(product)
                scan_window.destroy()
            else:
                result = messagebox.askyesno(
                    "Producto No Encontrado",
                    f"No se encontró un producto con el código '{code}'.\n¿Desea usar este código para un nuevo producto?"
                )
                
                if result:
                    self.barcode_var.set(code)
                    scan_window.destroy()
                    self._new_product()  # Crear nuevo producto con este código
                    
        except Exception as e:
            messagebox.showerror("Error", f"Error buscando producto: {e}")
    
    def _on_product_found_by_barcode(self, product: Producto):
        """Maneja cuando se encuentra un producto por código de barras."""
        # Seleccionar el producto en la lista
        for item in self.product_tree.get_children():
            values = self.product_tree.item(item)['values']
            if values[0] == product.id_producto:
                self.product_tree.selection_set(item)
                self.product_tree.see(item)
                break
        
        # Habilitar botones de edición
        self.edit_button.config(state='normal')
        self.delete_button.config(state='normal')
        
        messagebox.showinfo(
            "Producto Encontrado", 
            f"Producto: {product.nombre}\nID: {product.id_producto}"
        )
    
    # ELIMINADOS: Métodos adicionales innecesarios de barcode
    # - _on_barcode_scanned() 
    # - _search_by_barcode()
    # - _on_barcode_changed()
            
    # === MÉTODOS PRINCIPALES DEL FORMULARIO ===
    
    def _validate_form(self, *args):
        """Valida el formulario."""
        name = self.product_name_var.get().strip()
        category = self.category_var.get().strip()
        
        if (self.is_creating_new or self.editing_product is not None) and name and category:
            self.save_button.config(state='normal')
        else:
            self.save_button.config(state='disabled')
            
    def _save_product(self):
        """Guarda el producto."""
        try:
            # Validar datos
            name = self.product_name_var.get().strip()
            if not name:
                messagebox.showerror("Error", "El nombre es obligatorio")
                return
                
            category_selection = self.category_combo.get()
            if not category_selection:
                messagebox.showerror("Error", "Debe seleccionar una categoría")
                return
                
            category_index = self.category_combo.current()
            if category_index == -1:
                messagebox.showerror("Error", "Categoría no válida")
                return
                
            selected_category = self.categories[category_index]
            
            # Valores numéricos
            try:
                stock = int(float(self.stock_var.get() or "0"))
                cost = float(self.cost_var.get() or "0")
                price = float(self.price_var.get() or "0")
                tax_rate = float(self.tax_var.get() or "0")
            except ValueError:
                messagebox.showerror("Error", "Valores numéricos inválidos")
                return
            
            # Guardar producto
            if self.is_creating_new:
                result = self.product_service.create_product(
                    nombre=name,
                    categoria_id=selected_category.id_categoria,
                    stock_inicial=stock,
                    precio_compra=cost,
                    precio_venta=price,
                    tasa_impuesto=tax_rate
                )
                
                if result:
                    messagebox.showinfo("Éxito", "Producto creado exitosamente")
                    self._load_products_by_filter()
                    self._update_product_list()
                    self._update_stats_label()
                    self._cancel_edit()
                else:
                    messagebox.showerror("Error", "No se pudo crear el producto")
                    
            else:
                updated_product = self.product_service.update_product(
                    id_producto=self.editing_product.id_producto,
                    nombre=name,
                    id_categoria=selected_category.id_categoria,
                    stock=stock,
                    costo=cost,
                    precio=price,
                    tasa_impuesto=tax_rate
                )
                
                if updated_product:
                    messagebox.showinfo("Éxito", "Producto actualizado exitosamente")
                    self._load_products_by_filter()
                    self._update_product_list()
                    self._update_stats_label()
                    self._cancel_edit()
                else:
                    messagebox.showerror("Error", "No se pudo actualizar el producto")
                    
        except Exception as e:
            self.logger.error(f"Error guardando producto: {e}")
            messagebox.showerror("Error", f"Error guardando producto: {e}")
            
    def _new_product(self):
        """Crear nuevo producto."""
        self._clear_form()
        self.editing_product = None
        self.is_creating_new = True
        self._enable_form()
        
        self.new_button.config(state='disabled')
        self.edit_button.config(state='disabled')
        self.delete_button.config(state='disabled')
        self.cancel_button.config(state='normal')
        
        self.name_entry.focus()
        
    def _import_from_excel(self):
        """Importa productos desde un archivo Excel (.xlsx)."""
        # 1. Selección de archivo
        filepath = askopenfilename(
            title="Seleccionar archivo Excel",
            filetypes=[("Archivos Excel", "*.xlsx *.xls")]
        )
        if not filepath:
            return

        try:
            wb = openpyxl.load_workbook(filepath, data_only=True)
            sheet = wb.active
            rows = list(sheet.iter_rows(values_only=True))
            headers = [h.strip().lower() for h in rows[0]]

            # Validar que existan las columnas esperadas
            expected = {'nombre','categoría','stock','costo','precio','impuesto'}
            if not expected.issubset(set(headers)):
                messagebox.showerror(
                    "Formato inválido",
                    f"Faltan columnas: {expected - set(headers)}"
                )
                return

            count = 0
            for row in rows[1:]:
                data = dict(zip(headers, row))
                # Buscar categoría por nombre
                cat_name = data['categoría']
                cat = next((c for c in self.categories if c.nombre.lower() in cat_name.lower()), None)
                if not cat:
                    continue  # o mostrar warning

                # Leer valores
                nombre = str(data['nombre']).strip()
                stock = int(data.get('stock') or 0)
                costo = float(data.get('costo') or 0)
                precio = float(data.get('precio') or 0)
                impuesto = float(data.get('impuesto') or 0)

                # Crear producto
                result = self.product_service.create_product(
                    nombre=nombre,
                    categoria_id=cat.id_categoria,
                    stock_inicial=stock,
                    precio_compra=costo,
                    precio_venta=precio,
                    tasa_impuesto=impuesto
                )
                if result:
                    count += 1

            messagebox.showinfo("Importación completada", f"Se importaron {count} productos.")
            self._load_initial_data()

        except Exception as e:
            messagebox.showerror("Error al importar", f"No se pudo leer el archivo:\n{e}")

    def _download_sample_excel(self):
        """Permite guardar una copia local del archivo de ejemplo de importación."""
        # Ruta del archivo de ejemplo embebido en la aplicación
        sample_path = r"D:\inventario_app2\data\ejemplo_importacion_productos.xlsx"

        # Diálogo para escoger dónde guardar
        save_path = asksaveasfilename(
            title="Guardar archivo de ejemplo",
            initialfile="ejemplo_importacion_productos.xlsx",
            defaultextension=".xlsx",
            filetypes=[("Archivos Excel", "*.xlsx")]
        )
        # Si el usuario cancela
        if not save_path:
            return

        try:
            # Copiar el archivo al destino elegido
            shutil.copy(sample_path, save_path)
            messagebox.showinfo(
                "Descarga completada",
                f"Archivo de ejemplo guardado en:\n{save_path}"
            )
        except Exception as e:
            messagebox.showerror(
                "Error al guardar",
                f"No se pudo guardar el archivo de ejemplo:\n{e}"
            )

    def _edit_product(self):
        """Editar producto seleccionado."""
        selection = self.product_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un producto para editar")
            return
            
        item = self.product_tree.item(selection[0])
        product_id = int(item['values'][0])
        
        # Buscar producto
        selected_product = None
        for product in self.displayed_products:
            if product.id_producto == product_id:
                selected_product = product
                break
                
        if selected_product:
            self.editing_product = selected_product
            self.is_creating_new = False
            self._enable_form()
            
            self.new_button.config(state='disabled')
            self.edit_button.config(state='disabled')
            self.delete_button.config(state='disabled')
            self.cancel_button.config(state='normal')
            
            self.name_entry.focus()
            
    def _delete_product(self):
        """Eliminar producto seleccionado."""
        selection = self.product_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un producto para eliminar")
            return
            
        item = self.product_tree.item(selection[0])
        product_id = int(item['values'][0])
        product_name = item['values'][1]  # Índice simplificado sin columna Código
        
        result = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Está seguro que desea eliminar '{product_name}'?"
        )
        
        if result:
            try:
                success = self.product_service.delete_product(product_id)
                if success:
                    messagebox.showinfo("Éxito", "Producto eliminado exitosamente")
                    self._load_initial_data()
                    self._clear_form()
                    self._disable_form()
                    self.edit_button.config(state='disabled')
                    self.delete_button.config(state='disabled')
                else:
                    messagebox.showerror("Error", "No se pudo eliminar el producto")
            except Exception as e:
                messagebox.showerror("Error", f"Error eliminando producto: {e}")
                
    def _cancel_edit(self):
        """Cancelar edición."""
        self.editing_product = None
        self.is_creating_new = False
        self._clear_form()
        self._disable_form()
        
        self.new_button.config(state='normal')
        self.save_button.config(state='disabled')
        self.edit_button.config(state='disabled')
        self.delete_button.config(state='disabled')
        self.cancel_button.config(state='disabled')
        
    def _clear_form(self):
        """Limpiar formulario."""
        self.product_name_var.set("")
        self.category_var.set("")
        self.stock_var.set("")
        self.cost_var.set("")
        self.price_var.set("")
        self.tax_var.set("")
        
        # SIMPLIFICADO: Ya no hay campos de código de barras que limpiar
            
        for item in self.product_tree.selection():
            self.product_tree.selection_remove(item)
            
    def _enable_form(self):
        """Habilitar formulario."""
        self.name_entry.config(state='normal')
        self.category_combo.config(state='readonly')
        self.stock_entry.config(state='normal')
        self.cost_entry.config(state='normal')
        self.price_entry.config(state='normal')
        self.tax_entry.config(state='normal')
        
        # SIMPLIFICADO: Ya no hay campos de código de barras que habilitar
            
    def _disable_form(self):
        """Deshabilitar formulario."""
        self.name_entry.config(state='readonly')
        self.category_combo.config(state='disabled')
        self.stock_entry.config(state='readonly')
        self.cost_entry.config(state='readonly')
        self.price_entry.config(state='readonly')
        self.tax_entry.config(state='readonly')
        
        # SIMPLIFICADO: Ya no hay campos de código de barras que deshabilitar
            
    def _on_product_select(self, event):
        """Manejar selección de producto con lógica de reactivación."""
        selection = self.product_tree.selection()
        if selection:
            item = self.product_tree.item(selection[0])
            product_id = int(item['values'][0])
            
            # Buscar producto en la lista actual
            selected_product = None
            for product in self.displayed_products:
                if product.id_producto == product_id:
                    selected_product = product
                    break
                    
            if selected_product:
                self._show_product_in_form(selected_product)
                
                # Habilitar botones según estado del producto
                if selected_product.activo:
                    # Producto activo: habilitar editar y eliminar
                    self.edit_button.config(state='normal')
                    self.delete_button.config(state='normal')
                    self.reactivate_button.config(state='disabled')
                else:
                    # Producto inactivo: solo habilitar reactivar
                    self.edit_button.config(state='disabled')
                    self.delete_button.config(state='disabled')
                    self.reactivate_button.config(state='normal')
                
                self._disable_form()
                
    def _show_product_in_form(self, product: Producto):
        """Mostrar producto en formulario."""
        self.product_name_var.set(product.nombre)
        self.stock_var.set(str(product.stock))
        self.cost_var.set(f"{float(product.costo):.2f}")
        self.price_var.set(f"{float(product.precio):.2f}")
        self.tax_var.set(f"{float(product.tasa_impuesto):.2f}")
        
        # Seleccionar categoría
        for i, cat in enumerate(self.categories):
            if cat.id_categoria == product.id_categoria:
                self.category_combo.current(i)
                break
                
        # NOTA: El código es simplemente el ID del producto
        # No se necesita campo separado para mostrarlo
            
    def _on_search(self, *args):
        """Manejar búsqueda combinada con filtros."""
        search_text = self.search_var.get()
        self._update_product_list(search_text)
        
        # Actualizar estadísticas con filtro de búsqueda
        if search_text:
            filtered_count = len([
                p for p in self.displayed_products 
                if search_text.lower() in p.nombre.lower()
            ])
            current_filter = self.filter_var.get()
            self.stats_label.config(
                text=f"Búsqueda '{search_text}': {filtered_count} productos {current_filter.lower()}"
            )
        else:
            self._update_stats_label()
        
    def _close_window(self):
        """Cerrar ventana."""
        if self.editing_product is not None or self.is_creating_new:
            result = messagebox.askyesno(
                "Confirmar Cierre",
                "Hay cambios sin guardar. ¿Está seguro?"
            )
            if not result:
                return
                
        self.root.destroy()
    
    # === NUEVOS MÉTODOS SISTEMA FILTROS Y REACTIVACIÓN ===
    
    def _load_products_by_filter(self):
        """Carga productos según el filtro actual."""
        try:
            filter_map = {
                "Activos": "active",
                "Inactivos": "inactive", 
                "Todos": "all"
            }
            
            current_filter = self.filter_var.get()
            status = filter_map.get(current_filter, "active")
            self.current_filter_status = status
            
            # Usar método del ProductService para filtrar
            self.displayed_products = self.product_service.get_products_by_status(status)
            
            self.logger.debug(f"Filtro '{current_filter}': {len(self.displayed_products)} productos cargados")
            
        except Exception as e:
            self.logger.error(f"Error filtrando productos: {e}")
            self.displayed_products = []
    
    def _on_filter_change(self, *args):
        """Maneja cambio de filtro."""
        try:
            self.logger.debug(f"Cambio de filtro a: {self.filter_var.get()}")
            
            # Cargar productos con nuevo filtro
            self._load_products_by_filter()
            
            # Actualizar interfaz
            self._update_product_list()
            self._update_stats_label()
            
            # Limpiar selección y deshabilitar botones
            self._clear_selection()
            
        except Exception as e:
            self.logger.error(f"Error en cambio de filtro: {e}")
            messagebox.showerror("Error", f"Error cambiando filtro: {e}")
    
    def _update_stats_label(self):
        """Actualiza la etiqueta de estadísticas."""
        try:
            current_filter = self.filter_var.get()
            count = len(self.displayed_products)
            
            # Obtener conteos adicionales para estadísticas completas
            if current_filter == "Todos":
                # Mostrar desglose cuando se muestran todos
                activos_count = len([p for p in self.displayed_products if p.activo])
                inactivos_count = len([p for p in self.displayed_products if not p.activo])
                stats_text = f"Total: {count} productos | Activos: {activos_count} | Inactivos: {inactivos_count}"
            else:
                stats_text = f"Mostrando: {count} productos {current_filter.lower()}"
            
            self.stats_label.config(text=stats_text)
            
        except Exception as e:
            self.logger.error(f"Error actualizando estadísticas: {e}")
            self.stats_label.config(text="Error en estadísticas")
    
    def _clear_selection(self):
        """Limpia la selección actual y deshabilita botones."""
        # Limpiar selección en TreeView
        for item in self.product_tree.selection():
            self.product_tree.selection_remove(item)
        
        # Deshabilitar botones de acción
        self.edit_button.config(state='disabled')
        self.delete_button.config(state='disabled')
        self.reactivate_button.config(state='disabled')
        
        # Limpiar formulario si no está en modo edición
        if not self.is_creating_new and self.editing_product is None:
            self._clear_form()
    
    def _reactivate_product(self):
        """Reactivar producto inactivo seleccionado."""
        selection = self.product_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un producto inactivo para reactivar")
            return
        
        try:
            # Obtener ID del producto seleccionado
            item = self.product_tree.item(selection[0])
            product_id = int(item['values'][0])
            product_name = item['values'][1]  # Índice simplificado sin columna Código
            
            # Verificar que el producto esté inactivo
            selected_product = None
            for product in self.displayed_products:
                if product.id_producto == product_id:
                    selected_product = product
                    break
            
            if selected_product and selected_product.activo:
                messagebox.showwarning("Advertencia", "El producto seleccionado ya está activo")
                return
            
            # Confirmar reactivación
            result = messagebox.askyesno(
                "Confirmar Reactivación",
                f"¿Está seguro que desea reactivar '{product_name}'?"
            )
            
            if result:
                # Llamar al ProductService para reactivar
                success = self.product_service.reactivate_product(product_id)
                
                if success:
                    messagebox.showinfo("Éxito", f"Producto '{product_name}' reactivado exitosamente")
                    
                    # Recargar datos y mantener filtro actual
                    self._load_products_by_filter()
                    self._update_product_list()
                    self._update_stats_label()
                    self._clear_selection()
                    
                else:
                    messagebox.showerror("Error", "No se pudo reactivar el producto")
                    
        except Exception as e:
            self.logger.error(f"Error reactivando producto: {e}")
            messagebox.showerror("Error", f"Error reactivando producto: {e}")


def main():
    """Función principal para pruebas."""
    root = tk.Tk()
    root.withdraw()
    
    try:
        product_window = ProductWindow(root)
        root.wait_window(product_window.root)
    except Exception as e:
        messagebox.showerror("Error", f"Error: {e}")
        
    root.destroy()


if __name__ == "__main__":
    main()
