# Sistema de Inventario Copy Point S.A.

![Sistema de Inventario](https://img.shields.io/badge/Sistema-Inventario-blue)
![Versión](https://img.shields.io/badge/Versión-1.0.4-green)
![Estado](https://img.shields.io/badge/Estado-Activo-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-6.0+-orange)
![SQLite](https://img.shields.io/badge/SQLite-3.0+-yellow)

Sistema completo de gestión de inventario, ventas y reportes desarrollado especialmente para Copy Point S.A. Implementa funcionalidades críticas para la administración de productos, control de stock, procesamiento de ventas y generación de reportes empresariales.

## 🚀 Características Principales

### ✅ Gestión de Inventario
- **Productos y Servicios:** CRUD completo con categorización inteligente
- **Control de Stock:** Seguimiento en tiempo real con alertas automáticas
- **Movimientos:** Registro detallado de entradas y salidas con trazabilidad
- **Códigos de Barras:** Integración para lectura y generación automática
- **Inventario Físico:** Herramientas para conteos y ajustes

### ✅ Sistema de Ventas
- **Punto de Venta:** Interfaz intuitiva para procesamiento rápido
- **Facturación:** Generación automática con cálculo de impuestos
- **Gestión de Clientes:** Base de datos integrada con historial
- **Métodos de Pago:** Soporte para efectivo, tarjeta y crédito
- **Devoluciones:** Proceso simplificado con trazabilidad completa

### ✅ Reportes Empresariales
- **Reportes de Ventas:** Análisis por período, producto y vendedor
- **Control de Inventario:** Stock actual, rotación y valorización
- **Análisis Financiero:** Rentabilidad, márgenes y tendencias
- **Exportación:** PDF, Excel y CSV para análisis externo
- **Dashboard:** Métricas en tiempo real y KPIs principales

### ✅ Administración y Seguridad
- **Usuarios y Roles:** Control granular de permisos (Admin/Vendedor)
- **Autenticación:** Sistema seguro con encriptación de passwords
- **Auditoría:** Logs completos de todas las transacciones
- **Respaldos:** Sistema automático de backup y recuperación
- **Configuración:** Parametrización empresarial flexible

## 🛠️ Tecnologías Utilizadas

| Componente | Tecnología | Versión | Propósito |
|------------|------------|---------|-----------|
| **Frontend** | PyQt6 | 6.0+ | Interfaz de usuario moderna |
| **Backend** | Python | 3.8+ | Lógica de negocio y servicios |
| **Base de Datos** | SQLite | 3.0+ | Almacenamiento local eficiente |
| **Reportes** | ReportLab | 4.0+ | Generación de PDFs |
| **Códigos Barras** | python-barcode | 0.14+ | Lectura y generación |
| **Exportación** | openpyxl | 3.1+ | Archivos Excel |
| **Seguridad** | bcrypt | 4.0+ | Encriptación de passwords |
| **Testing** | pytest | 7.0+ | Suite de pruebas automatizadas |

## 📋 Requisitos del Sistema

### Requisitos Mínimos
- **Sistema Operativo:** Windows 10 (64-bit) o superior
- **Procesador:** Intel Core i3 o AMD equivalente
- **Memoria RAM:** 4 GB mínimo (8 GB recomendado)
- **Espacio en Disco:** 2 GB libres para instalación
- **Resolución:** 1366x768 mínimo (1920x1080 recomendado)
- **Conectividad:** Ethernet o Wi-Fi para actualizaciones

### Requisitos de Software
- **Python:** 3.8 o superior
- **pip:** Gestor de paquetes Python actualizado
- **Git:** Para control de versiones (opcional)

## 🔧 Instalación y Configuración

### Paso 1: Preparar el Entorno

```bash
# Verificar versión de Python
python --version

# Si no tienes Python 3.8+, descárgalo desde python.org
# https://www.python.org/downloads/
```

### Paso 2: Clonar o Descargar el Proyecto

```bash
# Opción 1: Clonar con Git
git clone [URL_DEL_REPOSITORIO]
cd inventario_app2

# Opción 2: Descargar ZIP y extraer
# Descargar desde el repositorio y extraer en carpeta deseada
```

### Paso 3: Crear Entorno Virtual

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate

# En Linux/Mac:
source venv/bin/activate
```

### Paso 4: Instalar Dependencias

```bash
# Instalar dependencias de producción
pip install -r requirements.txt

# Verificar instalación
pip list
```

### Paso 5: Configurar Base de Datos

```bash
# Ejecutar script de inicialización
python src/db/initialize_database.py

# Verificar creación de base de datos
# Debe crearse el archivo inventario.db
```

### Paso 6: Configurar Variables de Entorno

```bash
# Copiar archivo de configuración
cp .env.example .env

# Editar .env con tus configuraciones
# Variables principales:
# DB_PATH=inventario.db
# LOG_LEVEL=INFO
# BACKUP_INTERVAL=daily
```

### Paso 7: Ejecutar la Aplicación

```bash
# Ejecutar aplicación principal
python main.py

# O usar script de conveniencia
_run.bat    # En Windows
./run.sh    # En Linux/Mac
```

## 🎯 Primeros Pasos

### Login Inicial
Al ejecutar la aplicación por primera vez:

```
Usuario: admin
Password: admin123
```

**⚠️ IMPORTANTE:** Cambiar credenciales por defecto inmediatamente después del primer login.

### Configuración Inicial

1. **Configurar Empresa**
   - Ir a: `Configuración > Datos de Empresa`
   - Completar información fiscal y de contacto

2. **Crear Categorías**
   - Ir a: `Inventario > Categorías`
   - Crear categorías principales: Material, Servicio, etc.

3. **Configurar Impuestos**
   - Ir a: `Configuración > Impuestos`
   - Configurar tasas de IVA según normativa local

4. **Crear Usuarios**
   - Ir a: `Administración > Usuarios`
   - Crear usuarios vendedor con permisos específicos

### Flujo Básico de Trabajo

1. **Agregar Productos**
   ```
   Inventario > Productos > Nuevo Producto
   - Completar información básica
   - Asignar categoría
   - Definir precios de compra y venta
   - Establecer stock mínimo/máximo
   ```

2. **Registrar Entrada de Inventario**
   ```
   Inventario > Movimientos > Nueva Entrada
   - Seleccionar productos
   - Ingresar cantidad recibida
   - Confirmar movimiento
   ```

3. **Procesar Venta**
   ```
   Ventas > Nueva Venta
   - Agregar productos al carrito
   - Seleccionar cliente (opcional)
   - Procesar pago
   - Imprimir factura
   ```

4. **Generar Reportes**
   ```
   Reportes > [Tipo de Reporte]
   - Seleccionar período
   - Configurar filtros
   - Exportar en formato deseado
   ```

## 🔒 Usuarios y Permisos

### Rol Administrador
- **Acceso completo** a todas las funcionalidades
- Gestión de usuarios y configuración del sistema
- Acceso a reportes financieros y de auditoría
- Configuración de parámetros empresariales

### Rol Vendedor
- **Gestión de ventas** y procesamiento de pagos
- **Consulta de inventario** y stock disponible
- **Reportes básicos** de ventas propias
- **Sin acceso** a configuración crítica del sistema

### Seguridad
- Passwords encriptados con bcrypt y salt
- Sesiones con timeout automático
- Logs de auditoría para todas las transacciones
- Respaldos automáticos de base de datos

## 📊 Funcionalidades Avanzadas

### Códigos de Barras
```python
# Generar código de barras para producto
from src.services.barcode_service import BarcodeService

barcode_service = BarcodeService()
barcode_service.generate_barcode(product_id=123)
```

### Exportación de Reportes
```python
# Exportar reporte a Excel
from src.services.report_service import ReportService

report_service = ReportService()
report_service.export_sales_report(
    start_date="2025-01-01",
    end_date="2025-01-31",
    format="excel"
)
```

### API REST (Opcional)
```bash
# Iniciar servidor API (si está habilitado)
python src/api/main.py

# Documentación API disponible en:
# http://localhost:8000/docs
```

## 🧪 Testing y Calidad

### Ejecutar Suite de Tests

```bash
# Ejecutar todos los tests
pytest

# Ejecutar tests con cobertura
pytest --cov=src --cov-report=html

# Ejecutar tests específicos
pytest tests/test_basic_functionality.py

# Ver reporte de cobertura
# Abrir htmlcov/index.html en navegador
```

### Validación de Calidad

```bash
# Verificar estilo de código
flake8 src/

# Formatear código automáticamente
black src/

# Ordenar imports
isort src/

# Validar types (si configurado)
mypy src/
```

## 🚨 Troubleshooting Común

### Problema: Error al iniciar la aplicación

**Error:** `ModuleNotFoundError: No module named 'PyQt6'`

**Solución:**
```bash
# Verificar entorno virtual activado
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Reinstalar dependencias
pip install --upgrade -r requirements.txt
```

### Problema: Base de datos corrupta

**Error:** `Database is locked` o errores SQLite

**Solución:**
```bash
# Hacer backup de datos
cp inventario.db inventario_backup.db

# Reinicializar base de datos
python src/db/initialize_database.py --force

# Restaurar desde backup si es necesario
python src/db/restore_database.py inventario_backup.db
```

### Problema: Error de autenticación

**Error:** `Authentication failed` con credenciales correctas

**Solución:**
```bash
# Resetear password de admin
python src/scripts/reset_admin_password.py

# Verificar integridad de usuarios
python src/scripts/verify_users.py
```

### Problema: Interfaz no responde

**Error:** Aplicación se congela o no responde

**Solución:**
```bash
# Verificar logs de error
cat logs/application.log

# Ejecutar en modo debug
python main.py --debug

# Limpiar archivos temporales
rm -rf temp/*
rm -rf __pycache__/
```

### Problema: Reportes no se generan

**Error:** `PDF generation failed` o archivos vacíos

**Solución:**
```bash
# Verificar permisos de escritura
ls -la reports/

# Verificar dependencias de reportes
pip install --upgrade reportlab openpyxl

# Probar generación manual
python src/scripts/test_reports.py
```

## 📁 Estructura del Proyecto

```
inventario_app2/
├── src/                      # Código fuente principal
│   ├── db/                   # Capa de datos
│   ├── services/             # Servicios de negocio
│   ├── ui/                   # Interfaz de usuario
│   ├── models/               # Modelos de datos
│   ├── reports/              # Sistema de reportes
│   └── utils/                # Utilidades generales
├── tests/                    # Suite de pruebas
├── docs/                     # Documentación técnica
├── logs/                     # Archivos de log
├── backups/                  # Respaldos automáticos
├── data/                     # Datos del sistema
├── config/                   # Archivos de configuración
├── requirements.txt          # Dependencias Python
├── .env                      # Variables de entorno
├── pytest.ini               # Configuración tests
└── main.py                   # Punto de entrada
```

## 🔄 Respaldos y Mantenimiento

### Respaldos Automáticos
- **Frecuencia:** Diario a las 2:00 AM
- **Ubicación:** `backups/` con timestamp
- **Retención:** 30 días automático
- **Formato:** SQLite comprimido + logs

### Respaldo Manual
```bash
# Crear respaldo inmediato
python src/scripts/create_backup.py

# Restaurar desde respaldo específico
python src/scripts/restore_backup.py backup_2025-07-21.zip
```

### Mantenimiento de Base de Datos
```bash
# Optimizar base de datos
python src/scripts/optimize_database.py

# Verificar integridad
python src/scripts/check_integrity.py

# Limpiar logs antiguos
python src/scripts/cleanup_logs.py --days=30
```

## 📈 Performance y Escalabilidad

### Métricas de Performance
- **Transacciones:** 1000+ por día soportadas
- **Usuarios concurrentes:** Hasta 20 usuarios
- **Tiempo de respuesta:** < 2 segundos promedio
- **Base de datos:** Hasta 100,000 productos
- **Reportes:** Generación < 30 segundos

### Optimizaciones
- Índices automáticos en consultas frecuentes
- Cache en memoria para datos frecuentes
- Paginación en listados grandes
- Compresión automática de respaldos
- Limpieza automática de archivos temporales

## 🤝 Soporte y Contacto

### Soporte Técnico
- **Email:** soporte.inventario@copypoint.com
- **Teléfono:** +507 XXX-XXXX
- **Horario:** Lunes a Viernes, 8:00 AM - 5:00 PM

### Reportar Bugs
1. Verificar en troubleshooting si hay solución conocida
2. Revisar logs en `logs/application.log`
3. Crear reporte con:
   - Descripción del problema
   - Pasos para reproducir
   - Logs relevantes
   - Versión del sistema

### Solicitar Funcionalidades
- Enviar propuesta detallada por email
- Incluir justificación empresarial
- Especificar urgencia y criticidad
- Proporcionar casos de uso específicos

## 📜 Licencia y Copyright

```
Copyright (c) 2025 Copy Point S.A.
Todos los derechos reservados.

Este software es propiedad de Copy Point S.A. y está protegido por 
leyes de derechos de autor. Su uso está restringido al personal 
autorizado de la empresa.

Prohibida la distribución, modificación o uso comercial sin 
autorización expresa por escrito.
```

## 🔄 Historial de Versiones

### v1.0.4 (2025-07-21) - ACTUAL
- ✅ Corrección bugs críticos de autenticación
- ✅ Implementación suite testing funcional básico
- ✅ Mejoras en documentación técnica
- ✅ Optimizaciones de performance

### v1.0.3 (2025-07-19)
- ✅ Refactorización sistema de passwords
- ✅ Integración completa de servicios
- ✅ Documentación arquitectura Clean

### v1.0.2 (2025-07-19)
- ✅ Implementación backlog completo de funcionalidades
- ✅ Metodología TDD establecida
- ✅ Framework de testing implementado

### v1.0.1 (2025-07-19)
- ✅ Completar instrucciones Claude AI v2.0
- ✅ Optimización flujo de desarrollo
- ✅ Validación estándares de calidad

### v1.0.0 (2025-07-17)
- ✅ Lanzamiento inicial del sistema
- ✅ Funcionalidades core implementadas
- ✅ Documentación técnica completa
- ✅ Políticas de seguridad empresariales

---

**Sistema de Inventario Copy Point S.A.**  
*Desarrollado con tecnología Python + PyQt6*  
*Última actualización: 2025-07-21*