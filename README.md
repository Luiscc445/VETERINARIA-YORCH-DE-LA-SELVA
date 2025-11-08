# RamboPet - Sistema de Gestión Integral para Clínica Veterinaria

Sistema de gestión integral desarrollado con Django para la Clínica Veterinaria RamboPet.

## Stack Tecnológico

- **Backend:** Django 5.0
- **API:** Django REST Framework
- **Base de Datos:** PostgreSQL
- **Tareas Asíncronas:** Celery
- **Broker de Mensajes:** Redis
- **Servidor de Aplicación:** Gunicorn
- **Servidor Web:** Nginx
- **Contenedorización:** Docker y Docker Compose

## Estructura del Proyecto

El proyecto está organizado en 5 aplicaciones Django modulares:

### 1. Usuarios (`usuarios`)
- Gestión de autenticación y roles
- Tipos de usuarios: Tutor, Médico, Recepcionista, Administrador
- Perfiles personalizados con información adicional

### 2. Pacientes (`pacientes`)
- Gestión de mascotas y sus datos
- Control de especies y razas
- Información médica básica (alergias, condiciones crónicas)

### 3. Citas (`citas`)
- Sistema de agendamiento de citas
- Estados: Reservada, Confirmada, En Curso, Atendida, Cancelada
- Recordatorios automáticos vía email (Celery)

### 4. Historia Clínica Electrónica (`hce`)
- Episodios clínicos completos
- Constantes vitales
- Adjuntos médicos (radiografías, análisis, etc.)
- Diagnósticos y planes de tratamiento

### 5. Inventario (`inventario`)
- Gestión de productos (medicamentos, suministros, etc.)
- Control por lotes con fechas de vencimiento
- Movimientos de inventario con trazabilidad completa
- Alertas automáticas de stock bajo y productos próximos a vencer

## Instalación y Configuración

### Requisitos Previos

- Docker y Docker Compose
- Git

### Pasos de Instalación

1. **Clonar el repositorio:**
```bash
git clone <repository-url>
cd VETERINARIA-YORCH-DE-LA-SELVA
```

2. **Configurar variables de entorno:**
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

3. **Construir y levantar los contenedores:**
```bash
docker-compose up -d --build
```

4. **Crear las migraciones y aplicarlas:**
```bash
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate
```

5. **Crear superusuario:**
```bash
docker-compose exec backend python manage.py createsuperuser
```

6. **Acceder a la aplicación:**
- Admin: http://localhost/admin/
- API: http://localhost/api/v1/
- Documentación API: http://localhost/swagger/

## Características Principales

### Panel de Administración
- Interfaz completa para gestión de todas las entidades
- Visualización con badges de colores para estados
- Filtros y búsquedas avanzadas
- Acciones masivas personalizadas

### API REST
- Endpoints completos para todas las entidades
- Autenticación y permisos por rol
- Paginación automática
- Filtros y búsqueda integrados
- Documentación automática con Swagger

### Tareas Programadas (Celery)
- Recordatorios de citas (diario a las 9:00 AM)
- Verificación de stock bajo (diario a las 8:00 AM)
- Alertas de productos próximos a vencer (semanal)
- Envío de agenda diaria a médicos

### Seguridad
- Autenticación basada en sesiones
- Permisos por rol
- Validaciones en modelos y serializers
- Headers de seguridad en Nginx
- HTTPS en producción (configuración incluida)

## Estructura de la Base de Datos

### Relaciones Principales

```
Usuario (tutor) --< Mascota --< Cita --< EpisodioClinico
Usuario (médico) --< Cita
Usuario (médico) --< EpisodioClinico
Producto --< Lote --< MovimientoInventario
EpisodioClinico --< MovimientoInventario
EpisodioClinico --< ConstantesVitales
EpisodioClinico --< Adjunto
```

## API Endpoints

### Usuarios
- `GET /api/v1/usuarios/` - Lista usuarios
- `POST /api/v1/usuarios/` - Crear usuario
- `GET /api/v1/usuarios/medicos/` - Lista médicos
- `GET /api/v1/usuarios/profile/` - Perfil actual

### Pacientes
- `GET /api/v1/pacientes/mascotas/` - Lista mascotas
- `POST /api/v1/pacientes/mascotas/` - Crear mascota
- `GET /api/v1/pacientes/especies/` - Lista especies
- `GET /api/v1/pacientes/razas/` - Lista razas

### Citas
- `GET /api/v1/citas/` - Lista citas
- `POST /api/v1/citas/` - Crear cita
- `GET /api/v1/citas/mis-citas/` - Mis citas
- `GET /api/v1/citas/proximas/` - Próximas citas
- `POST /api/v1/citas/{id}/confirmar/` - Confirmar cita

### Historia Clínica
- `GET /api/v1/hce/episodios/` - Lista episodios
- `POST /api/v1/hce/episodios/` - Crear episodio
- `GET /api/v1/hce/episodios/por-mascota/{id}/` - Historial
- `GET /api/v1/hce/constantes/` - Constantes vitales
- `GET /api/v1/hce/adjuntos/` - Adjuntos

### Inventario
- `GET /api/v1/inventario/productos/` - Lista productos
- `POST /api/v1/inventario/productos/` - Crear producto
- `GET /api/v1/inventario/productos/stock-bajo/` - Stock bajo
- `GET /api/v1/inventario/lotes/` - Lista lotes
- `GET /api/v1/inventario/movimientos/` - Movimientos

## Comandos Útiles

### Docker
```bash
# Ver logs
docker-compose logs -f

# Reiniciar servicios
docker-compose restart

# Detener servicios
docker-compose down

# Ejecutar comando en contenedor
docker-compose exec backend python manage.py <comando>
```

### Django
```bash
# Crear migraciones
docker-compose exec backend python manage.py makemigrations

# Aplicar migraciones
docker-compose exec backend python manage.py migrate

# Crear superusuario
docker-compose exec backend python manage.py createsuperuser

# Shell de Django
docker-compose exec backend python manage.py shell

# Cargar datos de prueba (si existen fixtures)
docker-compose exec backend python manage.py loaddata <fixture>
```

### Celery
```bash
# Ver workers
docker-compose exec celery celery -A config inspect active

# Purgar tareas
docker-compose exec celery celery -A config purge
```

## Configuración de Producción

Para producción, asegúrate de:

1. Cambiar `DEBUG=False` en `.env`
2. Configurar `SECRET_KEY` único y seguro
3. Configurar `ALLOWED_HOSTS` apropiadamente
4. Habilitar HTTPS en Nginx
5. Configurar backups automáticos de la base de datos
6. Configurar monitoreo (ej: Sentry)
7. Revisar configuraciones de seguridad en `settings.py`

## Licencia

Proprietary - Clínica Veterinaria RamboPet

## Soporte

Para soporte, contactar a: contacto@rambopet.com
