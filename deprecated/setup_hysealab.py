#!/usr/bin/env python3
"""
Script de configuración rápida para usuarios de HySEALab
Puede ejecutarse desde terminal o desde un Jupyter Notebook

Uso desde terminal:
    python setup_hysealab.py

Uso desde Jupyter Notebook:
    %run ~/HySEALab/HySEALab-Library/setup_hysealab.py
    
O en una celda:
    import sys
    sys.path.insert(0, '~/HySEALab/HySEALab-Library')
    import setup_hysealab
    setup_hysealab.setup()
"""

import os
import shutil
from pathlib import Path


def print_header():
    print("=" * 50)
    print("Setup de Epsilon para HySEALab")
    print("=" * 50)
    print()


def verificar_entorno():
    """Verifica que estamos en el entorno HySEALab"""
    hysealab_path = Path.home() / "HySEALab"
    
    if not hysealab_path.exists():
        print("⚠️  ADVERTENCIA: No se detectó el enlace ~/HySEALab")
        print("   Este script está diseñado para el entorno HySEALab")
        respuesta = input("   ¿Continuar de todas formas? (s/n): ")
        if respuesta.lower() != 's':
            print("Setup cancelado")
            return False
    return True


def crear_estructura_directorios():
    """Crea la estructura de directorios en el home del usuario"""
    print("1. Creando estructura de directorios...")
    
    proyecto_dir = Path.home() / "proyecto_tsunami"
    
    # Crear directorios
    dirs_to_create = [
        proyecto_dir,
        proyecto_dir / "resultados" / "plots",
        proyecto_dir / "mis_notebooks"
    ]
    
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    print(f"   ✓ Directorio creado: {proyecto_dir}")
    return proyecto_dir


def copiar_manual(proyecto_dir):
    """Copia el manual del usuario a la carpeta personal"""
    print()
    print("2. Copiando Manual de Usuario...")
    
    manual_source = Path.home() / "HySEALab" / "HySEALab-Library" / "Manual_Usuario_Epsilon.ipynb"
    manual_dest = proyecto_dir / "Manual_Usuario_Epsilon.ipynb"
    
    if not manual_source.exists():
        print(f"   ✗ No se encontró el manual en {manual_source}")
        print("   Verifica que HySEALab-Library esté actualizado")
        return False
    
    if manual_dest.exists():
        print("   ⚠️  El manual ya existe en tu carpeta personal")
        respuesta = input("   ¿Sobrescribir? (s/n): ")
        if respuesta.lower() != 's':
            print("   - Manual existente conservado")
            return True
    
    shutil.copy2(manual_source, manual_dest)
    print(f"   ✓ Manual copiado a {manual_dest}")
    return True


def copiar_config(proyecto_dir):
    """Copia el archivo de configuración de ejemplo"""
    print()
    print("3. Creando archivo de configuración personalizado...")
    
    config_source = Path.home() / "HySEALab" / "HySEALab-Library" / "epsilon_config_example.py"
    config_dest = proyecto_dir / "epsilon_config.py"
    
    if not config_source.exists():
        print("   ℹ️  No se encontró epsilon_config_example.py")
        print("   Puedes configurar las rutas manualmente en el notebook")
        return True
    
    if config_dest.exists():
        print("   ⚠️  Ya existe epsilon_config.py")
        respuesta = input("   ¿Sobrescribir? (s/n): ")
        if respuesta.lower() != 's':
            print("   - Configuración existente conservada")
            return True
    
    shutil.copy2(config_source, config_dest)
    print(f"   ✓ Configuración copiada a {config_dest}")
    print()
    print(f"   📝 IMPORTANTE: Edita este archivo con tus rutas personalizadas:")
    print(f"      Desde JupyterLab: Abre {config_dest} y modifica las rutas")
    return True


def mostrar_resumen(proyecto_dir):
    """Muestra el resumen del setup"""
    print()
    print("=" * 50)
    print("✅ Setup completado!")
    print("=" * 50)
    print()
    print("📂 Tu estructura de directorios:")
    print(f"   {proyecto_dir}/")
    print("   ├── Manual_Usuario_Epsilon.ipynb")
    print("   ├── epsilon_config.py (edítalo con tus rutas)")
    print("   ├── mis_notebooks/")
    print("   └── resultados/plots/")
    print()
    print("🚀 Próximos pasos:")
    print()
    print("1. Editar configuración (opcional):")
    print(f"   Abre {proyecto_dir}/epsilon_config.py en JupyterLab")
    print()
    print("2. En JupyterLab, navega a:")
    print(f"   {proyecto_dir}/")
    print()
    print("3. Abre Manual_Usuario_Epsilon.ipynb y ejecuta las celdas")
    print()
    print("📖 Para más información, consulta:")
    print("   ~/HySEALab/HySEALab-Library/SETUP_USUARIO.md")
    print()


def setup():
    """Función principal de setup"""
    print_header()
    
    # Verificar entorno
    if not verificar_entorno():
        return False
    
    # Crear estructura
    proyecto_dir = crear_estructura_directorios()
    
    # Copiar archivos
    copiar_manual(proyecto_dir)
    copiar_config(proyecto_dir)
    
    # Mostrar resumen
    mostrar_resumen(proyecto_dir)
    
    return True


if __name__ == "__main__":
    setup()
