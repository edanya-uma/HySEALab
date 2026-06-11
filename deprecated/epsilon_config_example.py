"""
Archivo de configuración de ejemplo para epsilon.py

Copia este archivo a tu directorio de trabajo como 'epsilon_config.py' 
o 'mi_config.py' y modifica las rutas según tus necesidades.

Uso:
----
En tu notebook:

    import epsilon
    
    # Opción 1: Configurar manualmente
    epsilon.configure_paths(
        simulaciones="~/HySEALab/simulaciones",
        mallados="~/HySEALab/mallados",
        plots="~/mis_resultados/plots"
    )
    
    # Opción 2: Importar desde archivo de configuración
    import epsilon_config
    epsilon.configure_paths(**epsilon_config.PATHS)
"""

# =============================================================================
# CONFIGURACIÓN PARA ENTORNO HySEALab
# =============================================================================

# Opción A: Usando carpetas compartidas (recomendado para acceso a simulaciones comunes)
PATHS_HYSEALAB_SHARED = {
    'simulaciones': '~/HySEALab/simulaciones',
    'mallados': '~/HySEALab/mallados',
    'plots': '~/resultados/plots',
}

# Opción B: Usando carpetas personales
PATHS_HYSEALAB_PERSONAL = {
    'simulaciones': '~/mis_simulaciones',
    'mallados': '~/mis_mallados',
    'plots': '~/resultados/plots',
}

# Opción C: Mixto (simulaciones compartidas, resultados personales)
PATHS_HYSEALAB_MIXED = {
    'simulaciones': '~/HySEALab/simulaciones',
    'mallados': '~/HySEALab/mallados',
    'plots': '~/mi_proyecto/graficos',
}

# =============================================================================
# CONFIGURACIÓN PARA OTROS ENTORNOS
# =============================================================================

# Rutas relativas (por defecto)
PATHS_DEFAULT = {
    'simulaciones': './simulaciones',
    'mallados': './mallados',
    'plots': './plots',
}

# Rutas absolutas personalizadas
PATHS_CUSTOM = {
    'simulaciones': '/ruta/absoluta/a/simulaciones',
    'mallados': '/ruta/absoluta/a/mallados',
    'plots': '/ruta/donde/guardar/plots',
}

# =============================================================================
# CONFIGURACIÓN ACTIVA
# =============================================================================
# Descomenta la configuración que quieras usar:

PATHS = PATHS_HYSEALAB_MIXED  # <-- Cambia esto según tu entorno

# Ejemplos de configuraciones específicas por usuario:
# PATHS = PATHS_HYSEALAB_SHARED      # Usar carpetas compartidas
# PATHS = PATHS_HYSEALAB_PERSONAL    # Usar carpetas personales
# PATHS = PATHS_DEFAULT              # Usar rutas relativas por defecto
# PATHS = PATHS_CUSTOM               # Usar configuración personalizada

# =============================================================================
# CONFIGURACIÓN AVANZADA
# =============================================================================

# Puedes crear configuraciones personalizadas:
# PATHS = {
#     'simulaciones': '/mnt/scratch/HySEALab/simulaciones',
#     'mallados': '/home/usuario/datos/mallados',
#     'plots': '/home/usuario/proyecto_tsunami/resultados',
# }
