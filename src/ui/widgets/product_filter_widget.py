"""
ProductFilterWidget - Sistema de Filtros UI Productos Activos/Inactivos
======================================================================

FUNCIONALIDAD IMPLEMENTADA:
- Widget de filtros con 3 opciones: Todos/Activos/Inactivos  
- Lista de productos que actualiza según filtro seleccionado
- Botón "Reactivar" para productos inactivos
- Integración con ProductService backend (métodos ya implementados)
- Manejo robusto de errores
- Refresh automático después de reactivación

INTEGRACIÓN BACKEND:
- ProductService.get_products_by_status('all'|'active'|'inactive')
- ProductService.reactivate_product(id_producto)

Fecha: 2025-07-30
Protocolo: claude_instructions_v3.md FASE 2 - Desarrollo Atómico
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List, Any
import logging
from decimal import Decimal


class ProductFilterWidget(tk.Frame):
    """
    Widget para filtrar productos por estado (activo/inactivo) con funcionalidad de reactivación.
    
    CARACTERÍSTICAS:
    - Filtros: Todos/Activos/Inactivos
    - Lista de productos con información completa  
    - Botón reactivar para productos inactivos
    - Integración ProductService backend
    - Manejo robusto de errores
    - UI responsiva y user-friendly
    """
    
    def __init__(self, parent, product_service):
        """
        Inicializar widget de filtros de productos.
        
        Args:
            parent: Widget padre
            product_service: Instancia de ProductService con métodos implementados
        """
        super().__init__(parent)
        
        self.product_service = product_service
        self.logger = logging.getLogger('product_filter_widget')
        
        # Estado interno
        self._selected_product_id = None
        self._current_filter = 'Activos'  # Default
        
        # Crear interfaz
        self._create_interface()
        
        # Cargar datos iniciales
        self._load_initial_data()
        
        self.logger.info("ProductFilterWidget inicializado exitosamente")
    
    def _create_interface(self):
        """Crear elementos de la interfaz de usuario."""
        # Frame principal
        self.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # === SECCIÓN FILTROS ===
        filter_frame = tk.Frame(self)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Label filtros
        filter_label = tk.Label(filter_frame, text="Filtrar productos:", font=('Arial', 10, 'bold'))
        filter_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Combobox filtros
        self.filter_combo = ttk.Combobox(
            filter_frame,
            values=['Todos', 'Activos', 'Inactivos'],
            state='readonly',
            width=15
        )
        self.filter_combo.set('Activos')  # Default
        self.filter_combo.pack(side=tk.LEFT, padx=(0, 20))
        self.filter_combo.bind('<<ComboboxSelected>>', self._on_filter_changed)
        
        # Botón reactivar
        self.reactivate_button = tk.Button(
            filter_frame,
            text="Reactivar Producto",
            state='disabled',
            bg='#28a745',
            fg='white',
            font=('Arial', 9, 'bold'),
            command=self._on_reactivate_clicked
        )
        self.reactivate_button.pack(side=tk.RIGHT)
        
        # === SECCIÓN LISTA PRODUCTOS ===
        list_frame = tk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview para lista de productos
        columns = ('ID', 'Nombre', 'Estado', 'Stock', 'Precio', 'Categoría')
        self.products_list = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # Configurar columnas
        self.products_list.heading('ID', text='ID')
        self.products_list.heading('Nombre', text='Nombre')
        self.products_list.heading('Estado', text='Estado')
        self.products_list.heading('Stock', text='Stock')
        self.products_list.heading('Precio', text='Precio')
        self.products_list.heading('Categoría', text='Categoría')
        
        # Ancho columnas
        self.products_list.column('ID', width=60, anchor='center')
        self.products_list.column('Nombre', width=200, anchor='w')
        self.products_list.column('Estado', width=80, anchor='center')
        self.products_list.column('Stock', width=80, anchor='center')
        self.products_list.column('Precio', width=100, anchor='e')
        self.products_list.column('Categoría', width=150, anchor='w')
        
        # Scrollbar para lista
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.products_list.yview)
        self.products_list.configure(yscrollcommand=scrollbar.set)
        
        # Pack lista y scrollbar
        self.products_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selección de producto
        self.products_list.bind('<<TreeviewSelect>>', self._on_product_selected)
        
        # === SECCIÓN INFORMACIÓN ===
        info_frame = tk.Frame(self)
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.info_label = tk.Label(
            info_frame, 
            text="Seleccione un filtro para ver productos",
            font=('Arial', 9),
            fg='#666666'
        )
        self.info_label.pack(side=tk.LEFT)
        
        # Contador productos
        self.count_label = tk.Label(
            info_frame,
            text="",
            font=('Arial', 9, 'bold'),
            fg='#007bff'
        )
        self.count_label.pack(side=tk.RIGHT)
    
    def _load_initial_data(self):
        """Cargar datos iniciales (productos activos por defecto)."""
        self._on_filter_changed()
    
    def _on_filter_changed(self, event=None):
        """
        Manejar cambio de filtro.
        
        Llama ProductService.get_products_by_status() con el parámetro correcto.
        """
        try:
            selected_filter = self.filter_combo.get()
            self._current_filter = selected_filter
            
            # Mapear filtro UI a parámetro backend
            filter_mapping = {
                'Todos': 'all',
                'Activos': 'active', 
                'Inactivos': 'inactive'
            }
            
            backend_filter = filter_mapping.get(selected_filter, 'active')
            
            # Llamar ProductService con filtro correcto
            products = self.product_service.get_products_by_status(backend_filter)
            
            # Actualizar lista
            self._update_products_list(products)
            
            # Actualizar estado UI
            self._update_ui_state(selected_filter, len(products))
            
            self.logger.debug(f"Filtro '{selected_filter}': {len(products)} productos cargados")
            
        except Exception as e:
            self.logger.error(f"Error al cambiar filtro: {e}")
            self._handle_error(f"Error al cargar productos: {str(e)}")
    
    def _update_products_list(self, products: List[Any]):
        """
        Actualizar lista de productos en el Treeview.
        
        Args:
            products: Lista de productos del ProductService
        """
        # Limpiar lista actual
        for item in self.products_list.get_children():
            self.products_list.delete(item)
        
        # Agregar productos
        for product in products:
            try:
                # Extraer información del producto
                id_producto = getattr(product, 'id_producto', 'N/A')
                nombre = getattr(product, 'nombre', 'Sin nombre')
                activo = getattr(product, 'activo', True)
                stock = getattr(product, 'stock', 0)
                precio = getattr(product, 'precio', Decimal('0'))
                categoria_tipo = getattr(product, 'categoria_tipo', 'N/A')
                
                # Formatear información
                estado = "Activo" if activo else "Inactivo"
                precio_str = f"${float(precio):.2f}" if precio else "$0.00"
                stock_str = str(stock) if stock is not None else "0"
                categoria_str = categoria_tipo if categoria_tipo else "Sin categoría"
                
                # Insertar en lista
                item_id = self.products_list.insert(
                    '',
                    tk.END,
                    values=(id_producto, nombre, estado, stock_str, precio_str, categoria_str),
                    tags=(estado.lower(),)
                )
                
                # Guardar ID del producto en el item para referencia
                self.products_list.set(item_id, 'ID', id_producto)
                
            except Exception as e:
                self.logger.warning(f"Error al procesar producto: {e}")
                continue
        
        # Configurar colores por estado
        self.products_list.tag_configure('activo', background='#e8f5e8')
        self.products_list.tag_configure('inactivo', background='#f8e8e8')
    
    def _update_ui_state(self, selected_filter: str, product_count: int):
        """
        Actualizar estado de la UI según filtro seleccionado.
        
        Args:
            selected_filter: Filtro actualmente seleccionado
            product_count: Número de productos mostrados
        """
        # Actualizar información
        filter_info = {
            'Todos': f"Mostrando todos los productos",
            'Activos': f"Mostrando productos activos",
            'Inactivos': f"Mostrando productos inactivos"
        }
        
        self.info_label.config(text=filter_info.get(selected_filter, ""))
        self.count_label.config(text=f"Total: {product_count}")
        
        # Actualizar estado botón reactivar
        if selected_filter == 'Inactivos':
            # Habilitar solo si hay selección
            if self._selected_product_id:
                self.reactivate_button.config(state='normal')
            else:
                self.reactivate_button.config(state='disabled')
        else:
            # Deshabilitar para productos activos o vista todos
            self.reactivate_button.config(state='disabled')
    
    def _on_product_selected(self, event):
        """
        Manejar selección de producto en la lista.
        
        Actualiza estado interno y UI según producto seleccionado.
        """
        selection = self.products_list.selection()
        
        if selection:
            # Obtener ID del producto seleccionado
            item = selection[0]
            values = self.products_list.item(item)['values']
            
            if values:
                try:
                    self._selected_product_id = int(values[0])  # ID está en primera columna
                    
                    # Actualizar estado botón reactivar
                    if self._current_filter == 'Inactivos':
                        self.reactivate_button.config(state='normal')
                    
                    self.logger.debug(f"Producto seleccionado: {self._selected_product_id}")
                    
                except (ValueError, IndexError) as e:
                    self.logger.warning(f"Error al obtener ID de producto seleccionado: {e}")
                    self._selected_product_id = None
        else:
            # Sin selección
            self._selected_product_id = None
            self.reactivate_button.config(state='disabled')
    
    def _on_reactivate_clicked(self):
        """
        Manejar clic en botón reactivar.
        
        Llama ProductService.reactivate_product() y actualiza la lista.
        """
        if not self._selected_product_id:
            messagebox.showwarning(
                "Selección requerida",
                "Debe seleccionar un producto inactivo para reactivar."
            )
            return
        
        try:
            # Confirmar reactivación
            response = messagebox.askyesno(
                "Confirmar reactivación",
                f"¿Está seguro de que desea reactivar el producto ID {self._selected_product_id}?\n\n"
                "El producto volverá a estar disponible en el sistema."
            )
            
            if not response:
                return
            
            # Llamar ProductService.reactivate_product()
            success = self.product_service.reactivate_product(self._selected_product_id)
            
            if success:
                messagebox.showinfo(
                    "Reactivación exitosa",
                    f"El producto ID {self._selected_product_id} ha sido reactivado exitosamente."
                )
                
                # Actualizar lista después de reactivación
                self._on_filter_changed()
                
                # Reset selección
                self._selected_product_id = None
                self.reactivate_button.config(state='disabled')
                
                self.logger.info(f"Producto {self._selected_product_id} reactivado exitosamente")
                
            else:
                messagebox.showerror(
                    "Error en reactivación",
                    f"No se pudo reactivar el producto ID {self._selected_product_id}.\n"
                    "Verifique que el producto exista y esté inactivo."
                )
                
        except ValueError as e:
            # Error de validación de negocio
            messagebox.showerror(
                "Error de validación",
                f"No se puede reactivar el producto:\n\n{str(e)}"
            )
            
        except Exception as e:
            self.logger.error(f"Error al reactivar producto {self._selected_product_id}: {e}")
            messagebox.showerror(
                "Error del sistema",
                f"Error inesperado al reactivar producto:\n\n{str(e)}"
            )
    
    def _handle_error(self, error_message: str):
        """
        Manejar errores de manera consistente.
        
        Args:
            error_message: Mensaje de error para mostrar al usuario
        """
        # Limpiar lista
        for item in self.products_list.get_children():
            self.products_list.delete(item)
        
        # Mostrar mensaje de error en UI
        self.info_label.config(text=error_message, fg='red')
        self.count_label.config(text="Error")
        
        # Deshabilitar botón reactivar
        self.reactivate_button.config(state='disabled')
    
    def refresh(self):
        """
        Refrescar datos del widget manualmente.
        
        Útil para actualizar después de cambios externos.
        """
        self.logger.debug("Refrescando ProductFilterWidget...")
        self._on_filter_changed()
    
    def get_selected_product_id(self) -> Optional[int]:
        """
        Obtener ID del producto actualmente seleccionado.
        
        Returns:
            ID del producto seleccionado o None si no hay selección
        """
        return self._selected_product_id
    
    def set_filter(self, filter_name: str):
        """
        Establecer filtro programáticamente.
        
        Args:
            filter_name: Nombre del filtro ('Todos', 'Activos', 'Inactivos')
        """
        if filter_name in ['Todos', 'Activos', 'Inactivos']:
            self.filter_combo.set(filter_name)
            self._on_filter_changed()
        else:
            self.logger.warning(f"Filtro inválido: {filter_name}")


# === FACTORY FUNCTION PARA INTEGRACIÓN ===

def create_product_filter_widget(parent, product_service=None):
    """
    Factory function para crear ProductFilterWidget con ServiceContainer.
    
    Args:
        parent: Widget padre
        product_service: ProductService opcional (usa ServiceContainer si no se proporciona)
        
    Returns:
        Instancia configurada de ProductFilterWidget
    """
    if product_service is None:
        # Obtener ProductService del ServiceContainer
        try:
            from src.services.service_container import get_container
            container = get_container()
            product_service = container.get('product_service')
        except ImportError:
            raise ImportError(
                "No se pudo obtener ProductService del ServiceContainer. "
                "Asegúrese de que el sistema esté inicializado correctamente."
            )
    
    return ProductFilterWidget(parent, product_service)


# === EJEMPLO DE USO ===

if __name__ == '__main__':
    """
    Ejemplo de uso del ProductFilterWidget.
    Para testing y desarrollo.
    """
    import sys
    sys.path.append('../../../../')
    
    from src.services.service_container import get_container
    
    # Configurar logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Crear ventana principal
    root = tk.Tk()
    root.title("Sistema de Filtros Productos - Demo")
    root.geometry("800x600")
    
    try:
        # Obtener ProductService del container
        container = get_container()
        product_service = container.get('product_service')
        
        # Crear widget
        filter_widget = ProductFilterWidget(root, product_service)
        
        # Ejecutar aplicación
        root.mainloop()
        
    except Exception as e:
        print(f"Error al ejecutar demo: {e}")
        
        # Demo con mock para testing
        from unittest.mock import Mock
        
        mock_service = Mock()
        mock_service.get_products_by_status.return_value = [
            Mock(id_producto=1, nombre="Producto Demo 1", activo=True, stock=10, precio=100.0, categoria_tipo="MATERIAL"),
            Mock(id_producto=2, nombre="Producto Demo 2", activo=False, stock=0, precio=50.0, categoria_tipo="SERVICIO")
        ]
        mock_service.reactivate_product.return_value = True
        
        filter_widget = ProductFilterWidget(root, mock_service)
        root.mainloop()
