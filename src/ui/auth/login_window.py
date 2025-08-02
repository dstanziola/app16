"""
Ventana de autenticación de usuarios - Versión AuthService

Esta clase implementa la interfaz gráfica para el login de usuarios,
utilizando el AuthService del ServiceContainer para autenticación.

CARACTERÍSTICAS v2.0:
- Integración completa con AuthService via ServiceContainer
- Lazy loading de servicios siguiendo patrón arquitectónico
- Validación empresarial con logging detallado
- Manejo robusto de errores
- Compliance con Clean Architecture

PATRONES APLICADOS:
- Dependency Injection via ServiceContainer
- Service Layer para lógica de autenticación
- MVP Pattern (esta clase como View)
- Error Handling empresarial

TDD Implementation:
- Código refactorizado para pasar tests de integración
- AuthService usado en lugar de UserService directo
- Session management delegado a AuthService
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
import logging

from services.service_container import get_container


class LoginWindow:
    """
    Ventana de autenticación de usuarios con AuthService.
    
    Responsabilidades:
    - Presentar interfaz de login
    - Validar entrada de usuario
    - Delegar autenticación a AuthService
    - Manejar resultado de autenticación
    - Logging de eventos de seguridad
    """
    
    def __init__(self):
        """
        Inicializar ventana de login con lazy loading de servicios.
        """
        # Lazy loading de servicios via ServiceContainer
        self._auth_service = None
        self.login_successful = False
        
        # Configurar logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("LoginWindow inicializado")
        
        # Crear ventana principal
        self.root = tk.Tk()
        self.root.title("Sistema de Inventario - Login")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        # Centrar ventana en pantalla
        self._center_window()
        
        # Variables de formulario
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        
        # Crear interfaz
        self._create_ui()
        
        # Configurar eventos
        self._setup_events()
        
    @property
    def auth_service(self):
        """
        Lazy loading del AuthService via ServiceContainer.
        
        Returns:
            AuthService instance del container
            
        Raises:
            RuntimeError: Si no se puede obtener AuthService
        """
        if self._auth_service is None:
            try:
                container = get_container()
                self._auth_service = container.get('auth_service')
                self.logger.debug("AuthService obtenido del ServiceContainer")
            except Exception as e:
                self.logger.error(f"Error obteniendo AuthService: {e}")
                raise RuntimeError(f"No se pudo obtener AuthService: {e}")
        
        return self._auth_service
    
    def _center_window(self):
        """Centrar la ventana en la pantalla."""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.root.winfo_screenheight() // 2) - (300 // 2)
        self.root.geometry(f"400x300+{x}+{y}")
        
    def _create_ui(self):
        """Crear los elementos de la interfaz de usuario."""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Título
        title_label = ttk.Label(
            main_frame, 
            text="Sistema de Inventario v5.0", 
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Información de empresa
        company_label = ttk.Label(
            main_frame,
            text="Copy Point S.A.",
            font=("Arial", 12)
        )
        company_label.grid(row=1, column=0, columnspan=2, pady=(0, 30))
        
        # Campo usuario
        ttk.Label(main_frame, text="Usuario:").grid(
            row=2, column=0, sticky=tk.W, pady=(0, 5)
        )
        self.username_entry = ttk.Entry(
            main_frame, 
            textvariable=self.username_var,
            width=25
        )
        self.username_entry.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Campo contraseña
        ttk.Label(main_frame, text="Contraseña:").grid(
            row=4, column=0, sticky=tk.W, pady=(0, 5)
        )
        self.password_entry = ttk.Entry(
            main_frame, 
            textvariable=self.password_var,
            show="*",
            width=25
        )
        self.password_entry.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Frame de botones
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=(0, 10))
        
        # Botón login
        self.login_button = ttk.Button(
            button_frame,
            text="Iniciar Sesión",
            command=self._handle_login
        )
        self.login_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botón cancelar
        self.cancel_button = ttk.Button(
            button_frame,
            text="Cancelar",
            command=self._handle_cancel
        )
        self.cancel_button.pack(side=tk.LEFT)
        
        # Mensaje de estado
        self.status_label = ttk.Label(
            main_frame,
            text="",
            foreground="red"
        )
        self.status_label.grid(row=7, column=0, columnspan=2)
        
        # Información de usuario por defecto
        default_info = ttk.Label(
            main_frame,
            text="Usuario por defecto: admin / Password: admin123",
            font=("Arial", 8),
            foreground="gray"
        )
        default_info.grid(row=8, column=0, columnspan=2, pady=(20, 0))
        
    def _setup_events(self):
        """Configurar eventos de la ventana."""
        # Enter key para login
        self.root.bind('<Return>', lambda event: self._handle_login())
        
        # Escape key para cancelar
        self.root.bind('<Escape>', lambda event: self._handle_cancel())
        
        # Focus inicial en campo usuario
        self.username_entry.focus()
        
        # Validación en tiempo real
        self.username_var.trace('w', self._validate_form)
        self.password_var.trace('w', self._validate_form)
        
        # Protocolo de cierre de ventana
        self.root.protocol("WM_DELETE_WINDOW", self._handle_cancel)
        
    def _validate_form(self, *args):
        """Validar el formulario en tiempo real."""
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        
        # Habilitar/deshabilitar botón según validación
        if username and password:
            self.login_button.config(state='normal')
            self.status_label.config(text="")
        else:
            self.login_button.config(state='disabled')
            
    def _handle_login(self):
        """
        Manejar el proceso de autenticación usando AuthService.
        
        Implementa el flujo completo de autenticación:
        1. Validar entrada
        2. Usar AuthService para autenticar
        3. Manejar resultado
        4. Logging de eventos de seguridad
        """
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        
        # Validar campos obligatorios
        if not username or not password:
            self.status_label.config(text="Usuario y contraseña son obligatorios")
            self.logger.warning("Intento de login con campos vacíos")
            return
        
        # Validar longitud mínima
        if len(username) < 3:
            self.status_label.config(text="Usuario debe tener al menos 3 caracteres")
            return
            
        if len(password) < 6:
            self.status_label.config(text="Contraseña debe tener al menos 6 caracteres")
            return
            
        try:
            # Deshabilitar botón durante procesamiento
            self.login_button.config(state='disabled', text="Verificando...")
            self.cancel_button.config(state='disabled')
            self.root.update()
            
            self.logger.info(f"Iniciando autenticación para usuario: {username}")
            
            # Usar AuthService para autenticación - DELEGACIÓN CORRECTA
            user = self.auth_service.authenticate(username, password)
            
            if user:
                # Login exitoso - AuthService ya maneja session_manager.login()
                self.logger.info(f"Autenticación exitosa para usuario: {username}")
                
                # Verificar que el usuario está realmente autenticado
                if self.auth_service.is_authenticated():
                    self.logger.info("Sesión establecida correctamente")
                    
                    # Marcar como exitoso y cerrar
                    self.login_successful = True
                    self.status_label.config(text="Login exitoso", foreground="green")
                    self.root.after(500, self.root.quit)  # Pequeño delay para mostrar mensaje
                else:
                    # Error inesperado
                    self.logger.error("AuthService retornó usuario pero no hay sesión activa")
                    self.status_label.config(text="Error interno de autenticación")
                    
            else:
                # Credenciales inválidas
                self.status_label.config(text="Usuario o contraseña incorrectos")
                self.password_var.set("")  # Limpiar contraseña
                self.password_entry.focus()
                self.logger.warning(f"Autenticación fallida para usuario: {username}")
                
        except RuntimeError as e:
            # Error de configuración del sistema
            self.logger.error(f"Error de configuración durante autenticación: {e}")
            self.status_label.config(text="Error de configuración del sistema")
            messagebox.showerror("Error de Sistema", 
                               f"Error de configuración: {e}")
            
        except Exception as e:
            # Error inesperado
            self.logger.error(f"Error inesperado durante autenticación: {e}")
            self.status_label.config(text="Error de conexión. Intente nuevamente.")
            messagebox.showerror("Error", 
                               f"Error durante autenticación: {e}")
            
        finally:
            # Rehabilitar botones
            self.login_button.config(state='normal', text="Iniciar Sesión")
            self.cancel_button.config(state='normal')
            
    def _handle_cancel(self):
        """Manejar la cancelación del login."""
        self.logger.info("Login cancelado por usuario")
        self.login_successful = False
        self.root.quit()
        
    def show(self):
        """
        Mostrar la ventana de login y retornar el resultado.
        
        Returns:
            bool: True si login exitoso, False si cancelado
        """
        try:
            self.logger.info("Mostrando ventana de login")
            self.root.mainloop()
            
            self.logger.info(f"Login finalizado. Éxito: {self.login_successful}")
            return self.login_successful
            
        except Exception as e:
            self.logger.error(f"Error durante show(): {e}")
            return False
            
        finally:
            # Asegurar que la ventana se destruya
            try:
                self.root.destroy()
                self.logger.debug("Ventana de login destruida")
            except Exception as e:
                self.logger.warning(f"Error destruyendo ventana: {e}")
        
    def destroy(self):
        """Destruir la ventana de login."""
        try:
            if self.root:
                self.root.destroy()
                self.logger.debug("LoginWindow destruido explícitamente")
        except Exception as e:
            self.logger.warning(f"Error en destroy(): {e}")


# Función de compatibilidad para código existente
def create_login_window():
    """
    Función de compatibilidad para crear LoginWindow.
    
    Returns:
        LoginWindow instance
    """
    return LoginWindow()
