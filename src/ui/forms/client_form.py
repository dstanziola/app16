"""
Ventana de gestión de clientes.

Esta clase implementa la interfaz para el CRUD completo de clientes,
incluyendo validaciones de RUC, integración con el servicio de clientes
y manejo de estados activo/inactivo.

FUNCIONALIDADES:
- Lista de clientes existentes con búsqueda
- Formulario de creación/edición con validación RUC
- Desactivación en lugar de eliminación física
- Búsqueda en tiempo real por nombre
- Validación de campos en tiempo real
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List
import logging

from services.service_container import get_container
from models.cliente import Cliente


class ClientWindow:
    """
    Ventana de gestión de clientes del sistema de inventario.
    
    Esta clase implementa una interfaz completa para la gestión de clientes,
    proporcionando funcionalidades CRUD (Crear, Leer, Actualizar, Desactivar)
    con validaciones robustas e integración con la capa de servicios.
    
    La ventana incluye:
    - Lista de clientes existentes con búsqueda en tiempo real
    - Formulario de edición con validación de campos
    - Operaciones seguras con confirmaciones
    - Manejo de errores y logging completo
    - Integración con ClientService para persistencia
    
    Arquitectura:
    - Sigue principios de Clean Architecture
    - Separación clara entre UI y lógica de negocio
    - Inyección de dependencias para servicios
    - Patrón MVC para organización de código
    
    Funcionalidades principales:
    - Crear nuevos clientes con validación de datos
    - Visualizar lista completa de clientes activos e inactivos
    - Buscar clientes por nombre en tiempo real
    - Editar información de clientes existentes
    - Desactivar clientes (mantiene historial)
    - Validación de campos obligatorios y formatos
    - Confirmación de operaciones críticas
    """
    
    def __init__(self, parent: tk.Tk):
        """
        Inicializa la ventana de clientes.
        
        Args:
            parent: Ventana padre
        """
        self.parent = parent
        self._client_service = None  # Lazy loading
        
        # Configurar logging
        self.logger = logging.getLogger(__name__)
        
        # Crear ventana
        self.root = tk.Toplevel(parent)
        self.root.title("Gestión de Clientes")
        self.root.geometry("900x650")
        self.root.transient(parent)
        self.root.grab_set()
        
        # Variables de formulario
        self.client_name_var = tk.StringVar()
        self.client_ruc_var = tk.StringVar()
        self.search_var = tk.StringVar()

        # Variable de filtro de estado
        self.filter_var = tk.StringVar(value="Activos")  # Valor por defecto

        # Estado del formulario
        self.editing_client: Optional[Cliente] = None
        self.clients: List[Cliente] = []
        
        # Referencias a widgets que necesitamos modificar
        self.name_entry = None
        self.ruc_entry = None
        self.client_tree = None
        self.new_button = None
        self.save_button = None
        self.edit_button = None
        self.delete_button = None
        self.cancel_button = None
        
        # Crear interfaz
        self._create_ui()
        
        # Configurar eventos
        self._setup_events()
        
        # Cargar datos iniciales
        self._load_clients()
    
    @property
    def client_service(self):
        """Acceso lazy al ClientService a través del Service Container."""
        if self._client_service is None:
            container = get_container()
            self._client_service = container.get('client_service')
        return self._client_service
        
    def _create_ui(self):
        """Crea los elementos de la interfaz de usuario."""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configurar grid principal
        main_frame.columnconfigure(0, weight=2)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Título
        title_label = ttk.Label(
            main_frame,
            text="Gestión de Clientes",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Panel izquierdo - Lista de clientes
        self._create_list_panel(main_frame)
        
        # Panel derecho - Formulario
        self._create_form_panel(main_frame)
        
        # Panel inferior - Botones
        # self._create_button_panel(main_frame)
        
    def _create_list_panel(self, parent):
        """Crea el panel de lista de clientes."""
        # Frame de lista
        list_frame = ttk.LabelFrame(parent, text="Clientes Existentes", padding=10)
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        # Configurar grid
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(2, weight=1)
        
        # Frame de búsqueda
        search_frame = ttk.Frame(list_frame)
        search_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)
        
        # Campo de búsqueda
        ttk.Label(search_frame, text="Buscar:").grid(row=0, column=0, padx=(0, 5))
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # Filtro de estado
        ttk.Label(search_frame, text="Mostrar:").grid(row=1, column=0, pady=(5, 0), sticky=tk.W)
        filter_options = ["Activos", "Inactivos", "Todos"]
        filter_combo = ttk.Combobox(search_frame, textvariable=self.filter_var, values=filter_options, state="readonly", width=12)
        filter_combo.grid(row=1, column=1, pady=(5, 0), sticky=tk.W)
        filter_combo.bind("<<ComboboxSelected>>", self._on_filter_change)

        # TreeView para lista de clientes
        columns = ('ID', 'Nombre', 'RUC', 'Estado')
        self.client_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=20)
        
        # Configurar columnas
        self.client_tree.heading('ID', text='ID')
        self.client_tree.heading('Nombre', text='Nombre')
        self.client_tree.heading('RUC', text='RUC')
        self.client_tree.heading('Estado', text='Estado')
        
        self.client_tree.column('ID', width=50)
        self.client_tree.column('Nombre', width=200)
        self.client_tree.column('RUC', width=120)
        self.client_tree.column('Estado', width=80)
        
        # Scrollbar para TreeView
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.client_tree.yview)
        self.client_tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid TreeView y scrollbar
        self.client_tree.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=2, column=1, sticky=(tk.N, tk.S))
        
    def _create_form_panel(self, parent):
        """Crea el panel de formulario."""
        # Frame de formulario
        form_frame = ttk.LabelFrame(parent, text="Datos de Cliente", padding=10)
        form_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        
        # Configurar grid
        form_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # Campo nombre
        ttk.Label(form_frame, text="Nombre *:").grid(row=row, column=0, sticky=tk.W, pady=(0, 10))
        self.name_entry = ttk.Entry(form_frame, textvariable=self.client_name_var, width=30, state='readonly')
        self.name_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=(0, 10))
        row += 1
        
        # Campo RUC
        ttk.Label(form_frame, text="RUC:").grid(row=row, column=0, sticky=tk.W, pady=(0, 10))
        self.ruc_entry = ttk.Entry(form_frame, textvariable=self.client_ruc_var, width=30, state='readonly')
        self.ruc_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=(0, 10))
        row += 1
        
        # Información adicional
        info_frame = ttk.Frame(form_frame)
        info_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(20, 0))
        info_frame.columnconfigure(0, weight=1)
        
        info_text = """Información del Cliente:

