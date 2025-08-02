"""
Formulario para generación masiva de etiquetas.

Este módulo proporciona una interfaz gráfica completa para:
- Selección de productos con filtros
- Configuración de cantidades por producto  
- Selección de templates de etiquetas
- Preview de etiquetas antes de generar
- Generación masiva de PDFs
- Impresión directa

Autor: Sistema de Inventario Copy Point S.A.
Fecha: Junio 2025
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Dict, Optional, Any
import tempfile
import os
import threading
from PIL import Image, ImageTk

# Imports del sistema
from models.producto import Producto
from models.categoria import Categoria
from services.product_service import ProductService
from services.category_service import CategoryService
from services.label_service import LabelService
from services.service_container import get_container
from ui.utils.window_manager import WindowManager

# Configurar logging
logger = logging.getLogger(__name__)


class LabelGeneratorForm(tk.Toplevel):
    """
    Formulario para generación masiva de etiquetas.
    
    Permite seleccionar productos, configurar cantidades y templates,
    y generar etiquetas en PDF para impresión masiva.
    """
    
    def __init__(self, parent=None):
        """
        Inicializar formulario de generación de etiquetas.
        
        Args:
            parent: Ventana padre
        """
        super().__init__(parent)
        
        container = get_container()
        self.product_service  = container.get('product_service')
        self.category_service = container.get('category_service')
        self.label_service    = container.get('label_service')

        # Configuración de ventana
        self.title("Generador de Etiquetas")
        self.geometry("1000x500")
        self.resizable(True, False)
        
        # Centrar ventana
        WindowManager.center_window(self, 1000, 600)
        
        # Variables
        self.parent = parent
        self.selected_products = {}  # {product_id: quantity}
        self.current_template = None
        self.preview_images = {}
        self.generation_thread = None
        
        # Variables Tkinter
        self.search_var = tk.StringVar()
        self.category_filter_var = tk.StringVar()
        self.template_var = tk.StringVar()
        self.quantity_var = tk.StringVar(value="1")
        self.default_quantity_var = tk.StringVar(value="1")
        self.include_price_var = tk.BooleanVar(value=True)
        self.include_category_var = tk.BooleanVar(value=False)
        self.include_barcode_var = tk.BooleanVar(value=True)
        self.label_format_var = tk.StringVar(value="standard")
        
        # Servicios ya obtenidos del ServiceContainer en líneas 47-49
        # No necesitan re-inicialización - usando dependency injection correctamente
        
        # Datos
        self.products = []
        self.categories = []
        self.templates = []
        
        # Configurar interfaz
        self.setup_ui()
        
        # Cargar datos iniciales
        self.load_initial_data()
        
        # Configurar eventos
        self.setup_events()
        
        logger.info("LabelGeneratorForm inicializado correctamente")
    
    def setup_ui(self):
        """Configurar interfaz de usuario."""
        try:
            # Frame principal
            main_frame = ttk.Frame(self)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Panel superior - Filtros y búsqueda
            self.setup_filter_panel(main_frame)
            
            # Panel central - Selección de productos y configuración
            center_paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
            center_paned.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
            
            # Panel izquierdo - Lista de productos
            self.setup_product_panel(center_paned)
            
            # Panel derecho - Configuración y preview
            self.setup_config_panel(center_paned)
            
            # Panel inferior - Botones de acción
            self.setup_action_panel(main_frame)
            
        except Exception as e:
            logger.error(f"Error configurando UI: {e}")
            raise
    
    def setup_filter_panel(self, parent):
        """Configurar panel de filtros y búsqueda."""
        filter_frame = ttk.LabelFrame(parent, text="Filtros y Búsqueda")
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Primera fila - Búsqueda
        search_frame = ttk.Frame(filter_frame)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(search_frame, text="Buscar:").pack(side=tk.LEFT)
        
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        self.search_button = ttk.Button(search_frame, text="Buscar", command=self.on_search)
        self.search_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_search_button = ttk.Button(search_frame, text="Limpiar", command=self.clear_search)
        self.clear_search_button.pack(side=tk.LEFT)
        
        # Segunda fila - Filtros
        filter_row = ttk.Frame(filter_frame)
        filter_row.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(filter_row, text="Categoría:").pack(side=tk.LEFT)
        
        self.category_combo = ttk.Combobox(filter_row, textvariable=self.category_filter_var, 
                                          width=20, state="readonly")
        self.category_combo.pack(side=tk.LEFT, padx=(5, 10))
        
        self.filter_button = ttk.Button(filter_row, text="Filtrar", command=self.on_category_filter_changed)
        self.filter_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.show_all_button = ttk.Button(filter_row, text="Mostrar Todos", command=self.show_all_products)
        self.show_all_button.pack(side=tk.LEFT)
    
    def setup_product_panel(self, parent):
        """Configurar panel de selección de productos con altura limitada a 15 líneas."""
        product_frame = ttk.LabelFrame(parent, text="Productos Disponibles: Haz click a todos los productos que quieras imprimir etiquetas")
        parent.add(product_frame, weight=1)
        
        # Frame contenedor del Treeview con altura fija
        tree_frame = ttk.Frame(product_frame)
        # No expandir verticalmente: sólo llenará hasta la altura que configuremos
        tree_frame.pack(fill=tk.X, expand=False, padx=10, pady=10)
        tree_frame.pack_propagate(False)
        # Ajusta este valor si tu tema tiene otra altura de fila; aprox. 15 filas × 20px + encabezado ≃ 350px
        tree_frame.configure(height=350)
        
        # Treeview para productos con 15 filas visibles
        columns = ('id', 'nombre', 'categoria', 'precio', 'stock')
        self.product_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='headings',
            height=15
        )  # height=15 garantiza 15 filas antes del scrollbar :contentReference[oaicite:1]{index=1}.
        
        # Configurar encabezados
        self.product_tree.heading('id', text='ID')
        self.product_tree.heading('nombre', text='Producto')
        self.product_tree.heading('categoria', text='Categoría')
        self.product_tree.heading('precio', text='Precio')
        self.product_tree.heading('stock', text='Stock')
        
        # Configurar ancho de columnas
        self.product_tree.column('id', width=50, anchor='center')
        self.product_tree.column('nombre', width=200)
        self.product_tree.column('categoria', width=100)
        self.product_tree.column('precio', width=80, anchor='e')
        self.product_tree.column('stock', width=80, anchor='center')
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.product_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.product_tree.xview)
        self.product_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Empaquetar Treeview y scrollbars dentro de tree_frame
        self.product_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Información y botones de selección debajo del Treeview
        selection_frame = ttk.Frame(product_frame)
        selection_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.selection_label = ttk.Label(selection_frame, text="Productos seleccionados: 0")
        self.selection_label.pack(side=tk.LEFT)
        
        ttk.Button(selection_frame, text="Seleccionar Todo", command=self.select_all_products)\
            .pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(selection_frame, text="Limpiar Selección", command=self.clear_selection)\
            .pack(side=tk.RIGHT)
    
    def setup_config_panel(self, parent):
        """Configurar panel de configuración y preview."""
        config_frame = ttk.LabelFrame(parent, text="Configuración de Etiquetas")
        parent.add(config_frame, weight=1)
        
        # Notebook para organizar configuraciones
        self.config_notebook = ttk.Notebook(config_frame)
        self.config_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Pestaña de template
        self.setup_template_tab()
        
        # Pestaña de cantidades
        self.setup_quantity_tab()
        
        # Pestaña de formato
        self.setup_format_tab()
        
        # Pestaña de preview
        self.setup_preview_tab()
    
    def setup_template_tab(self):
        """Configurar pestaña de template."""
        template_frame = ttk.Frame(self.config_notebook)
        self.config_notebook.add(template_frame, text="Modelos")
        
        # Selección de template
        ttk.Label(template_frame, text="Modelos de Etiqueta (Template):").pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        self.template_combo = ttk.Combobox(template_frame, textvariable=self.template_var, state="readonly", width=40)
        self.template_combo.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Información del template
        self.template_info_frame = ttk.LabelFrame(template_frame, text="Información del Modelo")
        self.template_info_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.template_info_label = ttk.Label(self.template_info_frame, text="Seleccione un Modelo", justify=tk.LEFT, wraplength=300)
        self.template_info_label.pack(padx=10, pady=10)
        
        # Botones de template
        template_buttons = ttk.Frame(template_frame)
        template_buttons.pack(fill=tk.X, padx=10)
        
        # ttk.Button(template_buttons, text="Crear Template Personalizado", 
        #          command=self.create_custom_template).pack(side=tk.LEFT)
    
    def setup_quantity_tab(self):
        """Configurar pestaña de cantidades."""
        quantity_frame = ttk.Frame(self.config_notebook)
        self.config_notebook.add(quantity_frame, text="Cantidades")
        
        # Cantidad por defecto
        default_frame = ttk.LabelFrame(quantity_frame, text="Configuración por Defecto")
        default_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(default_frame, text="Cantidad por defecto:").pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        quantity_default_frame = ttk.Frame(default_frame)
        quantity_default_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.default_quantity_spinbox = ttk.Spinbox(quantity_default_frame, 
                                                   textvariable=self.default_quantity_var,
                                                   from_=1, to=100, width=10)
        self.default_quantity_spinbox.pack(side=tk.LEFT)
        
        ttk.Button(quantity_default_frame, text="Aplicar a Todos", 
                  command=self.apply_default_quantity).pack(side=tk.LEFT, padx=(10, 0))
        
        # Cantidad individual
        individual_frame = ttk.LabelFrame(quantity_frame, text="Producto Seleccionado")
        individual_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(individual_frame, text="Cantidad para producto actual:").pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        self.quantity_spinbox = ttk.Spinbox(individual_frame, textvariable=self.quantity_var,
                                          from_=0, to=100, width=10)
        self.quantity_spinbox.pack(anchor=tk.W, padx=10, pady=(0, 10))
        
        # Resumen de cantidades
        summary_frame = ttk.LabelFrame(quantity_frame, text="Resumen")
        summary_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.quantity_summary_label = ttk.Label(summary_frame, text="Total de etiquetas: 0")
        self.quantity_summary_label.pack(padx=10, pady=10)
    
    def setup_format_tab(self):
        """Configurar pestaña de formato."""
        format_frame = ttk.Frame(self.config_notebook)
        self.config_notebook.add(format_frame, text="Formato")
        
        # Formato de etiqueta
        format_label_frame = ttk.LabelFrame(format_frame, text="Formato de Etiqueta")
        format_label_frame.pack(fill=tk.X, padx=10, pady=10)
        
        format_options = [("Estándar", "standard"), ("Mini", "mini"), ("Detallado", "detailed")]
        
        for text, value in format_options:
            ttk.Radiobutton(format_label_frame, text=text, variable=self.label_format_var, 
                           value=value).pack(anchor=tk.W, padx=10, pady=2)
        
        # Contenido de etiqueta
        content_frame = ttk.LabelFrame(format_frame, text="Contenido de Etiqueta")
        content_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Checkbutton(content_frame, text="Incluir Precio", 
                       variable=self.include_price_var).pack(anchor=tk.W, padx=10, pady=2)
        # ttk.Checkbutton(content_frame, text="Incluir Categoría", 
        #                variable=self.include_category_var).pack(anchor=tk.W, padx=10, pady=2)
        ttk.Checkbutton(content_frame, text="Incluir Código de Barras", 
                       variable=self.include_barcode_var).pack(anchor=tk.W, padx=10, pady=2)
    
    def setup_preview_tab(self):
        """Configurar pestaña de preview."""
        # Crear el frame de la pestaña y añadirla al notebook
        preview_frame = ttk.Frame(self.config_notebook)
        self.config_notebook.add(preview_frame, text="Preview")
        
        # Botón para generar el preview
        ttk.Button(preview_frame, text="Generar Preview", command=self.preview_labels).pack(pady=10)
        
        # Frame contenedor del canvas de preview con altura fija
        self.preview_canvas_frame = ttk.Frame(preview_frame)
        self.preview_canvas_frame.pack(fill=tk.X, expand=False, padx=10, pady=(0, 10))
        self.preview_canvas_frame.pack_propagate(False)
        self.preview_canvas_frame.configure(height=250)
        
        # Canvas para dibujar el preview (altura coincidente)
        self.preview_canvas = tk.Canvas(self.preview_canvas_frame, bg='white', height=250)
        preview_scroll = ttk.Scrollbar(
            self.preview_canvas_frame,
            orient=tk.VERTICAL,
            command=self.preview_canvas.yview
        )
        self.preview_canvas.configure(yscrollcommand=preview_scroll.set)
        
        # Empaquetar canvas y scrollbar
        self.preview_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        preview_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    
    def setup_action_panel(self, parent):
        """Configurar panel de botones de acción."""
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Frame para botones principales
        button_frame = ttk.Frame(action_frame)
        button_frame.pack(side=tk.RIGHT)
        
        self.preview_button = ttk.Button(button_frame, text="Preview", 
                                        command=self.preview_labels)
        self.preview_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.generate_button = ttk.Button(button_frame, text="Generar PDF", 
                                         command=self.generate_and_save)
        self.generate_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.print_button = ttk.Button(button_frame, text="Imprimir", 
                                      command=self.print_labels_direct)
        self.print_button.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(button_frame, text="Cerrar", 
                  command=self.destroy).pack(side=tk.LEFT, padx=(0, 5))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(action_frame, variable=self.progress_var, 
                                           mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(8, 0), padx=(10, 30))
        
        # Label de estado
        self.status_label = ttk.Label(action_frame, text="Listo")
        self.status_label.pack(anchor=tk.W, pady=(5, 0))
    
    def setup_events(self):
        """Configurar eventos de la interfaz."""
        # Eventos del treeview
        self.product_tree.bind('<<TreeviewSelect>>', self.on_product_selection_changed)
        self.product_tree.bind('<Double-1>', self.on_product_double_click)
        
        # Eventos de búsqueda
        self.search_entry.bind('<Return>', lambda e: self.on_search())
        self.search_var.trace('w', self.on_search_changed)
        
        # Eventos de cantidad
        self.quantity_var.trace('w', self.on_quantity_changed)
        
        # Eventos de template
        self.template_combo.bind('<<ComboboxSelected>>', self.on_template_changed)
        
        # Evento de cierre
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def load_initial_data(self):
        """Cargar datos iniciales."""
        try:
            self.update_status("Cargando datos...")
            
            # Cargar productos
            self.products = self.product_service.get_all_products()
            self.load_products_to_tree(self.products)
            
            # Cargar categorías
            self.categories = self.category_service.get_all_categories()
            self.load_categories_to_combo()
            
            # Cargar templates
            self.templates = self.label_service.get_available_templates()
            self.load_templates_to_combo()
            
            self.update_status("Datos cargados correctamente")
            
        except Exception as e:
            logger.error(f"Error cargando datos iniciales: {e}")
            messagebox.showerror("Error", f"Error cargando datos: {e}")
    
    def load_products_to_tree(self, products: List[Producto]):
        """Cargar productos en el treeview."""
        try:
            # Limpiar tree
            for item in self.product_tree.get_children():
                self.product_tree.delete(item)
            
            # Agregar productos
            for product in products:
                # Obtener nombre de categoría
                category_name = ""
                if product.id_categoria:
                    try:
                        category = self.category_service.get_category_by_id(product.id_categoria)
                        category_name = category.nombre if category else "Sin categoría"
                    except:
                        category_name = "Sin categoría"
                
                # Formatear precio
                precio_str = f"B/. {product.precio:.2f}" if product.precio else "N/A"
                
                # Insertar en tree
                self.product_tree.insert('', 'end', values=(
                    product.id_producto,
                    product.nombre,
                    category_name,
                    precio_str,
                    product.stock or 0
                ))
            
            self.update_selection_count()
            
        except Exception as e:
            logger.error(f"Error cargando productos en tree: {e}")
            raise
    
    def load_categories_to_combo(self):
        """Cargar categorías en el combobox."""
        try:
            category_names = ["Todas las categorías"] + [cat.nombre for cat in self.categories]
            self.category_combo['values'] = category_names
            self.category_combo.set("Todas las categorías")
        except Exception as e:
            logger.error(f"Error cargando categorías: {e}")
    
    def load_templates_to_combo(self):
        """Cargar templates en el combobox."""
        try:
            template_names = [f"{template['name']} - {template['description']}" 
                            for template in self.templates]
            self.template_combo['values'] = template_names
            
            if template_names:
                self.template_combo.set(template_names[0])
                self.on_template_changed()
                
        except Exception as e:
            logger.error(f"Error cargando templates: {e}")
    
    def on_search(self):
        """Manejar evento de búsqueda."""
        try:
            search_term = self.search_var.get().strip()
            
            if search_term:
                # Buscar productos
                results = self.product_service.search_products(search_term)
                self.load_products_to_tree(results)
                self.update_status(f"Encontrados {len(results)} productos")
            else:
                self.show_all_products()
                
        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            messagebox.showerror("Error", f"Error en búsqueda: {e}")
    
    def on_search_changed(self, *args):
        """Manejar cambio en campo de búsqueda."""
        # Búsqueda automática después de 500ms sin cambios
        if hasattr(self, '_search_timer'):
            self.after_cancel(self._search_timer)
        
        self._search_timer = self.after(500, self.on_search)
    
    def clear_search(self):
        """Limpiar búsqueda."""
        self.search_var.set("")
        self.show_all_products()
    
    def on_category_filter_changed(self):
        """Manejar cambio de filtro de categoría."""
        try:
            selected_category = self.category_filter_var.get()
            
            if selected_category == "Todas las categorías":
                self.show_all_products()
            else:
                # Encontrar categoría seleccionada
                category = next((cat for cat in self.categories 
                               if cat.nombre == selected_category), None)
                
                if category:
                    products = self.product_service.get_products_by_category(category.id_categoria)
                    self.load_products_to_tree(products)
                    self.update_status(f"Mostrando {len(products)} productos de {selected_category}")
                
        except Exception as e:
            logger.error(f"Error filtrando por categoría: {e}")
            messagebox.showerror("Error", f"Error filtrando: {e}")
    
    def show_all_products(self):
        """Mostrar todos los productos."""
        self.load_products_to_tree(self.products)
        self.category_filter_var.set("Todas las categorías")
        self.update_status(f"Mostrando {len(self.products)} productos")
    
    def on_product_selection_changed(self, event):
        """Manejar cambio de selección de productos."""
        try:
            selected_items = self.product_tree.selection()
            
            if selected_items:
                # Obtener primer producto seleccionado
                item = selected_items[0]
                values = self.product_tree.item(item, 'values')
                product_id = int(values[0])
                
                # Actualizar cantidad si ya está seleccionado
                if product_id in self.selected_products:
                    self.quantity_var.set(str(self.selected_products[product_id]))
                else:
                    self.quantity_var.set(self.default_quantity_var.get())
            
            self.update_selection_count()
            
        except Exception as e:
            logger.error(f"Error en selección de producto: {e}")
    
    def on_product_double_click(self, event):
        """Manejar doble clic en producto."""
        try:
            selected_items = self.product_tree.selection()
            
            if selected_items:
                item = selected_items[0]
                values = self.product_tree.item(item, 'values')
                product_id = int(values[0])
                quantity = int(self.quantity_var.get() or 1)
                
                # Agregar/actualizar selección
                if quantity > 0:
                    self.selected_products[product_id] = quantity
                    self.update_status(f"Producto {values[1]} agregado con cantidad {quantity}")
                else:
                    self.selected_products.pop(product_id, None)
                    self.update_status(f"Producto {values[1]} removido de selección")
                
                self.update_selection_count()
                
        except Exception as e:
            logger.error(f"Error en doble clic: {e}")
    
    def on_quantity_changed(self, *args):
        """Manejar cambio de cantidad."""
        try:
            selected_items = self.product_tree.selection()
            
            if selected_items:
                item = selected_items[0]
                values = self.product_tree.item(item, 'values')
                product_id = int(values[0])
                quantity = int(self.quantity_var.get() or 0)
                
                if quantity > 0:
                    self.selected_products[product_id] = quantity
                else:
                    self.selected_products.pop(product_id, None)
                
                self.update_selection_count()
                
        except Exception as e:
            logger.debug(f"Error actualizando cantidad: {e}")
    
    def on_template_changed(self, event=None):
        """Manejar cambio de template."""
        try:
            selected = self.template_combo.get()
            
            if selected:
                # Encontrar template por nombre
                template = next((t for t in self.templates 
                               if f"{t['name']} - {t['description']}" == selected), None)
                
                if template:
                    self.current_template = template
                    
                    # Actualizar información del template
                    info_text = f"""
