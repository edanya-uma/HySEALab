# Biblioteca Epsilon - Visualización de Tsunami-HySEA

Herramienta interactiva para visualizar y analizar resultados de simulaciones de Tsunami-HySEA en formato NetCDF y otras utilidades.

## 📋 Contenido del Repositorio

- **epsilon.py**: Biblioteca principal con todas las funciones de visualización
- **Setup_HySEALab.ipynb**: 🎯 **Notebook de setup automático** (¡EJECUTA ESTO PRIMERO desde JupyterLab!)
- **setup_hysealab.sh**: Script bash de setup automático (alternativa desde terminal)
- **setup_hysealab.py**: Script Python de setup automático (alternativa desde Python)
- **Manual_Usuario_Epsilon.ipynb**: Tutorial interactivo y documentación completa
- **epsilon_config_example.py**: Plantilla de configuración para rutas personalizadas
- **SETUP_USUARIO.md**: Guía detallada de configuración para usuarios de HySEALab
- **README.md**: Este archivo

## 🚀 Inicio Rápido

### ⚠️ Para usuarios de HySEALab

**Lee primero:** [SETUP_USUARIO.md](SETUP_USUARIO.md) - Guía completa de configuración

**Opción 1: Setup desde Jupyter Notebook (RECOMENDADO para JupyterLab)** 🎯
1. Abre JupyterLab
2. Navega a `~/HySEALab/HySEALab-Library/`
3. Abre y ejecuta `Setup_HySEALab.ipynb`
4. Sigue las instrucciones en el notebook

**Opción 2: Setup desde terminal (si tienes acceso a terminal)** ⚡
```bash
cd ~/HySEALab/HySEALab-Library
bash setup_hysealab.sh
# O alternativamente:
python setup_hysealab.py
```

**Opción 3: Setup desde celda de notebook**
```python
# En cualquier notebook, ejecuta:
%run ~/HySEALab/HySEALab-Library/setup_hysealab.py
```

Cualquiera de estas opciones:
- Crea la estructura de directorios en tu home
- Copia el manual a tu carpeta personal
- Crea tu archivo de configuración personal

**Setup manual (si prefieres hacerlo a mano):**
1. **NO ejecutes notebooks desde esta carpeta** (HySEALab-Library)
2. Copia el manual: `cp Manual_Usuario_Epsilon.ipynb ~/proyecto_tsunami/`
3. Trabaja desde tu carpeta personal
4. Importa epsilon con `sys.path.insert(0, '~/HySEALab/HySEALab-Library')`

### Para otros usuarios

### 1. Clonar el repositorio

```bash
git clone git@github.com:JMGonvi/HySEALab-Library.git
cd HySEALab-Library
```

### 2. Instalar dependencias

**Opción recomendada con conda:**
```bash
conda create -n tsunami python=3.10
conda activate tsunami
conda install -c conda-forge numpy matplotlib ipywidgets netCDF4 xarray pyproj imageio gmt
pip install pygmt
```

**Opción con pip (sin PyGMT):**
```bash
pip install numpy matplotlib ipywidgets netCDF4 xarray pyproj imageio
```

### 3. Configurar rutas personalizadas

**En entorno HySEALab:**

El entorno HySEALab tiene una estructura específica donde cada usuario tiene:
- `~/HySEALab` → enlace a `/mnt/scratch/HySEALab` (carpeta compartida)
- Carpetas compartidas: `simulaciones/`, `mallados/`, `HySEALab-Library/`

Cada usuario debe configurar sus rutas según dónde tenga sus datos:

**Método 1: Configuración directa en el notebook**
```python
import epsilon

# Configurar rutas personalizadas
epsilon.configure_paths(
    simulaciones="~/HySEALab/simulaciones",  # o tu ruta personalizada
    mallados="~/HySEALab/mallados",
    plots="~/mis_resultados/plots"
)

# Ver configuración actual
epsilon.show_configuration()
```

**Método 2: Usar archivo de configuración (recomendado)**
```bash
# Copiar el ejemplo a tu directorio personal
cp epsilon_config_example.py ~/mi_proyecto/epsilon_config.py
# Editar con tus rutas
nano ~/mi_proyecto/epsilon_config.py
```

Luego en tu notebook:
```python
import epsilon
import sys
sys.path.insert(0, '~/mi_proyecto')
import epsilon_config

epsilon.configure_paths(**epsilon_config.PATHS)
```

