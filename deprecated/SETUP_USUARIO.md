# Guía de Configuración para Usuarios de HySEALab

## 📂 Estructura Recomendada

```
/mnt/scratch/HySEALab/
└── HySEALab-Library/              ← Repositorio GitHub (COMPARTIDO)
    ├── epsilon.py                 ← Biblioteca (NO MODIFICAR)
    ├── Manual_Usuario_Epsilon.ipynb
    ├── epsilon_config_example.py
    └── README.md

/home/tu_usuario/                  ← Tu directorio personal
├── HySEALab -> /mnt/scratch/HySEALab  (enlace simbólico)
├── proyecto_tsunami/              ← TU CARPETA DE TRABAJO
│   ├── Manual_Usuario_Epsilon.ipynb   ← COPIA DEL MANUAL (aquí trabajas)
│   ├── epsilon_config.py         ← Tu configuración personal
│   ├── mis_notebooks/
│   │   ├── analisis_japon.ipynb
│   │   └── experimento_1.ipynb
│   └── resultados/
│       └── plots/
├── mis_simulaciones/              ← Tus datos personales (opcional)
└── ...
```

## 🚀 Setup Inicial (Solo una vez)

### Opción A: Setup Automático (RECOMENDADO) ⚡

Usa el script de configuración automática:

```bash
cd ~/HySEALab/HySEALab-Library
bash setup_hysealab.sh
```

El script hará todo por ti:
- ✅ Crea `~/proyecto_tsunami/` con la estructura de directorios
- ✅ Copia el manual a tu carpeta personal
- ✅ Crea tu archivo de configuración personalizado
- ✅ Te guía en los siguientes pasos

Luego solo necesitas:
1. Editar `~/proyecto_tsunami/epsilon_config.py` con tus rutas (opcional)
2. `cd ~/proyecto_tsunami && jupyter lab`

### Opción B: Setup Manual 🔧

Si prefieres hacerlo manualmente:

### 1. Crear tu carpeta de trabajo

```bash
# Desde tu home
cd ~
mkdir -p proyecto_tsunami/resultados/plots
mkdir -p proyecto_tsunami/mis_notebooks
cd proyecto_tsunami
```

### 2. Copiar el manual del usuario a tu carpeta

```bash
# Copiar el manual desde el repositorio compartido
cp ~/HySEALab/HySEALab-Library/Manual_Usuario_Epsilon.ipynb .

# Copiar el ejemplo de configuración
cp ~/HySEALab/HySEALab-Library/epsilon_config_example.py epsilon_config.py

# Editar tu configuración
nano epsilon_config.py
```

### 3. Editar tu archivo de configuración

En `epsilon_config.py`, modifica según tus necesidades:

```python
# Opción A: Usar simulaciones compartidas
PATHS = {
    'simulaciones': '~/HySEALab/simulaciones',
    'mallados': '~/HySEALab/mallados',
    'plots': '~/proyecto_tsunami/resultados/plots',
}

# Opción B: Usar tus propias simulaciones
PATHS = {
    'simulaciones': '~/mis_simulaciones',
    'mallados': '~/HySEALab/mallados',
    'plots': '~/proyecto_tsunami/resultados/plots',
}
```

### 4. Abrir JupyterLab desde tu carpeta de trabajo

```bash
cd ~/proyecto_tsunami
jupyter lab
```

## 📓 En tu Notebook (Manual_Usuario_Epsilon.ipynb)

En la primera celda de tu notebook personal:

```python
import sys
import os

# Agregar la carpeta compartida al path para importar epsilon
sys.path.insert(0, os.path.expanduser('~/HySEALab/HySEALab-Library'))

# Importar epsilon desde la carpeta compartida
import epsilon

# Cargar tu configuración personal
import epsilon_config
epsilon.configure_paths(**epsilon_config.PATHS)

# Verificar configuración
epsilon.show_configuration()
```

## 🔄 Flujo de Trabajo Diario

