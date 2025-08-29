# Script de configuración inicial para Coolify (PowerShell)
# Este script ayuda a preparar el entorno para el despliegue en VPS Ubuntu

Write-Host "=== Configuración inicial para Coolify en VPS Ubuntu ===" -ForegroundColor Green

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "compose.yaml")) {
    Write-Host "Error: Este script debe ejecutarse desde el directorio raíz de frappe_docker" -ForegroundColor Red
    exit 1
}

# Crear archivo .env si no existe
if (-not (Test-Path ".env")) {
    Write-Host "Creando archivo .env desde coolify.env.example..." -ForegroundColor Yellow
    Copy-Item -Path "coolify.env.example" -Destination ".env"
    Write-Host "¡Archivo .env creado!" -ForegroundColor Green
    Write-Host "Por favor, edita el archivo .env y cambia los valores por defecto, especialmente DB_PASSWORD" -ForegroundColor Yellow
} else {
    Write-Host "El archivo .env ya existe" -ForegroundColor Green
}

# Verificar estructura de archivos
Write-Host "`n=== Verificación de archivos ===" -ForegroundColor Green

$files = @(
    @{Name = "coolify.yaml"; Description = "Configuración Docker Compose para Coolify"},
    @{Name = "COOLIFY_DEPLOYMENT.md"; Description = "Documentación de despliegue"},
    @{Name = "coolify.env.example"; Description = "Ejemplo de variables de entorno"},
    @{Name = ".env"; Description = "Variables de entorno (debes editarlo)"}
)

foreach ($file in $files) {
    if (Test-Path $file.Name) {
        Write-Host "✅ $($file.Name) - $($file.Description)" -ForegroundColor Green
    } else {
        Write-Host "❌ $($file.Name) - No encontrado" -ForegroundColor Red
    }
}

Write-Host "`n=== Próximos pasos para VPS Ubuntu ===" -ForegroundColor Green
Write-Host "1. Sube este proyecto a tu repositorio Git (GitHub, GitLab, etc.)" -ForegroundColor Yellow
Write-Host "2. En tu VPS Ubuntu con Coolify:" -ForegroundColor Yellow
Write-Host "   - Clona el repositorio: git clone <tu-repositorio>" -ForegroundColor Yellow
Write-Host "   - Navega al directorio: cd frappe_docker" -ForegroundColor Yellow
Write-Host "   - Ejecuta: ./setup-coolify.sh (para configurar .env)" -ForegroundColor Yellow
Write-Host "3. En la interfaz web de Coolify:" -ForegroundColor Yellow
Write-Host "   - Crea una nueva aplicación" -ForegroundColor Yellow
Write-Host "   - Selecciona 'Docker Compose'" -ForegroundColor Yellow
Write-Host "   - Configura la ruta al archivo: coolify.yaml" -ForegroundColor Yellow
Write-Host "   - Establece las variables de entorno" -ForegroundColor Yellow
Write-Host "4. Inicia el despliegue" -ForegroundColor Yellow

Write-Host "`n=== Configuración completada ===" -ForegroundColor Green
Write-Host "Tu proyecto está listo para desplegarse en Coolify en Ubuntu" -ForegroundColor Green
Write-Host "Consulta COOLIFY_DEPLOYMENT.md para instrucciones detalladas" -ForegroundColor Cyan