**Fuera del entorno HySEALab:**

Si no configuras nada, epsilon usa rutas relativas por defecto:
- `./simulaciones`
- `./mallados`
- `./plots`

### 4. Preparar estructura de directorios (opcional)

```bash
mkdir -p simulaciones plots
```

### 5. Abrir el notebook

```bash
jupyter notebook Manual_Usuario_Epsilon.ipynb
```

## ⚠️ Solución de Problemas

### Error: "epsilon.py contiene JSON en lugar de código Python"

**Síntoma:** Al importar epsilon obtienes un error como:
```
File epsilon.py:1
    {
    ^
SyntaxError: invalid syntax
```

**Causa:** El archivo epsilon.py fue guardado incorrectamente como JSON (contenido de un notebook).

**Solución:**
1. Verifica que descargaste el archivo correcto del repositorio
2. Asegúrate de descargar el archivo RAW desde GitHub
3. El archivo debe comenzar con `import os` o similar, NO con `{`

Para verificar en terminal:
```bash
head -5 epsilon.py
# Debe mostrar código Python, no JSON
```

### Error: "ModuleNotFoundError: No module named 'pygmt'"

**Solución:** PyGMT es opcional. Epsilon funciona sin él, solo no mostrará mapas base.

Para instalar PyGMT completo:
```bash
conda install -c conda-forge gmt pygmt
```

### Error: "GMTCLibNotFoundError"

**Solución:** GMT no está instalado en el sistema.

- macOS: `brew install gmt`
- Linux: `sudo apt-get install gmt gmt-dcw gmt-gshhg`
- Windows: Usar conda: `conda install -c conda-forge gmt`

## 📖 Documentación

Consulta el notebook `Manual_Usuario_Epsilon.ipynb` para:
- Tutorial completo paso a paso
- Ejemplos de uso
- Referencia de todas las funciones
- Casos de uso avanzados

## 🏢 Entorno HySEALab (Universidad de Málaga)

### Estructura del sistema

El cluster de HySEALab tiene una estructura específica:

```
/mnt/scratch/HySEALab/              (carpeta compartida)
├── HySEALab-Library/               (repositorio GitHub - código compartido)
│   ├── epsilon.py
│   ├── Manual_Usuario_Epsilon.ipynb
│   └── README.md
├── simulaciones/                    (simulaciones compartidas)
├── mallados/                        (mallados compartidos)
└── ...

/home/usuario/                       (home de cada usuario)
├── HySEALab -> /mnt/scratch/HySEALab  (enlace simbólico)
├── mis_simulaciones/                (datos personales del usuario)
└── resultados/                      (resultados personales)
```

### Uso recomendado en HySEALab

1. **Importar epsilon desde la carpeta compartida:**
```python
import sys
sys.path.insert(0, '~/HySEALab/HySEALab-Library')
import epsilon
```

2. **Configurar rutas según tus necesidades:**
```python
# Opción A: Usar carpetas compartidas
epsilon.configure_paths(
    simulaciones="~/HySEALab/simulaciones",
    mallados="~/HySEALab/mallados",
    plots="~/resultados/plots"
)

# Opción B: Usar tus carpetas personales
epsilon.configure_paths(
    simulaciones="~/mis_simulaciones",
    mallados="~/mis_mallados",
    plots="~/resultados/plots"
)

# Opción C: Mezclar carpetas compartidas y personales
epsilon.configure_paths(
    simulaciones="~/HySEALab/simulaciones",  # compartidas
    plots="~/mi_carpeta/graficos"             # personales
)
```

3. **Verificar configuración:**
```python
epsilon.show_configuration()
```

### Ventajas de este enfoque

- ✅ **Código compartido**: Todos usan la misma versión de epsilon.py
- ✅ **Datos flexibles**: Cada usuario decide dónde tiene sus simulaciones
- ✅ **Sin conflictos**: Los resultados se guardan en carpetas personales
- ✅ **Fácil actualización**: `git pull` en HySEALab-Library actualiza epsilon para todos

## 🤝 Contribuir

Si encuentras errores o tienes sugerencias, por favor abre un issue en GitHub.

## 📧 Contacto

HySEALab - Universidad de Málaga

## 📄 Licencia

[Especificar licencia]
