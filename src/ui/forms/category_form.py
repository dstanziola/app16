"""
Ventana de gestión de categorías - VERSIÓN CORREGIDA PARA CIERRE.

Esta clase implementa la interfaz para el CRUD completo de categorías,
con gestión mejorada de ventanas y protocolo de cierre corregido.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List
import logging

from services.service_container import get_container
from models.categoria import Categoria
from ui.utils.window_manager import window_manager, safe_widget_state, validate_widget_exists

class CategoryWindow:
    """Ventana de gestión de categorías con gestión mejorada."""
    
    def __init__(self, parent: tk.Tk):
        """
        Inicializa la ventana de categorías.
        
        Args:
            parent: Ventana padre
        """
        self.parent = parent
        self._category_service = None  # Lazy loading
        
        # Configurar logging
        self.logger = logging.getLogger(__name__)
        
        # Crear ventana
        self.root = tk.Toplevel(parent)
        self.root.title("Gestión de Categorías")
        self.root.geometry("800x600")
        self.root.transient(parent)
        self.root.grab_set()

        # Variables de formulario
        self.category_name_var = tk.StringVar()
        self.category_type_var = tk.StringVar()
        self.description_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.filter_type_var = tk.StringVar()
        
        # Estado del formulario
        self.editing_category: Optional[Categoria] = None
        self.categories: List[Categoria] = []
        
        # Referencias a widgets críticos
        self.widgets = {}
        
        # Flag para control de cierre
        self._closing = False
        
        # Crear interfaz
        self._create_ui()
        
        # Configurar eventos (incluyendo protocolo de cierre)
        self._setup_events()
        
        # NO registrar en window manager para evitar conflictos
        # El window manager puede interferir con el protocolo de cierre
        
        # Cargar datos iniciales
        self._load_categories()
    
    @property
    def category_service(self):
        """Acceso lazy al CategoryService a través del Service Container."""
        if self._category_service is None:
            container = get_container()
            self._category_service = container.get('category_service')
        return self._category_service
        
    def _create_ui(self):
        """Crea los elementos de la interfaz de usuario."""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configurar grid principal
        main_frame.columnconfigure(0, weight=1)
        # main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Título
        title_label = ttk.Label(
            main_frame,
            text="Gestión de Categorías",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=1, column=0, pady=(0, 10))

        """Crea el panel de botones."""
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, sticky=tk.W, pady=(0, 10))

        # Botones de acción
        self.widgets['new_button'] = ttk.Button(button_frame, text="Nuevo", command=self._new_category)
        self.widgets['new_button'].pack(side=tk.LEFT, padx=(0, 5))
        
        self.widgets['save_button'] = ttk.Button(button_frame, text="Guardar", command=self._save_category, state='disabled')
        self.widgets['save_button'].pack(side=tk.LEFT, padx=(0, 5))
        
        self.widgets['edit_button'] = ttk.Button(button_frame, text="Editar", command=self._edit_category, state='disabled')
        self.widgets['edit_button'].pack(side=tk.LEFT, padx=(0, 5))
        
        self.widgets['delete_button'] = ttk.Button(button_frame, text="Eliminar", command=self._delete_category, state='disabled')
        self.widgets['delete_button'].pack(side=tk.LEFT, padx=(0, 5))
        
        self.widgets['cancel_button'] = ttk.Button(button_frame, text="Cancelar", command=self._cancel_edit, state='disabled')
        self.widgets['cancel_button'].pack(side=tk.LEFT, padx=(0, 5))
        
        # Botón cerrar
        self.widgets['close_button'] = ttk.Button(button_frame, text="Cerrar", command=self._close_window)
        self.widgets['close_button'].pack(side=tk.LEFT, padx=(0, 5))

        # Panel superior - Formulario
        self._create_form_panel(main_frame)

        # Panel inferior - Lista de categorías
        self._create_list_panel(main_frame)

    def _create_form_panel(self, parent):
        """Crea el panel de formulario."""
        # Frame de formulario
        form_frame = ttk.LabelFrame(parent, text="Datos de Categoría: Seleccione Nuevo para crear o haga click en una categoría", padding=10)
        form_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), padx=(5, 0))
        
        # Configurar grid
        form_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # Campo nombre
        ttk.Label(form_frame, text="Nombre:").grid(row=row, column=0, sticky=tk.W, pady=(0, 5))
        self.name_entry = ttk.Entry(form_frame, textvariable=self.category_name_var, width=30)
        self.name_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        row += 1
        
        # Campo tipo
        ttk.Label(form_frame, text="Tipo:").grid(row=row, column=0, sticky=tk.W, pady=(0, 5))
        self.type_combo = ttk.Combobox(
            form_frame, 
            textvariable=self.category_type_var,
            values=["MATERIAL", "SERVICIO"],
            state='readonly',
            width=27
        )
        self.type_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        row += 1
        
        # Campo descripción
        # ttk.Label(form_frame, text="Descripción:").grid(row=row, column=0, sticky=(tk.W, tk.N), pady=(0, 5))
        # description_frame = ttk.Frame(form_frame)
        # description_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        # description_frame.columnconfigure(0, weight=1)
        
        # self.description_text = tk.Text(description_frame, height=1, width=30, wrap=tk.WORD)
        # desc_scrollbar = ttk.Scrollbar(description_frame, orient=tk.VERTICAL, command=self.description_text.yview)
        # self.description_text.configure(yscrollcommand=desc_scrollbar.set)
        
        # self.description_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        # desc_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        # row += 1
 
        # Campo descripción
        ttk.Label(form_frame, text="Descripción:").grid(row=row, column=0, sticky=tk.W, pady=(0, 5))
        self.description_entry = ttk.Entry(form_frame, textvariable=self.description_var, width=30)
        self.description_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        row += 1

    def _create_list_panel(self, parent):
        """Crea el panel de lista de categorías."""
        # Frame de lista
        list_frame = ttk.LabelFrame(parent, text="Categorías Existentes", padding=10)
        list_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 15))
        
        # Configurar grid
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(2, weight=1)
        
        # Frame de filtros
        filter_frame = ttk.Frame(list_frame)
        filter_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        filter_frame.columnconfigure(1, weight=1)
        
        # Campo de búsqueda
        ttk.Label(filter_frame, text="Buscar:").grid(row=0, column=0, padx=(0, 5))
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Filtro por tipo
        ttk.Label(filter_frame, text="Tipo:").grid(row=0, column=2, padx=(0, 5))
        filter_combo = ttk.Combobox(
            filter_frame, 
            textvariable=self.filter_type_var,
            values=["Todos", "MATERIAL", "SERVICIO"],
            state='readonly',
            width=10
        )
        filter_combo.set("Todos")
        filter_combo.grid(row=0, column=3)
        
        # TreeView para lista de categorías
        columns = ('ID', 'Nombre', 'Tipo', 'Descripción')
        self.category_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # Configurar columnas
        self.category_tree.heading('ID', text='ID')
        self.category_tree.heading('Nombre', text='Nombre')
        self.category_tree.heading('Tipo', text='Tipo')
        self.category_tree.heading('Descripción', text='Descripción')
        
        self.category_tree.column('ID', width=50)
        self.category_tree.column('Nombre', width=150)
        self.category_tree.column('Tipo', width=100)
        self.category_tree.column('Descripción', width=200)
        
        # Scrollbar para TreeView
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.category_tree.yview)
        self.category_tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid TreeView y scrollbar
        self.category_tree.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=2, column=1, sticky=(tk.N, tk.S))
        

    def _setup_events(self):
        """Configura eventos de la ventana."""
        # Selección en TreeView
        self.category_tree.bind('<<TreeviewSelect>>', self._on_category_select)
        
        # Búsqueda en tiempo real
        self.search_var.trace('w', self._on_search)
        self.filter_type_var.trace('w', self._on_search)
        
        # Validación en tiempo real
        self.category_name_var.trace('w', self._validate_form)
        self.category_type_var.trace('w', self._validate_form)
        
        # Sincronizar texto de descripción
        # self.description_entry.bind('<KeyRelease>', self._sync_description)
        
        # PROTOCOLO DE CIERRE CRÍTICO - NO DEBE SER SOBRESCRITO
        self.root.protocol("WM_DELETE_WINDOW", self._handle_window_close)
        
    def _load_categories(self):
        """Carga las categorías desde la base de datos."""
        try:
            self.categories = self.category_service.get_all_categories()
            self._update_category_list()
            self.logger.info(f"Cargadas {len(self.categories)} categorías")
            
        except Exception as e:
            self.logger.error(f"Error al cargar categorías: {e}")
            messagebox.showerror("Error", f"No se pudieron cargar las categorías: {e}")
            
    def _update_category_list(self, filter_text: str = "", filter_type: str = "Todos"):
        """Actualiza la lista de categorías en el TreeView."""
        # Limpiar TreeView
        for item in self.category_tree.get_children():
            self.category_tree.delete(item)
            
        # Agregar categorías filtradas
        for category in self.categories:
            # Aplicar filtros
            name_match = not filter_text or filter_text.lower() in category.nombre.lower()
            type_match = filter_type == "Todos" or filter_type == category.tipo
            
            if name_match and type_match:
                description = category.descripcion or ""
                if len(description) > 50:
                    description = description[:47] + "..."
                    
                self.category_tree.insert('', tk.END, values=(
                    category.id_categoria,
                    category.nombre,
                    category.tipo,
                    description
                ))
                
    def _on_category_select(self, event):
        """Maneja la selección de una categoría en la lista."""
        selection = self.category_tree.selection()
        if selection:
            item = self.category_tree.item(selection[0])
            category_id = int(item['values'][0])
            
            # Buscar categoría seleccionada
            selected_category = None
            for category in self.categories:
                if category.id_categoria == category_id:
                    selected_category = category
                    break
                    
            if selected_category:
                # Mostrar datos en formulario (solo lectura)
                self.category_name_var.set(selected_category.nombre)
                self.category_type_var.set(selected_category.tipo)
                
                # Mostrar descripción
                # self.description_text.delete(1.0, tk.END)
                # if selected_category.descripcion:
                #    self.description_text.insert(1.0, selected_category.descripcion)
                
                self.description_var.set(selected_category.descripcion or "")

                # Habilitar botones de edición - CON VALIDACIÓN
                safe_widget_state(self.widgets.get('edit_button'), 'normal')
                safe_widget_state(self.widgets.get('delete_button'), 'normal')
                
                # Deshabilitar campos de formulario
                self._disable_form()
                
    def _on_search(self, *args):
        """Maneja la búsqueda y filtrado en tiempo real."""
        search_text = self.search_var.get()
        filter_type = self.filter_type_var.get()
        self._update_category_list(search_text, filter_type)
        
    def _validate_form(self, *args):
        """Valida el formulario en tiempo real - CON PROTECCIÓN."""
        try:
            name = self.category_name_var.get().strip()
            type_val = self.category_type_var.get()
            
            save_button = self.widgets.get('save_button')
            if save_button and validate_widget_exists(save_button):
                if name and type_val and self.editing_category is not None:
                    safe_widget_state(save_button, 'normal')
                else:
                    safe_widget_state(save_button, 'disabled')
        except Exception as e:
            self.logger.error(f"Error en validación de formulario: {e}")
            
 #    def _sync_description(self, event):
 #       """Sincroniza el texto de descripción con la variable."""
 #       try:
 #           content = self.description_text.get(1.0, tk.END).strip()
 #           self.description_var.set(content)
 #       except Exception as e:
 #           self.logger.error(f"Error al sincronizar descripción: {e}")
        
    def _enable_form(self):
        """Habilita los campos del formulario."""
        try:
            if validate_widget_exists(self.name_entry):
                self.name_entry.config(state='normal')
            if validate_widget_exists(self.type_combo):
                self.type_combo.config(state='readonly')
            # if validate_widget_exists(self.description_text):
            #    self.description_text.config(state='normal')
            if validate_widget_exists(self.description_entry):
                self.description_entry.config(state='normal')


        except Exception as e:
            self.logger.error(f"Error al habilitar formulario: {e}")
        
    def _disable_form(self):
        """Deshabilita los campos del formulario."""
        try:
            if validate_widget_exists(self.name_entry):
                self.name_entry.config(state='readonly')
            if validate_widget_exists(self.type_combo):
                self.type_combo.config(state='disabled')
            # if validate_widget_exists(self.description_text):
            #     self.description_text.config(state='disabled')
            if validate_widget_exists(self.description_entry):
                self.description_entry.config(state='readonly')


        except Exception as e:
            self.logger.error(f"Error al deshabilitar formulario: {e}")
        
    def _new_category(self):
        """Inicia el proceso de creación de nueva categoría."""
        self._clear_form()
        self.editing_category = True
        self._enable_form()
        
        # Configurar botones - CON VALIDACIÓN
        safe_widget_state(self.widgets.get('new_button'), 'disabled')
        safe_widget_state(self.widgets.get('edit_button'), 'disabled')
        safe_widget_state(self.widgets.get('delete_button'), 'disabled')
        safe_widget_state(self.widgets.get('cancel_button'), 'normal')
        
        if validate_widget_exists(self.name_entry):
            self.name_entry.focus()
        
    def _edit_category(self):
        """Inicia el proceso de edición de categoría seleccionada."""
        selection = self.category_tree.selection()
        if not selection:
            return
            
        item = self.category_tree.item(selection[0])
        category_id = int(item['values'][0])
        
        # Buscar categoría seleccionada
        for category in self.categories:
            if category.id_categoria == category_id:
                self.editing_category = category
                break
                
        if self.editing_category:
            self._enable_form()
            
            # Configurar botones - CON VALIDACIÓN
            safe_widget_state(self.widgets.get('new_button'), 'disabled')
            safe_widget_state(self.widgets.get('edit_button'), 'disabled')
            safe_widget_state(self.widgets.get('delete_button'), 'disabled')
            safe_widget_state(self.widgets.get('cancel_button'), 'normal')
            
            if validate_widget_exists(self.name_entry):
                self.name_entry.focus()

            # Forzar validación para habilitar botón Guardar si corresponde
            self._validate_form()
            
    def _save_category(self):
        """Guarda la categoría (nueva o editada)."""
        try:
            # Obtener datos del formulario
            name = self.category_name_var.get().strip()
            type_val = self.category_type_var.get()
            # description = self.description_text.get(1.0, tk.END).strip()
            description = self.description_var.get().strip()

            
            # Validaciones básicas
            if not name:
                messagebox.showerror("Error", "El nombre es obligatorio")
                return
                
            if not type_val:
                messagebox.showerror("Error", "El tipo es obligatorio")
                return
                
            if isinstance(self.editing_category, Categoria):
                # Editar categoría existente
                updated_category = self.category_service.update_category(
                    id_categoria=self.editing_category.id_categoria,
                    nombre=name,
                    tipo=type_val,
                    descripcion=description if description else None
                )
                messagebox.showinfo("Éxito", "Categoría actualizada exitosamente")
                self.logger.info(f"Categoría actualizada: {name}")
                
            else:
                # Crear nueva categoría
                new_category = self.category_service.create_category(
                    nombre=name,
                    tipo=type_val,
                    descripcion=description if description else None
                )
                messagebox.showinfo("Éxito", "Categoría creada exitosamente")
                self.logger.info(f"Categoría creada: {name}")
                
            # Recargar lista y limpiar formulario
            self._load_categories()
            self._cancel_edit()
            
        except ValueError as e:
            messagebox.showerror("Error de Validación", str(e))
        except Exception as e:
            self.logger.error(f"Error al guardar categoría: {e}")
            messagebox.showerror("Error", f"No se pudo guardar la categoría: {e}")
            
    def _delete_category(self):
        """Elimina la categoría seleccionada."""
        selection = self.category_tree.selection()
        if not selection:
            return
            
        item = self.category_tree.item(selection[0])
        category_id = int(item['values'][0])
        category_name = item['values'][1]
        
        # Confirmar eliminación
        result = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Está seguro que desea eliminar la categoría '{category_name}'?\n\n"
            "Esta acción no se puede deshacer."
        )
        
        if result:
            try:
                self.category_service.delete_category(category_id)
                messagebox.showinfo("Éxito", "Categoría eliminada exitosamente")
                self.logger.info(f"Categoría eliminada: {category_name}")
                
                # Recargar lista
                self._load_categories()
                self._clear_form()
                
            except ValueError as e:
                messagebox.showerror("Error de Validación", str(e))
            except Exception as e:
                self.logger.error(f"Error al eliminar categoría: {e}")
                messagebox.showerror("Error", f"No se pudo eliminar la categoría: {e}")
                
    def _cancel_edit(self):
        """Cancela la edición actual."""
        self.editing_category = None
        self._clear_form()
        
        # Deshabilitar campos
        if validate_widget_exists(self.name_entry):
            self.name_entry.config(state='readonly')
        if validate_widget_exists(self.type_combo):
            self.type_combo.config(state='disabled')
        if validate_widget_exists(self.description_entry):
            self.description_entry.config(state='disabled')
        
        # Configurar botones - CON VALIDACIÓN
        safe_widget_state(self.widgets.get('new_button'), 'normal')
        safe_widget_state(self.widgets.get('save_button'), 'disabled')
        safe_widget_state(self.widgets.get('edit_button'), 'disabled')
        safe_widget_state(self.widgets.get('delete_button'), 'disabled')
        safe_widget_state(self.widgets.get('cancel_button'), 'disabled')
        
    def _clear_form(self):
        """Limpia los campos del formulario."""
        self.category_name_var.set("")
        self.category_type_var.set("")
        
        # try:
        #     if validate_widget_exists(self.description_text):
        #         self.description_text.delete(1.0, tk.END)
        # except Exception as e:
        #     self.logger.error(f"Error al limpiar descripción: {e}")

        self.description_var.set("")
        
        # Limpiar selección en TreeView
        try:
            for item in self.category_tree.selection():
                self.category_tree.selection_remove(item)
        except Exception as e:
            self.logger.error(f"Error al limpiar selección: {e}")
    
    def _handle_window_close(self):
        """
        Maneja el evento de cierre de ventana desde la X.
        
        Este método es llamado directamente por el protocolo WM_DELETE_WINDOW
        y asegura que la ventana se cierre correctamente.
        """
        if self._closing:
            return  # Evitar múltiples llamadas
            
        self._closing = True
        
        try:
            # Verificar si hay cambios sin guardar
            if self.editing_category is not None:
                result = messagebox.askyesno(
                    "Confirmar Cierre",
                    "Hay cambios sin guardar. ¿Está seguro que desea cerrar?"
                )
                if not result:
                    self._closing = False
                    return
            
            # Ejecutar cierre inmediato
            self._force_close()
            
        except Exception as e:
            self.logger.error(f"Error en protocolo de cierre: {e}")
            # Forzar cierre en caso de error
            self._force_close()
    
    def _close_window(self):
        """
        Cierra la ventana desde el botón Cerrar.
        
        Este método puede ser llamado por botones u otros controles.
        """
        self._handle_window_close()
    
    def _force_close(self):
        """
        Fuerza el cierre de la ventana sin confirmaciones adicionales.
        
        Método de último recurso para garantizar que la ventana se cierre.
        """
        try:
            # Liberar grab set ANTES de destruir
            if hasattr(self.root, 'grab_release'):
                self.root.grab_release()
        except Exception as e:
            self.logger.debug(f"Error al liberar grab: {e}")
        
        try:
            # Destruir ventana inmediatamente
            if hasattr(self.root, 'destroy'):
                self.root.destroy()
                
            self.logger.info("Ventana de categorías cerrada exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error crítico al forzar cierre: {e}")
            # En último caso, intentar salir del mainloop si es necesario
            try:
                if hasattr(self.root, 'quit'):
                    self.root.quit()
            except Exception:
                pass  # Último recurso exhausto
