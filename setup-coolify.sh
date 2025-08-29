#!/bin/bash

# Script de configuración inicial para Coolify
# Este script ayuda a preparar el entorno para el despliegue

echo "=== Configuración inicial para Coolify ==="

# Verificar que estamos en el directorio correcto
if [ ! -f "compose.yaml" ]; then
    echo "Error: Este script debe ejecutarse desde el directorio raíz de frappe_docker"
    exit 1
fi

# Crear archivo .env si no existe
if [ ! -f ".env" ]; then
    echo "Creando archivo .env desde coolify.env.example..."
    cp coolify.env.example .env
    echo "¡Archivo .env creado!"
    echo "Por favor, edita el archivo .env y cambia los valores por defecto, especialmente DB_PASSWORD"
else
    echo "El archivo .env ya existe"
fi

# Verificar estructura de archivos
echo ""
echo "=== Verificación de archivos ==="
echo "Archivos creados para Coolify:"

if [ -f "coolify.yaml" ]; then
    echo "✅ coolify.yaml - Configuración Docker Compose para Coolify"
else
    echo "❌ coolify.yaml - No encontrado"
fi

if [ -f "COOLIFY_DEPLOYMENT.md" ]; then
    echo "✅ COOLIFY_DEPLOYMENT.md - Documentación de despliegue"
else
    echo "❌ COOLIFY_DEPLOYMENT.md - No encontrado"
fi

if [ -f "coolify.env.example" ]; then
    echo "✅ coolify.env.example - Ejemplo de variables de entorno"
else
    echo "❌ coolify.env.example - No encontrado"
fi

if [ -f ".env" ]; then
    echo "✅ .env - Variables de entorno (debes editarlo)"
else
    echo "❌ .env - No encontrado"
fi

echo ""
echo "=== Próximos pasos ==="
echo "1. Edita el archivo .env y configura tus variables:"
echo "   - Cambia DB_PASSWORD por una contraseña segura"
echo "   - Ajusta otras variables según necesites"
echo ""
echo "2. Sube este proyecto a tu repositorio Git"
echo ""
echo "3. En Coolify:"
echo "   - Crea una nueva aplicación"
echo "   - Selecciona 'Docker Compose'"
echo "   - Conecta tu repositorio"
echo "   - Especifica 'coolify.yaml' como archivo compose"
echo "   - Configura las variables de entorno"
echo ""
echo "4. Inicia el despliegue desde Coolify"
echo ""
echo "Para más detalles, consulta COOLIFY_DEPLOYMENT.md"

echo ""
echo "=== Configuración completada ==="
