"""
Ventana principal del sistema de gestión de inventario.

Esta clase implementa la interfaz principal de la aplicación, proporcionando
acceso a todas las funcionalidades del sistema a través de un menú organizado
y botones de acceso rápido.

FUNCIONALIDADES PRINCIPALES:
- Menú de navegación completo
- Área de bienvenida con información del usuario
- Accesos rápidos a funciones principales
- Control de permisos basado en roles
- Gestión de ventanas secundarias
- Barra de estado con información del sistema
- Sistema de Reportes integrado (FASE 2)

REQUISITOS:
- Usuario debe estar autenticado
- Base de datos inicializada correctamente
- Servicios del sistema disponibles
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Dict, Any
from datetime import datetime

# Importaciones de servicios - Service Container Integration
from services.service_container import get_container

# Importar configuración de base de datos para path correcto
from config_db import get_database_path

# Importaciones de ventanas
from ui.forms.category_form import CategoryWindow
from ui.forms.product_form import ProductWindow
from ui.forms.client_form import ClientWindow
from ui.forms.sales_form import SalesWindow
from ui.forms.movement_form import MovementForm
from ui.forms.label_generator_form import LabelGeneratorForm  # SISTEMA DE ETIQUETAS


from ui.forms.reports_form import ReportsForm  # FASE 2: Sistema de Reportes
from ui.forms.ticket_preview_form import TicketPreviewForm  # FASE 3: Sistema de Tickets
from ui.forms.company_config_form import CompanyConfigForm  # FASE 3: Configuración de Empresa
# from ui.auth.session_manager import session_manager  # DEPRECATED: Usar ServiceContainer
from services.service_container import get_container
from ui.utils.window_manager import window_manager

class MainWindow:
    """Ventana principal del sistema de gestión de inventario."""
    
    def __init__(self):
        """
        Inicializa la ventana principal del sistema.
        
        Raises:
            RuntimeError: Si no hay usuario autenticado
            ConnectionError: Si hay problemas con la base de datos
        """
        # CORRECCIÓN: Configurar logging ANTES de _initialize_services()
        self.logger = logging.getLogger(__name__)
        
        # Inicializar servicios después de configurar logger
        self._initialize_services()
        
        # Verificar autenticación usando ServiceContainer
        if not self.session_manager.is_authenticated:
            raise RuntimeError("Debe autenticarse antes de acceder al sistema principal")
        
        # (servicios ya inicializados en verificación de autenticación)
        
        # Crear ventana principal
        self.root = tk.Tk()
        self.root.title("Sistema de Gestión de Inventario - Copy Point S.A.")
        self.root.geometry("1024x768")
        self.root.minsize(800, 600)
        
        # Centrar ventana
        self._center_window()
        
        # Variables para ventanas
        self.reports_form = None
        self.ticket_preview_form = None
        self.company_config_form = None
        
        # Crear interfaz de usuario
        self._create_menu()
        self._create_toolbar()
        self._create_main_area()
        self._create_status_bar()
        self._setup_events()
        
        self.logger.info("Ventana principal inicializada correctamente")
    
    # === PROPIEDADES LAZY PARA SERVICIOS DEL CONTAINER ===
    
    @property
    def db_connection(self):
        """Obtiene conexión de base de datos del container (lazy)."""
        return self.container.get('database')
    
    @property 
    def category_service(self):
        """Obtiene CategoryService del container (lazy)."""
        return self.container.get('category_service')
    
    @property
    def product_service(self):
        """Obtiene ProductService del container (lazy)."""
        return self.container.get('product_service')
    
    @property
    def client_service(self):
        """Obtiene ClientService del container (lazy)."""
        return self.container.get('client_service')
    
    @property
    def sales_service(self):
        """Obtiene SalesService del container (lazy)."""
        return self.container.get('sales_service')
        
    @property
    def session_manager(self):
        """Obtiene SessionManager del container (lazy)."""
        return self.container.get('session_manager')
        
    def _initialize_services(self):
        """Inicializa los servicios usando Service Container."""
        try:
            # Obtener Service Container configurado
            self.container = get_container()
            
            # Validar que el container tenga los servicios necesarios
            required_services = ['database', 'category_service', 'product_service', 'client_service', 'sales_service']
            for service in required_services:
                if not self.container.is_registered(service):
                    raise ConnectionError(f"Servicio '{service}' no está registrado en el container")
            
            # Los servicios se obtienen lazy a través de propiedades
            self.logger.info("Servicios inicializados correctamente usando Service Container")
            
        except Exception as e:
            self.logger.error(f"Error al inicializar servicios: {e}")
            raise ConnectionError(f"No se pudo inicializar el Service Container: {e}")
            
    def _center_window(self):
        """Centra la ventana en la pantalla."""
        self.root.update_idletasks()
        width = 800   # Nuevo ancho
        height = 600  # Nueva altura
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _create_menu(self):
        """Crea la barra de menú principal."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Cambiar Usuario", command=self._change_user)
        file_menu.add_separator()
        if self.session_manager.has_permission('admin'):
            file_menu.add_command(label="⚙️ Configuración de Empresa", command=self._open_company_config)
            file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self._exit_application)
        
        # Menú Gestión
        manage_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Gestión", menu=manage_menu)
        
        if self.session_manager.has_permission('admin'):
            manage_menu.add_command(label="Categorías", command=self._open_categories)
            manage_menu.add_command(label="Productos", command=self._open_products)
            manage_menu.add_separator()
            
        manage_menu.add_command(label="Clientes", command=self._open_clients)
        manage_menu.add_separator()
        manage_menu.add_command(label="Procesar Venta", command=self._open_sales)
        
        # Menú Inventario (solo administradores)
        if self.session_manager.has_permission('admin'):
            inventory_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Inventario", menu=inventory_menu)
            inventory_menu.add_command(label="Movimientos", command=self._open_movements)
            inventory_menu.add_separator()
            inventory_menu.add_command(label="Ver Inventario Actual", command=self._open_inventory_report)
        
        # Menú Reportes (solo administradores) - FASE 2
        if self.session_manager.has_permission('admin'):
            reports_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Reportes", menu=reports_menu)
            reports_menu.add_command(label="📊 Sistema de Reportes", command=self._open_reports_system)
            reports_menu.add_separator()
            reports_menu.add_command(label="📦 Inventario Actual", command=self._open_inventory_report_direct)
            reports_menu.add_command(label="📋 Movimientos", command=self._open_movements_report_direct)
            reports_menu.add_command(label="💰 Ventas", command=self._open_sales_report_direct)
            reports_menu.add_command(label="📊 Rentabilidad", command=self._open_profitability_report_direct)
        
        # Menú Etiquetas (solo administradores)
        if self.session_manager.has_permission('admin'):
            labels_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Etiquetas", menu=labels_menu)
            labels_menu.add_command(label="🏷️ Generador de Etiquetas", command=self._open_label_generator)
            labels_menu.add_separator()
            labels_menu.add_command(label="📄 Templates de Etiquetas", command=self._open_label_templates)
            
        # Menú Tickets - FASE 3
        # tickets_menu = tk.Menu(menubar, tearoff=0)
        # menubar.add_cascade(label="Tickets", menu=tickets_menu)
        # tickets_menu.add_command(label="🎫 Generar Ticket de Venta", command=self._generate_sales_ticket)
        # if self.session_manager.has_permission('admin'):
        #     tickets_menu.add_command(label="📦 Generar Ticket de Entrada", command=self._generate_entry_ticket)
        #     tickets_menu.add_separator()
        #     tickets_menu.add_command(label="🔍 Buscar Tickets", command=self._search_tickets)
        #     tickets_menu.add_command(label="🗞️ Vista Previa de Tickets", command=self._open_ticket_preview)
            
        # Menú Ayuda
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=help_menu)
        help_menu.add_command(label="Manual de Usuario", command=self._show_user_manual)
        help_menu.add_separator()
        help_menu.add_command(label="Acerca de", command=self._show_about)
        
    def _create_toolbar(self):
        """Crea la barra de herramientas con accesos rápidos."""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # Botón nueva venta
        ttk.Button(
            toolbar,
            text="💰 Ventas",
            command=self._open_sales
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # Separador
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Botón clientes
        ttk.Button(
            toolbar,
            text="👥 Clientes",
            command=self._open_clients
        ).pack(side=tk.LEFT, padx=5)
        
        # Botones de administración (solo para administradores)
        if self.session_manager.has_permission('admin'):

            ttk.Button(
                toolbar,
                text="🏷️ Categorías",
                command=self._open_categories
            ).pack(side=tk.LEFT, padx=5)

            ttk.Button(
                toolbar,
                text="📦 Productos",
                command=self._open_products
            ).pack(side=tk.LEFT, padx=5)
                    
            ttk.Button(
                toolbar,
                text="📋 Movimientos",
                command=self._open_movements
            ).pack(side=tk.LEFT, padx=5)
            
            # Separador
            ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
            
            # FASE 2: Botón de reportes
            ttk.Button(
                toolbar,
                text="📊 Reportes",
                command=self._open_reports_system
            ).pack(side=tk.LEFT, padx=5)
            
            # Botón de etiquetas
            ttk.Button(
                toolbar,
                text="🏷️ Etiquetas",
                command=self._open_label_generator
            ).pack(side=tk.LEFT, padx=5)
            
            # FASE 3: Botón de tickets
            # ttk.Button(
            #     toolbar,
            #     text="🎫 Tickets",
            #     command=self._open_ticket_preview
            # ).pack(side=tk.LEFT, padx=5)
            
    def _create_main_area(self):
        """Crea el área principal de la aplicación."""
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Área de bienvenida
        welcome_frame = ttk.LabelFrame(main_frame, text="Panel de Control", padding=20)
        welcome_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título de bienvenida
        user_info = self.session_manager.get_user_info()
        welcome_title = ttk.Label(
            welcome_frame,
            text=f"Bienvenido, {user_info['nombre_usuario']}",
            font=("Arial", 18, "bold")
        )
        welcome_title.pack(pady=(0, 10))
        
        # Información de la empresa
        # info_label = ttk.Label(
        #     welcome_frame,
        #     text="Copy Point S.A.\nSistema de Gestión de Inventario v1.1\nLas Lajas, Las Cumbres, Panamá\nTeléfono: 6342-9218\ne-mail: tus_amigos@copypoint.online",
        #     font=("Arial", 12),
        #     justify=tk.CENTER
        # )
        # info_label.pack(pady=(0, 20))
        
        # Información de la empresa (dinámica)
        config = self.container.get('company_service').obtener_configuracion()
        company_text = (
            f"{config.nombre}\n"
            f"Sistema de Gestión de Inventario v1.2\n"
            f"{config.direccion}\n"
            f"Teléfono: {config.telefono}\n"
            f"E-mail: {config.email}"
        )
        self.company_info_label = ttk.Label(
            welcome_frame,
            text=company_text,
            font=("Arial", 12),
            justify=tk.CENTER
        )
        self.company_info_label.pack(pady=(0, 20))




        # Información de usuario
        user_info = self.session_manager.get_user_info()
        user_label = ttk.Label(
            welcome_frame,
            text=f"Usuario: {user_info['nombre_usuario']} ({user_info['rol']})",
            font=("Arial", 14)
        )
        user_label.pack(pady=(0, 20))
        
    def _create_status_bar(self):
        """Crea la barra de estado en la parte inferior."""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Información de usuario
        user_info = self.session_manager.get_user_info()
        self.user_status = ttk.Label(
            self.status_bar,
            text=f"Usuario: {user_info['nombre_usuario']} | Rol: {user_info['rol']}"
        )
        self.user_status.pack(side=tk.LEFT, padx=5)
        
        # Separador
        ttk.Separator(self.status_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Estado de conexión
        self.connection_status = ttk.Label(
            self.status_bar,
            text="Base de datos: Conectada"
        )
        self.connection_status.pack(side=tk.LEFT, padx=5)
        
        # FASE 3: Información de versión
        version_label = ttk.Label(
            self.status_bar,
            text="v1.2 (FASE 3 - Tickets)"
        )
        version_label.pack(side=tk.LEFT, padx=5)
        
        # Fecha y hora (se puede actualizar periódicamente)
        from datetime import datetime
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.time_status = ttk.Label(
            self.status_bar,
            text=f"Fecha: {current_time}"
        )
        self.time_status.pack(side=tk.RIGHT, padx=5)
        
    def _setup_events(self):
        """Configura eventos de la ventana."""
        # Protocolo de cierre de ventana
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Actualizar tiempo cada minuto
        self._update_time()
        
    def _update_time(self):
        """Actualiza la hora en la barra de estado."""
        try:
            from datetime import datetime
            current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
            if hasattr(self, 'time_status') and self.time_status.winfo_exists():
                self.time_status.config(text=f"Fecha: {current_time}")
            
            # Programar próxima actualización en 60 segundos
            self.root.after(60000, self._update_time)
        except Exception as e:
            self.logger.error(f"Error al actualizar tiempo: {e}")
        
    # Métodos de navegación
    def _open_categories(self):
        """Abre la ventana de gestión de categorías."""
        if not self.session_manager.has_permission('admin'):
            messagebox.showwarning("Acceso Denegado", "No tiene permisos para acceder a esta función")
            return
            
        # Verificar si ya está abierta y es válida
        if window_manager.is_window_open('categories'):
            window_manager.bring_to_front('categories')
            return
            
        try:
            # Crear nueva ventana
            category_window = CategoryWindow(self.root)
            self.logger.info("Ventana de categorías abierta")
        except Exception as e:
            self.logger.error(f"Error al abrir ventana de categorías: {e}")
            messagebox.showerror("Error", f"No se pudo abrir la ventana de categorías: {e}")
            
    def _open_products(self):
        """Abre la ventana de gestión de productos."""
        if not self.session_manager.has_permission('admin'):
            messagebox.showwarning("Acceso Denegado", "No tiene permisos para acceder a esta función")
            return
            
        # Verificar si ya está abierta y es válida
        if window_manager.is_window_open('products'):
            window_manager.bring_to_front('products')
            return
            
        try:
            # Crear nueva ventana
            product_window = ProductWindow(self.root)
            self.logger.info("Ventana de productos abierta")
        except Exception as e:
            self.logger.error(f"Error al abrir ventana de productos: {e}")
            messagebox.showerror("Error", f"No se pudo abrir la ventana de productos: {e}")
            
    def _open_clients(self):
        """Abre la ventana de gestión de clientes."""
        # Verificar si ya está abierta y es válida
        if window_manager.is_window_open('clients'):
            window_manager.bring_to_front('clients')
            return
            
        try:
            # Crear nueva ventana
            client_window = ClientWindow(self.root)
            self.logger.info("Ventana de clientes abierta")
        except Exception as e:
            self.logger.error(f"Error al abrir ventana de clientes: {e}")
            messagebox.showerror("Error", f"No se pudo abrir la ventana de clientes: {e}")
            
    def _open_sales(self):
        """Abre la ventana de procesamiento de ventas."""
        # Verificar si ya está abierta y es válida
        if window_manager.is_window_open('sales'):
            window_manager.bring_to_front('sales')
            return
            
        try:
            # Crear nueva ventana
            sales_window = SalesWindow(self.root)
            self.logger.info("Ventana de ventas abierta")
        except Exception as e:
            self.logger.error(f"Error al abrir ventana de ventas: {e}")
            messagebox.showerror("Error", f"No se pudo abrir la ventana de ventas: {e}")
            
    def _open_movements(self):
        """Abre la ventana de movimientos de inventario."""
        if not self.session_manager.has_permission('admin'):
            messagebox.showwarning("Acceso Denegado", "No tiene permisos para acceder a esta función")
            return
            
        # Verificar si ya está abierta y es válida
        if window_manager.is_window_open('movements'):
            window_manager.bring_to_front('movements')
            return

        try:
            # Crear nueva ventana usando MovementForm
            movement_form = MovementForm(self.root, self.db_connection)
            if movement_form.window:
                window_manager.register_window('movements', movement_form.window)
                self.logger.info("Ventana de movimientos abierta")
        except Exception as e:
            self.logger.error(f"Error al abrir ventana de movimientos: {e}")
            messagebox.showerror("Error", f"No se pudo abrir la ventana de movimientos: {e}")

    # FASE 2: Métodos del sistema de reportes
    def _open_reports_system(self):
        """Abre el sistema principal de reportes - FASE 2"""
        if not self.session_manager.has_permission('admin'):
            messagebox.showwarning("Acceso Denegado", "No tiene permisos para acceder a esta función")
            return
            
        try:
            # Verificar si ya existe una instancia
            if self.reports_form and hasattr(self.reports_form, 'window') and self.reports_form.window:
                try:
                    if self.reports_form.window.winfo_exists():
                        self.reports_form.window.lift()
                        self.reports_form.window.focus_set()
                        return
                except tk.TclError:
                    # La ventana fue destruida, crear nueva
                    pass
            
            # CORRECCIÓN: Usar path de base de datos en lugar del objeto conexión
            db_path = get_database_path()  # Obtener string path
            
            # Crear nueva instancia del formulario de reportes con path correcto
            self.reports_form = ReportsForm(self.root, db_path)  # ✅ CORREGIDO
            self.reports_form.show()
            self.logger.info("Sistema de reportes abierto exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error al abrir sistema de reportes: {e}")
            messagebox.showerror("Error", f"No se pudo abrir el sistema de reportes: {e}")
    
    def _open_inventory_report_direct(self):
        """Abre directamente el reporte de inventario - FASE 2"""
        try:
            self._open_reports_system()
            if self.reports_form:
                # Configurar para reporte de inventario
                self.reports_form.report_type_var.set("inventory")
                self.reports_form._on_report_type_changed()
        except Exception as e:
            self.logger.error(f"Error abriendo reporte de inventario: {e}")
    
    def _open_movements_report_direct(self):
        """Abre directamente el reporte de movimientos - FASE 2"""
        try:
            self._open_reports_system()
            if self.reports_form:
                # Configurar para reporte de movimientos
                self.reports_form.report_type_var.set("movements")
                self.reports_form._on_report_type_changed()
        except Exception as e:
            self.logger.error(f"Error abriendo reporte de movimientos: {e}")
    
    def _open_sales_report_direct(self):
        """Abre directamente el reporte de ventas - FASE 2"""
        try:
            self._open_reports_system()
            if self.reports_form:
                # Configurar para reporte de ventas
                self.reports_form.report_type_var.set("sales")
                self.reports_form._on_report_type_changed()
        except Exception as e:
            self.logger.error(f"Error abriendo reporte de ventas: {e}")
    
    def _open_profitability_report_direct(self):
        """Abre directamente el reporte de rentabilidad - FASE 2"""
        try:
            self._open_reports_system()
            if self.reports_form:
                # Configurar para reporte de rentabilidad
                self.reports_form.report_type_var.set("profitability")
                self.reports_form._on_report_type_changed()
        except Exception as e:
            self.logger.error(f"Error abriendo reporte de rentabilidad: {e}")
    
    def _open_label_generator(self):
        """Abre el generador de etiquetas."""
        if not self.session_manager.has_permission('admin'):
            messagebox.showwarning("Acceso Denegado", "No tiene permisos para acceder a esta función")
            return
            
        try:
            # Crear nueva ventana
            label_generator = LabelGeneratorForm(self.root)
            self.logger.info("Generador de etiquetas abierto")
        except Exception as e:
            self.logger.error(f"Error al abrir generador de etiquetas: {e}")
            messagebox.showerror("Error", f"No se pudo abrir el generador de etiquetas: {e}")
    
    def _open_label_templates(self):
        """Abre la gestión de templates de etiquetas."""
        if not self.session_manager.has_permission('admin'):
            messagebox.showwarning("Acceso Denegado", "No tiene permisos para acceder a esta función")
            return
            
        # TODO: Implementar gestión de templates personalizada
        messagebox.showinfo(
            "Información", 
            "Gestión de templates de etiquetas en desarrollo.\n\n"
            "Por ahora puede usar los templates disponibles en el generador de etiquetas."
        )
    
    # Métodos legacy mantenidos para compatibilidad
    def _open_inventory_report(self):
        """Abre la ventana de reporte de inventario (método legacy)"""
        self._open_inventory_report_direct()
        
    def _open_sales_report(self):
        """Abre la ventana de reporte de ventas (método legacy)"""
        self._open_sales_report_direct()
        
    def _open_movements_report(self):
        """Abre la ventana de reporte de movimientos (método legacy)"""
        self._open_movements_report_direct()
        
    def _open_profitability_report(self):
        """Abre la ventana de reporte de rentabilidad (método legacy)"""
        self._open_profitability_report_direct()
        
    # ==========================================
    # MÉTODOS DE SISTEMA DE TICKETS - FASE 3
    # ==========================================
    
    def _open_company_config(self):
        """Abre configuración de empresa - FASE 3"""
        if not self.session_manager.has_permission('admin'):
            messagebox.showwarning("Acceso Denegado", "No tiene permisos para acceder a esta función")
            return
            
        try:
            # Verificar si ya existe una instancia
            if self.company_config_form and hasattr(self.company_config_form, 'window') and self.company_config_form.window:
                try:
                    if self.company_config_form.window.winfo_exists():
                        self.company_config_form.window.lift()
                        self.company_config_form.window.focus_set()
                        return
                except tk.TclError:
                    # La ventana fue destruida, crear nueva
                    pass
            
            db_path = get_database_path()  # Obtener string path
            
            # self.company_config_form = CompanyConfigForm(self.root)
            # self.company_config_form.show()
            # self.logger.info("Configuración de empresa abierta exitosamente")
            
            self.company_config_form = CompanyConfigForm(self.root)
            # Mostrar el formulario (bloquea hasta cerrarse)
            self.company_config_form.show()
            # Al volver, recargar la info en la ventana principal
            self._refresh_company_info()
            self.logger.info("Configuración de empresa actualizada y ventana principal refrescada")

        except Exception as e:
            self.logger.error(f"Error al abrir configuración de empresa: {e}")
            messagebox.showerror("Error", f"No se pudo abrir la configuración de empresa: {e}")
    
    def _generate_sales_ticket(self):
        """Generar ticket para última venta"""
        try:
            from services.sales_service import SalesService
            from services.ticket_service import TicketService
            
            sales_service = SalesService(self.db_connection)
            ticket_service = TicketService(self.db_connection)
            
            # Obtener la última venta
            ventas = sales_service.listar_ventas(limite=1)
            if not ventas:
                messagebox.showwarning("Sin Ventas", "No hay ventas registradas para generar ticket")
                return
                
            ultima_venta = ventas[0]
            
            # Confirmar generación
            if messagebox.askyesno(
                "Generar Ticket", 
                f"¿Desea generar un ticket para la venta #{ultima_venta.id_venta}?\n"
                f"Total: ${ultima_venta.total:.2f}\n"
                f"Fecha: {ultima_venta.fecha_venta.strftime('%d/%m/%Y %H:%M')}"
            ):
                # Generar ticket
                ticket = ticket_service.generar_ticket_venta(
                id_venta=ultima_venta.id_venta,
                responsable=self.session_manager.get_user_info()['nombre_usuario']
                )
                
                messagebox.showinfo(
                    "Ticket Generado",
                    f"Ticket de venta generado exitosamente\n"
                    f"Número: {ticket.ticket_number}\n"
                    f"Archivo: {ticket.pdf_path}"
                )
                
                # Preguntar si desea abrir el archivo PDF
                if messagebox.askyesno("Abrir PDF", "¿Desea abrir el archivo PDF generado?"):
                    import os
                    import subprocess
                    if os.path.exists(ticket.pdf_path):
                        try:
                            os.startfile(ticket.pdf_path)  # Windows
                        except AttributeError:
                            subprocess.run(['xdg-open', ticket.pdf_path])  # Linux
                        except Exception:
                            messagebox.showinfo("Archivo Listo", f"El archivo se guardó en: {ticket.pdf_path}")
                
        except Exception as e:
            self.logger.error(f"Error al generar ticket de venta: {e}")
            messagebox.showerror("Error", f"No se pudo generar el ticket de venta: {e}")
    
    def _generate_entry_ticket(self):
        """Generar ticket para último movimiento de entrada"""
        if not self.session_manager.has_permission('admin'):
            messagebox.showwarning("Acceso Denegado", "No tiene permisos para acceder a esta función")
            return
            
        try:
            from services.movement_service import MovementService
            from services.ticket_service import TicketService
            
            movement_service = MovementService(self.db_connection)
            ticket_service = TicketService(self.db_connection)
            
            # Obtener últimos movimientos de entrada
            movimientos = movement_service.listar_movimientos(
                tipo_movimiento='ENTRADA',
                limite=1
            )
            
            if not movimientos:
                messagebox.showwarning("Sin Movimientos", "No hay movimientos de entrada registrados para generar ticket")
                return
                
            ultimo_movimiento = movimientos[0]
            
            # Confirmar generación
            if messagebox.askyesno(
                "Generar Ticket", 
                f"¿Desea generar un ticket para el movimiento de entrada?\n"
                f"Producto: {ultimo_movimiento.nombre_producto}\n"
                f"Cantidad: {ultimo_movimiento.cantidad}\n"
                f"Fecha: {ultimo_movimiento.fecha_movimiento.strftime('%d/%m/%Y %H:%M')}"
            ):
                # Generar ticket
                ticket = ticket_service.generar_ticket_entrada(
                    id_movimiento=ultimo_movimiento.id_movimiento,
                    responsable=self.session_manager.get_user_info()['nombre_usuario']
                )
                
                messagebox.showinfo(
                    "Ticket Generado",
                    f"Ticket de entrada generado exitosamente\n"
                    f"Número: {ticket.ticket_number}\n"
                    f"Archivo: {ticket.pdf_path}"
                )
                
                # Preguntar si desea abrir el archivo PDF
                if messagebox.askyesno("Abrir PDF", "¿Desea abrir el archivo PDF generado?"):
                    import os
                    import subprocess
                    if os.path.exists(ticket.pdf_path):
                        try:
                            os.startfile(ticket.pdf_path)  # Windows
                        except AttributeError:
                            subprocess.run(['xdg-open', ticket.pdf_path])  # Linux
                        except Exception:
                            messagebox.showinfo("Archivo Listo", f"El archivo se guardó en: {ticket.pdf_path}")
                
        except Exception as e:
            self.logger.error(f"Error al generar ticket de entrada: {e}")
            messagebox.showerror("Error", f"No se pudo generar el ticket de entrada: {e}")
    
    def _search_tickets(self):
        """Buscar tickets existentes"""
        if not self.session_manager.has_permission('admin'):
            messagebox.showwarning("Acceso Denegado", "No tiene permisos para acceder a esta función")
            return
            
        try:
            from services.ticket_service import TicketService
            
            ticket_service = TicketService(self.db_connection)
            
            # Crear ventana de búsqueda simple
            search_window = tk.Toplevel(self.root)
            search_window.title("Buscar Tickets")
            search_window.geometry("600x400")
            search_window.resizable(True, True)
            
            # Centrar ventana
            x = (search_window.winfo_screenwidth() // 2) - (600 // 2)
            y = (search_window.winfo_screenheight() // 2) - (400 // 2)
            search_window.geometry(f"600x400+{x}+{y}")
            
            # Frame principal
            main_frame = ttk.Frame(search_window)
            main_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Frame de búsqueda
            search_frame = ttk.LabelFrame(main_frame, text="Criterios de Búsqueda", padding=10)
            search_frame.pack(fill="x", pady=(0, 10))
            
            # Tipo de ticket
            ttk.Label(search_frame, text="Tipo de Ticket:").grid(row=0, column=0, sticky="w", padx=(0, 10))
            
            tipo_var = tk.StringVar(value="TODOS")
            tipo_combo = ttk.Combobox(
                search_frame,
                textvariable=tipo_var,
                values=["TODOS", "VENTA", "ENTRADA"],
                state="readonly",
                width=15
            )
            tipo_combo.grid(row=0, column=1, sticky="w")
            
            # Botón buscar
            def buscar_tickets():
                try:
                    tipo_filtro = None if tipo_var.get() == "TODOS" else tipo_var.get()
                    tickets = ticket_service.buscar_tickets(tipo_ticket=tipo_filtro, limite=50)
                    
                    # Limpiar lista
                    for item in tree.get_children():
                        tree.delete(item)
                    
                    # Llenar lista
                    for ticket in tickets:
                        tree.insert("", "end", values=(
                            ticket.ticket_number,
                            ticket.ticket_type,
                            ticket.generated_at.strftime("%d/%m/%Y %H:%M"),
                            ticket.generated_by,
                            ticket.reprint_count
                        ))
                        
                    status_label.config(text=f"Encontrados: {len(tickets)} tickets")
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Error al buscar tickets: {e}")
            
            ttk.Button(search_frame, text="Buscar", command=buscar_tickets).grid(row=0, column=2, padx=(10, 0))
            
            # Lista de resultados
            list_frame = ttk.LabelFrame(main_frame, text="Resultados", padding=10)
            list_frame.pack(fill="both", expand=True)
            
            # Treeview
            columns = ("numero", "tipo", "fecha", "responsable", "reimpresos")
            tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
            
            # Configurar columnas
            tree.heading("numero", text="Número")
            tree.heading("tipo", text="Tipo")
            tree.heading("fecha", text="Fecha/Hora")
            tree.heading("responsable", text="Responsable")
            tree.heading("reimpresos", text="Reimpresos")
            
            tree.column("numero", width=120)
            tree.column("tipo", width=80)
            tree.column("fecha", width=120)
            tree.column("responsable", width=120)
            tree.column("reimpresos", width=80)
            
            # Scrollbar
            scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Status
            status_label = ttk.Label(main_frame, text="Haga clic en 'Buscar' para ver los tickets")
            status_label.pack(pady=(10, 0))
            
            # Cargar tickets inicialmente
            buscar_tickets()
            
        except Exception as e:
            self.logger.error(f"Error al abrir búsqueda de tickets: {e}")
            messagebox.showerror("Error", f"No se pudo abrir la búsqueda de tickets: {e}")
    
    def _open_ticket_preview(self):
        """Abrir formulario de preview de tickets"""
        try:
            # Verificar si ya existe una instancia
            if self.ticket_preview_form and hasattr(self.ticket_preview_form, 'window') and self.ticket_preview_form.window:
                try:
                    if self.ticket_preview_form.window.winfo_exists():
                        self.ticket_preview_form.window.lift()
                        self.ticket_preview_form.window.focus_set()
                        return
                except tk.TclError:
                    # La ventana fue destruida, crear nueva
                    pass
            
            # CORRECCIÓN: Usar path de base de datos para consistencia
            db_path = get_database_path()  # Obtener string path
            
            # Crear nueva instancia del formulario de preview
            self.ticket_preview_form = TicketPreviewForm(self.root, db_path)
            self.ticket_preview_form.show()
            self.logger.info("Vista previa de tickets abierta exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error al abrir vista previa de tickets: {e}")
            messagebox.showerror("Error", f"No se pudo abrir la vista previa de tickets: {e}")
        
    def _show_user_manual(self):
        """Muestra el manual de usuario."""
        manual_text = """Manual de Usuario - Sistema de Inventario Copy Point S.A.

FUNCIONALIDADES PRINCIPALES:

1. GESTIÓN DE PRODUCTOS Y CATEGORÍAS
   - Crear, editar y eliminar productos
   - Organizar por categorías (Material/Servicio)
   - Control de stock y precios

2. PROCESAMIENTO DE VENTAS
   - Registro de ventas rápido
   - Cálculo automático de impuestos
   - Asociación con clientes

3. CONTROL DE INVENTARIO
   - Movimientos de entrada y salida
   - Ajustes de inventario
   - Historial completo

4. SISTEMA DE REPORTES (NUEVO)
   - Inventario actual por categoría
   - Movimientos por período
   - Ventas con filtros
   - Análisis de rentabilidad
   - Exportación a PDF

5. GESTIÓN DE CLIENTES
   - Base de datos de clientes
   - Información de contacto y RUC

6. SISTEMA DE ETIQUETAS (NUEVO)
   - Generación masiva de etiquetas
   - Múltiples templates (Avery, A4, Térmico)
   - Códigos de barras automáticos
   - Impresión directa
   - Configuración personalizable

Para soporte técnico contactar:
tus_amigos@copypoint.online"""
        
        # Crear ventana para el manual
        manual_window = tk.Toplevel(self.root)
        manual_window.title("Manual de Usuario")
        manual_window.geometry("600x500")
        manual_window.resizable(True, True)
        
        # Centrar ventana
        x = (manual_window.winfo_screenwidth() // 2) - (600 // 2)
        y = (manual_window.winfo_screenheight() // 2) - (500 // 2)
        manual_window.geometry(f"600x500+{x}+{y}")
        
        # Crear texto con scroll
        text_frame = ttk.Frame(manual_window)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap="word", font=("Arial", 10))
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        text_widget.insert("1.0", manual_text)
        text_widget.config(state="disabled")
        
        # Botón cerrar
        ttk.Button(manual_window, text="Cerrar", command=manual_window.destroy).pack(pady=10)
        
    def _show_about(self):
        """Muestra información sobre la aplicación."""
        about_text = """Sistema de Gestión de Inventario v1.2
FASE 3: Sistema de Tickets Implementado

Desarrollado para Copy Point S.A.
Las Lajas, Las Cumbres, Panamá

FUNCIONALIDADES IMPLEMENTADAS:
• ✅ Gestión de inventario y productos
• ✅ Procesamiento de ventas
• ✅ Control de clientes
• ✅ Movimientos de inventario
• ✅ Sistema completo de reportes
• ✅ Sistema de tickets y facturación
• ✅ Configuración de empresa
• ✅ Sistema de etiquetas con códigos de barras
• ⏳ Lectores de código de barras (Próxima fase)

NUEVAS CARACTERÍSTICAS FASE 3:
• 🎫 Generación de tickets de venta
• 📦 Tickets de entrada de inventario
• 📄 Exportación a PDF profesional
• ⚙️ Configuración de empresa editable
• 🔍 Búsqueda y gestión de tickets
• 📝 Formato térmico y A4 soportados

TECNOLOGÍAS:
• Python 3.8+ con Tkinter
• SQLite para base de datos
• reportlab para PDFs
• qrcode para códigos QR
• Arquitectura Clean Code + TDD

© 2025 - Copy Point S.A.
Desarrollado siguiendo metodología TDD"""
        
        messagebox.showinfo("Acerca de", about_text)
        
    def _change_user(self):
        """Cambia de usuario (logout y nuevo login)."""
        result = messagebox.askyesno(
            "Cambiar Usuario",
            "¿Está seguro que desea cambiar de usuario?\nSe cerrará la sesión actual."
        )
        
        if result:
            self._logout_and_close()
            
    def _exit_application(self):
        """Sale de la aplicación."""
        self._on_closing()
        
    def _logout_and_close(self):
        """Cierra sesión y la aplicación."""
        try:
            # Cerrar ventana de reportes si está abierta
            if self.reports_form and hasattr(self.reports_form, 'window') and self.reports_form.window:
                try:
                    if self.reports_form.window.winfo_exists():
                        self.reports_form.window.destroy()
                except tk.TclError:
                    pass
            
            # Cerrar ventanas de tickets si están abiertas - FASE 3
            if self.ticket_preview_form and hasattr(self.ticket_preview_form, 'window') and self.ticket_preview_form.window:
                try:
                    if self.ticket_preview_form.window.winfo_exists():
                        self.ticket_preview_form.window.destroy()
                except tk.TclError:
                    pass
                    
            if self.company_config_form and hasattr(self.company_config_form, 'window') and self.company_config_form.window:
                try:
                    if self.company_config_form.window.winfo_exists():
                        self.company_config_form.window.destroy()
                except tk.TclError:
                    pass
            
            # Cerrar todas las ventanas secundarias
            window_manager.close_all_windows()
            
            # Cerrar sesión
            user_info = self.session_manager.get_user_info()
            self.session_manager.logout()
            self.logger.info(f"Sesión cerrada para usuario: {user_info['nombre_usuario']}")
            
            # Cerrar ventana principal
            self.root.quit()
            self.root.destroy()
        except Exception as e:
            self.logger.error(f"Error al cerrar aplicación: {e}")
        
    def _on_closing(self):
        """Maneja el evento de cierre de ventana."""
        result = messagebox.askyesno(
            "Confirmar Salida",
            "¿Está seguro que desea salir del sistema?"
        )
        
        if result:
            self._logout_and_close()
            
    def show(self):
        """Muestra la ventana principal."""
        self.root.mainloop()
        
    def destroy(self):
        """Destruye la ventana principal."""
        if self.root:
            self.root.destroy()

    def _refresh_company_info(self):
        """
        Recarga la configuración de empresa y actualiza la etiqueta en la ventana principal.
        """
        try:
            config = self.container.get('company_service').obtener_configuracion()
            company_text = (
                f"{config.nombre}\n"
                f"Sistema de Gestión de Inventario v1.2\n"
                f"{config.direccion}\n"
                f"Teléfono: {config.telefono}\n"
                f"E-mail: {config.email}"
            )
            self.company_info_label.config(text=company_text)
        except Exception as e:
            self.logger.error(f"Error al refrescar información de empresa: {e}")

# Función auxiliar para iniciar la aplicación principal
def start_main_window():
    """
    Inicia la ventana principal del sistema.
    
    Raises:
        RuntimeError: Si no hay usuario autenticado
    """
    # Usar session_manager del ServiceContainer para verificación
    container = get_container()
    session_manager = container.get('session_manager')
    
    if not session_manager.is_authenticated:
        raise RuntimeError("Debe autenticarse antes de iniciar la aplicación principal")
        
    main_window = MainWindow()
    main_window.show()
    return main_window
