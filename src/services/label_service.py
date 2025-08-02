"""
Servicio para generación de etiquetas y códigos de barras.

Este módulo proporciona funcionalidades completas para:
- Generación de imágenes de códigos de barras
- Creación de etiquetas de productos
- Generación de PDFs con múltiples etiquetas
- Gestión de templates de etiquetas
- Funcionalidades de impresión

Autor: Sistema de Inventario Copy Point S.A.
Fecha: Junio 2025
"""

import logging
import os
import tempfile
from decimal import Decimal
from io import BytesIO
from typing import List, Dict, Optional, Union, Tuple
import json
import threading
from pathlib import Path

from networkx import draw

# Importaciones de librerías externas
try:
    import barcode
    from barcode import Code128, Code39, EAN13, EAN8, UPCA
    from barcode.writer import ImageWriter
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm, inch
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.graphics.barcode import code128
    from PIL import Image, ImageDraw, ImageFont
except ImportError as e:
    logging.error(f"Error importando dependencias: {e}")
    raise

# Importaciones del sistema
from models.producto import Producto
from models.categoria import Categoria
from services.category_service import CategoryService

# Configurar logging
logger = logging.getLogger(__name__)


class LabelService:
    """
    Servicio para generación de etiquetas y códigos de barras.
    
    Proporciona funcionalidades completas para la generación automática
    de etiquetas de productos, códigos de barras y documentos PDF.
    """
    
    # Templates predefinidos
    DEFAULT_TEMPLATES = {
        'avery_5160': {
            'id': 'avery_5160',
            'name': 'Avery 5160',
            'description': '30 etiquetas por página (2.625" x 1")',
            'labels_per_page': 30,
            'label_width': 66.675,  # mm
            'label_height': 25.4,   # mm
            'page_width': 215.9,    # mm (carta)
            'page_height': 279.4,   # mm
            'top_margin': 12.7,
            'left_margin': 5.5,
            'columns': 3,
            'rows': 10,
            'h_spacing': 3.2,
            'v_spacing': 0
        },
        'avery_5163': {
            'id': 'avery_5163',
            'name': 'Avery 5163',
            'description': '10 etiquetas por página (2" x 4")',
            'labels_per_page': 10,
            'label_width': 101.6,   # mm
            'label_height': 50.8,   # mm
            'page_width': 215.9,    # mm
            'page_height': 279.4,   # mm
            'top_margin': 12.7,
            'left_margin': 5.5,
            'columns': 2,
            'rows': 5,
            'h_spacing': 3.2,
            'v_spacing': 0
        },
        'a4_standard': {
            'id': 'a4_standard',
            'name': 'A4 Standard',
            'description': '21 etiquetas por página (70mm x 40mm)',
            'labels_per_page': 21,
            'label_width': 70,      # mm
            'label_height': 40,     # mm
            'page_width': 210,      # mm (A4)
            'page_height': 297,     # mm
            'top_margin': 15,
            'left_margin': 5,
            'columns': 3,
            'rows': 7,
            'h_spacing': 0,
            'v_spacing': 2.5
        },
        'thermal_80mm': {
            'id': 'thermal_80mm',
            'name': 'Térmica 80mm',
            'description': 'Rollo continuo para impresoras térmicas',
            'labels_per_page': 1,
            'label_width': 80,      # mm
            'label_height': 50,     # mm
            'page_width': 80,       # mm
            'page_height': 50,      # mm
            'top_margin': 2,
            'left_margin': 2,
            'columns': 1,
            'rows': 1,
            'h_spacing': 0,
            'v_spacing': 0
        }
    }
    
    # Formatos de códigos soportados
    SUPPORTED_FORMATS = [
        'Code128', 'Code39', 'EAN13', 'EAN8', 'UPC', 'UPCA'
    ]
    
    def __init__(self, category_service: CategoryService = None):
        """Inicializar el servicio de etiquetas.
        
        Args:
            category_service: Servicio de categorías (inyección de dependencia)
        """
        self.templates = self.DEFAULT_TEMPLATES.copy()
        self.custom_templates_file = 'config/custom_templates.json'
        self.category_service = category_service
        self._lock = threading.Lock()
        
        # Cargar templates personalizados si existen
        self._load_custom_templates()
        
        logger.info("LabelService inicializado correctamente")
    
    def generate_barcode_image(self, 
                              code: str, 
                              format: str = 'Code128',
                              width: int = 150,
                              height: int = 50,
                              font_size: int = 10,
                              text_below: bool = True) -> bytes:
        """
        Generar imagen de código de barras.
        
        Args:
            code: Código a generar
            format: Formato del código (Code128, EAN13, etc.)
            width: Ancho en píxeles
            height: Alto en píxeles
            font_size: Tamaño de fuente para texto
            text_below: Si mostrar texto debajo del código
            
        Returns:
            bytes: Imagen del código en formato PNG
            
        Raises:
            ValueError: Si el código o formato son inválidos
        """
        try:
            # Validar entrada
            if not code or code is None:
                raise ValueError("El código no puede estar vacío")
            
            if format not in self.SUPPORTED_FORMATS:
                raise ValueError(f"Formato {format} no soportado. Usar: {self.SUPPORTED_FORMATS}")
            
            # Convertir código a string y limpiar
            code_str = str(code).strip()
            
            # Validar según el formato
            if format == 'EAN13' and len(code_str) != 13:
                raise ValueError("EAN13 requiere exactamente 13 dígitos")
            elif format == 'EAN8' and len(code_str) != 8:
                raise ValueError("EAN8 requiere exactamente 8 dígitos")
            
            # Generar código de barras con mapeo de formatos
            format_mapping = {
                'code128': Code128,
                'code39': Code39,
                'ean13': EAN13,
                'ean8': EAN8,
                'upc': UPCA,
                'upca': UPCA
            }
            
            barcode_class = format_mapping.get(format.lower())
            if not barcode_class:
                raise ValueError(f"Formato {format} no soportado en la implementación actual")
            
            # Configurar writer con opciones
            writer = ImageWriter()
            writer.set_options({
                'module_width': 0.2,
                'module_height': height / 2.0,
                'font_size': font_size,
                'text_distance': 5,
                'quiet_zone': 6
            })
            
            # Generar código
            barcode_obj = barcode_class(code_str, writer=writer)
            
            # Crear imagen en memoria
            buffer = BytesIO()
            barcode_obj.write(buffer, {
                'format': 'PNG',
                'write_text': text_below
            })
            
            # Redimensionar si es necesario
            buffer.seek(0)
            image = Image.open(buffer)
            
            if image.size[0] != width or image.size[1] != height:
                image = image.resize((width, height), Image.Resampling.LANCZOS)
            
            # Convertir a bytes
            output_buffer = BytesIO()
            image.save(output_buffer, format='PNG')
            
            logger.debug(f"Código de barras generado: {format} - {code_str}")
            return output_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error generando código de barras: {e}")
            raise
    
    def create_product_label(self, 
                           product: Producto,
                           format: str = 'standard',
                           include_category: bool = False,
                           include_price: bool = True,
                           include_barcode: bool = True) -> bytes:
        """
        Crear etiqueta de producto.
        
        Args:
            product: Producto para generar etiqueta
            format: Formato de etiqueta (standard, mini, detailed)
            include_category: Si incluir información de categoría
            include_price: Si incluir precio
            include_barcode: Si incluir código de barras
            
        Returns:
            bytes: Imagen de la etiqueta en formato PNG
            
        Raises:
            ValueError: Si el producto es inválido
        """
        try:
            # Validar producto
            if not product or product is None:
                raise ValueError("El producto no puede ser None")
            
            if not product.id_producto:
                raise ValueError("El producto debe tener un ID válido")
            
            # Obtener categoría si se solicita
            category = None
            if include_category and product.id_categoria:
                if self.category_service is None:
                    logger.warning("CategoryService no está disponible, omitiendo información de categoría")
                else:
                    try:
                        category = self.category_service.get_category_by_id(product.id_categoria)
                    except Exception as e:
                        logger.warning(f"No se pudo obtener categoría {product.id_categoria}: {e}")
            
            # Configurar dimensiones según formato
            if format == 'mini':
                width, height = 200, 120
                font_sizes = {'title': 12, 'detail': 8, 'price': 10}
            elif format == 'detailed':
                width, height = 400, 250
                font_sizes = {'title': 16, 'detail': 12, 'price': 14}
            else:  # standard
                width, height = 300, 180
                font_sizes = {'title': 14, 'detail': 10, 'price': 12}
            
            # Crear imagen
            image = Image.new('RGB', (width, height), 'white')
            draw = ImageDraw.Draw(image)
            
            # Intentar cargar fuentes
            try:
                font_title = ImageFont.truetype("arial.ttf", font_sizes['title'])
                font_detail = ImageFont.truetype("arial.ttf", font_sizes['detail'])
                font_price = ImageFont.truetype("arialbd.ttf", font_sizes['price'])
            except:
                # Usar fuente por defecto si no se encuentran las TTF
                font_title = ImageFont.load_default()
                font_detail = ImageFont.load_default()
                font_price = ImageFont.load_default()
            
            # Calcular posiciones
            y_pos = 10
            x_margin = 10
            
            # Título del producto
            product_name = product.nombre[:30] + "..." if len(product.nombre) > 30 else product.nombre
            # draw.text((x_margin, y_pos), product_name, fill='black', font=font_title)
            text_width = draw.textlength(product_name, font=font_title)
            x_centered = (width - text_width) // 2
            draw.text((x_centered, y_pos), product_name, fill='black', font=font_title)
            y_pos += font_sizes['title'] + 5
            
            # Información de categoría
            if include_category and category:
                category_text = f"Categoría: {category.nombre}"
                # draw.text((x_margin, y_pos), category_text, fill='gray', font=font_detail)

                text_width = draw.textlength(category_text, font=font_title)
                x_centered = (width - text_width) // 2
                draw.text((x_centered, y_pos), category_text, fill='black', font=font_title)

                y_pos += font_sizes['detail'] + 3
            
            # ID del producto
            # id_text = f"ID: {product.id_producto}"
            # text_width = draw.textlength(id_text, font=font_title)
            # x_centered = (width - text_width) // 2
            # draw.text((x_centered, y_pos), id_text, fill='black', font=font_title)

            # y_pos += font_sizes['detail'] + 5
            
            # Precio
            if include_price and product.precio:
                # price_text = f"Precio: B/. {product.precio:.2f}"
                price_text = f"B/. {product.precio:.2f}"
                text_width = draw.textlength(price_text, font=font_title)
                x_centered = (width - text_width) // 2
                draw.text((x_centered, y_pos), price_text, fill='black', font=font_title)

                y_pos += font_sizes['price'] + 8
            
            # Código de barras
            if include_barcode:
                try:
                    # barcode_width = width - (x_margin * 2)
                    # barcode_height = 40 if format != 'mini' else 25
                    
                    # barcode_image_data = self.generate_barcode_image(
                    #     str(product.id_producto),
                    #     width=barcode_width,
                    #     height=barcode_height,
                    #     font_size=8 if format == 'mini' else 10
                    # )
                    
                    # Altura del código de barras basada en un porcentaje del alto total
                    barcode_height = int(height * 0.50)  # 25% de la altura total
                    barcode_width = int(width * 0.50)    # 85% del ancho total

                    barcode_image_data = self.generate_barcode_image(
                        str(product.id_producto),
                        width=barcode_width,
                        height=barcode_height,
                        font_size=font_sizes['detail'] + 2  # Asegura legibilidad
                    )

                    # Pegar código de barras
                    barcode_buffer = BytesIO(barcode_image_data)
                    barcode_img = Image.open(barcode_buffer)
                    
                    # Calcular posición centrada
                    # barcode_x = (width - barcode_img.width) // 2
                    # barcode_y = height - barcode_img.height - 10
                    
                    barcode_x = (width - barcode_img.width) // 2
                    barcode_y = y_pos + 4  # menor espacio entre texto y código de barras


                    image.paste(barcode_img, (barcode_x, barcode_y))
                    
                except Exception as e:
                    logger.warning(f"No se pudo generar código de barras para producto {product.id_producto}: {e}")
            
            # Convertir a bytes
            output_buffer = BytesIO()
            image.save(output_buffer, format='PNG')
            
            logger.debug(f"Etiqueta creada para producto {product.id_producto}")
            return output_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error creando etiqueta de producto: {e}")
            raise
    
    def generate_labels_pdf(self, 
                          products: Union[List[Producto], List[Dict]],
                          template: str = 'a4_standard',
                          use_quantities: bool = False,
                          label_format: str = 'standard') -> bytes:
        """
        Generar PDF con múltiples etiquetas.
        
        Args:
            products: Lista de productos o diccionarios con producto y cantidad
            template: Template a usar
            use_quantities: Si usar cantidades específicas
            label_format: Formato de etiquetas individuales
            
        Returns:
            bytes: PDF con las etiquetas
            
        Raises:
            ValueError: Si el template no existe o productos inválidos
        """
        try:
            # Validar template
            if template not in self.templates:
                raise ValueError(f"Template '{template}' no encontrado")
            
            template_data = self.templates[template]
            
            # Validar productos
            if not products:
                raise ValueError("La lista de productos no puede estar vacía")
            
            # Preparar lista de etiquetas a generar
            labels_to_generate = []
            
            for item in products:
                if use_quantities and isinstance(item, dict):
                    product = item['product']
                    quantity = item.get('quantity', 1)
                else:
                    product = item
                    quantity = 1
                
                # Agregar etiquetas según cantidad
                for _ in range(quantity):
                    labels_to_generate.append(product)
            
            # Crear PDF
            pdf_buffer = BytesIO()
            
            # Configurar página
            page_width = template_data['page_width'] * mm
            page_height = template_data['page_height'] * mm
            
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=(page_width, page_height),
                topMargin=template_data['top_margin'] * mm,
                leftMargin=template_data['left_margin'] * mm,
                rightMargin=5 * mm,
                bottomMargin=5 * mm
            )
            
            # Calcular posiciones
            positions = self._calculate_label_positions(template_data)
            
            # Crear canvas para dibujo directo
            canvas_pdf = canvas.Canvas(pdf_buffer, pagesize=(page_width, page_height))
            
            labels_per_page = template_data['labels_per_page']
            current_page = 0
            
            for i, product in enumerate(labels_to_generate):
                position_index = i % labels_per_page
                
                # Nueva página si es necesario
                if position_index == 0 and i > 0:
                    canvas_pdf.showPage()
                    current_page += 1
                
                # Obtener posición
                pos = positions[position_index]
                
                # Generar etiqueta individual
                try:
                    label_image_data = self.create_product_label(
                        product, 
                        format=label_format
                    )
                    
                    # Crear archivo temporal para la imagen
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                        tmp_file.write(label_image_data)
                        tmp_path = tmp_file.name
                    
                    # Dibujar imagen en PDF
                    canvas_pdf.drawImage(
                        tmp_path,
                        pos['x'] * mm,
                        (template_data['page_height'] - pos['y'] - pos['height']) * mm,
                        width=pos['width'] * mm,
                        height=pos['height'] * mm,
                        preserveAspectRatio=False
                    )
                    
                    # Limpiar archivo temporal
                    os.unlink(tmp_path)
                    
                except Exception as e:
                    logger.warning(f"Error generando etiqueta para producto {product.id_producto}: {e}")
                    
                    # Dibujar marco de error
                    canvas_pdf.setStrokeColor(colors.red)
                    canvas_pdf.rect(
                        pos['x'] * mm,
                        (template_data['page_height'] - pos['y'] - pos['height']) * mm,
                        pos['width'] * mm,
                        pos['height'] * mm
                    )
                    
                    # Texto de error
                    canvas_pdf.setFillColor(colors.red)
                    canvas_pdf.drawString(
                        (pos['x'] + 5) * mm,
                        (template_data['page_height'] - pos['y'] - pos['height']/2) * mm,
                        "ERROR"
                    )
            
            # Finalizar PDF
            canvas_pdf.save()
            
            logger.info(f"PDF generado con {len(labels_to_generate)} etiquetas usando template {template}")
            return pdf_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error generando PDF de etiquetas: {e}")
            raise
    
    def get_available_templates(self) -> List[Dict]:
        """
        Obtener lista de templates disponibles.
        
        Returns:
            List[Dict]: Lista de templates con su información
        """
        templates_list = []
        
        for template_id, template_data in self.templates.items():
            templates_list.append({
                'id': template_id,
                'name': template_data['name'],
                'description': template_data['description'],
                'labels_per_page': template_data['labels_per_page'],
                'page_size': f"{template_data['page_width']}x{template_data['page_height']}mm"
            })
        
        return templates_list
    
    def create_custom_template(self, template_data: Dict) -> bool:
        """
        Crear template personalizado.
        
        Args:
            template_data: Datos del template
            
        Returns:
            bool: True si se creó exitosamente
            
        Raises:
            ValueError: Si los datos son inválidos
        """
        try:
            # Validar datos requeridos
            if not self._validate_template_data(template_data):
                raise ValueError("Datos de template inválidos")
            
            # Agregar timestamp si no tiene ID
            if 'id' not in template_data:
                import time
                template_data['id'] = f"custom_{int(time.time())}"
            
            # Agregar a templates
            with self._lock:
                self.templates[template_data['id']] = template_data
                
                # Guardar en archivo
                self._save_custom_templates()
            
            logger.info(f"Template personalizado creado: {template_data['id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error creando template personalizado: {e}")
            raise
    
    def print_labels(self, pdf_data: bytes, printer_name: Optional[str] = None) -> bool:
        """
        Imprimir etiquetas.
        
        Args:
            pdf_data: Datos del PDF a imprimir
            printer_name: Nombre de impresora específica (opcional)
            
        Returns:
            bool: True si se imprimió exitosamente
            
        Raises:
            ValueError: Si los datos son inválidos
        """
        try:
            # Validar datos
            if not pdf_data or pdf_data is None:
                raise ValueError("Los datos PDF no pueden estar vacíos")
            
            if len(pdf_data) == 0:
                raise ValueError("Los datos PDF están vacíos")
            
            # Verificar que sea un PDF válido
            if not pdf_data.startswith(b'%PDF'):
                raise ValueError("Los datos no corresponden a un PDF válido")
            
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(pdf_data)
                tmp_path = tmp_file.name
            
            try:
                # Comando de impresión según el sistema operativo
                import platform
                
                if platform.system() == "Windows":
                    if printer_name:
                        # Imprimir en impresora específica
                        cmd = f'powershell -Command "Start-Process -FilePath \\"{tmp_path}\\" -Verb Print -ArgumentList \\"{printer_name}\\""'
                    else:
                        # Imprimir en impresora por defecto
                        cmd = f'powershell -Command "Start-Process -FilePath \\"{tmp_path}\\" -Verb Print"'
                elif platform.system() == "Linux":
                    if printer_name:
                        cmd = f'lp -d "{printer_name}" "{tmp_path}"'
                    else:
                        cmd = f'lp "{tmp_path}"'
                else:  # macOS
                    if printer_name:
                        cmd = f'lpr -P "{printer_name}" "{tmp_path}"'
                    else:
                        cmd = f'lpr "{tmp_path}"'
                
                # Ejecutar comando
                result = os.system(cmd)
                
                success = (result == 0)
                
                if success:
                    logger.info(f"Etiquetas enviadas a imprimir: {printer_name or 'predeterminada'}")
                else:
                    logger.error(f"Error en impresión, código: {result}")
                
                return success
                
            finally:
                # Limpiar archivo temporal
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            
        except Exception as e:
            logger.error(f"Error imprimiendo etiquetas: {e}")
            return False
    
    def get_barcode_formats(self) -> List[str]:
        """
        Obtener lista de formatos de códigos soportados.
        
        Returns:
            List[str]: Formatos soportados
        """
        return self.SUPPORTED_FORMATS.copy()
    
    def _validate_template_data(self, template_data: Dict) -> bool:
        """
        Validar datos de template.
        
        Args:
            template_data: Datos a validar
            
        Returns:
            bool: True si son válidos
        """
        required_fields = [
            'name', 'labels_per_page', 'label_width', 'label_height',
            'page_width', 'page_height', 'top_margin', 'left_margin',
            'columns', 'rows'
        ]
        
        # Verificar campos requeridos
        for field in required_fields:
            if field not in template_data:
                logger.error(f"Campo requerido faltante: {field}")
                return False
        
        # Verificar valores positivos
        numeric_fields = [
            'labels_per_page', 'label_width', 'label_height',
            'page_width', 'page_height', 'columns', 'rows'
        ]
        
        for field in numeric_fields:
            if template_data[field] <= 0:
                logger.error(f"Campo {field} debe ser positivo")
                return False
        
        # Verificar coherencia
        expected_labels = template_data['columns'] * template_data['rows']
        if template_data['labels_per_page'] != expected_labels:
            logger.error("labels_per_page no coincide con columns * rows")
            return False
        
        return True
    
    def _calculate_label_positions(self, template_data: Dict) -> List[Dict]:
        """
        Calcular posiciones de etiquetas en la página.
        
        Args:
            template_data: Datos del template
            
        Returns:
            List[Dict]: Lista de posiciones con x, y, width, height
        """
        positions = []
        
        cols = template_data['columns']
        rows = template_data['rows']
        
        label_width = template_data['label_width']
        label_height = template_data['label_height']
        
        top_margin = template_data['top_margin']
        left_margin = template_data['left_margin']
        
        h_spacing = template_data.get('h_spacing', 0)
        v_spacing = template_data.get('v_spacing', 0)
        
        for row in range(rows):
            for col in range(cols):
                x = left_margin + col * (label_width + h_spacing)
                y = top_margin + row * (label_height + v_spacing)
                
                positions.append({
                    'x': x,
                    'y': y,
                    'width': label_width,
                    'height': label_height
                })
        
        return positions
    
    def _load_custom_templates(self):
        """Cargar templates personalizados desde archivo."""
        try:
            if os.path.exists(self.custom_templates_file):
                with open(self.custom_templates_file, 'r', encoding='utf-8') as f:
                    custom_templates = json.load(f)
                    self.templates.update(custom_templates)
                    logger.info(f"Cargados {len(custom_templates)} templates personalizados")
        except Exception as e:
            logger.warning(f"No se pudieron cargar templates personalizados: {e}")
    
    def _save_custom_templates(self):
        """Guardar templates personalizados en archivo."""
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(self.custom_templates_file), exist_ok=True)
            
            # Filtrar solo templates personalizados
            custom_templates = {
                k: v for k, v in self.templates.items() 
                if k not in self.DEFAULT_TEMPLATES
            }
            
            with open(self.custom_templates_file, 'w', encoding='utf-8') as f:
                json.dump(custom_templates, f, indent=2, ensure_ascii=False)
                
            logger.debug("Templates personalizados guardados")
            
        except Exception as e:
            logger.error(f"Error guardando templates personalizados: {e}")


# Singleton instance
_label_service_instance = None

def get_label_service() -> LabelService:
    """
    Obtener instancia singleton del servicio de etiquetas.
    DEPRECATED: Usar ServiceContainer.get('label_service') en su lugar
    
    Returns:
        LabelService: Instancia del servicio
    """
    # DEPRECATED: Esta función está obsoleta
    # Usar ServiceContainer para obtener la instancia con dependencias correctas
    from services.service_container import get_container
    container = get_container()
    return container.get('label_service')
