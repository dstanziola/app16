"""
MovementAdjustForm - Formulario de ajustes individuales de producto
Arquitectura: Clean Architecture - Capa Presentación
Patrón: MVP + Service Layer + TDD
Requerimientos: Sección 3.2 - Ajustes de Producto
FLUJO DIRECTO SIMPLIFICADO
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional
import logging
from datetime import datetime
import subprocess
import os

# Importaciones del sistema
from services.service_container import get_container
from utils.logger import get_logger

# Importaciones de widgets reutilizables
from ui.widgets.product_search_widget import ProductSearchWidget


class MovementAdjustForm:
    """
    Formulario para ajustes individuales de productos en inventario
    FLUJO DIRECTO SIMPLIFICADO
    
    Responsabilidades:
    - Interfaz para ajustar un producto por movimiento
    - Validación de permisos de administrador
    - Búsqueda y autoselección automática de productos
    - Validación cantidades positivas/negativas
    - Motivos predefinidos de ajuste
    - Flujo directo: código → cantidad → REGISTRAR (genera ticket automáticamente)
    - Solo confirmación para imprimir ticket
    
    Patrón Arquitectónico: MVP
    - Model: Services (MovementService, ProductService, ExportService)
    - View: Tkinter UI components  
    - Presenter: Esta clase (MovementAdjustForm)
    """
    
    def __init__(self, parent, db_connection):
        """
        Constructor del formulario de ajustes
        
        Args:
            parent: Ventana padre
            db_connection: Conexión a base de datos
            
        Raises:
            PermissionError: Si el usuario no tiene permisos de administrador
        """
        self.parent = parent
        self.db = db_connection
        self.window = None
        self.logger = get_logger(__name__)
        
        # Estado del formulario (simplificado)
        self.selected_product: Optional[Dict] = None
        
        # Variables de Tkinter
        self.adjustment_quantity = tk.StringVar(value="0")
        self.responsible_var = tk.StringVar()
        
        # Widgets principales
        self.product_search_widget: Optional[ProductSearchWidget] = None
        self.selected_product_label: Optional[ttk.Label] = None
        self.quantity_entry: Optional[ttk.Entry] = None
        self.reason_combobox: Optional[ttk.Combobox] = None
        self.observations_text: Optional[tk.Text] = None
        
        # Botones simplificados
        self.register_btn: Optional[ttk.Button] = None
        self.cancel_btn: Optional[ttk.Button] = None
        self.close_btn: Optional[ttk.Button] = None
        
        # Lazy loading de servicios
        self._movement_service = None
        self._product_service = None
        self._export_service = None
        self._session_manager = None
        
        # Validar permisos de administrador
        self._validate_admin_permissions()
        
        # Crear interfaz
        self._create_interface()
        
        # Configurar foco inicial en búsqueda de producto
        if self.product_search_widget:
            self.product_search_widget.set_focus()
        
        self.logger.info("MovementAdjustForm inicializado con flujo directo simplificado")
    
    def _validate_admin_permissions(self):
        """
        Valida que el usuario actual tenga permisos de administrador
        
        Raises:
            PermissionError: Si el usuario no tiene permisos de administrador
        """
        current_user = self.session_manager.get_current_user()
        
        if not current_user:
            raise PermissionError("No hay usuario autenticado")
        
        if not self.session_manager.has_permission('admin'):
            raise PermissionError("Acceso denegado. Solo administradores pueden gestionar ajustes")
    
    def _create_interface(self):
        """Crear la interfaz principal del formulario"""
        # Crear ventana principal
        self.window = tk.Toplevel(self.parent)
        self.window.title("Gestión de Ajustes al Inventario")
        self.window.geometry("700x600")
        self.window.resizable(False, False)
        
        # Centrar ventana
        self._center_window()
        
        # Crear widgets principales
        self._create_title_panel()
        self._create_product_search_panel()
        self._create_adjustment_details_panel()
        self._create_buttons_panel_simplified()
        
        # Configurar validaciones
        self._setup_validations()
    
    def _center_window(self):
        """Centra la ventana en la pantalla"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_title_panel(self):
        """Crear el panel de título"""
        title_frame = ttk.Frame(self.window)
        title_frame.pack(fill=tk.X, padx=20, pady=15)
        
        title_label = ttk.Label(
            title_frame, 
            text="Gestión de Ajustes al Inventario",
            font=("Arial", 16, "bold")
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            title_frame,
            text="Código de producto y dele clic → Cantidad → Motivo → Observaciones → REGISTRAR",
            font=("Arial", 10)
        )
        subtitle_label.pack(pady=(5, 0))
    
    def _create_product_search_panel(self):
        """Crear panel de búsqueda de productos con autoselección"""
        search_frame = ttk.LabelFrame(self.window, text="Búsqueda de Producto", padding=10)
        search_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Widget de búsqueda reutilizable con autoselección
        self.product_search_widget = ProductSearchWidget(
            search_frame, 
            self.product_service
        )
        self.product_search_widget.pack(fill=tk.X)
        
        # Configurar callback para selección automática
        self.product_search_widget.on_product_selected = self._on_product_selected
        
        # Label para producto seleccionado
        self.selected_product_label = ttk.Label(
            search_frame,
            text="Ingrese código de producto por teclado o lector de código de barras",
            foreground="gray",
            font=("Arial", 10, "italic")
        )
        self.selected_product_label.pack(pady=(10, 0))
    
    def _create_adjustment_details_panel(self):
        """Crear panel de detalles del ajuste"""
        details_frame = ttk.LabelFrame(self.window, text="Detalles del Ajuste", padding=10)
        details_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Configurar grid
        details_frame.grid_columnconfigure(1, weight=1)
        
        # Cantidad de ajuste
        ttk.Label(details_frame, text="Cantidad de ajuste:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        
        self.quantity_entry = ttk.Entry(
            details_frame,
            textvariable=self.adjustment_quantity,
            width=15,
            font=("Arial", 12)
        )
        self.quantity_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(details_frame, text="(Positivo: suma, Negativo: resta)", 
                 foreground="gray", font=("Arial", 8)).grid(
            row=0, column=2, sticky="w", padx=5
        )
        
        # Motivo del ajuste (con valor por defecto)
        ttk.Label(details_frame, text="Motivo:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        
        self.reason_combobox = ttk.Combobox(
            details_frame,
            values=[
                "CORRECCIÓN INVENTARIO FÍSICO",
                "PRODUCTO DAÑADO",
                "PRODUCTO VENCIDO",
                "ERROR SISTEMA",
                "ROBO/PÉRDIDA",
                "OTRO"
            ],
            state="readonly",
            width=30
        )
        self.reason_combobox.grid(row=1, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        self.reason_combobox.set("CORRECCIÓN INVENTARIO FÍSICO")  # Valor por defecto
        
        # Responsable (automático del usuario actual)
        ttk.Label(details_frame, text="Responsable:").grid(
            row=2, column=0, sticky="w", padx=5, pady=5
        )
        
        current_user = self.session_manager.get_current_user()
        self.responsible_var.set(current_user.nombre_usuario if current_user else "")
        
        responsible_entry = ttk.Entry(
            details_frame,
            textvariable=self.responsible_var,
            width=30,
            state="readonly"  # Solo lectura, se establece automáticamente
        )
        responsible_entry.grid(row=2, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # Observaciones (opcional)
        ttk.Label(details_frame, text="Observaciones (opcional):").grid(
            row=3, column=0, sticky="nw", padx=5, pady=5
        )
        
        self.observations_text = tk.Text(
            details_frame,
            width=50,
            height=3
        )
        self.observations_text.grid(row=3, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # Scrollbar para observaciones
        obs_scrollbar = ttk.Scrollbar(details_frame, orient="vertical", command=self.observations_text.yview)
        obs_scrollbar.grid(row=3, column=3, sticky="ns", pady=5)
        self.observations_text.configure(yscrollcommand=obs_scrollbar.set)
    
    def _create_buttons_panel_simplified(self):
        """Crear panel de botones simplificado (3 botones únicamente)"""
        buttons_frame = ttk.Frame(self.window)
        buttons_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Frame principal para los 3 botones
        main_buttons_frame = ttk.Frame(buttons_frame)
        main_buttons_frame.pack(fill=tk.X)
        
        # Botón REGISTRAR AJUSTE (acción principal)
        self.register_btn = ttk.Button(
            main_buttons_frame,
            text="REGISTRAR AJUSTE",
            command=self._register_adjustment_direct,
            style="Accent.TButton",
            width=20
        )
        self.register_btn.pack(side=tk.LEFT, padx=5)
        
        # Botón CANCELAR (limpiar formulario)
        self.cancel_btn = ttk.Button(
            main_buttons_frame,
            text="CANCELAR",
            command=self._clear_form,
            width=15
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # Botón CERRAR (cerrar formulario)
        self.close_btn = ttk.Button(
            main_buttons_frame,
            text="CERRAR",
            command=self.destroy,
            width=15
        )
        self.close_btn.pack(side=tk.RIGHT, padx=5)
        
        # Instrucciones de uso
        instructions_frame = ttk.Frame(buttons_frame)
        instructions_frame.pack(fill=tk.X, pady=(10, 0))
        
        instructions_label = ttk.Label(
            instructions_frame,
            text="1) Busque producto por código  2) Ingrese cantidad  3) REGISTRAR genera movimiento y ticket automáticamente",
            font=("Arial", 9),
            foreground="blue"
        )
        instructions_label.pack()
    
    def _setup_validations(self):
        """Configurar validaciones en tiempo real"""
        # Validación de cantidad en tiempo real
        self.adjustment_quantity.trace("w", self._on_quantity_change)
        
        # Configurar Enter en campo cantidad para registro rápido
        if self.quantity_entry:
            self.quantity_entry.bind("<Return>", lambda e: self._register_adjustment_direct())
    
    def _on_product_selected(self, product: Dict, **kwargs):
        """
        Callback cuando se selecciona un producto automáticamente
        
        Args:
            product: Diccionario con datos del producto seleccionado
        """
        self.selected_product = product
        
        # Actualizar label con información completa
        stock_info = f" (Stock actual: {product.get('stock_actual', 'N/A')})" if 'stock_actual' in product else ""
        category_info = f" | Categoría: {product.get('categoria', 'N/A')}"
        
        self.selected_product_label.config(
            text=f"✓ Producto: {product['nombre']}{stock_info}{category_info}",
            foreground="green",
            font=("Arial", 10, "bold")
        )
        
        # Enfocar automáticamente en cantidad después de selección
        if self.quantity_entry:
            self.quantity_entry.focus_set()
            self.quantity_entry.select_range(0, tk.END)
        
        self.logger.debug(f"Producto auto-seleccionado: {product['nombre']}")
    
    def _on_quantity_change(self, *args):
        """Callback cuando cambia la cantidad"""
        quantity_str = self.adjustment_quantity.get()
        
        # Validación visual en tiempo real
        if self._validate_quantity(quantity_str):
            if self.quantity_entry:
                self.quantity_entry.config(foreground="black")
        else:
            if self.quantity_entry:
                self.quantity_entry.config(foreground="red")
    
    def _validate_quantity(self, quantity_str: str) -> bool:
        """
        Validar que la cantidad sea un entero válido (positivo o negativo)
        
        Args:
            quantity_str: String de la cantidad a validar
            
        Returns:
            bool: True si es válida, False en caso contrario
        """
        if not quantity_str or quantity_str.strip() == "":
            return False
        
        try:
            quantity = int(quantity_str)
            # No permitir cero (debe ser ajuste real)
            return quantity != 0
        except ValueError:
            return False
    
    def _register_adjustment_direct(self) -> bool:
        """
        Registrar el ajuste de inventario en flujo directo
        NUEVO: Un solo método que ejecuta todo el proceso
        
        Returns:
            bool: True si se completó exitosamente, False en caso contrario
        """
        try:
            # Paso 1: Validaciones previas
            if not self._validate_form_complete():
                return False
            
            # Paso 2: Preparar datos del ajuste
            adjustment_data = self._prepare_adjustment_data()
            
            # Paso 3: Crear movimiento en el servicio
            self.logger.info("Registrando ajuste de inventario...")
            result = self.movement_service.create_ajuste_inventario(
                id_producto=adjustment_data['product_id'],
                cantidad_ajuste=adjustment_data['quantity'],
                responsable=adjustment_data['responsible'],
                motivo=adjustment_data['reason']
            )
            
            # Convertir resultado a formato esperado por el resto del código
            if result and hasattr(result, 'id_movimiento'):
                result = {
                    'success': True,
                    'id': result.id_movimiento
                }
            else:
                result = {'success': False}
            
            if not result or not result.get('success'):
                messagebox.showerror(
                    "Error", 
                    "Error al registrar el ajuste en la base de datos",
                    parent=self.window
                )
                return False
            
            movement_id = result['id']
            
            # Paso 4: Generar ticket PDF automáticamente
            self.logger.info(f"Generando ticket para movimiento {movement_id}...")
            ticket = self.export_service.generate_adjustment_ticket(
                movement_id, 
                adjustment_data
            )
            
            # Paso 5: Mostrar resultado y opción de impresión
            if ticket:
                # Mostrar mensaje de éxito
                success_message = (
                    f"✓ Ajuste registrado exitosamente\n\n"
                    f"• ID de Movimiento: {movement_id}\n"
                    f"• Producto: {adjustment_data['product_name']}\n"
                    f"• Cantidad: {adjustment_data['quantity']:+d}\n"
                    f"• Motivo: {adjustment_data['reason']}\n"
                    f"• Ticket PDF generado automáticamente"
                )
                
                messagebox.showinfo(
                    "Ajuste Completado",
                    success_message,
                    parent=self.window
                )
                
                # Preguntar si desea imprimir ticket (única confirmación)
                print_ticket = messagebox.askyesno(
                    "Imprimir Ticket",
                    "¿Desea abrir el ticket para visualizarlo e imprimirlo?",
                    parent=self.window
                )
                
                if print_ticket:
                    self._open_ticket_for_printing(ticket)
                
            else:
                # Ajuste registrado pero sin ticket
                messagebox.showwarning(
                    "Parcialmente Completado",
                    f"✓ Ajuste registrado exitosamente (ID: {movement_id})\n"
                    f"⚠ Error al generar ticket PDF",
                    parent=self.window
                )
            
            # Paso 6: Limpiar formulario para siguiente ajuste
            self._clear_form()
            
            self.logger.info(f"Ajuste completado exitosamente: ID {movement_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error en flujo directo de ajuste: {e}")
            messagebox.showerror(
                "Error", 
                f"Error procesando ajuste: {str(e)}",
                parent=self.window
            )
            return False
    
    def _validate_form_complete(self) -> bool:
        """
        Validar el formulario completo para flujo directo
        
        Returns:
            bool: True si es válido, False en caso contrario
        """
        # Producto seleccionado
        if not self.selected_product:
            messagebox.showerror(
                "Error", 
                "Debe seleccionar un producto.\n\nIngrese el código por teclado o lector de código de barras.",
                parent=self.window
            )
            # Enfocar en búsqueda
            if self.product_search_widget:
                self.product_search_widget.set_focus()
            return False
        
        # Cantidad válida (no cero)
        if not self._validate_quantity(self.adjustment_quantity.get()):
            messagebox.showerror(
                "Error", 
                "La cantidad debe ser un número entero diferente de cero.\n\n• Positivo: suma al stock\n• Negativo: resta del stock",
                parent=self.window
            )
            # Enfocar en cantidad
            if self.quantity_entry:
                self.quantity_entry.focus_set()
                self.quantity_entry.select_range(0, tk.END)
            return False
        
        # Motivo seleccionado (debería tener valor por defecto)
        if not self.reason_combobox.get():
            messagebox.showerror(
                "Error", 
                "Debe seleccionar un motivo del ajuste",
                parent=self.window
            )
            if self.reason_combobox:
                self.reason_combobox.focus_set()
            return False
        
        # Responsable (se establece automáticamente)
        if not self.responsible_var.get().strip():
            messagebox.showerror(
                "Error", 
                "Error: No se pudo determinar el usuario responsable",
                parent=self.window
            )
            return False
        
        return True
    
    def _prepare_adjustment_data(self) -> Dict:
        """
        Preparar datos del ajuste para enviar al servicio
        
        Returns:
            Dict: Datos del ajuste preparados
        """
        current_user = self.session_manager.get_current_user()
        
        return {
            'product_id': self.selected_product['id'],
            'product_name': self.selected_product['nombre'],
            'quantity': int(self.adjustment_quantity.get()),
            'reason': self.reason_combobox.get(),
            'observations': self.observations_text.get('1.0', tk.END).strip(),
            'responsible': self.responsible_var.get().strip(),
            'user_id': current_user.id if current_user else None,
            'timestamp': datetime.now().isoformat(),
            'movement_type': 'AJUSTE'
        }
    
    def _open_ticket_for_printing(self, ticket):
        """
        Abrir ticket PDF para visualización e impresión
        Args:
            ticket: instancia de Ticket con atributo .pdf_path
        """
        pdf_path = getattr(ticket, 'pdf_path', None)
        if not pdf_path or not os.path.exists(pdf_path):
            messagebox.showerror(
                "Error",
                f"No se encontró el archivo PDF:\n{pdf_path}",
                parent=self.window
            )
            return

        try:
            if os.name == 'nt':  # Windows
                os.startfile(pdf_path)
            else:  # macOS / Linux
                subprocess.run(['xdg-open', pdf_path], check=False)
        except Exception as e:
            messagebox.showerror(
                "Error abriendo PDF",
                f"No se pudo abrir el PDF:\n{e}",
                parent=self.window
            )
    
    def _clear_form(self):
        """Limpiar el formulario completamente"""
        # Limpiar búsqueda de producto
        if self.product_search_widget:
            self.product_search_widget.clear_selection()
        
        # Limpiar variables
        self.selected_product = None
        self.adjustment_quantity.set("0")
        
        # Limpiar widgets
        if self.selected_product_label:
            self.selected_product_label.config(
                text="Ingrese código de producto por teclado o lector de código de barras",
                foreground="gray",
                font=("Arial", 10, "italic")
            )
        
        # Restablecer motivo por defecto
        if self.reason_combobox:
            self.reason_combobox.set("CORRECCIÓN INVENTARIO FÍSICO")
        
        # Limpiar observaciones
        if self.observations_text:
            self.observations_text.delete('1.0', tk.END)
        
        # Mantener responsable actual
        current_user = self.session_manager.get_current_user()
        self.responsible_var.set(current_user.nombre_usuario if current_user else "")
        
        # Enfocar en búsqueda para siguiente producto
        if self.product_search_widget:
            self.product_search_widget.set_focus()
        
        self.logger.debug("Formulario limpiado - listo para siguiente ajuste")
    
    # ============================================================================
    # COMPATIBILIDAD - Métodos legacy mantenidos para evitar breaking changes
    # ============================================================================
    
    def _register_adjustment(self) -> bool:
        """
        Método legacy mantenido para compatibilidad
        Ahora redirige al nuevo flujo directo
        
        Returns:
            bool: True si se completó exitosamente, False en caso contrario
        """
        self.logger.info("Usando método legacy _register_adjustment - redirigiendo a flujo directo")
        return self._register_adjustment_direct()
    
    # ============================================================================
    # LAZY LOADING DE SERVICIOS (Properties)
    # ============================================================================
    
    @property
    def movement_service(self):
        """Lazy loading del MovementService"""
        if self._movement_service is None:
            container = get_container()
            self._movement_service = container.get('movement_service')
        return self._movement_service
    
    @property
    def product_service(self):
        """Lazy loading del ProductService"""
        if self._product_service is None:
            container = get_container()
            self._product_service = container.get('product_service')
        return self._product_service
    
    @property
    def export_service(self):
        """Lazy loading del ExportService"""
        if self._export_service is None:
            container = get_container()
            self._export_service = container.get('export_service')
        return self._export_service
    
    @property
    def session_manager(self):
        """Lazy loading del SessionManager"""
        if self._session_manager is None:
            container = get_container()
            self._session_manager = container.get('session_manager')
        return self._session_manager
    
    def destroy(self):
        """Destruir la ventana y limpiar recursos"""
        try:
            if self.window:
                self.window.destroy()
                self.window = None
            self.logger.info("MovementAdjustForm destruido correctamente")
        except Exception as e:
            self.logger.error(f"Error al destruir MovementAdjustForm: {e}")
