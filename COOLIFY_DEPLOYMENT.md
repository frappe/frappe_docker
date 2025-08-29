# Despliegue de ERPNext con Coolify

Esta guía explica cómo desplegar ERPNext en un VPS utilizando Coolify.

## Requisitos Previos

- Un VPS con Docker instalado
- Coolify instalado y configurado en el VPS
- Acceso SSH al servidor

## Configuración para Coolify

### Archivo de Configuración Principal

El archivo `coolify.yaml` proporciona una configuración simplificada optimizada para Coolify que incluye:

1. **Servicio ERPNext principal** con healthchecks
2. **Base de datos MariaDB** con configuración óptima
3. **Servicios Redis** para cache y colas
4. **Volúmenes persistentes** para datos
5. **Variables de entorno** configurables

### Variables de Entorno

Crea un archivo `.env` con las siguientes variables:

```bash
# Versión de ERPNext
ERPNEXT_VERSION=v15.77.0

# Contraseña de la base de datos
DB_PASSWORD=tu_password_seguro

# Puerto HTTP
HTTP_PORT=8080

# Configuración del host del sitio
FRAPPE_SITE_NAME_HEADER=$$host
```

## Pasos de Despliegue

### 1. Preparar el Servidor

```bash
# Clonar el repositorio
git clone https://github.com/frappe/frappe_docker
cd frappe_docker

# Crear archivo .env
cp example.env .env
# Editar .env con tus configuraciones
```

### 2. Configurar en Coolify

1. **Crear una nueva aplicación** en Coolify
2. **Seleccionar "Docker Compose"** como tipo de aplicación
3. **Conectar el repositorio** o subir los archivos manualmente
4. **Especificar el archivo compose**: `coolify.yaml`
5. **Configurar las variables de entorno** en la interfaz de Coolify

### 3. Variables de Entorno en Coolify

Configura las siguientes variables en la interfaz de Coolify:

- `ERPNEXT_VERSION`: Versión de ERPNext (ej: v15.77.0)
- `DB_PASSWORD`: Contraseña segura para MariaDB
- `HTTP_PORT`: Puerto para acceder a la aplicación
- `FRAPPE_SITE_NAME_HEADER`: Configuración del host (dejar por defecto)

### 4. Despliegue

1. **Iniciar el despliegue** desde la interfaz de Coolify
2. **Monitorear los logs** durante el proceso
3. **Verificar que todos los servicios** estén saludables

## Configuraciones Avanzadas

### Usar Base de Datos Externa

Si prefieres usar una base de datos externa:

```bash
# En el archivo .env o variables de Coolify
DB_HOST=tu_host_de_bd_externa
DB_PORT=3306
DB_PASSWORD=password_de_tu_bd
```

### Configurar Dominio Personalizado

1. **Configurar DNS** apuntando a tu VPS
2. **Configurar reverse proxy** en Coolify
3. **Actualizar `FRAPPE_SITE_NAME_HEADER`** con tu dominio

### Backup y Restauración

Coolify proporciona herramientas integradas para:
- Backups automáticos de volúmenes
- Restauración desde snapshots
- Monitorización de recursos

## Solución de Problemas

### Errores Comunes

1. **Healthcheck failures**: Verificar que todos los servicios estén ejecutándose
2. **Problemas de conexión a BD**: Verificar credenciales y configuración de red
3. **Problemas de permisos**: Asegurar que los volúmenes tengan los permisos correctos

### Logs y Monitorización

- Usar la interfaz de Coolify para ver logs en tiempo real
- Configurar alertas para servicios críticos
- Monitorizar uso de CPU, memoria y almacenamiento

## Mantenimiento

### Actualizaciones

1. **Actualizar versión de ERPNext**: Cambiar `ERPNEXT_VERSION` en las variables
2. **Reiniciar aplicación**: Desde la interfaz de Coolify
3. **Verificar compatibilidad**: Antes de actualizar a versiones mayores

### Escalado

Coolify permite:
- Escalar horizontalmente los servicios
- Ajustar recursos (CPU, memoria)
- Configurar auto-scaling basado en métricas

## Recursos Adicionales

- [Documentación oficial de Coolify](https://coolify.io/docs)
- [Foro de la comunidad ERPNext](https://discuss.erpnext.com)
- [Repositorio frappe_docker](https://github.com/frappe/frappe_docker)

## Soporte

Para problemas específicos de:
- **Configuración de Coolify**: Consultar documentación de Coolify
- **Problemas de ERPNext**: Abrir issue en el repositorio frappe_docker
- **Problemas de base de datos**: Verificar logs de MariaDB/Redis
