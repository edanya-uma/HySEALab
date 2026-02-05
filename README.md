# Biblioteca Epsilon - Visualización de Tsunami-HySEA

Herramienta interactiva para visualizar y analizar resultados de simulaciones de Tsunami-HySEA en formato NetCDF.

## 📋 Contenido del Repositorio

- **epsilon.py**: Biblioteca principal con todas las funciones de visualización
- **Manual_Usuario_Epsilon.ipynb**: Tutorial interactivo y documentación completa
- **simulaciones/**: Directorio para tus archivos .nc (crear si no existe)

## 🚀 Inicio Rápido

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

### 3. Preparar estructura de directorios

```bash
mkdir -p simulaciones plots
```

### 4. Abrir el notebook

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

## 🤝 Contribuir

Si encuentras errores o tienes sugerencias, por favor abre un issue en GitHub.

## 📧 Contacto

HySEALab - Universidad de Málaga

## 📄 Licencia

[Especificar licencia]