• Nombre: Es obligatorio poner nombre. No puede estar repetido.
• RUC / Cédula: Es opcional.

Nota: Al eliminar un cliente sus datos no son 
  eliminados para poder mantener el historial."""
        
        info_label = ttk.Label(
            info_frame,
            text=info_text,
            font=("Arial", 9),
            foreground="gray",
            justify=tk.LEFT
        )
        info_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Botones de acción

        # Frame para los botones de acción dentro del mismo panel
        button_frame = ttk.Frame(form_frame)
        row += 1
        button_frame.grid(row=row, column=0, columnspan=2, pady=(20, 0))

        # Primera fila de botones
        self.new_button = ttk.Button(button_frame, text="Nuevo", command=self._new_client)
        self.new_button.grid(row=0, column=0, padx=5, pady=5)

        self.save_button = ttk.Button(button_frame, text="Guardar", command=self._save_client, state='disabled')
        self.save_button.grid(row=0, column=1, padx=5, pady=5)

        self.edit_button = ttk.Button(button_frame, text="Editar", command=self._edit_client, state='disabled')
        self.edit_button.grid(row=0, column=2, padx=5, pady=5)

        # Segunda fila de botones
        self.delete_button = ttk.Button(button_frame, text="Desactivar", command=self._delete_client, state='disabled')
        self.delete_button.grid(row=1, column=0, padx=5, pady=5)

        self.cancel_button = ttk.Button(button_frame, text="Cancelar", command=self._cancel_edit, state='disabled')
        self.cancel_button.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(button_frame, text="Cerrar", command=self._close_window).grid(row=1, column=2, padx=5, pady=5)


    # def _create_button_panel(self, parent):
    #     """Crea el panel de botones."""
    #     button_frame = ttk.Frame(parent)
    #     button_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(20, 0))
        
        # Botones de acción
    #     self.new_button = ttk.Button(button_frame, text="Nuevo", command=self._new_client)
    #     self.new_button.pack(side=tk.LEFT, padx=(0, 5))
        
    #     self.save_button = ttk.Button(button_frame, text="Guardar", command=self._save_client, state='disabled')
    #     self.save_button.pack(side=tk.LEFT, padx=(0, 5))
        
    #     self.edit_button = ttk.Button(button_frame, text="Editar", command=self._edit_client, state='disabled')
     #    self.edit_button.pack(side=tk.LEFT, padx=(0, 5))
        
    #     self.delete_button = ttk.Button(button_frame, text="Desactivar", command=self._delete_client, state='disabled')
    #     self.delete_button.pack(side=tk.LEFT, padx=(0, 5))
        
    #     self.cancel_button = ttk.Button(button_frame, text="Cancelar", command=self._cancel_edit, state='disabled')
    #     self.cancel_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Botón cerrar
    #     ttk.Button(button_frame, text="Cerrar", command=self._close_window).pack(side=tk.RIGHT)
        
    def _setup_events(self):
        """Configura eventos de la ventana."""
        # Selección en TreeView
        self.client_tree.bind('<<TreeviewSelect>>', self._on_client_select)
        
        # Búsqueda en tiempo real
        self.search_var.trace('w', self._on_search)
        
        # Validación en tiempo real
        self.client_name_var.trace('w', self._validate_form)
        
        # Protocolo de cierre
        self.root.protocol("WM_DELETE_WINDOW", self._close_window)

    def _load_clients(self):
        """Carga los clientes desde la base de datos."""
        try:
            # Siempre cargamos TODOS, filtraremos al mostrar
            self.clients = self.client_service.get_all_clients(only_active=False)
            self._update_client_list()
            self.logger.info(f"Cargados {len(self.clients)} clientes")
        except Exception as e:
            self.logger.error(f"Error al cargar clientes: {e}")
            messagebox.showerror("Error", f"No se pudieron cargar los clientes: {e}")
    
    def _update_client_list(self, filter_text: str = ""):
        """Actualiza la lista de clientes en el TreeView."""
        
        filter_text = filter_text.lower() if filter_text else ""
        filter_option = self.filter_var.get()
        
        # Limpiar TreeView
        for item in self.client_tree.get_children():
            self.client_tree.delete(item)

        # Agregar clientes filtrados
        for client in self.clients:
            if filter_option == "Activos" and not client.activo:
                continue
            if filter_option == "Inactivos" and client.activo:
                continue
            if filter_text and filter_text not in client.nombre.lower():
                continue

            status = "Activo" if client.activo else "Inactivo"
            ruc_display = client.ruc if client.ruc else "N/A"

            self.client_tree.insert('', tk.END, values=(
                client.id_cliente,
                client.nombre,
                ruc_display,
                status
            ))

    def _on_filter_change(self, event):
        """Actualiza la lista al cambiar el filtro."""
        self._update_client_list(self.search_var.get())

    def _on_client_select(self, event):
        """Maneja la selección de un cliente en la lista."""
        selection = self.client_tree.selection()
        if selection:
            item = self.client_tree.item(selection[0])
            client_id = int(item['values'][0])
            
            # Buscar cliente seleccionado
            selected_client = None
            for client in self.clients:
                if client.id_cliente == client_id:
                    selected_client = client
                    break
                    
            if selected_client:
                # Mostrar datos en formulario (solo lectura)
                self.client_name_var.set(selected_client.nombre)
                self.client_ruc_var.set(selected_client.ruc if selected_client.ruc else "")
                
                # Habilitar botones de edición
                self.edit_button.config(state='normal')
                self.delete_button.config(state='normal')
                
                # Deshabilitar campos de formulario
                self.name_entry.config(state='readonly')
                self.ruc_entry.config(state='readonly')
                
    def _on_search(self, *args):
        """Maneja la búsqueda en tiempo real."""
        search_text = self.search_var.get()
        self._update_client_list(search_text)
        
    def _validate_form(self, *args):
        """Valida el formulario en tiempo real."""
        name = self.client_name_var.get().strip()
        
        if name and self.editing_client is not None:
            self.save_button.config(state='normal')
        else:
            self.save_button.config(state='disabled')
            
    def _new_client(self):
        """Inicia el proceso de creación de nuevo cliente."""
        self._clear_form()
        self.editing_client = True
        
        # Habilitar campos
        self.name_entry.config(state='normal')
        self.ruc_entry.config(state='normal')
        
        # Configurar botones
        self.new_button.config(state='disabled')
        self.edit_button.config(state='disabled')
        self.delete_button.config(state='disabled')
        self.cancel_button.config(state='normal')
        
        self.name_entry.focus()
        
    def _edit_client(self):
        """Inicia el proceso de edición de cliente seleccionado."""
        selection = self.client_tree.selection()
        if not selection:
            messagebox.showwarning("Selección Requerida", "Debe seleccionar un cliente para editar")
            return
            
        item = self.client_tree.item(selection[0])
        client_id = int(item['values'][0])
        
        # Buscar cliente para editar
        for client in self.clients:
            if client.id_cliente == client_id:
                self.editing_client = client
                break
                
        # Habilitar campos
        self.name_entry.config(state='normal')
        self.ruc_entry.config(state='normal')
        
        # Configurar botones
        self.new_button.config(state='disabled')
        self.edit_button.config(state='disabled')
        self.delete_button.config(state='disabled')
        self.cancel_button.config(state='normal')
        
        self.name_entry.focus()
        
    def _save_client(self):
        """Guarda el cliente (nuevo o editado)."""
        name = self.client_name_var.get().strip()
        ruc = self.client_ruc_var.get().strip()
        
        # Validar campos
        if not name:
            messagebox.showwarning("Campo Requerido", "El nombre es obligatorio")
            return
            
        try:
            if self.editing_client is True:  # Nuevo cliente
                client = self.client_service.create_client(
                    nombre=name,
                    ruc=ruc if ruc else None
                )
                messagebox.showinfo("Éxito", "Cliente creado exitosamente")
                self.logger.info(f"Cliente creado: {name}")
                
            else:  # Editar cliente existente
                client = self.client_service.update_client(
                    id_cliente=self.editing_client.id_cliente,
                    nombre=name,
                    ruc=ruc if ruc else None
                )
                messagebox.showinfo("Éxito", "Cliente actualizado exitosamente")
                self.logger.info(f"Cliente actualizado: {name}")
                
            # Recargar lista
            self._load_clients()
            self._cancel_edit()
            
        except ValueError as e:
            messagebox.showerror("Error de Validación", str(e))
        except Exception as e:
            self.logger.error(f"Error al guardar cliente: {e}")
            messagebox.showerror("Error", f"No se pudo guardar el cliente: {e}")
            
    def _delete_client(self):
        """Elimina el cliente seleccionado."""
        selection = self.client_tree.selection()
        if not selection:
            messagebox.showwarning("Selección Requerida", "Debe seleccionar un cliente para eliminar")
            return
            
        item = self.client_tree.item(selection[0])
        client_id = int(item['values'][0])
        client_name = item['values'][1]
        
        # Confirmar eliminación
        result = messagebox.askyesno(
            "Confirmar Desactivación",
            f"¿Está seguro que desea desactivar el cliente '{client_name}'?\n\nEsta acción no se puede deshacer."
        )
        
        if result:
            try:
                # En lugar de eliminar físicamente, desactivar cliente
                # self.client_service.deactivate_user(client_id)
                self.client_service.deactivate_client(client_id)

                messagebox.showinfo("Éxito", "Cliente desactivado exitosamente")
                self.logger.info(f"Cliente desactivado: {client_name}")
                
                # Recargar lista
                self._load_clients()
                self._clear_form()
                
            except Exception as e:
                self.logger.error(f"Error al desactivar cliente: {e}")
                messagebox.showerror("Error", f"No se pudo desactivar el cliente: {e}")
                
    def _cancel_edit(self):
        """Cancela la edición actual."""
        self.editing_client = None
        self._clear_form()
        
        # Deshabilitar campos
        self.name_entry.config(state='readonly')
        self.ruc_entry.config(state='readonly')
        
        # Configurar botones
        self.new_button.config(state='normal')
        self.save_button.config(state='disabled')
        self.edit_button.config(state='disabled')
        self.delete_button.config(state='disabled')
        self.cancel_button.config(state='disabled')
        
    def _clear_form(self):
        """Limpia los campos del formulario."""
        self.client_name_var.set("")
        self.client_ruc_var.set("")
        
        # Limpiar selección en TreeView
        for item in self.client_tree.selection():
            self.client_tree.selection_remove(item)
            
    def _close_window(self):
        """Cierra la ventana."""
        if self.editing_client is not None:
            result = messagebox.askyesno(
                "Confirmar Cierre",
                "Hay cambios sin guardar. ¿Está seguro que desea cerrar?"
            )
            if not result:
                return
                
        self.root.destroy()