### Actualizar epsilon.py (cuando haya cambios)

```bash
cd ~/HySEALab/HySEALab-Library
git pull origin main
```

### Trabajar en tus notebooks

```bash
cd ~/proyecto_tsunami
jupyter lab
# Abrir Manual_Usuario_Epsilon.ipynb o tus propios notebooks
```

### Si quieres actualizar tu copia del manual

```bash
cd ~/proyecto_tsunami
# Hacer backup de tu versión actual si tiene cambios importantes
cp Manual_Usuario_Epsilon.ipynb Manual_Usuario_Epsilon_backup.ipynb

# Copiar la nueva versión
cp ~/HySEALab/HySEALab-Library/Manual_Usuario_Epsilon.ipynb .
```

## ⚠️ Importante: NO hacer esto

❌ **NO ejecutar notebooks directamente desde HySEALab-Library:**
```bash
# MAL - NO HACER ESTO:
cd ~/HySEALab/HySEALab-Library
jupyter lab Manual_Usuario_Epsilon.ipynb
```

**Problemas:**
- Los outputs del notebook se guardan en el repositorio
- Tus cambios pueden causar conflictos con git
- Otros usuarios verían tus outputs

✅ **CORRECTO - Trabajar desde tu carpeta personal:**
```bash
# BIEN - HACER ESTO:
cd ~/proyecto_tsunami
jupyter lab Manual_Usuario_Epsilon.ipynb
```

## 🎓 Ventajas de este Enfoque

1. ✅ **Código compartido actualizado**: `git pull` actualiza epsilon.py para todos
2. ✅ **Trabajo personal aislado**: Tus notebooks y configuraciones en tu carpeta
3. ✅ **Sin conflictos de git**: No modificas archivos del repositorio
4. ✅ **Resultados organizados**: Cada usuario tiene su carpeta de plots
5. ✅ **Flexibilidad**: Puedes tener múltiples notebooks con diferentes configuraciones

## 📝 Ejemplo Completo de Celda de Inicio

```python
# ============================================================================
# CONFIGURACIÓN INICIAL - Ejecutar esta celda primero
# ============================================================================
import sys
import os

# 1. Agregar epsilon.py del repositorio compartido al path
epsilon_path = os.path.expanduser('~/HySEALab/HySEALab-Library')
if epsilon_path not in sys.path:
    sys.path.insert(0, epsilon_path)

# 2. Importar epsilon
import epsilon

# 3. Cargar configuración personal (si tienes epsilon_config.py)
try:
    import epsilon_config
    epsilon.configure_paths(**epsilon_config.PATHS)
    print("✅ Configuración cargada desde epsilon_config.py")
except ImportError:
    # Si no tienes epsilon_config.py, configurar manualmente
    epsilon.configure_paths(
        simulaciones="~/HySEALab/simulaciones",
        plots="~/proyecto_tsunami/resultados/plots"
    )
    print("✅ Configuración manual aplicada")

# 4. Verificar configuración
epsilon.show_configuration()

# 5. Configurar matplotlib
%matplotlib inline
import warnings
warnings.filterwarnings('ignore')

print("\n✅ Entorno listo para trabajar!")
```

## 🆘 Solución de Problemas

### "No puedo importar epsilon"

```python
# Verificar que la ruta es correcta
import os
print(os.path.exists(os.path.expanduser('~/HySEALab/HySEALab-Library/epsilon.py')))
```

### "No encuentra las simulaciones"

```python
# Verificar tu configuración actual
epsilon.show_configuration()

# Reconfigurar si es necesario
epsilon.configure_paths(simulaciones="~/HySEALab/simulaciones")
```

### "Problemas con git pull"

```bash
cd ~/HySEALab/HySEALab-Library
git status  # Ver si hay cambios no commiteados

# Si hay cambios locales no deseados, descartarlos:
git reset --hard origin/main
git pull origin main
```

## 📧 Contacto

Si tienes dudas sobre la configuración, contacta al equipo de HySEALab.
