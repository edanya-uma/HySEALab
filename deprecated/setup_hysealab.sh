#!/bin/bash
# Script de configuración rápida para usuarios de HySEALab
# Uso: bash setup_hysealab.sh

echo "=============================================="
echo "Setup de Epsilon para HySEALab"
echo "=============================================="
echo ""

# 1. Verificar que estamos en el entorno correcto
if [ ! -d "$HOME/HySEALab" ]; then
    echo "⚠️  ADVERTENCIA: No se detectó el enlace ~/HySEALab"
    echo "   Este script está diseñado para el entorno HySEALab"
    echo "   ¿Continuar de todas formas? (s/n)"
    read -r respuesta
    if [ "$respuesta" != "s" ]; then
        echo "Setup cancelado"
        exit 0
    fi
fi

# 2. Crear estructura de directorios
echo "1. Creando estructura de directorios..."
PROYECTO_DIR="$HOME/proyecto_tsunami"

mkdir -p "$PROYECTO_DIR"
mkdir -p "$PROYECTO_DIR/resultados/plots"
mkdir -p "$PROYECTO_DIR/mis_notebooks"

echo "   ✓ Directorio creado: $PROYECTO_DIR"

# 3. Copiar el manual del usuario
echo ""
echo "2. Copiando Manual de Usuario..."
MANUAL_SOURCE="$HOME/HySEALab/HySEALab-Library/Manual_Usuario_Epsilon.ipynb"
MANUAL_DEST="$PROYECTO_DIR/Manual_Usuario_Epsilon.ipynb"

if [ -f "$MANUAL_SOURCE" ]; then
    if [ -f "$MANUAL_DEST" ]; then
        echo "   ⚠️  El manual ya existe en tu carpeta personal"
        echo "   ¿Sobrescribir? (s/n)"
        read -r respuesta
        if [ "$respuesta" = "s" ]; then
            cp "$MANUAL_SOURCE" "$MANUAL_DEST"
            echo "   ✓ Manual actualizado"
        else
            echo "   - Manual existente conservado"
        fi
    else
        cp "$MANUAL_SOURCE" "$MANUAL_DEST"
        echo "   ✓ Manual copiado a $MANUAL_DEST"
    fi
else
    echo "   ✗ No se encontró el manual en $MANUAL_SOURCE"
    echo "   Verifica que HySEALab-Library esté actualizado"
fi

# 4. Crear archivo de configuración
echo ""
echo "3. Creando archivo de configuración personalizado..."
CONFIG_SOURCE="$HOME/HySEALab/HySEALab-Library/epsilon_config_example.py"
CONFIG_DEST="$PROYECTO_DIR/epsilon_config.py"

if [ -f "$CONFIG_SOURCE" ]; then
    if [ -f "$CONFIG_DEST" ]; then
        echo "   ⚠️  Ya existe epsilon_config.py"
        echo "   ¿Sobrescribir? (s/n)"
        read -r respuesta
        if [ "$respuesta" = "s" ]; then
            cp "$CONFIG_SOURCE" "$CONFIG_DEST"
            echo "   ✓ Configuración actualizada"
        else
            echo "   - Configuración existente conservada"
        fi
    else
        cp "$CONFIG_SOURCE" "$CONFIG_DEST"
        echo "   ✓ Configuración copiada a $CONFIG_DEST"
        echo ""
        echo "   📝 IMPORTANTE: Edita este archivo con tus rutas personalizadas:"
        echo "      nano $CONFIG_DEST"
    fi
else
    echo "   ℹ️  No se encontró epsilon_config_example.py"
    echo "   Puedes configurar las rutas manualmente en el notebook"
fi

# 5. Resumen
echo ""
echo "=============================================="
echo "✅ Setup completado!"
echo "=============================================="
echo ""
echo "📂 Tu estructura de directorios:"
echo "   $PROYECTO_DIR/"
echo "   ├── Manual_Usuario_Epsilon.ipynb"
echo "   ├── epsilon_config.py (edítalo con tus rutas)"
echo "   ├── mis_notebooks/"
echo "   └── resultados/plots/"
echo ""
echo "🚀 Próximos pasos:"
echo ""
echo "1. Editar configuración (opcional):"
echo "   nano $PROYECTO_DIR/epsilon_config.py"
echo ""
echo "2. Abrir JupyterLab:"
echo "   cd $PROYECTO_DIR"
echo "   jupyter lab"
echo ""
echo "3. Abrir Manual_Usuario_Epsilon.ipynb y ejecutar las celdas"
echo ""
echo "📖 Para más información, consulta:"
echo "   $HOME/HySEALab/HySEALab-Library/SETUP_USUARIO.md"
echo ""
