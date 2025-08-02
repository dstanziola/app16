"""
Formulario de preview y configuración de tickets.
Permite previsualizar tickets antes de imprimir y configurar opciones de impresión.

Este formulario maneja:
- Preview de tickets antes de imprimir
- Configuración de impresora
- Opciones de formato
- Generación y guardado de PDFs

Autor: Sistema TDD - FASE 3
Fecha: 2025-06-25
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import subprocess
import platform
from datetime import datetime
from typing import Optional, Dict, Any

from models.ticket import Ticket
from reports.ticket_generator import TicketGenerator
from services.ticket_service import TicketService
from services.company_service import CompanyService


class TicketPreviewForm:
    """
    Formulario para preview e impresión de tickets.
    
    Permite configurar opciones de impresión y generar PDFs.
    """
    
    def __init__(self, parent=None, ticket: Optional[Ticket] = None):
        """
        Inicializar formulario de preview de tickets.
        
        Args:
            parent: Ventana padre
            ticket: Ticket a mostrar (opcional)
        """
        self.parent = parent
        self.ticket = ticket
        # self.ticket_generator = TicketGenerator()
        self.ticket_service = TicketService()
        self.ticket_generator = TicketGenerator(self.ticket_service.sales_service.db)
        self.company_service = CompanyService()
        
        # Variables del formulario
        self.formato_var = tk.StringVar()
        self.incluir_qr_var = tk.BooleanVar()
        self.guardar_archivo_var = tk.BooleanVar()
        self.imprimir_directo_var = tk.BooleanVar()
        
        # Configurar valores por defecto
        self.formato_var.set(TicketGenerator.FORMATO_A4)
        self.incluir_qr_var.set(True)
        self.guardar_archivo_var.set(True)
        self.imprimir_directo_var.set(False)
        
        self.window = None
        self.setup_ui()
    
    def setup_ui(self):
        """
        Configurar la interfaz de usuario.
        """
        # Crear ventana
        self.window = tk.Toplevel(self.parent) if self.parent else tk.Tk()
        self.window.title("Preview e Impresión de Tickets")
        self.window.geometry("800x600")
        self.window.resizable(True, True)
        
        # Frame principal
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # Sección de información del ticket
        self._create_ticket_info_section(main_frame, row)
        row += 1
        
        # Separador
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10
        )
        row += 1
        
        # Sección de configuración
        self._create_config_section(main_frame, row)
        row += 1
        
        # Separador
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10
        )
        row += 1
        
        # Sección de preview
        self._create_preview_section(main_frame, row)
        row += 1
        
        # Separador
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10
        )
        row += 1
        
        # Botones de acción
        self._create_action_buttons(main_frame, row)
        
        # Cargar información del ticket si está disponible
        if self.ticket:
            self._load_ticket_info()
    
    def _create_ticket_info_section(self, parent, row):
        """
        Crear sección de información del ticket.
        """
        # Label de sección
        ttk.Label(parent, text="Información del Ticket", 
                 font=('TkDefaultFont', 10, 'bold')).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10)
        )
        row += 1
        
        # Frame para información
        info_frame = ttk.LabelFrame(parent, text="Datos del Ticket", padding="10")
        info_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        info_frame.columnconfigure(1, weight=1)
        
        # Información del ticket
        ttk.Label(info_frame, text="Número:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.numero_label = ttk.Label(info_frame, text="N/A")
        self.numero_label.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(info_frame, text="Tipo:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.tipo_label = ttk.Label(info_frame, text="N/A")
        self.tipo_label.grid(row=1, column=1, sticky=tk.W)
        
        ttk.Label(info_frame, text="Fecha:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10))
        self.fecha_label = ttk.Label(info_frame, text="N/A")
        self.fecha_label.grid(row=2, column=1, sticky=tk.W)
        
        ttk.Label(info_frame, text="Generado por:").grid(row=3, column=0, sticky=tk.W, padx=(0, 10))
        self.generado_por_label = ttk.Label(info_frame, text="N/A")
        self.generado_por_label.grid(row=3, column=1, sticky=tk.W)
        
        ttk.Label(info_frame, text="Reimpresiones:").grid(row=4, column=0, sticky=tk.W, padx=(0, 10))
        self.reimpresiones_label = ttk.Label(info_frame, text="N/A")
        self.reimpresiones_label.grid(row=4, column=1, sticky=tk.W)
    
    def _create_config_section(self, parent, row):
        """
        Crear sección de configuración de impresión.
        """
        # Label de sección
        ttk.Label(parent, text="Configuración de Impresión", 
                 font=('TkDefaultFont', 10, 'bold')).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10)
        )
        row += 1
        
        # Frame para configuración
        config_frame = ttk.LabelFrame(parent, text="Opciones", padding="10")
        config_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)
        
        # Formato de papel
        ttk.Label(config_frame, text="Formato:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        formato_combo = ttk.Combobox(config_frame, textvariable=self.formato_var, 
                                   state="readonly", width=30)
        
        # Obtener formatos disponibles
        formatos_disponibles = self.ticket_generator.obtener_formatos_disponibles()
        formato_combo['values'] = list(formatos_disponibles.values())
        
        # Mapear valores para mostrar descripciones
        self.formato_map = {v: k for k, v in formatos_disponibles.items()}
        
        formato_combo.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # Checkboxes de opciones
        ttk.Checkbutton(config_frame, text="Incluir código QR", 
                       variable=self.incluir_qr_var).grid(
            row=1, column=0, columnspan=2, sticky=tk.W, pady=2
        )
        
        ttk.Checkbutton(config_frame, text="Guardar archivo PDF", 
                       variable=self.guardar_archivo_var).grid(
            row=2, column=0, columnspan=2, sticky=tk.W, pady=2
        )
        
        ttk.Checkbutton(config_frame, text="Imprimir directamente", 
                       variable=self.imprimir_directo_var).grid(
            row=3, column=0, columnspan=2, sticky=tk.W, pady=2
        )
    
    def _create_preview_section(self, parent, row):
        """
        Crear sección de preview del ticket.
        """
        # Label de sección
        ttk.Label(parent, text="Preview del Ticket", 
                 font=('TkDefaultFont', 10, 'bold')).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10)
        )
        row += 1
        
        # Frame para preview con scrollbar
        preview_frame = ttk.LabelFrame(parent, text="Vista Previa", padding="5")
        preview_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        # Text widget con scrollbar
        text_frame = ttk.Frame(preview_frame)
        text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        self.preview_text = tk.Text(text_frame, height=15, width=70, 
                                   wrap=tk.WORD, state=tk.DISABLED)
        self.preview_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.preview_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.preview_text.configure(yscrollcommand=scrollbar.set)
        
        # Configurar peso del grid del parent
        parent.rowconfigure(row, weight=1)
    
    def _create_action_buttons(self, parent, row):
        """
        Crear botones de acción.
        """
        # Frame para botones
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=row, column=0, columnspan=2, pady=10)
        
        # Botones
        ttk.Button(button_frame, text="Actualizar Preview", 
                  command=self._update_preview).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Generar PDF", 
                  command=self._generate_pdf).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Reimprimir", 
                  command=self._reprint_ticket).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Abrir PDF", 
                  command=self._open_pdf).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Cerrar", 
                  command=self._close_window).pack(side=tk.RIGHT, padx=5)
    
    def _load_ticket_info(self):
        """
        Cargar información del ticket en la interfaz.
        """
        if not self.ticket:
            return
        
        self.numero_label.config(text=self.ticket.ticket_number)
        self.tipo_label.config(text=self.ticket.obtener_descripcion_tipo())
        self.fecha_label.config(text=self.ticket.obtener_fecha_formateada())
        self.generado_por_label.config(text=self.ticket.generated_by)
        self.reimpresiones_label.config(text=str(self.ticket.reprint_count))
        
        # Actualizar preview
        self._update_preview()
    
    def _update_preview(self):
        """
        Actualizar el preview del ticket.
        """
        if not self.ticket:
            self._show_preview_text("No hay ticket seleccionado para mostrar.")
            return
        
        try:
            # Generar contenido de preview
            preview_content = self._generate_preview_content()
            self._show_preview_text(preview_content)
            
        except Exception as e:
            self._show_preview_text(f"Error al generar preview: {str(e)}")
    
    def _generate_preview_content(self) -> str:
        """
        Generar contenido textual para preview.
        
        Returns:
            String con el contenido del ticket
        """
        if not self.ticket:
            return "No hay ticket disponible"
        
        # Obtener datos de empresa
        try:
            datos_empresa = self.company_service.obtener_encabezado_documentos()
        except Exception:
            datos_empresa = {
                'nombre': 'EMPRESA',
                'ruc': 'R.U.C.: 000-000-0000',
                'direccion': 'Dirección no disponible',
                'telefono': 'Tel.: 0000-0000',
                'email': 'E-mail: info@empresa.com'
            }
        
        # Construir contenido
        content = []
        content.append("=" * 50)
        content.append(datos_empresa['nombre'].center(50))
        content.append(datos_empresa['ruc'].center(50))
        content.append(datos_empresa['direccion'].center(50))
        content.append(datos_empresa['telefono'].center(50))
        content.append(datos_empresa['email'].center(50))
        content.append("=" * 50)
        content.append("")
        
        # Título del ticket
        if self.ticket.es_ticket_venta():
            content.append("TICKET DE VENTA".center(50))
        else:
            content.append("TICKET DE ENTRADA DE INVENTARIO".center(50))
        
        content.append("")
        content.append(f"Ticket No: {self.ticket.ticket_number}")
        content.append(f"Fecha: {self.ticket.obtener_fecha_formateada()}")
        content.append(f"Atendido por: {self.ticket.generated_by}")
        
        if self.ticket.reprint_count > 0:
            content.append(f"REIMPRESIÓN #{self.ticket.reprint_count}")
        
        content.append("")
        content.append("-" * 50)
        
        # Contenido específico del tipo de ticket
        if self.ticket.es_ticket_venta():
            content.extend(self._get_venta_preview_content())
        else:
            content.extend(self._get_entrada_preview_content())
        
        content.append("-" * 50)
        content.append("")
        
        # Información adicional
        if self.incluir_qr_var.get():
            content.append("Incluye código QR para verificación")
            content.append("")
        
        content.append("¡Gracias por su compra!".center(50))
        content.append(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}".center(50))
        content.append("=" * 50)
        
        return "\n".join(content)
    
    def _get_venta_preview_content(self) -> list:
        """
        Obtener contenido de preview para ticket de venta.
        
        Returns:
            Lista de líneas de contenido
        """
        content = []
        
        try:
            # Intentar obtener datos de la venta
            from services.sales_service import SalesService
            sales_service = SalesService()
            
            venta = sales_service.obtener_venta_por_id(self.ticket.id_venta)
            if venta:
                detalles = sales_service.obtener_detalles_venta(self.ticket.id_venta)
                
                # Tabla de productos
                content.append("PRODUCTOS:")
                content.append("")
                content.append("Producto".ljust(25) + "Cant.".rjust(5) + "Precio".rjust(10) + "Total".rjust(10))
                content.append("-" * 50)
                
                for detalle in detalles:
                    nombre = str(detalle.get('nombre_producto', 'N/A'))[:24]
                    cant = str(detalle.get('cantidad', 0))
                    precio = f"${detalle.get('precio_unitario', 0):.2f}"
                    total = f"${detalle.get('subtotal_item', 0):.2f}"
                    
                    content.append(nombre.ljust(25) + cant.rjust(5) + precio.rjust(10) + total.rjust(10))
                
                content.append("")
                content.append(f"Subtotal:".ljust(40) + f"${venta.get('subtotal', 0):.2f}".rjust(10))
                content.append(f"ITBMS:".ljust(40) + f"${venta.get('impuestos', 0):.2f}".rjust(10))
                content.append(f"TOTAL:".ljust(40) + f"${venta.get('total', 0):.2f}".rjust(10))
            else:
                content.append("No se pudieron cargar los detalles de la venta")
                
        except Exception as e:
            content.append(f"Error al cargar datos de venta: {str(e)}")
        
        return content
    
    def _get_entrada_preview_content(self) -> list:
        """
        Obtener contenido de preview para ticket de entrada.
        
        Returns:
            Lista de líneas de contenido
        """
        content = []
        
        try:
            # Intentar obtener datos del movimiento
            from services.movement_service import MovementService
            movement_service = MovementService()
            
            movimiento = movement_service.get_movement_by_id(self.ticket.id_movimiento)
            if movimiento:
                content.append("DETALLES DEL MOVIMIENTO:")
                content.append("")
                content.append(f"Tipo: {movimiento.get('tipo_movimiento', 'N/A')}")
                content.append(f"Cantidad: {movimiento.get('cantidad', 0)}")
                content.append(f"Fecha movimiento: {movimiento.get('fecha_movimiento', 'N/A')}")
                
                if movimiento.get('observaciones'):
                    content.append(f"Observaciones:")
                    content.append(f"  {movimiento.get('observaciones')}")
            else:
                content.append("No se pudieron cargar los detalles del movimiento")
                
        except Exception as e:
            content.append(f"Error al cargar datos de movimiento: {str(e)}")
        
        return content
    
    def _show_preview_text(self, text: str):
        """
        Mostrar texto en el area de preview.
        
        Args:
            text: Texto a mostrar
        """
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(1.0, text)
        self.preview_text.config(state=tk.DISABLED)
    
    def _generate_pdf(self):
        """
        Generar PDF del ticket.
        """
        if not self.ticket:
            messagebox.showerror("Error", "No hay ticket para generar PDF")
            return
        
        try:
            # Obtener formato seleccionado
            formato_desc = self.formato_var.get()
            formato_codigo = self.formato_map.get(formato_desc, TicketGenerator.FORMATO_A4)
            
            # Generar ruta de archivo
            if self.guardar_archivo_var.get():
                # Permitir al usuario seleccionar ubicación
                filename = filedialog.asksaveasfilename(
                    title="Guardar ticket como...",
                    defaultextension=".pdf",
                    filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                    initialname=f"{self.ticket.ticket_number}.pdf"
                )
                
                if not filename:
                    return  # Usuario canceló
                
                output_path = filename
            else:
                # Usar ruta temporal
                output_path = self.ticket_generator.generar_ruta_archivo(
                    self.ticket, "temp"
                )
            
            # Generar PDF
            success = self.ticket_generator.generar_ticket_pdf(
                ticket=self.ticket,
                output_path=output_path,
                formato=formato_codigo,
                incluir_qr=self.incluir_qr_var.get()
            )
            
            if success:
                # Actualizar ruta en el ticket si es necesario
                if hasattr(self.ticket, 'id_ticket') and self.ticket.id_ticket:
                    self.ticket_service.actualizar_pdf_path(self.ticket.id_ticket, output_path)
                
                messagebox.showinfo("Éxito", f"PDF generado exitosamente:\n{output_path}")
                
                # Imprimir si está habilitado
                if self.imprimir_directo_var.get():
                    self._print_pdf(output_path)
                
                # Guardar ruta para botón "Abrir PDF"
                self.last_pdf_path = output_path
                
            else:
                messagebox.showerror("Error", "No se pudo generar el PDF")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar PDF:\n{str(e)}")
    
    def _print_pdf(self, pdf_path: str):
        """
        Imprimir PDF directamente.
        
        Args:
            pdf_path: Ruta del archivo PDF
        """
        try:
            system = platform.system()
            
            if system == "Windows":
                # En Windows, usar el comando de impresión por defecto
                os.startfile(pdf_path, "print")
            elif system == "Darwin":  # macOS
                subprocess.run(["lp", pdf_path])
            else:  # Linux
                subprocess.run(["lp", pdf_path])
                
            messagebox.showinfo("Impresión", "Documento enviado a la impresora")
            
        except Exception as e:
            messagebox.showerror("Error de Impresión", f"No se pudo imprimir:\n{str(e)}")
    
    def _reprint_ticket(self):
        """
        Reimprimir el ticket (crear nueva entrada con contador incrementado).
        """
        if not self.ticket or not hasattr(self.ticket, 'id_ticket') or not self.ticket.id_ticket:
            messagebox.showerror("Error", "No hay ticket válido para reimprimir")
            return
        
        try:
            # Solicitar confirmación
            if not messagebox.askyesno("Confirmar Reimpresión", 
                                     f"¿Está seguro de reimprimir el ticket {self.ticket.ticket_number}?"):
                return
            
            # Reimprimir ticket
            from ui.auth.session_manager import SessionManager
            session = SessionManager()
            usuario_actual = session.get_current_user()
            
            if not usuario_actual:
                messagebox.showerror("Error", "No hay usuario autenticado")
                return
            
            ticket_reimpreso = self.ticket_service.reimprimir_ticket(
                self.ticket.id_ticket, 
                usuario_actual.get('nombre_usuario', 'admin')
            )
            
            # Actualizar ticket actual y recargar información
            self.ticket = ticket_reimpreso
            self._load_ticket_info()
            
            messagebox.showinfo("Éxito", f"Ticket reimpreso como #{ticket_reimpreso.reprint_count}")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo reimprimir el ticket:\n{str(e)}")
    
    def _open_pdf(self):
        """
        Abrir el último PDF generado.
        """
        if hasattr(self, 'last_pdf_path') and os.path.exists(self.last_pdf_path):
            try:
                system = platform.system()
                
                if system == "Windows":
                    os.startfile(self.last_pdf_path)
                elif system == "Darwin":  # macOS
                    subprocess.run(["open", self.last_pdf_path])
                else:  # Linux
                    subprocess.run(["xdg-open", self.last_pdf_path])
                    
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el PDF:\n{str(e)}")
        else:
            messagebox.showwarning("Advertencia", "No hay PDF generado para abrir")
    
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
    # Crear ticket de prueba
    from models.ticket import Ticket
    from datetime import datetime
    
    ticket_prueba = Ticket.crear_ticket_venta(
        ticket_number="V000001",
        id_venta=1,
        generated_by="admin"
    )
    ticket_prueba.id_ticket = 1
    
    # Mostrar formulario
    form = TicketPreviewForm(ticket=ticket_prueba)
    form.show()


if __name__ == "__main__":
    main()
