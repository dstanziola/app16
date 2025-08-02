"""
MovementForm - Formulario principal de gestión de movimientos
Arquitectura: Clean Architecture - Capa Presentación
Patrón: MVP + Service Layer + TDD
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging

# Importaciones del sistema
from services.service_container import get_container
from utils.logger import get_logger

# Importaciones de subformularios (lazy loading)
# from ui.forms.movement_entry_form import MovementEntryForm
# from ui.forms.movement_adjust_form import MovementAdjustForm
# from ui.forms.movement_history_form import MovementHistoryForm
# MovementStockForm se importa dinámicamente en _open_stock_low_form()


class MovementForm:
    """
    Formulario principal para gestión de movimientos de inventario
    
    Responsabilidades:
    - Interfaz principal con 4 botones de acceso
    - Validación de permisos de administrador
    - Lazy loading de servicios
    - Navegación a subformularios
    """
    
    def __init__(self, parent, db_connection):
        """
        Constructor del formulario principal
        
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
        
        # Lazy loading de servicios usando ServiceContainer
        self._movement_service = None
        self._product_service = None
        self._export_service = None
        self._session_manager = None
        self._container = None
        
        # Validar permisos de administrador
        self._validate_admin_permissions()
        
        # Crear interfaz principal
        self._create_main_interface()
        
        self.logger.info("MovementForm inicializado correctamente")
    
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
            raise PermissionError("Acceso denegado. Solo administradores pueden gestionar movimientos")
    
    def _create_main_interface(self):
        """
        Crea la interfaz principal con 4 botones de acceso
        """
        # Crear ventana principal
        self.window = tk.Toplevel(self.parent)
        self.window.title("Gestión de Movimientos de Inventario")
        self.window.geometry("600x400")
        self.window.resizable(False, False)
        
        # Centrar ventana
        self._center_window()
        
        # Crear widgets principales
        self._create_title_panel()
        self._create_buttons_panel()
        self._create_status_bar()
    
    def _center_window(self):
        """Centra la ventana en la pantalla"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_title_panel(self):
        """Crea el panel de título"""
        title_frame = ttk.Frame(self.window)
        title_frame.pack(fill=tk.X, padx=20, pady=20)
        
        title_label = ttk.Label(
            title_frame, 
            text="Gestión de Movimientos de Inventario",
            font=("Arial", 16, "bold")
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            title_frame,
            text="Seleccione el tipo de movimiento a gestionar",
            font=("Arial", 10)
        )
        subtitle_label.pack(pady=(5, 0))
    
    def _create_buttons_panel(self):
        """Crea el panel con los 4 botones principales"""
        buttons_frame = ttk.Frame(self.window)
        buttons_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Configurar grid
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        buttons_frame.grid_rowconfigure(0, weight=1)
        buttons_frame.grid_rowconfigure(1, weight=1)
        
        # Botón 1: Entradas al Inventario
        self.btn_entries = ttk.Button(
            buttons_frame,
            text="ENTRADAS AL\nINVENTARIO",
            command=self._open_entries_form,
            width=20
        )
        self.btn_entries.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Botón 2: Ajustes de Producto
        self.btn_adjustments = ttk.Button(
            buttons_frame,
            text="AJUSTES DE\nPRODUCTO",
            command=self._open_adjustments_form,
            width=20
        )
        self.btn_adjustments.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # Botón 3: Historial de Movimientos
        self.btn_history = ttk.Button(
            buttons_frame,
            text="HISTORIAL DE\nMOVIMIENTOS",
            command=self._open_history_form,
            # command=self._feature_under_construction,
            width=20
        )
        self.btn_history.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        # Botón 4: Stock Bajo
        self.btn_stock_low = ttk.Button(
            buttons_frame,
            text="STOCK BAJO",
            command=self._open_stock_low_form,
            # command=self._feature_under_construction,
            width=20
        )
        self.btn_stock_low.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
    
    def _create_status_bar(self):
        """Crea la barra de estado"""
        status_frame = ttk.Frame(self.window)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        current_user = self.session_manager.get_current_user()
        user_text = f"Usuario: {current_user.nombre_usuario}" if current_user else "Usuario: Sin autenticar"
        
        status_label = ttk.Label(status_frame, text=user_text)
        status_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Botón cerrar
        close_btn = ttk.Button(
            status_frame,
            text="Cerrar",
            command=self.destroy
        )
        close_btn.pack(side=tk.RIGHT, padx=10, pady=5)
    
    # Lazy loading de servicios usando ServiceContainer
    @property
    def container(self):
        """Lazy loading del ServiceContainer"""
        if self._container is None:
            self._container = get_container()
        return self._container
    
    @property
    def session_manager(self):
        """Lazy loading del SessionManager desde ServiceContainer"""
        if self._session_manager is None:
            self._session_manager = self.container.get('session_manager')
        return self._session_manager
    
    @property
    def movement_service(self):
        """Lazy loading del MovementService"""
        if self._movement_service is None:
            self._movement_service = self.container.get('movement_service')
        return self._movement_service
    
    @property
    def product_service(self):
        """Lazy loading del ProductService"""
        if self._product_service is None:
            self._product_service = self.container.get('product_service')
        return self._product_service
    
    @property
    def export_service(self):
        """Lazy loading del ExportService"""
        if self._export_service is None:
            self._export_service = self.container.get('export_service')
        return self._export_service
    
    # Métodos para abrir subformularios
    def _open_entries_form(self):
        """Abre el formulario de entradas al inventario"""
        try:
            self.logger.info("Abriendo formulario de entradas al inventario")
            
            from ui.forms.movement_entry_form import MovementEntryForm
            entry_form = MovementEntryForm(self.window, self.db)
            
            self.logger.info("Formulario de entradas abierto exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error al abrir formulario de entradas: {e}")
            messagebox.showerror("Error", f"Error al abrir formulario de entradas: {str(e)}")
    
    def _open_adjustments_form(self):
        """Abre el formulario de ajustes de producto"""
        try:
            self.logger.info("Abriendo formulario de ajustes de producto")
            
            from ui.forms.movement_adjust_form import MovementAdjustForm
            adjust_form = MovementAdjustForm(self.window, self.db)
            
            self.logger.info("Formulario de ajustes abierto exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error al abrir formulario de ajustes: {e}")
            messagebox.showerror("Error", f"Error al abrir formulario de ajustes: {str(e)}")
    
    def _open_history_form(self):
        """Abre el formulario de historial de movimientos"""
        try:
            self.logger.info("Abriendo formulario de historial de movimientos")
            
            from ui.forms.movement_history_form import MovementHistoryForm
            history_form = MovementHistoryForm(self.window, self.db)
            
            self.logger.info("Formulario de historial abierto exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error al abrir formulario de historial: {e}")
            messagebox.showerror("Error", f"Error al abrir formulario de historial: {str(e)}")
    
    def _open_stock_low_form(self):
        """Abre el formulario de stock bajo"""
        try:
            self.logger.info("Abriendo formulario de stock bajo")
            
            # Validación adicional de permisos específica
            if not self.session_manager.has_permission('admin'):
                messagebox.showwarning(
                    "Acceso Denegado", 
                    "Solo administradores pueden acceder a gestión de stock bajo"
                )
                return
            
            # Importación lazy del formulario stock bajo
            from ui.forms.movement_stock_form import MovementStockForm
            
            # Crear y mostrar formulario
            stock_form = MovementStockForm(self.window, self.db)
            
            if stock_form.window:  # Verificar que se creó correctamente
                stock_form.show()
                self.logger.info("MovementStockForm abierto exitosamente")
            else:
                self.logger.warning("MovementStockForm no se pudo crear correctamente")
                messagebox.showwarning("Advertencia", "No se pudo abrir el formulario de stock bajo")
            
        except ImportError as e:
            self.logger.error(f"Error de importación MovementStockForm: {e}")
            messagebox.showerror("Error", "Módulo de stock bajo no disponible")
            
        except PermissionError as e:
            self.logger.warning(f"Error de permisos: {e}")
            messagebox.showwarning("Acceso Denegado", str(e))
            
        except Exception as e:
            self.logger.error(f"Error al abrir formulario de stock bajo: {e}")
            messagebox.showerror("Error", f"Error al abrir formulario de stock bajo: {str(e)}")
    
    def _feature_under_construction(self):
        """
        Aviso genérico para funcionalidades pendientes.
        """
        messagebox.showinfo(
            "En construcción",
            "Esta funcionalidad está en construcción y estará disponible próximamente.",
            parent=self.window
        )
        # Asegura que la ventana permanezca en foco
        self.window.focus_force()

    def destroy(self):
        """Destruye la ventana y limpia recursos"""
        try:
            if self.window:
                self.window.destroy()
                self.window = None
            self.logger.info("MovementForm destruido correctamente")
        except Exception as e:
            self.logger.error(f"Error al destruir MovementForm: {e}")
