Para poner en marcha en Windows 10/11 tu aplicación Python tal como está en el `requirements.txt`, necesitas instalar previamente estas **dependencias de sistema**:

1. **Python 3.9+**

   * **Qué**: Intérprete de Python con `pip`, `venv`, módulo `sqlite3` y Tcl/Tk incluido (para `tkinter`/`tkcalendar`).
   * **Cómo**:

     1. Ve a [https://www.python.org/downloads/windows/](https://www.python.org/downloads/windows/)
     2. Descarga el instalador ejecutable (por ejemplo “Windows installer (64-bit)”).
     3. Durante la instalación, marca **Add Python 3.x to PATH** y asegúrate de que “Tcl/Tk and IDLE” esté seleccionado.
     4. Al terminar, verifica en PowerShell:

        ```powershell
        python --version
        pip --version
        python -m tkinter  # debe abrirse una ventana de prueba
        ```

2. **Microsoft Visual C++ Build Tools**

   * **Qué**: Compilador C/C++ y cabeceras necesarias para construir extensiones nativas (bcrypt, psutil, etc.).
   * **Cómo**:

     1. Accede a [https://visualstudio.microsoft.com/visual-cpp-build-tools/](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
     2. Descarga y ejecuta el instalador “Build Tools for Visual Studio”.
     3. En “Workloads”, selecciona **Desktop development with C++**.
     4. Completa la instalación (aprox. 2 GB).

3. **Biblioteca ZBar** (para que `pyzbar` decodifique códigos de barras)

   * **Qué**: Ejecutables y DLL de ZBar que proveen la funcionalidad de escaneo.
   * **Cómo**:

     1. Descarga el instalador Windows de ZBar (versión 0.10) desde SourceForge:
        [https://sourceforge.net/projects/zbar/files/zbar/0.10/zbar-0.10-setup.exe](https://sourceforge.net/projects/zbar/files/zbar/0.10/zbar-0.10-setup.exe)
     2. Ejecuta el instalador (por defecto instala en `C:\Program Files (x86)\ZBar`).
     3. Agrega `C:\Program Files (x86)\ZBar\bin` al **PATH** de Windows:

        * Panel de Control → Sistema → Configuración avanzada → Variables de entorno → PATH → Editar → Nuevo → pega la ruta.
     4. Abre PowerShell y ejecuta `zbarimg --version` para confirmar que responde.

4. **(Opcional) Herramientas de línea de comandos de Windows**

   * **Qué**: PowerShell 7+ o Windows Terminal para comandos avanzados (no es imprescindible, pero recomendado).
   * **Cómo**: Descárgalos desde Microsoft Store o [https://github.com/microsoft/terminal/releases](https://github.com/microsoft/terminal/releases).

---

**Flujo de instalación en limpia**:

```powershell
# 1. Instalas Python y agregas al PATH
# 2. Instalación de Visual C++ Build Tools
# 3. Instalación de ZBar y ajuste de PATH
# 4. Creas entorno virtual y pip-install:

python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

Con estos pasos garantizas que todas las extensiones en C se compilen correctamente, que `tkinter` funcione para tu GUI y que `pyzbar` tenga la biblioteca nativa necesaria para decodificar códigos de barras.
