# Guía de Usuario Básica - Sistema de Inventario Copy Point S.A.

![Guía Usuario](https://img.shields.io/badge/Guía-Usuario_Básica-blue)
![Versión](https://img.shields.io/badge/Versión-1.0.4-green)
![Nivel](https://img.shields.io/badge/Nivel-Básico-yellow)

Esta guía proporciona instrucciones paso a paso para las operaciones más comunes del Sistema de Inventario Copy Point S.A. Está diseñada para usuarios que necesitan realizar tareas básicas sin conocimiento técnico profundo.

## 📋 Tabla de Contenidos

1. [Inicio de Sesión](#inicio-de-sesión)
2. [Panel Principal](#panel-principal)
3. [Gestión de Productos](#gestión-de-productos)
4. [Control de Inventario](#control-de-inventario)
5. [Procesamiento de Ventas](#procesamiento-de-ventas)
6. [Generación de Reportes](#generación-de-reportes)
7. [Configuración Básica](#configuración-básica)
8. [Resolución de Problemas Comunes](#resolución-de-problemas-comunes)

---

## 🔐 Inicio de Sesión

### Acceder al Sistema

1. **Ejecutar la aplicación:**
   - Hacer doble clic en el icono del sistema
   - O ejecutar `main.py` si tienes acceso técnico

2. **Ingresar credenciales:**
   ```
   👤 Usuario: [tu_usuario]
   🔑 Password: [tu_contraseña]
   ```

3. **Roles disponibles:**
   - **Administrador:** Acceso completo al sistema
   - **Vendedor:** Acceso limitado a ventas e inventario

### Primer Login (Solo Administrador)

Si es tu primera vez:
```
👤 Usuario: admin
🔑 Password: admin123
```

**⚠️ IMPORTANTE:** Cambiar estas credenciales inmediatamente después del primer acceso.

### Cambiar Contraseña

1. Ir a `Configuración → Usuarios`
2. Seleccionar tu usuario
3. Hacer clic en "Cambiar Contraseña"
4. Ingresar contraseña actual y nueva contraseña
5. Confirmar cambios

---

## 🏠 Panel Principal

### Navegación Básica

El panel principal está dividido en secciones:

```
┌─────────────────────────────────────────┐
│ [Logo] Sistema Inventario    [Usuario] │
├─────────────────────────────────────────┤
│ 📦 INVENTARIO │ 💰 VENTAS │ 📊 REPORTES │
├─────────────────────────────────────────┤
│                                         │
│         ÁREA DE TRABAJO                 │
│                                         │
├─────────────────────────────────────────┤
│ Estado: Conectado │ Hora: [actual]     │
└─────────────────────────────────────────┘
```

### Menús Principales

#### 📦 INVENTARIO
- **Productos:** Gestionar catálogo de productos
- **Categorías:** Organizar productos por tipo
- **Movimientos:** Registrar entradas y salidas
- **Stock:** Consultar niveles de inventario

#### 💰 VENTAS  
- **Nueva Venta:** Procesar venta de productos
- **Historial:** Consultar ventas anteriores
- **Clientes:** Gestionar base de clientes
- **Devoluciones:** Procesar devoluciones

#### 📊 REPORTES
- **Ventas:** Reportes de desempeño de ventas
- **Inventario:** Estado y valorización del stock
- **Financieros:** Análisis de rentabilidad
- **Exportar:** Generar archivos PDF/Excel

#### ⚙️ CONFIGURACIÓN (Solo Admin)
- **Usuarios:** Gestionar accesos al sistema
- **Empresa:** Datos fiscales y contacto
- **Impuestos:** Configurar tasas de IVA
- **Respaldos:** Gestionar copias de seguridad

---

## 📦 Gestión de Productos

### Crear Nuevo Producto

1. **Acceder al módulo:**
   - Ir a `Inventario → Productos`
   - Hacer clic en "➕ Nuevo Producto"

2. **Completar información básica:**
   ```
   📝 Nombre: [nombre del producto]
   📂 Categoría: [seleccionar de lista]
   📊 Stock Inicial: [cantidad numérica]
   💰 Precio Compra: [precio sin impuestos]
   💰 Precio Venta: [precio final al cliente]
   📈 Impuesto (%): [tasa de IVA aplicable]
   ```

3. **Información adicional (opcional):**
   ```
   📄 Descripción: [detalles del producto]
   📦 Stock Mínimo: [alerta de reposición]
   📦 Stock Máximo: [límite de inventario]
   🏷️ Código Barras: [código EAN/UPC]
   ```

4. **Guardar producto:**
   - Hacer clic en "💾 Guardar"
   - Verificar mensaje de confirmación

### Buscar y Editar Productos

1. **Buscar producto:**
   - En la lista de productos, usar el campo de búsqueda
   - Filtros disponibles: Nombre, Categoría, Estado

2. **Editar producto:**
   - Hacer doble clic en el producto deseado
   - O seleccionar y hacer clic en "✏️ Editar"

3. **Modificar información:**
   - Cambiar los campos necesarios
   - Hacer clic en "💾 Actualizar"

### Activar/Desactivar Productos

1. **Desactivar producto:**
   - Seleccionar producto en la lista
   - Hacer clic en "❌ Desactivar"
   - Confirmar acción

2. **Reactivar producto:**
   - Cambiar filtro a "Mostrar inactivos"
   - Seleccionar producto desactivado
   - Hacer clic en "✅ Activar"

---

## 📊 Control de Inventario

### Consultar Stock Actual

1. **Ver inventario general:**
   - Ir a `Inventario → Stock`
   - Revisar lista de productos con cantidades

2. **Filtros útiles:**
   - **Stock Bajo:** Productos cerca del mínimo
   - **Sin Stock:** Productos agotados
   - **Por Categoría:** Filtrar por tipo de producto

### Registrar Entrada de Mercancía

1. **Acceder a movimientos:**
   - Ir a `Inventario → Movimientos`
   - Hacer clic en "📥 Nueva Entrada"

2. **Seleccionar productos:**
   - Buscar producto por nombre o código
   - Agregar a la lista de entrada

3. **Ingresar cantidades:**
   ```
   📦 Producto: [nombre del producto]
   🔢 Cantidad: [cantidad recibida]
   💰 Costo: [precio de compra actual]
   📝 Observaciones: [nota sobre la entrada]
   ```

4. **Finalizar entrada:**
   - Revisar información
   - Hacer clic en "✅ Confirmar Entrada"
   - El stock se actualiza automáticamente

### Registrar Ajuste de Inventario

1. **Cuando usar ajustes:**
   - Diferencias en conteo físico
   - Productos dañados o vencidos
   - Correcciones de errores

2. **Proceso de ajuste:**
   - Ir a `Inventario → Movimientos`
   - Hacer clic en "⚖️ Ajuste de Stock"
   - Seleccionar producto
   - Ingresar diferencia (positiva o negativa)
   - Especificar motivo del ajuste
   - Confirmar operación

---

## 💰 Procesamiento de Ventas

### Realizar Nueva Venta

1. **Iniciar venta:**
   - Ir a `Ventas → Nueva Venta`
   - Se abre el punto de venta

2. **Agregar productos:**
   ```
   Método 1 - Búsqueda manual:
   📝 Escribir nombre del producto
   🔍 Seleccionar de la lista
   🔢 Ingresar cantidad
   ➕ Agregar al carrito
   
   Método 2 - Código de barras:
   📷 Escanear código de barras
   🔢 Confirmar cantidad
   ✅ Se agrega automáticamente
   ```

3. **Revisar carrito:**
   ```
   📦 Producto     │ 🔢 Cant │ 💰 Precio │ 💰 Total
   ────────────────┼──────────┼───────────┼──────────
   Producto A      │    2     │  $15.00   │  $30.00
   Producto B      │    1     │  $25.00   │  $25.00
   ────────────────┼──────────┼───────────┼──────────
                   │ Subtotal │           │  $55.00
                   │ IVA (7%) │           │   $3.85
                   │ TOTAL    │           │  $58.85
   ```

4. **Seleccionar cliente (opcional):**
   - Hacer clic en "👤 Cliente"
   - Buscar cliente existente o crear nuevo
   - Asociar a la venta

5. **Procesar pago:**
   ```
   💰 Método de Pago:
   ▶️ Efectivo    ▷ Tarjeta    ▷ Crédito
   
   💵 Total a pagar: $58.85
   💵 Recibido:      $60.00
   💵 Cambio:        $1.15
   ```

6. **Finalizar venta:**
   - Hacer clic en "✅ Procesar Venta"
   - Imprimir factura si es necesario
   - El stock se actualiza automáticamente

### Consultar Historial de Ventas

1. **Acceder al historial:**
   - Ir a `Ventas → Historial`

2. **Filtros disponibles:**
   - **Por fecha:** Desde/hasta
   - **Por vendedor:** Usuario que procesó
   - **Por cliente:** Ventas a cliente específico
   - **Por monto:** Rango de valores

3. **Ver detalles de venta:**
   - Hacer doble clic en la venta
   - Ver productos vendidos, precios y totales

### Procesar Devolución

1. **Acceder a devoluciones:**
   - Ir a `Ventas → Devoluciones`
   - Hacer clic en "↩️ Nueva Devolución"

2. **Buscar venta original:**
   - Ingresar número de venta
   - O buscar por cliente/fecha

3. **Seleccionar productos a devolver:**
   - Marcar productos de la venta
   - Ingresar cantidad a devolver
   - Especificar motivo

4. **Finalizar devolución:**
   - Confirmar devolución
   - El stock se ajusta automáticamente
   - Se genera nota de crédito

---

## 📊 Generación de Reportes

### Reportes de Ventas

1. **Reporte de ventas por período:**
   - Ir a `Reportes → Ventas`
   - Seleccionar `Ventas por Período`
   - Configurar fechas
   - Elegir formato (PDF/Excel)
   - Generar reporte

2. **Reporte de productos más vendidos:**
   - Seleccionar `Productos Más Vendidos`
   - Configurar período
   - Especificar top N productos
   - Generar reporte

### Reportes de Inventario

1. **Estado actual del stock:**
   - Ir a `Reportes → Inventario`
   - Seleccionar `Stock Actual`
   - Filtrar por categoría si es necesario
   - Generar reporte

2. **Productos con stock bajo:**
   - Seleccionar `Stock Bajo`
   - Sistema muestra automáticamente productos bajo mínimo
   - Generar reporte de reposición

### Exportar Reportes

1. **Formatos disponibles:**
   - **PDF:** Para impresión y presentación
   - **Excel:** Para análisis y cálculos
   - **CSV:** Para importar a otros sistemas

2. **Proceso de exportación:**
   - Configurar reporte deseado
   - Seleccionar formato en "📤 Exportar"
   - Elegir ubicación de guardado
   - Abrir archivo generado

---

## ⚙️ Configuración Básica

### Configurar Datos de la Empresa

1. **Acceder a configuración:**
   - Ir a `Configuración → Empresa`

2. **Completar información:**
   ```
   🏢 Razón Social: [nombre legal de la empresa]
   📄 RUC/NIT: [número de identificación fiscal]
   📍 Dirección: [dirección completa]
   📞 Teléfono: [número de contacto]
   📧 Email: [correo empresarial]
   ```

3. **Información fiscal:**
   ```
   💰 Régimen Fiscal: [régimen aplicable]
   📈 IVA por Defecto: [tasa estándar]
   💵 Moneda: [moneda local]
   ```

### Gestionar Usuarios

1. **Crear nuevo usuario:**
   - Ir a `Configuración → Usuarios`
   - Hacer clic en "➕ Nuevo Usuario"

2. **Información del usuario:**
   ```
   👤 Nombre: [nombre completo]
   📧 Usuario: [nombre de usuario único]
   🔑 Contraseña: [contraseña segura]
   🎭 Rol: [Administrador/Vendedor]
   ✅ Activo: [habilitado/deshabilitado]
   ```

3. **Permisos por rol:**
   - **Administrador:** Acceso completo
   - **Vendedor:** Solo ventas e inventario básico

---

## 🚨 Resolución de Problemas Comunes

### Problemas de Login

**❌ Error: "Usuario o contraseña incorrectos"**

**Soluciones:**
1. Verificar que CAPS LOCK esté desactivado
2. Confirmar usuario y contraseña con administrador
3. Intentar resetear contraseña si eres administrador

**❌ Error: "No se puede conectar al sistema"**

**Soluciones:**
1. Cerrar y volver a abrir la aplicación
2. Verificar que el archivo de base de datos no esté corrupto
3. Contactar soporte técnico

### Problemas con Productos

**❌ Error: "No se puede agregar producto"**

**Soluciones:**
1. Verificar que todos los campos obligatorios estén completos
2. Confirmar que el nombre del producto no existe ya
3. Verificar que la categoría esté seleccionada

**❌ Error: "Producto no encontrado en venta"**

**Soluciones:**
1. Verificar que el producto esté activo
2. Confirmar que hay stock disponible
3. Revisar ortografía en la búsqueda

### Problemas con Ventas

**❌ Error: "Stock insuficiente"**

**Soluciones:**
1. Verificar stock actual del producto
2. Reducir cantidad en la venta
3. Registrar entrada de mercancía si hay productos disponibles

**❌ Error: "No se puede procesar venta"**

**Soluciones:**
1. Verificar que hay al menos un producto en el carrito
2. Confirmar método de pago seleccionado
3. Verificar que el monto recibido sea suficiente

### Problemas con Reportes

**❌ Error: "No se puede generar reporte"**

**Soluciones:**
1. Verificar que las fechas sean válidas
2. Confirmar que hay datos en el período seleccionado
3. Verificar permisos de escritura en la carpeta de destino

**❌ Error: "Archivo no se puede abrir"**

**Soluciones:**
1. Verificar que tienes el software apropiado (PDF/Excel)
2. Cerrar el archivo si ya está abierto
3. Verificar espacio disponible en disco

### Problemas de Rendimiento

**❌ Sistema lento o no responde**

**Soluciones:**
1. Cerrar otras aplicaciones para liberar memoria
2. Reiniciar la aplicación
3. Verificar espacio disponible en disco duro
4. Contactar soporte para optimización de base de datos

---

## 📞 Contacto y Soporte

### Soporte Técnico Inmediato

```
📧 Email: soporte.inventario@copypoint.com
📞 Teléfono: +507 XXX-XXXX
🕒 Horario: Lunes a Viernes, 8:00 AM - 5:00 PM
```

### Antes de Contactar Soporte

1. **Anotar el error exacto** que aparece en pantalla
2. **Documentar los pasos** que causaron el problema
3. **Verificar** si el problema ocurre consistentemente
4. **Revisar** esta guía para soluciones comunes

### Información a Proporcionar

Cuando contactes soporte, ten lista esta información:

```
🖥️ Versión del sistema: [visible en ventana principal]
👤 Usuario afectado: [nombre de usuario]
📅 Fecha y hora del problema: [cuando ocurrió]
🔄 Pasos para reproducir: [secuencia de acciones]
📄 Mensaje de error: [texto exacto del error]
💻 Sistema operativo: [Windows 10/11]
```

### Capacitación Adicional

Si necesitas capacitación adicional:

- **Capacitación grupal:** Disponible para equipos de 3+ personas
- **Capacitación individual:** Sesiones personalizadas de 1-2 horas
- **Manuales avanzados:** Documentación detallada por módulo
- **Videos tutoriales:** Disponibles en plataforma interna

---

## 📚 Recursos Adicionales

### Documentación Técnica

- **Manual de Administrador:** Para configuraciones avanzadas
- **Guía de Respaldos:** Procedimientos de backup y restauración
- **Manual de Troubleshooting:** Resolución de problemas técnicos

### Atajos de Teclado

```
Ctrl + N    → Nueva venta
Ctrl + S    → Guardar/Confirmar
Ctrl + F    → Buscar
Ctrl + P    → Imprimir
F1          → Ayuda contextual
F5          → Actualizar pantalla
ESC         → Cancelar operación actual
```

### Mejores Prácticas

1. **Realizar respaldos regulares** de la información
2. **Mantener actualizado** el catálogo de productos
3. **Revisar stock** semanalmente para reposiciones
4. **Capacitar** a todos los usuarios en procedimientos básicos
5. **Documentar** cualquier proceso especial de tu empresa

---

**© 2025 Copy Point S.A. - Guía de Usuario Básica v1.0.4**  
*Última actualización: 2025-07-21*  
*Para consultas técnicas: soporte.inventario@copypoint.com*