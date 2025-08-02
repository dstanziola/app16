"""
ReportsForm - Interfaz para generación de reportes

Formulario principal para configurar y generar los 4 tipos de reportes:
1. Reporte de Inventario Actual
2. Reporte de Movimientos por período
3. Reporte de Ventas con filtros  
4. Reporte de Rentabilidad

Integra con ReportService para la lógica de negocio y exportación a PDF.

Autor: Sistema de Inventario Copy Point S.A.
Fecha: Junio 2025 - FASE 2
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional
import threading
import os
import logging

# ReportService se obtiene desde ServiceContainer
from services.category_service import CategoryService
from services.client_service import ClientService
from ui.utils.window_manager import WindowManager


class ReportsForm:
    """Formulario para generación de reportes del sistema"""
    
    def __init__(self, parent=None, db_path: str = None):
        """
        Inicializa el formulario de reportes
        
        Args:
            parent: Ventana padre
            db_path: Ruta a la base de datos (deprecado - se usa ServiceContainer)
        """
        self.parent = parent
        self.db_path = db_path  # Mantenido para compatibilidad, no se usa
        self.window = None
        self.logger = logging.getLogger(__name__)
        
        # CORRECCIÓN: Usar ServiceContainer en lugar de inicializar servicios directamente
        from services.service_container import get_container
        self.container = get_container()
        
        # ✅ CORRECTO: Obtener servicios del container (ya configurados con DatabaseConnection)
        self.report_service = self.container.get('report_service')
        self.category_service = self.container.get('category_service')
        self.client_service = self.container.get('client_service')
        
        # Variables de control
        self.report_type_var = tk.StringVar(value="inventory")
        self.date_inicio_var = tk.StringVar()
        self.date_fin_var = tk.StringVar()
        self.categoria_var = tk.StringVar()
        self.cliente_var = tk.StringVar()
        self.group_by_var = tk.StringVar(value="none")
        self.solo_con_stock_var = tk.BooleanVar()
        self.include_details_var = tk.BooleanVar(value=True)
        
        # Datos para combos
        self.categorias_data = []
        self.clientes_data = []
        
        # Widget references
        self.widgets = {}
        
        self._setup_dates()
        self._load_combo_data()
    
    def _setup_dates(self):
        """Configura fechas por defecto"""
        today = date.today()
        first_day_month = today.replace(day=1)
        
        self.date_inicio_var.set(first_day_month.strftime("%Y-%m-%d"))
        self.date_fin_var.set(today.strftime("%Y-%m-%d"))
    
    def _load_combo_data(self):
        """Carga datos para los combos de categorías y clientes"""
        try:
            # Cargar categorías
            categorias = self.category_service.get_all_categories()
            self.categorias_data = [{"id": 0, "nombre": "Todas las categorías"}]
            self.categorias_data.extend([
                {"id": cat.id_categoria, "nombre": cat.nombre} 
                for cat in categorias
            ])
            
            # Cargar clientes
            clientes = self.client_service.get_all_clients()
            self.clientes_data = [{"id": 0, "nombre": "Todos los clientes"}]
            self.clientes_data.extend([
                {"id": client.id_cliente, "nombre": client.nombre}
                for client in clientes
            ])
            
        except Exception as e:
            self.logger.error(f"Error cargando datos para combos: {e}")
            messagebox.showerror("Error", f"Error cargando datos: {e}")
    
    def show(self):
        """Muestra el formulario de reportes"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
            
        self.window = tk.Toplevel(self.parent)
        self.window.title("Reportes del Sistema")
        self.window.geometry("750x650")
        self.window.resizable(True, True)
        
        # Centrar ventana
        # WindowManager.center_window(self.window, 800, 600)
        
        self._create_widgets()
        self._setup_layout()
        self._bind_events()
        
        # Configurar cierre
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Focus inicial
        self.window.focus_set()
    
    def _create_widgets(self):
        """Crea los widgets del formulario"""
        
        # Frame principal con scroll
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Título
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill="x", pady=(0, 10))
        
        title_label = ttk.Label(
            title_frame, 
            text="Sistema de Reportes", 
            font=("Arial", 16, "bold")
        )
        title_label.pack()
        
        # Frame para contenido con scroll
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Empaqutar canvas y scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Contenido principal
        self._create_report_type_section(scrollable_frame)
        self._create_filters_section(scrollable_frame)
        self._create_options_section(scrollable_frame)
        self._create_buttons_section(scrollable_frame)
        self._create_progress_section(scrollable_frame)
        
        # Guardar referencias
        self.widgets['canvas'] = canvas
        self.widgets['scrollable_frame'] = scrollable_frame
    
    def _create_report_type_section(self, parent):
        """Crea sección de selección de tipo de reporte"""
        section_frame = ttk.LabelFrame(parent, text="Tipo de Reporte", padding="10")
        section_frame.pack(fill="x", pady=(0, 10))
        
        # Opciones de tipo de reporte
        report_types = [
            ("inventory", "📦 Reporte de Inventario Actual"),
            ("movements", "📋 Reporte de Movimientos"),
            ("sales", "💰 Reporte de Ventas"),
            ("profitability", "📊 Reporte de Rentabilidad")
        ]
        
        for i, (value, text) in enumerate(report_types):
            rb = ttk.Radiobutton(
                section_frame,
                text=text,
                variable=self.report_type_var,
                value=value,
                command=self._on_report_type_changed
            )
            rb.grid(row=i//2, column=i%2, sticky="w", padx=10, pady=5)
        
        self.widgets['report_type_frame'] = section_frame
    
    def _create_filters_section(self, parent):
        """Crea sección de filtros"""
        filters_frame = ttk.LabelFrame(parent, text="Filtros", padding="10")
        filters_frame.pack(fill="x", pady=(0, 10))
        
        # Fechas
        dates_frame = ttk.Frame(filters_frame)
        dates_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(dates_frame, text="Fecha Inicio:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        date_inicio_entry = ttk.Entry(dates_frame, textvariable=self.date_inicio_var, width=12)
        date_inicio_entry.grid(row=0, column=1, padx=(0, 20))
        
        ttk.Label(dates_frame, text="Fecha Fin:").grid(row=0, column=2, sticky="w", padx=(0, 5))
        date_fin_entry = ttk.Entry(dates_frame, textvariable=self.date_fin_var, width=12)
        date_fin_entry.grid(row=0, column=3)
        
        # Categoría
        category_frame = ttk.Frame(filters_frame)
        category_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(category_frame, text="Categoría:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        categoria_combo = ttk.Combobox(
            category_frame, 
            textvariable=self.categoria_var,
            width=30,
            state="readonly"
        )
        categoria_combo.grid(row=0, column=1, sticky="w")
        
        # Configurar valores del combo de categorías
        categoria_values = [cat["nombre"] for cat in self.categorias_data]
        categoria_combo['values'] = categoria_values
        categoria_combo.set(categoria_values[0] if categoria_values else "")
        
        # Cliente
        cliente_frame = ttk.Frame(filters_frame)
        cliente_frame.pack(fill="x")
        
        ttk.Label(cliente_frame, text="Cliente:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        cliente_combo = ttk.Combobox(
            cliente_frame,
            textvariable=self.cliente_var,
            width=30,
            state="readonly"
        )
        cliente_combo.grid(row=0, column=1, sticky="w")
        
        # Configurar valores del combo de clientes
        cliente_values = [client["nombre"] for client in self.clientes_data]
        cliente_combo['values'] = cliente_values
        cliente_combo.set(cliente_values[0] if cliente_values else "")
        
        # Guardar referencias
        self.widgets['categoria_combo'] = categoria_combo
        self.widgets['cliente_combo'] = cliente_combo
        self.widgets['filters_frame'] = filters_frame
    
    def _create_options_section(self, parent):
        """Crea sección de opciones específicas"""
        options_frame = ttk.LabelFrame(parent, text="Opciones", padding="10")
        options_frame.pack(fill="x", pady=(0, 10))
        
        # Opciones para inventario
        inventory_frame = ttk.Frame(options_frame)
        solo_stock_cb = ttk.Checkbutton(
            inventory_frame,
            text="Solo productos con stock",
            variable=self.solo_con_stock_var
        )
        solo_stock_cb.pack(anchor="w")
        
        # Opciones para ventas
        sales_frame = ttk.Frame(options_frame)
        
        ttk.Label(sales_frame, text="Agrupar por:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        group_combo = ttk.Combobox(
            sales_frame,
            textvariable=self.group_by_var,
            values=["none", "day", "month", "year"],
            state="readonly",
            width=15
        )
        group_combo.grid(row=0, column=1, sticky="w")
        group_combo.set("none")
        
        details_cb = ttk.Checkbutton(
            sales_frame,
            text="Incluir detalles",
            variable=self.include_details_var
        )
        details_cb.grid(row=1, column=0, columnspan=2, sticky="w", pady=(5, 0))
        
        # Guardar referencias
        self.widgets['inventory_options'] = inventory_frame
        self.widgets['sales_options'] = sales_frame
        self.widgets['options_frame'] = options_frame
        
        # Mostrar opciones según tipo de reporte
        self._update_options_visibility()
    
    def _create_buttons_section(self, parent):
        """Crea sección de botones"""
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill="x", pady=(10, 0))
        
        # Frame para centrar botones
        center_frame = ttk.Frame(buttons_frame)
        center_frame.pack(anchor="center")
        
        # Botón generar reporte
        generate_btn = ttk.Button(
            center_frame,
            text="🔍 Generar Reporte",
            command=self._generate_report,
            width=20
        )
        generate_btn.pack(side="left", padx=(0, 10))
        
        # Botón exportar PDF
        export_btn = ttk.Button(
            center_frame,
            text="📄 Exportar a PDF",
            command=self._export_to_pdf,
            state="disabled",
            width=20
        )
        export_btn.pack(side="left", padx=(0, 10))
        
        # Botón cerrar
        close_btn = ttk.Button(
            center_frame,
            text="❌ Cerrar",
            command=self._on_close,
            width=15
        )
        close_btn.pack(side="left")
        
        # Guardar referencias
        self.widgets['generate_btn'] = generate_btn
        self.widgets['export_btn'] = export_btn
        self.widgets['close_btn'] = close_btn
    
    def _create_progress_section(self, parent):
        """Crea sección de progreso y resultados"""
        progress_frame = ttk.LabelFrame(parent, text="Estado", padding="10")
        progress_frame.pack(fill="x", pady=(10, 0))
        
        # Barra de progreso
        progress_bar = ttk.Progressbar(
            progress_frame,
            mode='indeterminate'
        )
        progress_bar.pack(fill="x", pady=(0, 10))
        
        # Etiqueta de estado
        status_label = ttk.Label(
            progress_frame,
            text="Listo para generar reporte",
            foreground="blue"
        )
        status_label.pack(anchor="w")
        
        # Frame para estadísticas
        stats_frame = ttk.Frame(progress_frame)
        stats_frame.pack(fill="x", pady=(10, 0))
        
        stats_text = tk.Text(
            stats_frame,
            height=6,
            wrap="word",
            state="disabled"
        )
        stats_scrollbar = ttk.Scrollbar(stats_frame, orient="vertical", command=stats_text.yview)
        stats_text.configure(yscrollcommand=stats_scrollbar.set)
        
        stats_text.pack(side="left", fill="both", expand=True)
        stats_scrollbar.pack(side="right", fill="y")
        
        # Guardar referencias
        self.widgets['progress_bar'] = progress_bar
        self.widgets['status_label'] = status_label
        self.widgets['stats_text'] = stats_text
        
        # Variable para datos del último reporte
        self.last_report_data = None
    
    def _setup_layout(self):
        """Configura el layout final"""
        # Configurar grid weights para responsive design
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
    
    def _bind_events(self):
        """Vincula eventos"""
        # Bind del mouse wheel al canvas
        def _on_mousewheel(event):
            if 'canvas' in self.widgets:
                self.widgets['canvas'].yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.window.bind("<MouseWheel>", _on_mousewheel)
        
        # Teclas de acceso rápido
        self.window.bind("<Control-g>", lambda e: self._generate_report())
        self.window.bind("<Control-e>", lambda e: self._export_to_pdf())
        self.window.bind("<Escape>", lambda e: self._on_close())
    
    def _on_report_type_changed(self):
        """Callback cuando cambia el tipo de reporte"""
        self._update_options_visibility()
        self._update_status("Tipo de reporte cambiado. Configure filtros y genere el reporte.")
    
    def _update_options_visibility(self):
        """Actualiza visibilidad de opciones según tipo de reporte"""
        report_type = self.report_type_var.get()
        
        # Ocultar todos los frames de opciones
        if 'inventory_options' in self.widgets:
            self.widgets['inventory_options'].pack_forget()
        if 'sales_options' in self.widgets:
            self.widgets['sales_options'].pack_forget()
            
        # Mostrar opciones específicas
        if report_type == "inventory":
            self.widgets['inventory_options'].pack(fill="x", pady=(0, 5))
        elif report_type == "sales":
            self.widgets['sales_options'].pack(fill="x", pady=(0, 5))
    
    def _validate_dates(self) -> bool:
        """Valida las fechas ingresadas"""
        try:
            fecha_inicio_str = self.date_inicio_var.get()
            fecha_fin_str = self.date_fin_var.get()
            
            fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
            fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
            
            if fecha_fin < fecha_inicio:
                messagebox.showerror(
                    "Error de Fechas",
                    "La fecha de fin debe ser posterior a la fecha de inicio"
                )
                return False
                
            return True
            
        except ValueError:
            messagebox.showerror(
                "Error de Formato",
                "Las fechas deben tener el formato YYYY-MM-DD"
            )
            return False
    
    def _get_selected_categoria_id(self) -> Optional[int]:
        """Obtiene ID de categoría seleccionada"""
        categoria_nombre = self.categoria_var.get()
        for cat in self.categorias_data:
            if cat["nombre"] == categoria_nombre:
                return cat["id"] if cat["id"] > 0 else None
        return None
    
    def _get_selected_cliente_id(self) -> Optional[int]:
        """Obtiene ID de cliente seleccionado"""
        cliente_nombre = self.cliente_var.get()
        for client in self.clientes_data:
            if client["nombre"] == cliente_nombre:
                return client["id"] if client["id"] > 0 else None
        return None
    
    def _update_status(self, message: str, color: str = "blue"):
        """Actualiza el mensaje de estado"""
        if 'status_label' in self.widgets:
            self.widgets['status_label'].config(text=message, foreground=color)
            self.window.update_idletasks()
    
    def _show_progress(self, show: bool = True):
        """Muestra/oculta la barra de progreso"""
        if 'progress_bar' in self.widgets:
            if show:
                self.widgets['progress_bar'].start()
            else:
                self.widgets['progress_bar'].stop()
    
    def _display_report_stats(self, report_data: Dict[str, Any]):
        """Muestra estadísticas del reporte generado"""
        if 'stats_text' not in self.widgets:
            return
            
        stats_text = self.widgets['stats_text']
        stats_text.config(state="normal")
        stats_text.delete(1.0, tk.END)
        
        # Formatear estadísticas según tipo de reporte
        report_type = self.report_type_var.get()
        
        if report_type == "inventory":
            self._format_inventory_stats(stats_text, report_data)
        elif report_type == "movements":
            self._format_movements_stats(stats_text, report_data)
        elif report_type == "sales":
            self._format_sales_stats(stats_text, report_data)
        elif report_type == "profitability":
            self._format_profitability_stats(stats_text, report_data)
        
        stats_text.config(state="disabled")
    
    def _format_inventory_stats(self, text_widget, data):
        """Formatea estadísticas de inventario"""
        summary = data.get('summary', {})
        
        text_widget.insert(tk.END, "📦 RESUMEN DE INVENTARIO\n")
        text_widget.insert(tk.END, "=" * 30 + "\n")
        text_widget.insert(tk.END, f"Total de productos: {summary.get('total_productos', 0)}\n")
        text_widget.insert(tk.END, f"Productos con stock: {summary.get('productos_con_stock', 0)}\n")
        text_widget.insert(tk.END, f"Productos sin stock: {summary.get('productos_sin_stock', 0)}\n")
        text_widget.insert(tk.END, f"Valor total inventario: ${summary.get('valor_total_inventario', 0):,.2f}\n")
        text_widget.insert(tk.END, f"Fecha de corte: {summary.get('fecha_corte', 'N/A')}\n")
    
    def _format_movements_stats(self, text_widget, data):
        """Formatea estadísticas de movimientos"""
        summary = data.get('summary', {})
        
        text_widget.insert(tk.END, "📋 RESUMEN DE MOVIMIENTOS\n")
        text_widget.insert(tk.END, "=" * 30 + "\n")
        text_widget.insert(tk.END, f"Total movimientos: {summary.get('total_movimientos', 0)}\n")
        text_widget.insert(tk.END, f"Total entradas: {summary.get('total_entradas', 0)}\n")
        text_widget.insert(tk.END, f"Total salidas: {summary.get('total_salidas', 0)}\n")
        text_widget.insert(tk.END, f"Valor total: ${summary.get('valor_total_movimientos', 0):,.2f}\n")
        text_widget.insert(tk.END, f"Período: {summary.get('periodo', 'N/A')}\n")
    
    def _format_sales_stats(self, text_widget, data):
        """Formatea estadísticas de ventas"""
        summary = data.get('summary', {})
        totals = data.get('totals', {})
        
        text_widget.insert(tk.END, "💰 RESUMEN DE VENTAS\n")
        text_widget.insert(tk.END, "=" * 30 + "\n")
        text_widget.insert(tk.END, f"Total ventas: {summary.get('total_ventas', 0)}\n")
        text_widget.insert(tk.END, f"Promedio por venta: ${summary.get('promedio_venta', 0):,.2f}\n")
        text_widget.insert(tk.END, f"Subtotal: ${totals.get('subtotal_total', 0):,.2f}\n")
        text_widget.insert(tk.END, f"Impuestos: ${totals.get('impuestos_total', 0):,.2f}\n")
        text_widget.insert(tk.END, f"Total: ${totals.get('gran_total', 0):,.2f}\n")
        text_widget.insert(tk.END, f"Período: {summary.get('periodo', 'N/A')}\n")
    
    def _format_profitability_stats(self, text_widget, data):
        """Formatea estadísticas de rentabilidad"""
        summary = data.get('summary', {})
        totals = data.get('totals', {})
        
        text_widget.insert(tk.END, "📊 RESUMEN DE RENTABILIDAD\n")
        text_widget.insert(tk.END, "=" * 30 + "\n")
        text_widget.insert(tk.END, f"Productos analizados: {summary.get('productos_analizados', 0)}\n")
        text_widget.insert(tk.END, f"Ingresos totales: ${totals.get('total_ingresos', 0):,.2f}\n")
        text_widget.insert(tk.END, f"Costos totales: ${totals.get('total_costos', 0):,.2f}\n")
        text_widget.insert(tk.END, f"Ganancia bruta: ${totals.get('total_ganancia', 0):,.2f}\n")
        text_widget.insert(tk.END, f"Margen: {totals.get('margen_total_porcentaje', 0):.2f}%\n")
        text_widget.insert(tk.END, f"Período: {summary.get('periodo', 'N/A')}\n")
    
    def _generate_report(self):
        """Genera el reporte seleccionado"""
        # Validar fechas para reportes que las requieren
        report_type = self.report_type_var.get()
        
        if report_type in ["movements", "sales", "profitability"]:
            if not self._validate_dates():
                return
        
        # Deshabilitar botón durante generación
        if 'generate_btn' in self.widgets:
            self.widgets['generate_btn'].config(state="disabled")
        
        self._update_status("Generando reporte...", "orange")
        self._show_progress(True)
        
        # Ejecutar en hilo separado para no bloquear UI
        thread = threading.Thread(target=self._generate_report_worker)
        thread.daemon = True
        thread.start()
    
    def _generate_report_worker(self):
        """Worker para generar reporte en hilo separado"""
        try:
            report_type = self.report_type_var.get()
            
            if report_type == "inventory":
                report_data = self._generate_inventory_report()
            elif report_type == "movements":
                report_data = self._generate_movements_report()
            elif report_type == "sales":
                report_data = self._generate_sales_report()
            elif report_type == "profitability":
                report_data = self._generate_profitability_report()
            else:
                raise ValueError(f"Tipo de reporte no soportado: {report_type}")
            
            # Actualizar UI en hilo principal
            self.window.after(0, self._on_report_generated, report_data)
            
        except Exception as e:
            self.logger.error(f"Error generando reporte: {e}")
            self.window.after(0, self._on_report_error, str(e))
    
    def _generate_inventory_report(self) -> Dict[str, Any]:
        """Genera reporte de inventario"""
        categoria_id = self._get_selected_categoria_id()
        solo_con_stock = self.solo_con_stock_var.get()
        
        return self.report_service.generate_inventory_report(
            categoria_id=categoria_id,
            solo_con_stock=solo_con_stock
        )
    
    def _generate_movements_report(self) -> Dict[str, Any]:
        """Genera reporte de movimientos"""
        fecha_inicio = datetime.strptime(self.date_inicio_var.get(), "%Y-%m-%d").date()
        fecha_fin = datetime.strptime(self.date_fin_var.get(), "%Y-%m-%d").date()
        categoria_id = self._get_selected_categoria_id()
        
        return self.report_service.generate_movements_report(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            categoria_id=categoria_id
        )
    
    def _generate_sales_report(self) -> Dict[str, Any]:
        """Genera reporte de ventas"""
        fecha_inicio = datetime.strptime(self.date_inicio_var.get(), "%Y-%m-%d").date()
        fecha_fin = datetime.strptime(self.date_fin_var.get(), "%Y-%m-%d").date()
        cliente_id = self._get_selected_cliente_id()
        group_by = self.group_by_var.get() if self.group_by_var.get() != "none" else None
        include_details = self.include_details_var.get()
        
        return self.report_service.generate_sales_report(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            cliente_id=cliente_id,
            group_by=group_by,
            include_details=include_details
        )
    
    def _generate_profitability_report(self) -> Dict[str, Any]:
        """Genera reporte de rentabilidad"""
        fecha_inicio = datetime.strptime(self.date_inicio_var.get(), "%Y-%m-%d").date()
        fecha_fin = datetime.strptime(self.date_fin_var.get(), "%Y-%m-%d").date()
        categoria_id = self._get_selected_categoria_id()
        
        return self.report_service.generate_profitability_report(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            categoria_id=categoria_id
        )
    
    def _on_report_generated(self, report_data: Dict[str, Any]):
        """Callback cuando se genera exitosamente un reporte"""
        self._show_progress(False)
        self._update_status("Reporte generado exitosamente", "green")
        
        # Guardar datos del reporte
        self.last_report_data = report_data
        
        # Mostrar estadísticas
        self._display_report_stats(report_data)
        
        # Habilitar botón de exportar
        if 'export_btn' in self.widgets:
            self.widgets['export_btn'].config(state="normal")
        
        # Habilitar botón generar
        if 'generate_btn' in self.widgets:
            self.widgets['generate_btn'].config(state="normal")
    
    def _on_report_error(self, error_message: str):
        """Callback cuando hay error generando reporte"""
        self._show_progress(False)
        self._update_status(f"Error: {error_message}", "red")
        
        # Habilitar botón generar
        if 'generate_btn' in self.widgets:
            self.widgets['generate_btn'].config(state="normal")
        
        messagebox.showerror("Error", f"Error generando reporte:\n{error_message}")
    
    def _export_to_pdf(self):
        """Exporta el último reporte a PDF"""
        if not self.last_report_data:
            messagebox.showwarning("Sin Datos", "Primero debe generar un reporte")
            return
        
        # Seleccionar archivo destino
        report_type = self.report_type_var.get()
        default_filename = f"reporte_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        file_path = filedialog.asksaveasfilename(
            title="Guardar Reporte como PDF",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=default_filename  # ✅ CORRECTO: initialfile en lugar de initialvalue
        )
        
        if not file_path:
            return
        
        # Exportar en hilo separado
        self._update_status("Exportando a PDF...", "orange")
        self._show_progress(True)
        
        thread = threading.Thread(target=self._export_pdf_worker, args=(file_path,))
        thread.daemon = True
        thread.start()
    
    def _export_pdf_worker(self, file_path: str):
        """Worker para exportar PDF en hilo separado"""
        try:
            company_info = {
                'nombre': 'Copy Point S.A.',
                'ruc': '888-888-8888',
                'direccion': 'Las Lajas, Las Cumbres, Panamá',
                'telefono': '6666-6666',
                'email': 'copy.point@gmail.com'
            }
            
            report_type = self.report_type_var.get()
            
            success = self.report_service.export_to_pdf(
                self.last_report_data,
                file_path,
                report_type,
                company_info
            )
            
            if success:
                self.window.after(0, self._on_pdf_exported, file_path)
            else:
                self.window.after(0, self._on_pdf_error, "Error desconocido exportando PDF")
                
        except Exception as e:
            self.logger.error(f"Error exportando PDF: {e}")
            self.window.after(0, self._on_pdf_error, str(e))
    
    def _on_pdf_exported(self, file_path: str):
        """Callback cuando se exporta exitosamente el PDF"""
        self._show_progress(False)
        self._update_status(f"PDF exportado: {os.path.basename(file_path)}", "green")
        
        # Preguntar si abrir el archivo
        if messagebox.askyesno("Exportación Exitosa", f"PDF guardado en:\n{file_path}\n\n¿Desea abrir el archivo?"):
            try:
                os.startfile(file_path)  # Windows
            except AttributeError:
                try:
                    os.system(f"open '{file_path}'")  # macOS
                except:
                    os.system(f"xdg-open '{file_path}'")  # Linux
    
    def _on_pdf_error(self, error_message: str):
        """Callback cuando hay error exportando PDF"""
        self._show_progress(False)
        self._update_status(f"Error exportando PDF: {error_message}", "red")
        messagebox.showerror("Error", f"Error exportando PDF:\n{error_message}")
    
    def _on_close(self):
        """Cierra el formulario"""
        if self.window:
            self.window.destroy()
            self.window = None

def main():
    """Función principal para testing"""
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    root = tk.Tk()
    root.withdraw()  # Ocultar ventana principal
    
    # Crear formulario de reportes
    reports_form = ReportsForm(root, "test.db")
    reports_form.show()
    
    root.mainloop()


if __name__ == "__main__":
    main()
