"""
DataGrid - Widget de tabla de datos avanzado
Arquitectura: Clean Architecture - Capa Presentación
Patrón: Component + Observer
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Tuple, Optional, Any, Callable
import logging

from utils.logger import get_logger


class DataGrid(ttk.Frame):
    """
    Widget de tabla de datos con funcionalidades avanzadas:
    - Múltiples columnas configurables
    - Búsqueda y filtrado
    - Paginación
    - Ordenamiento
    - Selección de filas
    - Exportación de datos
    
    Arquitectura:
    - Component Pattern: Widget reutilizable
    - Observer Pattern: Notificación de eventos
    - Strategy Pattern: Diferentes tipos de celda
    """
    
    def __init__(self, parent: tk.Widget, columns: List[Tuple[str, str, int]], 
                 show_search: bool = True, show_pagination: bool = True,
                 page_size: int = 50, **kwargs):
        """
        Constructor del DataGrid
        
        Args:
            parent: Widget padre
            columns: Lista de tuplas (id, title, width) para columnas
            show_search: Mostrar barra de búsqueda
            show_pagination: Mostrar controles de paginación
            page_size: Elementos por página
            **kwargs: Argumentos adicionales para ttk.Frame
        """
        super().__init__(parent, **kwargs)
        
        self.logger = get_logger(self.__class__.__name__)
        self.columns = columns
        self.show_search = show_search
        self.show_pagination = show_pagination
        self.page_size = page_size
        
        # Datos y estado
        self.all_data: List[List[Any]] = []
        self.filtered_data: List[List[Any]] = []
        self.current_page = 0
        self.total_pages = 0
        
        # Variables de control
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._on_search_changed)
        
        # Callbacks de eventos
        self.row_select_callback: Optional[Callable] = None
        self.row_double_click_callback: Optional[Callable] = None
        
        # Crear componentes
        self._create_components()
        self._setup_layout()
        self._bind_events()
        
        self.logger.debug("DataGrid inicializado exitosamente")
    
    def _create_components(self) -> None:
        """Crear todos los componentes del DataGrid"""
        # Barra de búsqueda (opcional)
        if self.show_search:
            self._create_search_bar()
        
        # Tabla principal
        self._create_treeview()
        
        # Controles de paginación (opcional)
        if self.show_pagination:
            self._create_pagination_controls()
    
    def _create_search_bar(self) -> None:
        """Crear barra de búsqueda"""
        search_frame = ttk.Frame(self)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(search_frame, text="Buscar:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.search_entry = ttk.Entry(
            search_frame, 
            textvariable=self.search_var,
            width=30
        )
        self.search_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botón limpiar búsqueda
        clear_btn = ttk.Button(
            search_frame,
            text="Limpiar",
            command=self._clear_search,
            width=8
        )
        clear_btn.pack(side=tk.LEFT)
    
    def _create_treeview(self) -> None:
        """Crear el Treeview principal"""
        # Frame para Treeview con scrollbars
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configurar columnas
        column_ids = [col[0] for col in self.columns]
        
        # Crear Treeview
        self.tree = ttk.Treeview(
            tree_frame,
            columns=column_ids,
            show='headings',
            selectmode='extended'
        )
        
        # Configurar columnas
        for col_id, col_title, col_width in self.columns:
            self.tree.heading(col_id, text=col_title, anchor='w')
            self.tree.column(col_id, width=col_width, anchor='w')
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout para tree y scrollbars
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
    
    def _create_pagination_controls(self) -> None:
        """Crear controles de paginación"""
        pagination_frame = ttk.Frame(self)
        pagination_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Información de página
        self.page_info_var = tk.StringVar()
        self.page_info_label = ttk.Label(
            pagination_frame,
            textvariable=self.page_info_var
        )
        self.page_info_label.pack(side=tk.LEFT)
        
        # Botones de navegación
        nav_frame = ttk.Frame(pagination_frame)
        nav_frame.pack(side=tk.RIGHT)
        
        self.first_btn = ttk.Button(
            nav_frame,
            text="<<",
            command=lambda: self.go_to_page(0),
            width=4
        )
        self.first_btn.pack(side=tk.LEFT, padx=2)
        
        self.prev_btn = ttk.Button(
            nav_frame,
            text="<",
            command=self.previous_page,
            width=4
        )
        self.prev_btn.pack(side=tk.LEFT, padx=2)
        
        self.next_btn = ttk.Button(
            nav_frame,
            text=">",
            command=self.next_page,
            width=4
        )
        self.next_btn.pack(side=tk.LEFT, padx=2)
        
        self.last_btn = ttk.Button(
            nav_frame,
            text=">>",
            command=self.last_page,
            width=4
        )
        self.last_btn.pack(side=tk.LEFT, padx=2)
        
        # Actualizar estado inicial
        self._update_pagination_info()
    
    def _setup_layout(self) -> None:
        """Configurar layout del DataGrid"""
        self.grid_rowconfigure(1 if self.show_search else 0, weight=1)
        self.grid_columnconfigure(0, weight=1)
    
    def _bind_events(self) -> None:
        """Vincular eventos del DataGrid"""
        # Selección de fila
        self.tree.bind('<<TreeviewSelect>>', self._on_row_select)
        
        # Doble click
        self.tree.bind('<Double-1>', self._on_row_double_click)
        
        # Ordenamiento por columna
        for col_id, _, _ in self.columns:
            self.tree.heading(col_id, command=lambda c=col_id: self._sort_by_column(c))
    
    # ========== MÉTODOS PÚBLICOS - GESTIÓN DE DATOS ==========
    
    def set_data(self, data: List[List[Any]]) -> None:
        """
        Establecer datos completos del grid
        
        Args:
            data: Lista de listas con datos de filas
        """
        try:
            self.all_data = data.copy()
            self.filtered_data = data.copy()
            self.current_page = 0
            self._calculate_pages()
            self._update_display()
            
            self.logger.debug(f"Datos establecidos: {len(data)} filas")
            
        except Exception as e:
            self.logger.error(f"Error estableciendo datos: {e}")
    
    def add_row(self, row_data: List[Any]) -> None:
        """
        Agregar una fila al grid
        
        Args:
            row_data: Datos de la fila a agregar
        """
        try:
            self.all_data.append(row_data)
            self._apply_current_filter()
            
        except Exception as e:
            self.logger.error(f"Error agregando fila: {e}")
    
    def remove_row(self, row_index: int) -> bool:
        """
        Remover una fila del grid
        
        Args:
            row_index: Índice de la fila a remover
            
        Returns:
            bool: True si se removió exitosamente
        """
        try:
            if 0 <= row_index < len(self.all_data):
                del self.all_data[row_index]
                self._apply_current_filter()
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error removiendo fila: {e}")
            return False
    
    def clear_data(self) -> None:
        """Limpiar todos los datos del grid"""
        try:
            self.all_data.clear()
            self.filtered_data.clear()
            self.current_page = 0
            self._calculate_pages()
            self._update_display()
            
        except Exception as e:
            self.logger.error(f"Error limpiando datos: {e}")
    
    def get_selected_rows(self) -> List[List[Any]]:
        """
        Obtener filas seleccionadas
        
        Returns:
            List[List[Any]]: Datos de filas seleccionadas
        """
        try:
            selected_items = self.tree.selection()
            selected_rows = []
            
            for item in selected_items:
                values = self.tree.item(item, 'values')
                selected_rows.append(list(values))
            
            return selected_rows
            
        except Exception as e:
            self.logger.error(f"Error obteniendo filas seleccionadas: {e}")
            return []
    
    def get_all_data(self) -> List[List[Any]]:
        """
        Obtener todos los datos (sin filtrar)
        
        Returns:
            List[List[Any]]: Todos los datos
        """
        return self.all_data.copy()
    
    def get_filtered_data(self) -> List[List[Any]]:
        """
        Obtener datos filtrados actuales
        
        Returns:
            List[List[Any]]: Datos filtrados
        """
        return self.filtered_data.copy()
    
    # ========== MÉTODOS PÚBLICOS - PAGINACIÓN ==========
    
    def next_page(self) -> None:
        """Ir a la siguiente página"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._update_display()
    
    def previous_page(self) -> None:
        """Ir a la página anterior"""
        if self.current_page > 0:
            self.current_page -= 1
            self._update_display()
    
    def go_to_page(self, page: int) -> None:
        """
        Ir a página específica
        
        Args:
            page: Número de página (base 0)
        """
        if 0 <= page < self.total_pages:
            self.current_page = page
            self._update_display()
    
    def last_page(self) -> None:
        """Ir a la última página"""
        if self.total_pages > 0:
            self.current_page = self.total_pages - 1
            self._update_display()
    
    # ========== MÉTODOS PÚBLICOS - CALLBACKS ==========
    
    def set_row_select_callback(self, callback: Callable) -> None:
        """
        Establecer callback para selección de fila
        
        Args:
            callback: Función a llamar cuando se selecciona una fila
        """
        self.row_select_callback = callback
    
    def set_row_double_click_callback(self, callback: Callable) -> None:
        """
        Establecer callback para doble click en fila
        
        Args:
            callback: Función a llamar con doble click
        """
        self.row_double_click_callback = callback
    
    # ========== MÉTODOS PRIVADOS ==========
    
    def _apply_current_filter(self) -> None:
        """Aplicar filtro actual y actualizar display"""
        search_term = self.search_var.get().lower()
        
        if not search_term:
            self.filtered_data = self.all_data.copy()
        else:
            self.filtered_data = []
            for row in self.all_data:
                # Buscar en todas las columnas
                if any(search_term in str(cell).lower() for cell in row):
                    self.filtered_data.append(row)
        
        self.current_page = 0
        self._calculate_pages()
        self._update_display()
    
    def _calculate_pages(self) -> None:
        """Calcular número total de páginas"""
        if self.show_pagination and self.page_size > 0:
            self.total_pages = max(1, (len(self.filtered_data) + self.page_size - 1) // self.page_size)
        else:
            self.total_pages = 1
    
    def _update_display(self) -> None:
        """Actualizar display del Treeview"""
        try:
            # Limpiar items existentes
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Calcular rango de datos para página actual
            if self.show_pagination:
                start_idx = self.current_page * self.page_size
                end_idx = min(start_idx + self.page_size, len(self.filtered_data))
                page_data = self.filtered_data[start_idx:end_idx]
            else:
                page_data = self.filtered_data
            
            # Insertar datos
            for row_data in page_data:
                self.tree.insert('', 'end', values=row_data)
            
            # Actualizar info de paginación
            if self.show_pagination:
                self._update_pagination_info()
                self._update_pagination_buttons()
            
        except Exception as e:
            self.logger.error(f"Error actualizando display: {e}")
    
    def _update_pagination_info(self) -> None:
        """Actualizar información de paginación"""
        if hasattr(self, 'page_info_var'):
            if self.total_pages > 0:
                info_text = f"Página {self.current_page + 1} de {self.total_pages} ({len(self.filtered_data)} registros)"
            else:
                info_text = "Sin datos"
            self.page_info_var.set(info_text)
    
    def _update_pagination_buttons(self) -> None:
        """Actualizar estado de botones de paginación"""
        if hasattr(self, 'first_btn'):
            # Botones de retroceso
            can_go_back = self.current_page > 0
            self.first_btn.configure(state='normal' if can_go_back else 'disabled')
            self.prev_btn.configure(state='normal' if can_go_back else 'disabled')
            
            # Botones de avance
            can_go_forward = self.current_page < self.total_pages - 1
            self.next_btn.configure(state='normal' if can_go_forward else 'disabled')
            self.last_btn.configure(state='normal' if can_go_forward else 'disabled')
    
    def _clear_search(self) -> None:
        """Limpiar búsqueda"""
        self.search_var.set('')
    
    def _sort_by_column(self, col_id: str) -> None:
        """
        Ordenar por columna específica
        
        Args:
            col_id: ID de la columna
        """
        try:
            # Encontrar índice de columna
            col_index = next(i for i, (id_, _, _) in enumerate(self.columns) if id_ == col_id)
            
            # Ordenar datos filtrados
            reverse = getattr(self, f'_sort_{col_id}_reverse', False)
            self.filtered_data.sort(key=lambda row: str(row[col_index]), reverse=reverse)
            
            # Alternar dirección para próximo sort
            setattr(self, f'_sort_{col_id}_reverse', not reverse)
            
            self._update_display()
            
        except Exception as e:
            self.logger.error(f"Error ordenando por columna {col_id}: {e}")
    
    # ========== EVENT HANDLERS ==========
    
    def _on_search_changed(self, *args) -> None:
        """Handler para cambio en búsqueda"""
        self._apply_current_filter()
    
    def _on_row_select(self, event) -> None:
        """Handler para selección de fila"""
        try:
            if self.row_select_callback:
                selected_rows = self.get_selected_rows()
                self.row_select_callback(selected_rows)
        except Exception as e:
            self.logger.error(f"Error en callback selección: {e}")
    
    def _on_row_double_click(self, event) -> None:
        """Handler para doble click en fila"""
        try:
            if self.row_double_click_callback:
                selected_rows = self.get_selected_rows()
                if selected_rows:
                    self.row_double_click_callback(selected_rows[0])
        except Exception as e:
            self.logger.error(f"Error en callback doble click: {e}")


# Factory function para DataGrid simple
def create_simple_data_grid(parent: tk.Widget, columns: List[Tuple[str, str, int]],
                           data: List[List[Any]] = None) -> DataGrid:
    """
    Factory function para crear DataGrid simple
    
    Args:
        parent: Widget padre
        columns: Definición de columnas
        data: Datos iniciales (opcional)
        
    Returns:
        DataGrid: Instancia configurada
    """
    grid = DataGrid(parent, columns)
    
    if data:
        grid.set_data(data)
    
    return grid


if __name__ == "__main__":
    # Test básico de DataGrid
    root = tk.Tk()
    root.title("Test DataGrid")
    root.geometry("800x600")
    
    try:
        # Definir columnas
        columns = [
            ('id', 'ID', 50),
            ('name', 'Nombre', 200),
            ('category', 'Categoría', 150),
            ('stock', 'Stock', 100),
            ('price', 'Precio', 100)
        ]
        
        # Crear DataGrid
        data_grid = DataGrid(root, columns, show_search=True, show_pagination=True)
        data_grid.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Datos de prueba
        test_data = [
            [1, "Producto A", "Categoría 1", 100, "$10.00"],
            [2, "Producto B", "Categoría 2", 50, "$20.00"],
            [3, "Producto C", "Categoría 1", 75, "$15.00"],
            [4, "Producto D", "Categoría 3", 25, "$30.00"],
            [5, "Producto E", "Categoría 2", 0, "$5.00"]
        ]
        
        data_grid.set_data(test_data)
        
        # Callback de ejemplo
        def on_row_select(rows):
            print(f"Filas seleccionadas: {rows}")
        
        data_grid.set_row_select_callback(on_row_select)
        
        root.mainloop()
        
    except Exception as e:
        print(f"Error en test DataGrid: {e}")
    finally:
        root.destroy()
