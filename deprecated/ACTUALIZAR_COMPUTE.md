# INSTRUCCIONES DE ACTUALIZACIÓN PARA COMPUTE-2-0

## ⚠️ IMPORTANTE: Ejecuta estos comandos en compute-2-0

El repositorio ha sido actualizado con correcciones importantes. Para obtener la última versión:

### Opción 1: Forzar actualización completa (RECOMENDADO)

```bash
cd ~/HySEALab/HySEALab-Library
git fetch origin
git reset --hard origin/main
```

### Opción 2: Si quieres ver los cambios antes

```bash
cd ~/HySEALab/HySEALab-Library
git fetch origin
git diff origin/main
git reset --hard origin/main
```

## ✅ Verificar que tienes la última versión

Después de actualizar, verifica que la celda de verificación de epsilon.py tiene este código:

```python
# Verificar que epsilon.py existe y es un archivo Python válido
import os
from pathlib import Path

# Buscar epsilon.py en múltiples ubicaciones posibles
posibles_ubicaciones = [
    Path.home() / "HySEALab" / "HySEALab-Library" / "epsilon.py",  # HySEALab compartido
    Path(os.getcwd()) / "epsilon.py",  # Directorio actual
]
```

Si ves esto en la celda 7 del Manual, tienes la versión correcta.

## 🔄 Después de actualizar

1. Si ya ejecutaste `Setup_HySEALab.ipynb`, no necesitas hacerlo de nuevo
2. Tu carpeta `~/proyecto_tsunami/` y tu configuración se mantendrán intactas
3. Solo necesitas copiar el manual actualizado si quieres:
   ```bash
   cp ~/HySEALab/HySEALab-Library/Manual_Usuario_Epsilon.ipynb ~/proyecto_tsunami/
   ```

## 📝 Cambios Principales

- ✅ La celda de verificación ahora busca epsilon.py en la carpeta compartida de HySEALab
- ✅ Ya no da error cuando trabajas desde ~/proyecto_tsunami/
- ✅ Detecta automáticamente la ubicación correcta de epsilon.py
