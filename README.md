# EnCore · Control de Materiales

Aplicación de escritorio para el control y registro de materiales por empleado en un taller/planta. Desarrollada en Python con **customtkinter** (UI moderna y oscura), **matplotlib** (gráficas) y **SQLite** (persistencia local).

La UI está pensada para pantallas de tipo quiosco o estaciones fijas: abre maximizada cubriendo toda la pantalla, con escalado automático según la resolución del monitor.

---

## Características

- **Autenticación** con usuario y contraseña (hash PBKDF2). En el primer arranque se crea la cuenta de administrador.
- **Dashboard** con indicadores (KPIs) y gráficas:
  - Piezas por día
  - Piezas por material
  - Distribución por turno
  - Top empleados
  - Filtros por turno, material y periodo
- **Registros** (vista única que integra captura + historial):
  - Formulario paso a paso: número de empleado → material → cantidad
  - Historial con filtros por turno, material y periodo
  - Eliminar registros (solo administrador)
  - Exportar toda la información a Excel
- **Empleados**: alta, verificación de disponibilidad, edición y baja.
- **Materiales**: catálogo con nombre único, renombrado (actualiza el historial) y eliminación.
- **Usuarios** (solo administrador): crear y eliminar accesos.
- **Exportación a Excel**: un libro `.xlsx` con tres hojas:
  - `Reporte` (ID, empleado, nombre, turno, material, cantidad, fecha)
  - `Empleados`
  - `Materiales`
- **Adaptación a cualquier pantalla**: escalado automático tomando 1920×1080 como base; arranca en ventana maximizada y **F11** alterna a pantalla completa pura.

---

## Requisitos

- Python 3.10 o superior (probado con 3.12)
- Windows (el escalado y el maximizado están optimizados para Windows; la app es multiplataforma con soporte parcial).

## Instalación

```powershell
pip install -r requirements.txt
```

Dependencias: `customtkinter`, `matplotlib`, `pillow`, `openpyxl`.

## Ejecución

```powershell
python main.py
```

> En el **primer arranque** la app te pide crear el usuario administrador (usuario de 3+ caracteres y contraseña de 6+). Esa cuenta queda registrada localmente en `encore.db`.

---

## Uso

1. **Inicia sesión** con tu usuario.
2. **Registros** — captura piezas:
   - Paso 1: escribe el número de empleado y presiona **Validar**.
   - Paso 2: elige el material.
   - Paso 3: escribe la cantidad y presiona **Guardar registro**.
   - Debajo verás el historial; usa los filtros para acotar la búsqueda.
3. **Empleados** — agrega personal indicando número, nombre y turno (A/B/C). Los números deben ser únicos.
4. **Materiales** — administra el catálogo; los nombres no pueden repetirse.
5. **Usuarios** — (admin) crea o elimina accesos.
6. **Exportar a Excel** — botón en la vista **Registros**; guarda un `.xlsx` con las tres hojas mencionadas.
7. **Eliminar registros** — selecciona una fila del historial y presiona **Eliminar registro** (solo admin; el registro se borra de la base de datos).

### Teclado

| Atajo | Acción |
|-------|--------|
| `F11` | Alternar entre ventana maximizada y **full screen** |
| `Enter` | En los campos de número de empleado, dispara la validación/captura correspondiente |

---

## Estructura del proyecto

```
├── main.py          # Punto de entrada: ventana, login, navegación, full screen
├── views.py         # Vistas: Dashboard, Registros, Empleados, Materiales, Usuarios
├── database.py      # Capa de datos (SQLite): usuarios, empleados, materiales, reportes
├── exporter.py      # Exportación a Excel (3 hojas) con openpyxl
├── theme.py         # Paleta de colores, componentes y escalado automático (auto_scale)
├── requirements.txt
└── assets/
    ├── logo_light.png   # Logo usado en login y sidebar
    ├── favicon.png      # Ícono de la app (ventana y barra de tareas)
    ├── favicon.ico      # Versión .ico para el ícono de Windows
    └── logo.png
```

### Base de datos

Se genera automáticamente en `encore.db` (SQLite) junto al proyecto. Tablas:

- `usuarios` — `id`, `username`, `password` (hash), `is_admin`
- `empleados` — `id`, `nombre`, `turno` (A/B/C)
- `materiales` — `nombre` (único)
- `reporte` — `id`, `empleado`, `nombre`, `turno`, `material`, `cantidad`, `fecha`

Los borrados de empleados/materiales conservan el historial de registros.

---

## Notas técnicas

- **Escalado automático**: `theme.auto_scale()` (en `theme.py`) se ejecuta *antes* de crear la ventana: activa el modo DPI-aware del proceso, lee la resolución física con `GetSystemMetrics` y ajusta toda la UI respecto a una base de 1920×1080. En pantallas 4K todo crece y en pantallas pequeñas todo se reduce.
- **Maximizado al abrir**: la ventana se fuerza a `zoomed` tras mostrarse y se reaplica al restaurarse, para que siempre ocupe la pantalla.
- **Gráficas responsivas**: las figuras de matplotlib se redimensionan para llenar su tarjeta (`views.py: Chart._resize`).
- **Ícono**: `favicon.ico` se aplica con `iconbitmap()`, lo que evita que customtkinter lo sobrescriba con el suyo.
- **GIT**: `encore.db`, `__pycache__/` y `files.zip` están excluidos del repositorio (`.gitignore`).

## Problemas comunes

| Síntoma | Solución |
|---------|----------|
| La app no llena la pantalla al abrir | Ejecuta `python main.py` desde la carpeta del proyecto; usa `F11` para full screen puro |
| No arranca (falta `customtkinter`/`openpyxl`) | `pip install -r requirements.txt` |
| Error al exportar "el archivo está abierto" | Cierra el Excel que tiene abierto el `.xlsx` y vuelve a exportar |