Nombre: {template['name']}
Descripción: {template['description']}
Etiquetas por página: {template['labels_per_page']}
Tamaño de página: {template['page_size']}
"""
                    self.template_info_label.config(text=info_text.strip())
                    
        except Exception as e:
            logger.error(f"Error cambiando template: {e}")
    
    def select_all_products(self):
        """Seleccionar todos los productos visibles."""
        try:
            default_qty = int(self.default_quantity_var.get() or 1)
            
            for item in self.product_tree.get_children():
                values = self.product_tree.item(item, 'values')
                product_id = int(values[0])
                self.selected_products[product_id] = default_qty
            
            self.update_selection_count()
            self.update_status(f"Todos los productos seleccionados con cantidad {default_qty}")
            
        except Exception as e:
            logger.error(f"Error seleccionando todos: {e}")
            messagebox.showerror("Error", f"Error seleccionando productos: {e}")
    
    def clear_selection(self):
        """Limpiar selección de productos."""
        self.selected_products.clear()
        self.update_selection_count()
        self.update_status("Selección limpiada")
    
    def apply_default_quantity(self):
        """Aplicar cantidad por defecto a productos seleccionados."""
        try:
            default_qty = int(self.default_quantity_var.get() or 1)
            
            for product_id in self.selected_products:
                self.selected_products[product_id] = default_qty
            
            self.quantity_var.set(str(default_qty))
            self.update_selection_count()
            self.update_status(f"Cantidad {default_qty} aplicada a productos seleccionados")
            
        except Exception as e:
            logger.error(f"Error aplicando cantidad: {e}")
            messagebox.showerror("Error", f"Error aplicando cantidad: {e}")
    
    def update_selection_count(self):
        """Actualizar contador de selección."""
        try:
            count = len(self.selected_products)
            total_labels = sum(self.selected_products.values())
            
            self.selection_label.config(text=f"Productos seleccionados: {count}")
            self.quantity_summary_label.config(text=f"Total de etiquetas: {total_labels}")
            
        except Exception as e:
            logger.error(f"Error actualizando contador: {e}")
    
    def preview_labels(self):
        """Generar preview de etiquetas."""
        try:
            if not self.validate_selection():
                return
            
            self.update_status("Generando preview...")
            
            # Limpiar canvas
            self.preview_canvas.delete("all")
            
            # Obtener primer producto para preview
            first_product_id = next(iter(self.selected_products))
            product = next(p for p in self.products if p.id_producto == first_product_id)
            
            # Generar etiqueta de muestra
            label_image_data = self.label_service.create_product_label(
                product,
                format=self.label_format_var.get(),
                include_category=self.include_category_var.get(),
                include_price=self.include_price_var.get(),
                include_barcode=self.include_barcode_var.get()
            )
            
            # Mostrar en canvas
            self.show_preview_image(label_image_data)
            
            self.update_status("Preview generado")
            
        except Exception as e:
            logger.error(f"Error generando preview: {e}")
            messagebox.showerror("Error", f"Error generando preview: {e}")
    
    def show_preview_image(self, image_data: bytes):
        """Mostrar imagen de preview en canvas."""
        try:
            # Crear imagen PIL
            from io import BytesIO
            image_buffer = BytesIO(image_data)
            pil_image = Image.open(image_buffer)
            
            # Redimensionar para preview
            pil_image.thumbnail((300, 200), Image.Resampling.LANCZOS)
            
            # Convertir para Tkinter
            tk_image = ImageTk.PhotoImage(pil_image)
            
            # Mostrar en canvas
            self.preview_canvas.create_image(150, 100, image=tk_image)
            self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all"))
            
            # Mantener referencia
            self.preview_canvas.image = tk_image
            
        except Exception as e:
            logger.error(f"Error mostrando preview: {e}")
    
    def generate_and_save(self):
        """Generar PDF y guardar archivo."""
        try:
            if not self.validate_selection():
                return
            
            # Seleccionar archivo de destino
            filename = filedialog.asksaveasfilename(
                title="Guardar Etiquetas",
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
            )
            
            if not filename:
                return
            
            # Generar en hilo separado
            self.generation_thread = threading.Thread(
                target=self._generate_pdf_thread,
                args=(filename,)
            )
            self.generation_thread.start()
            
        except Exception as e:
            logger.error(f"Error iniciando generación: {e}")
            messagebox.showerror("Error", f"Error iniciando generación: {e}")
    
    def _generate_pdf_thread(self, filename: str):
        """Generar PDF en hilo separado."""
        try:
            self.update_status("Generando PDF...")
            self.progress_var.set(0)
            
            # Preparar datos de productos
            products_with_quantities = []
            total_products = len(self.selected_products)
            
            for i, (product_id, quantity) in enumerate(self.selected_products.items()):
                product = next(p for p in self.products if p.id_producto == product_id)
                
                for _ in range(quantity):
                    products_with_quantities.append({
                        'product': product,
                        'quantity': 1
                    })
                
                # Actualizar progreso
                progress = (i + 1) / total_products * 50  # 50% para preparación
                self.progress_var.set(progress)
            
            # Generar PDF
            self.update_status("Generando etiquetas...")
            
            pdf_data = self.label_service.generate_labels_pdf(
                products_with_quantities,
                template=self.current_template['id'],
                use_quantities=True,
                label_format=self.label_format_var.get()
            )
            
            self.progress_var.set(75)
            
            # Guardar archivo
            self.update_status("Guardando archivo...")
            
            with open(filename, 'wb') as f:
                f.write(pdf_data)
            
            self.progress_var.set(100)
            self.update_status("PDF generado exitosamente")
            
            # Mostrar mensaje de éxito
            self.after(0, lambda: messagebox.showinfo(
                "Éxito", 
                f"PDF generado exitosamente:\n{filename}"
            ))
            
            # Abrir archivo automáticamente
            self.after(0, lambda: self.open_file(filename))
            
        except Exception as e:
            logger.error(f"Error generando PDF: {e}")
            self.after(0, lambda: messagebox.showerror("Error", f"Error generando PDF: {e}"))
        finally:
            self.progress_var.set(0)
    
    def print_labels_direct(self):
        """Imprimir etiquetas directamente."""
        try:
            if not self.validate_selection():
                return
            
            self.update_status("Generando PDF para impresión...")
            
            # Preparar datos
            products_with_quantities = []
            for product_id, quantity in self.selected_products.items():
                product = next(p for p in self.products if p.id_producto == product_id)
                
                for _ in range(quantity):
                    products_with_quantities.append({
                        'product': product,
                        'quantity': 1
                    })
            
            # Generar PDF
            pdf_data = self.label_service.generate_labels_pdf(
                products_with_quantities,
                template=self.current_template['id'],
                use_quantities=True,
                label_format=self.label_format_var.get()
            )
            
            # Imprimir
            self.update_status("Enviando a impresora...")
            
            success = self.label_service.print_labels(pdf_data)
            
            if success:
                self.update_status("Etiquetas enviadas a impresora")
                messagebox.showinfo("Éxito", "Etiquetas enviadas a impresora exitosamente")
            else:
                self.update_status("Error en impresión")
                messagebox.showerror("Error", "Error enviando etiquetas a impresora")
                
        except Exception as e:
            logger.error(f"Error imprimiendo: {e}")
            messagebox.showerror("Error", f"Error imprimiendo etiquetas: {e}")
    
    # def create_custom_template(self):
    #     """Crear template personalizado."""
    #    # TODO: Implementar diálogo para crear template personalizado
    #    messagebox.showinfo("Información", "Funcionalidad de template personalizado en desarrollo")
    
    def validate_selection(self) -> bool:
        """Validar selección antes de generar."""
        if not self.selected_products:
            messagebox.showwarning("Advertencia", "Debe seleccionar al menos un producto")
            return False
        
        if not self.current_template:
            messagebox.showwarning("Advertencia", "Debe seleccionar un template")
            return False
        
        return True
    
    def update_status(self, message: str):
        """Actualizar mensaje de estado."""
        self.status_label.config(text=message)
        self.update_idletasks()
    
    def open_file(self, filepath: str):
        """Abrir archivo con aplicación por defecto."""
        try:
            import platform
            
            if platform.system() == "Windows":
                os.startfile(filepath)
            elif platform.system() == "Darwin":  # macOS
                os.system(f"open '{filepath}'")
            else:  # Linux
                os.system(f"xdg-open '{filepath}'")
                
        except Exception as e:
            logger.warning(f"No se pudo abrir archivo automáticamente: {e}")
    
    def on_closing(self):
        """Manejar cierre de ventana."""
        try:
            # Cancelar hilos activos
            if self.generation_thread and self.generation_thread.is_alive():
                # TODO: Implementar cancelación de hilo si es necesario
                pass
            
            self.destroy()
            
        except Exception as e:
            logger.error(f"Error cerrando ventana: {e}")
            self.destroy()


if __name__ == "__main__":
    # Test independiente
    root = tk.Tk()
    root.withdraw()
    
    form = LabelGeneratorForm(root)
    root.mainloop()
