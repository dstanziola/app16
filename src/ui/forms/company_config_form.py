"""
Formulario de configuración de empresa.
Permite editar datos corporativos y configuraciones del sistema.

Este formulario maneja:
- Edición de datos de empresa
- Validación en tiempo real
- Configuración de impuestos
- Gestión de logo corporativo

Autor: Sistema TDD - FASE 3
Fecha: 2025-06-25
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from datetime import datetime
from typing import Optional, Dict, Any

from models.company_config import CompanyConfig
from services.company_service import CompanyService


class CompanyConfigForm:
    """
    Formulario para configuración de empresa.
    
    Permite editar y validar datos corporativos.
    """
    
    def __init__(self, parent=None, db_path=None):
        """
        Inicializar formulario de configuración.
        
        Args:
            parent: Ventana padre
        """
        self.parent = parent
        self.db_path = db_path
        
        self.company_service = CompanyService()
        
        # Variables del formulario
        self.nombre_var = tk.StringVar()
        self.ruc_var = tk.StringVar()
        self.direccion_var = tk.StringVar()
        self.telefono_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.itbms_rate_var = tk.StringVar()
        self.moneda_var = tk.StringVar()
        self.logo_path_var = tk.StringVar()
        
        # Variables de validación
        self.validation_vars = {}
        
        # Configuración actual
        self.current_config = None
        
        self.window = None
        self.setup_ui()
        self._load_current_config()
    
    def setup_ui(self):
        """
        Configurar la interfaz de usuario.
        CORRECCIÓN CRÍTICA APLICADA: Patrón modal optimizado siguiendo MovementEntryForm exitoso
        """
        # Crear ventana
        self.window = tk.Toplevel(self.parent) if self.parent else tk.Tk()
        
        # CORRECCIÓN CRÍTICA OPTIMIZADA: Aplicar configuración modal INMEDIATAMENTE
        # Siguiendo patrón exitoso de MovementEntryForm (sin interferencia)
        if self.parent:
            # ———> Aplicar comportamiento modal ANTES de cualquier otra configuración
            self.window.transient(self.parent)   # Liga la ventana al parent
            self.window.grab_set()               # Captura todos los eventos  
            self.window.focus_force()            # Fuerza el foco inmediatamente
        
        # Configuración básica DESPUÉS de modal (como MovementEntryForm)
        self.window.title("Configuración de Empresa")
        self.window.geometry("600x650")
        self.window.resizable(True, False)
        
        # Configuraciones adicionales DESPUÉS de modal básico
        if self.parent:
            # Centrar ventana (movido DESPUÉS de configuración modal base)
            self._center_window_on_parent()
            
            # Configurar protocolo de cierre
            self.window.protocol("WM_DELETE_WINDOW", self._close_window)
        
        # Frame principal con scroll
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # Título
        title_label = ttk.Label(main_frame, text="Configuración de Empresa", 
                               font=('TkDefaultFont', 14, 'bold'))
        title_label.grid(row=row, column=0, columnspan=2, pady=(0, 10))
        row += 1
        
        # Sección de datos básicos
        self._create_basic_data_section(main_frame, row)
        row += 5
        
        # Separador
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10
        )
        row += 1
        
        # Sección de contacto
        self._create_contact_section(main_frame, row)
        row += 3
        
        # Separador
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10
        )
        row += 1
        
        # Sección de configuración fiscal
        self._create_fiscal_section(main_frame, row)
        row += 3
        
        # Separador
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10
        )
        row += 1
        
        # Sección de logo
        self._create_logo_section(main_frame, row)
        row += 3
        
        # Separador
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10
        )
        row += 1
        
        # Sección de validación
        self._create_validation_section(main_frame, row)
        row += 2
        
        # Separador
        # ttk.Separator(main_frame, orient='horizontal').grid(
        #     row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10
        # )
        # row += 1
        
        # Botones de acción
        self._create_action_buttons(main_frame, row)
        
        # Configurar validación en tiempo real
        self._setup_validation()
    
    def _create_basic_data_section(self, parent, start_row):
        """
        Crear sección de datos básicos.
        """
        # Label de sección
        ttk.Label(parent, text="Datos Básicos", 
                 font=('TkDefaultFont', 10, 'bold')).grid(
            row=start_row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10)
        )
        
        row = start_row + 1
        
        # Nombre de la empresa
        ttk.Label(parent, text="* Nombre de la empresa:").grid(
            row=row, column=0, sticky=tk.W, pady=2
        )
        self.nombre_entry = ttk.Entry(parent, textvariable=self.nombre_var, width=40)
        self.nombre_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2, padx=(10, 0))
        row += 1
        
        # RUC
        ttk.Label(parent, text="* RUC:").grid(
            row=row, column=0, sticky=tk.W, pady=2
        )
        self.ruc_entry = ttk.Entry(parent, textvariable=self.ruc_var, width=20)
        self.ruc_entry.grid(row=row, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        # Label de ayuda para formato RUC
        ttk.Label(parent, text="Formato: 123-456-7890", 
                 font=('TkDefaultFont', 8), foreground='gray').grid(
            row=row, column=1, sticky=tk.W, padx=(150, 0)
        )
        row += 1
        
        # Dirección
        ttk.Label(parent, text="* Dirección:").grid(
            row=row, column=0, sticky=tk.W, pady=2
        )
        self.direccion_entry = ttk.Entry(parent, textvariable=self.direccion_var, width=50)
        self.direccion_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2, padx=(10, 0))
        row += 1
    
    def _create_contact_section(self, parent, start_row):
        """
        Crear sección de datos de contacto.
        """
        # Label de sección
        ttk.Label(parent, text="Datos de Contacto", 
                 font=('TkDefaultFont', 10, 'bold')).grid(
            row=start_row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10)
        )
        
        row = start_row + 1
        
        # Teléfono
        ttk.Label(parent, text="* Teléfono:").grid(
            row=row, column=0, sticky=tk.W, pady=2
        )
        self.telefono_entry = ttk.Entry(parent, textvariable=self.telefono_var, width=20)
        self.telefono_entry.grid(row=row, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        # Label de ayuda para formato teléfono
        ttk.Label(parent, text="Formato: 1234-5678", 
                 font=('TkDefaultFont', 8), foreground='gray').grid(
            row=row, column=1, sticky=tk.W, padx=(150, 0)
        )
        row += 1
        
        # Email
        ttk.Label(parent, text="* Email:").grid(
            row=row, column=0, sticky=tk.W, pady=2
        )
        self.email_entry = ttk.Entry(parent, textvariable=self.email_var, width=40)
        self.email_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2, padx=(10, 0))
        row += 1
    
    def _create_fiscal_section(self, parent, start_row):
        """
        Crear sección de configuración fiscal.
        """
        # Label de sección
        ttk.Label(parent, text="Configuración Fiscal", 
                 font=('TkDefaultFont', 10, 'bold')).grid(
            row=start_row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10)
        )
        
        row = start_row + 1
        
        # Tasa de ITBMS
        ttk.Label(parent, text="* Tasa de ITBMS (%):").grid(
            row=row, column=0, sticky=tk.W, pady=2
        )
        
        itbms_frame = ttk.Frame(parent)
        itbms_frame.grid(row=row, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        self.itbms_entry = ttk.Entry(itbms_frame, textvariable=self.itbms_rate_var, width=10)
        self.itbms_entry.pack(side=tk.LEFT)
        
        ttk.Label(itbms_frame, text="%").pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(itbms_frame, text="(0-100)", 
                 font=('TkDefaultFont', 8), foreground='gray').pack(side=tk.LEFT, padx=(10, 0))
        row += 1
        
        # Moneda
        ttk.Label(parent, text="* Moneda:").grid(
            row=row, column=0, sticky=tk.W, pady=2
        )
        
        moneda_frame = ttk.Frame(parent)
        moneda_frame.grid(row=row, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        self.moneda_combo = ttk.Combobox(moneda_frame, textvariable=self.moneda_var, 
                                        width=10, state="readonly")
        self.moneda_combo['values'] = ('USD', 'PAB', 'EUR', 'MXN', 'COP')
        self.moneda_combo.pack(side=tk.LEFT)
        
        # Mostrar símbolo de moneda
        self.simbolo_moneda_label = ttk.Label(moneda_frame, text="", 
                                            font=('TkDefaultFont', 10, 'bold'))
        self.simbolo_moneda_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Bind para actualizar símbolo
        self.moneda_combo.bind('<<ComboboxSelected>>', self._update_currency_symbol)
        row += 1
    
    def _create_logo_section(self, parent, start_row):
        """
        Crear sección de logo corporativo.
        """
        # Label de sección
        ttk.Label(parent, text="Logo Corporativo", 
                 font=('TkDefaultFont', 10, 'bold')).grid(
            row=start_row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10)
        )
        
        row = start_row + 1
        
        # Ruta del logo
        ttk.Label(parent, text="Ruta del logo:").grid(
            row=row, column=0, sticky=tk.W, pady=2
        )
        
        logo_frame = ttk.Frame(parent)
        logo_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2, padx=(10, 0))
        logo_frame.columnconfigure(0, weight=1)
        
        self.logo_entry = ttk.Entry(logo_frame, textvariable=self.logo_path_var, 
                                   state="readonly")
        self.logo_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(logo_frame, text="Examinar...", 
                  command=self._browse_logo).grid(row=0, column=1)
        
        ttk.Button(logo_frame, text="Quitar", 
                  command=self._remove_logo).grid(row=0, column=2, padx=(5, 0))
        row += 1
        
        # Estado del logo
        self.logo_status_label = ttk.Label(parent, text="", 
                                          font=('TkDefaultFont', 8))
        self.logo_status_label.grid(row=row, column=1, sticky=tk.W, padx=(10, 0))
        row += 1
    
    def _create_validation_section(self, parent, start_row):
        """
        Crear sección de validación.
        """
        # Label de sección
        ttk.Label(parent, text="Estado de Validación", 
                 font=('TkDefaultFont', 10, 'bold')).grid(
            row=start_row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10)
        )
        
        row = start_row + 1
        
        # Frame para mensajes de validación
        self.validation_frame = ttk.LabelFrame(parent, text="Validación", padding="10")
        self.validation_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        self.validation_frame.columnconfigure(0, weight=1)
        
        # Text widget para mensajes de validación
        self.validation_text = tk.Text(self.validation_frame, height=2, width=60, 
                                      wrap=tk.WORD, state=tk.DISABLED,
                                      font=('TkDefaultFont', 8))
        self.validation_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Scrollbar para validación
        validation_scroll = ttk.Scrollbar(self.validation_frame, orient=tk.VERTICAL, 
                                        command=self.validation_text.yview)
        validation_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.validation_text.configure(yscrollcommand=validation_scroll.set)
        
        row += 1
    
    def _create_action_buttons(self, parent, row):
        """
        Crear botones de acción.
        """
        # Frame para botones
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=row, column=0, columnspan=2, pady=5)
        
        # Botones principales
        ttk.Button(button_frame, text="Guardar Cambios", 
                  command=self._save_config).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Validar", 
                  command=self._validate_config).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Restablecer Defecto", 
                  command=self._reset_to_default).pack(side=tk.LEFT, padx=5)
        
        # Separador
        ttk.Separator(button_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Botones de importar/exportar
        # ttk.Button(button_frame, text="Exportar...", 
        #           command=self._export_config).pack(side=tk.LEFT, padx=5)
        
        # ttk.Button(button_frame, text="Importar...", 
        #          command=self._import_config).pack(side=tk.LEFT, padx=5)
        
        # Botón cerrar
        ttk.Button(button_frame, text="Cerrar", 
                  command=self._close_window).pack(side=tk.RIGHT, padx=5)
    
    def _setup_validation(self):
        """
        Configurar validación en tiempo real.
        """
        # Bind eventos para validación en tiempo real
        self.nombre_var.trace('w', self._on_field_change)
        self.ruc_var.trace('w', self._on_field_change)
        self.direccion_var.trace('w', self._on_field_change)
        self.telefono_var.trace('w', self._on_field_change)
        self.email_var.trace('w', self._on_field_change)
        self.itbms_rate_var.trace('w', self._on_field_change)
        self.moneda_var.trace('w', self._on_field_change)
    
    def _load_current_config(self):
        """
        Cargar configuración actual en el formulario.
        """
        try:
            self.current_config = self.company_service.obtener_configuracion()
            
            # Cargar valores en las variables
            self.nombre_var.set(self.current_config.nombre)
            self.ruc_var.set(self.current_config.ruc)
            self.direccion_var.set(self.current_config.direccion)
            self.telefono_var.set(self.current_config.telefono)
            self.email_var.set(self.current_config.email)
            self.itbms_rate_var.set(str(float(self.current_config.itbms_rate)))
            self.moneda_var.set(self.current_config.moneda)
            self.logo_path_var.set(self.current_config.logo_path or "")
            
            # Actualizar símbolo de moneda
            self._update_currency_symbol()
            
            # Actualizar estado del logo
            self._update_logo_status()
            
            # Validar configuración inicial
            self._validate_config()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la configuración:\n{str(e)}", parent=self.window)
    
    def _on_field_change(self, *args):
        """
        Callback para cambios en campos del formulario.
        CORRECCIÓN APLICADA: Opcional refuerzo de foco modal tras actualizaciones
        """
        # Validar después de un pequeño delay para evitar validación constante
        self.window.after(500, self._validate_config)
        
        # OPCIONAL: Reforzar foco modal tras actualización si se detecta pérdida
        # Descomentear la siguiente línea solo si persiste problema de foco:
        # self.window.after(100, self._reinforce_modal_focus)
    
    def _update_currency_symbol(self, event=None):
        """
        Actualizar símbolo de moneda mostrado.
        """
        try:
            # Crear configuración temporal para obtener símbolo
            temp_config = CompanyConfig(moneda=self.moneda_var.get())
            simbolo = temp_config.obtener_simbolo_moneda()
            self.simbolo_moneda_label.config(text=f"({simbolo})")
        except:
            self.simbolo_moneda_label.config(text="")
    
    def _update_logo_status(self):
        """
        Actualizar estado del logo.
        """
        logo_path = self.logo_path_var.get()
        
        if not logo_path:
            self.logo_status_label.config(text="Sin logo configurado", foreground='gray')
        elif os.path.exists(logo_path):
            self.logo_status_label.config(text="✓ Archivo encontrado", foreground='green')
        else:
            self.logo_status_label.config(text="✗ Archivo no encontrado", foreground='red')
    
    def _browse_logo(self):
        """
        Examinar archivo de logo.
        """
        filetypes = [
            ("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp"),
            ("PNG files", "*.png"),
            ("JPEG files", "*.jpg *.jpeg"),
            ("Todos los archivos", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Seleccionar logo de empresa",
            filetypes=filetypes
        )
        
        if filename:
            self.logo_path_var.set(filename)
            self._update_logo_status()
    
    def _remove_logo(self):
        """
        Quitar logo configurado.
        """
        self.logo_path_var.set("")
        self._update_logo_status()
    
    def _validate_config(self):
        """
        Validar configuración actual y mostrar resultados.
        """
        try:
            # Crear configuración temporal con datos del formulario
            temp_config = CompanyConfig(
                nombre=self.nombre_var.get(),
                ruc=self.ruc_var.get(),
                direccion=self.direccion_var.get(),
                telefono=self.telefono_var.get(),
                email=self.email_var.get(),
                itbms_rate=float(self.itbms_rate_var.get() or 0),
                moneda=self.moneda_var.get(),
                logo_path=self.logo_path_var.get() or None
            )
            
            # Validar
            errores = temp_config.validar_datos()
            
            # Mostrar resultados
            self._show_validation_results(errores)
            
        except ValueError as e:
            if "itbms_rate" in str(e).lower():
                self._show_validation_results(["Tasa de ITBMS debe ser un número válido"])
            else:
                self._show_validation_results([str(e)])
        except Exception as e:
            self._show_validation_results([f"Error de validación: {str(e)}"])
    
    def _show_validation_results(self, errores: list):
        """
        Mostrar resultados de validación.
        
        Args:
            errores: Lista de errores encontrados
        """
        self.validation_text.config(state=tk.NORMAL)
        self.validation_text.delete(1.0, tk.END)
        
        if not errores:
            self.validation_text.insert(tk.END, "✓ La configuración es válida y completa")
            self.validation_text.config(bg='#e8f5e8')  # Fondo verde claro
        else:
            self.validation_text.insert(tk.END, "Errores encontrados:\n\n")
            for i, error in enumerate(errores, 1):
                self.validation_text.insert(tk.END, f"{i}. {error}\n")
            self.validation_text.config(bg='#fdf2f2')  # Fondo rojo claro
        
        self.validation_text.config(state=tk.DISABLED)
    
    def _save_config(self):
        """
        Guardar configuración actual.
        """
        try:
            # Validar antes de guardar
            temp_config = CompanyConfig(
                nombre=self.nombre_var.get(),
                ruc=self.ruc_var.get(),
                direccion=self.direccion_var.get(),
                telefono=self.telefono_var.get(),
                email=self.email_var.get(),
                itbms_rate=float(self.itbms_rate_var.get() or 0),
                moneda=self.moneda_var.get(),
                logo_path=self.logo_path_var.get() or None
            )
            
            errores = temp_config.validar_datos()
            if errores:
                messagebox.showerror("Error de Validación", 
                                   f"No se puede guardar. Errores:\n\n" + "\n".join(errores), parent=self.window)
                return
            
            # Confirmar guardado
            if not messagebox.askyesno("Confirmar Guardado", 
                                     "¿Está seguro de guardar los cambios en la configuración?", parent=self.window):
                return
            
            # Guardar configuración
            config_actualizada = self.company_service.actualizar_configuracion(
                nombre=self.nombre_var.get(),
                ruc=self.ruc_var.get(),
                direccion=self.direccion_var.get(),
                telefono=self.telefono_var.get(),
                email=self.email_var.get(),
                itbms_rate=float(self.itbms_rate_var.get()),
                moneda=self.moneda_var.get(),
                logo_path=self.logo_path_var.get() or None
            )
            
            self.current_config = config_actualizada
            
            messagebox.showinfo("Éxito", "Configuración guardada exitosamente", parent=self.window)
            
            # Revalidar
            self._validate_config()
            
        except ValueError as e:
            messagebox.showerror("Error", f"Error en los datos:\n{str(e)}", parent=self.window)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la configuración:\n{str(e)}", parent=self.window)
    
    def _reset_to_default(self):
        """
        Restablecer configuración a valores por defecto.
        """
        if not messagebox.askyesno("Confirmar Restablecimiento", 
                                 "¿Está seguro de restablecer la configuración a los valores por defecto?\n\n"
                                 "Esta acción no se puede deshacer.", parent=self.window):
            return
        
        try:
            # Restablecer en el servicio
            config_defecto = self.company_service.restablecer_configuracion_defecto()
            
            # Recargar formulario
            self._load_current_config()
            
            messagebox.showinfo("Éxito", "Configuración restablecida a valores por defecto", parent=self.window)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo restablecer la configuración:\n{str(e)}", parent=self.window)
    
    def _export_config(self):
        """
        Exportar configuración a archivo.
        """
        try:
            filename = filedialog.asksaveasfilename(
                title="Exportar configuración",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialname=f"config_empresa_{datetime.now().strftime('%Y%m%d')}.json"
            )
            
            if not filename:
                return
            
            # Exportar configuración actual
            config_data = self.company_service.exportar_configuracion()
            
            import json
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False, default=str)
            
            messagebox.showinfo("Éxito", f"Configuración exportada a:\n{filename}", parent=self.window)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar la configuración:\n{str(e)}", parent=self.window)
    
    def _import_config(self):
        """
        Importar configuración desde archivo.
        """
        try:
            filename = filedialog.askopenfilename(
                title="Importar configuración",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if not filename:
                return
            
            # Confirmar importación
            if not messagebox.askyesno("Confirmar Importación", 
                                     "¿Está seguro de importar la configuración?\n\n"
                                     "Esto sobrescribirá la configuración actual.", parent=self.window):
                return
            
            # Leer archivo
            import json
            with open(filename, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Importar configuración
            config_importada = self.company_service.importar_configuracion(config_data)
            
            # Recargar formulario
            self._load_current_config()
            
            messagebox.showinfo("Éxito", "Configuración importada exitosamente", parent=self.window)
            
        except FileNotFoundError:
            messagebox.showerror("Error", "Archivo no encontrado", parent=self.window)
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Archivo JSON inválido", parent=self.window)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo importar la configuración:\n{str(e)}", parent=self.window)
    
    def _center_window_on_parent(self):
        """
        Centrar la ventana respecto al parent.
        Método agregado para comportamiento modal consistente.
        """
        if not self.parent:
            return
            
        # Obtener dimensiones del parent
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Obtener dimensiones de esta ventana
        self.window.update_idletasks()  # Asegurar que geometry esté disponible
        window_width = 600  # Ancho definido en geometry
        window_height = 650  # Alto definido en geometry
        
        # Calcular posición centrada
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2
        
        # Asegurar que la ventana esté dentro de la pantalla
        if x < 0:
            x = 0
        if y < 0:
            y = 0
            
        # Aplicar posición
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def _reinforce_modal_focus(self):
        """
        Reforzar comportamiento modal si se pierde el foco.
        
        Método adicional para casos donde actualizaciones de campos
        podrían interferir con el comportamiento modal.
        Usar con moderación, solo cuando sea necesario.
        """
        try:
            if self.parent and hasattr(self, 'window') and self.window.winfo_exists():
                # Reforzar configuración modal siguiendo patrón MovementEntryForm
                self.window.transient(self.parent)
                self.window.grab_set()
                self.window.focus_force()
                self.window.lift()  # Traer al frente
        except Exception as e:
            # Manejo silencioso para evitar interrumpir flujo de usuario
            pass
    
    def _close_window(self):
        """
        Cerrar la ventana.
        """
        if self.window:
            self.window.destroy()
    
    def show(self):
        """
        Mostrar el formulario.
        """
        if self.window:
            self.window.mainloop()


def main():
    """
    Función principal para testing del formulario.
    """
    form = CompanyConfigForm()
    form.show()


if __name__ == "__main__":
    main()
