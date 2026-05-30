# INFORME TÉCNICO — TocaCasa

**Plataforma Inmobiliaria — Tocancipá, Cundinamarca**

---

## 1. DATOS GENERALES

| Ítem | Detalle |
|------|---------|
| Nombre del proyecto | TocaCasa |
| Tipo | Aplicación web transaccional |
| Entorno | Desarrollo (`DEBUG = True`) |
| URL base | `http://127.0.0.1:8000/` |
| Framework | Django 4.2.10 |
| Lenguaje | Python 3.11.9 |
| Base de datos | MySQL (`tocancipa_propiedades`) |
| Tema administrativo | django-jazzmin 3.0.4 (tema darkly) |
| Servidor | WSGI integrado de Django (development) |

### Estructura del proyecto

```
C:\proyecto_tocancipa\
├── backend/                  # Configuración del proyecto Django
│   ├── settings.py           # Configuración general
│   ├── urls.py               # Rutas raíz
│   ├── wsgi.py / asgi.py     # Puntos de entrada WSGI/ASGI
├── propiedades/              # Aplicación principal
│   ├── models.py             # 8 modelos de datos
│   ├── views.py              # 14 vistas
│   ├── urls.py               # 13 rutas
│   ├── admin.py              # Config panel admin
│   ├── auth_backend.py       # Backend de autenticación
│   ├── decorators.py         # Decoradores de acceso
│   ├── migrations/           # 8 migraciones
│   └── templates/propiedades/# 7 plantillas HTML
├── media/                    # Archivos subidos (imágenes propiedades)
└── env/                      # Entorno virtual Python
```

---

## 2. ARQUITECTURA

### 2.1 Stack tecnológico

| Componente | Tecnología |
|------------|-----------|
| Backend | Django 4.2.10 (Python 3.11) |
| Base de datos | MySQL (mysqlclient 2.2.8) |
| ORM | Django ORM (modelos gestionados manualmente) |
| Autenticación | Backend personalizado (`UsuariosAuthBackend`) |
| Frontend | Bootstrap 5.3 + Font Awesome 6.4 + Google Fonts |
| Admin Theme | django-jazzmin 3.0.4 |

### 2.2 Paquetes instalados

| Paquete | Versión | Estado |
|---------|---------|--------|
| Django | 4.2.10 | Activo |
| mysqlclient | 2.2.8 | Activo |
| Pillow | 12.1.1 | Activo (subida de imágenes) |
| django-jazzmin | 3.0.4 | Activo (tema admin) |
| djangorestframework | 3.16.1 | Instalado, **no configurado** |
| django-cors-headers | 4.9.0 | Instalado, **no configurado** |

### 2.3 Base de datos

- **Motor**: MySQL
- **Base de datos**: `tocancipa_propiedades`
- **Host**: `127.0.0.1:3306`
- **Usuario**: `root` (sin contraseña)
- **Tablas**: 9 tablas gestionadas (`managed = True`)
- **Sin restricciones FK**: Todas las claves foráneas usan `db_constraint=False`

---

## 3. MODELOS DE DATOS

### 3.1 Roles
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | BigAutoField (PK) | |
| nombre | CharField(50) | SuperAdmin, Admin, Cliente |

### 3.2 Usuarios
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | BigAutoField (PK) | |
| nombre | CharField(100) | Nombre completo |
| email | CharField(100) (unique) | Usuario para login |
| password | CharField(255) | Almacenado con PBKDF2 |
| rol | FK → Roles | SuperAdmin, Admin, Cliente |
| fecha_registro | DateTimeField | Autogenerado |
| last_login | DateTimeField (nullable) | Actualizado al login |

**Propiedades de compatibilidad**: `is_authenticated`, `is_active`, `is_staff`, `is_anonymous`, `has_perm()`, `has_perms()`, `has_module_perms()`, `get_all_permissions()`, `get_group_permissions()`, `get_user_permissions()`, `get_username()`, `set_password()`, `check_password()`.

### 3.3 Inmuebles
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | BigAutoField (PK) | |
| titulo | CharField(200) | Título de la propiedad |
| descripcion | TextField (nullable) | |
| ubicacion_especifica | CharField(255) (nullable) | |
| valor_inmueble | DecimalField(15,2) | Precio |
| tipo_negocio | CharField(20) | Venta / Arriendo |
| zona | CharField(20) | Urbana / Rural |
| imagen | ImageField | Upload a `propiedades/` |
| propietario | FK → Usuarios (nullable) | Dueño de la propiedad |

**Métodos de negocio**:
- `calcular_comision()` → 10% arriendo, 10% rural, 3% urbana
- `total_con_comision()` → valor + comisión

### 3.4 Favoritos
| Campo | Tipo |
|-------|------|
| usuario | FK → Usuarios |
| inmueble | FK → Inmuebles |
| creado | DateTimeField (autogenerado) |

**Restricción**: unique_together (usuario, inmueble)

### 3.5 HistorialBusqueda
| Campo | Tipo |
|-------|------|
| usuario | FK → Usuarios |
| query | CharField(200) |
| creado | DateTimeField (autogenerado) |

### 3.6 Comisiones
| Campo | Tipo |
|-------|------|
| inmueble | FK → Inmuebles (nullable) |
| monto_pagado | DecimalField(15,2) (nullable) |
| tipo_pago | CharField(50) (nullable) |
| fecha_pago | DateField (nullable) |

### 3.7 Conversacion
| Campo | Tipo |
|-------|------|
| inmueble | FK → Inmuebles |
| cliente | FK → Usuarios |
| asesor | FK → Usuarios (nullable) |
| estado | CharField(20): Pendiente / En Negociación / Cerrado |
| creado | DateTimeField (autogenerado) |
| actualizado | DateTimeField (auto-update) |

### 3.8 Mensaje
| Campo | Tipo |
|-------|------|
| conversacion | FK → Conversacion |
| remitente | FK → Usuarios |
| contenido | TextField |
| archivo | FileField (nullable, upload a `mensajes/`) |
| leido | BooleanField (default False) |
| creado | DateTimeField (autogenerado) |

---

## 4. SISTEMA DE AUTENTICACIÓN

### 4.1 Backend personalizado (`auth_backend.py`)

```python
class UsuariosAuthBackend(BaseBackend):
    def authenticate(request, username, password):
        # 1. Busca por email en modelo Usuarios
        # 2. Verifica password hasheado (PBKDF2)
        # 3. Fallback: passwords legacy en texto plano → los migra automáticamente
```

### 4.2 Backends configurados
```python
AUTHENTICATION_BACKENDS = [
    'propiedades.auth_backend.UsuariosAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
]
```

### 4.3 Flujo de autenticación
1. Usuario ingresa email + password en `/login/`
2. `UsuariosAuthBackend.authenticate()` busca en tabla `usuarios`
3. Si password legacy (texto plano) → lo hashea y guarda
4. Si password ya hasheado → verifica con `check_password()`
5. Si ok → `login(request, user)` → inicia sesión

---

## 5. SISTEMA DE ROLES Y PERMISOS

### 5.1 Roles existentes

| Rol | Acceso Admin Django | Panel Web | Conversaciones |
|-----|:---:|:---:|:---:|
| **SuperAdmin** | ✅ Sí | Dashboard completo | Todas |
| **Admin** | ✅ Sí | Dashboard completo | Asignadas |
| **Cliente** | ❌ No | Panel cliente | Solo propias |

### 5.2 Decoradores de acceso

- `@login_required` → Redirige a `/login/` si no autenticado
- `@role_required('Admin', 'SuperAdmin')` → Restringe por rol

### 5.3 Lógica en vistas

```python
ROLES_ADMIN = ('SuperAdmin', 'Admin')
ROLES_CLIENTE = ('Cliente',)

def _es_admin(usuario):
    return usuario.rol and usuario.rol.nombre in ROLES_ADMIN
```

---

## 6. RUTAS (URLS)

| Ruta | Vista | Nombre | Método |
|------|-------|--------|--------|
| `/` | `lista_inmuebles` | `index` | GET |
| `/login/` | `login_view` | `login` | GET, POST |
| `/logout/` | `logout_view` | `logout` | GET |
| `/register/` | `register_view` | `register` | GET, POST |
| `/dashboard/` | `dashboard` | `dashboard` | GET |
| `/propiedades/agregar/` | `agregar_propiedad` | `agregar_propiedad` | GET, POST |
| `/propiedades/editar/<id>/` | `editar_propiedad` | `editar_propiedad` | GET, POST |
| `/propiedades/favorito/<id>/` | `toggle_favorito` | `toggle_favorito` | GET |
| `/conversaciones/` | `mis_conversaciones` | `mis_conversaciones` | GET |
| `/conversaciones/iniciar/<id>/` | `iniciar_conversacion` | `iniciar_conversacion` | GET |
| `/conversaciones/<id>/` | `conversacion_detalle` | `conversacion_detalle` | GET |
| `/conversaciones/<id>/enviar/` | `enviar_mensaje` | `enviar_mensaje` | POST |
| `/conversaciones/<id>/estado/` | `cambiar_estado` | `cambiar_estado` | POST |
| `/admin/` | Django Admin | — | Todos |

---

## 7. FUNCIONALIDADES IMPLEMENTADAS

### 7.1 Catálogo público (`/`)
- Listado de propiedades con tarjetas visuales
- Buscador por título y ubicación
- Botón "Cotizar" (modal con desglose valor + comisión + total)
- Botón "Estoy interesado" (crea conversación)
- Botón "Solicitar visita" (crea conversación con mensaje de visita)
- ❤️ Marcar favoritos (solo autenticados)
- Guardado automático de historial de búsqueda

### 7.2 Autenticación y registro
- Login con email + contraseña
- Registro público (asigna rol Cliente)
- Cierre de sesión

### 7.3 Panel de control (`/dashboard/`)
**Admin/SuperAdmin:**
- Estadísticas: total, en venta, en arriendo
- Listado de todas las propiedades
- Enlace al admin de Django
- Conversaciones recientes

**Cliente:**
- Estadísticas de sus propiedades
- Mis propiedades (solo las que publicó)
- Publicar nueva propiedad
- Editar propiedades propias
- Mis favoritos
- Mis conversaciones
- Búsquedas recientes

### 7.4 Publicación de propiedades
- Formulario: título, descripción, ubicación, valor, tipo, zona, foto
- Solo clientes (no admins) desde el panel web
- Edición solo de propiedades propias

### 7.5 Conversaciones (mensajería)
- Inicio desde propiedad: "Estoy interesado" o "Solicitar visita"
- Mensajes de texto con adjuntos (archivos/imágenes)
- Marcación de mensajes como leídos
- Estados: Pendiente → En Negociación → Cerrado
- Solo admins cambian estado
- Cliente solo ve sus conversaciones
- Asignación automática de asesor

### 7.6 Panel administrativo (Django Admin)
- Potenciado con Jazzmin (tema oscuro moderno)
- Gestión CRUD de: Roles, Usuarios, Inmuebles, Comisiones, Favoritos, Historial, Conversaciones, Mensajes
- Vista previa de imágenes en listado
- Cálculo de comisión visible en listado
- Búsqueda global habilitada

---

## 8. FUNCIONALIDADES NO IMPLEMENTADAS

| Funcionalidad | Observación |
|---------------|-------------|
| API REST | DRF instalado pero no configurado |
| CORS | Paquete instalado pero no configurado |
| Notificaciones en tiempo real | No hay WebSockets ni polling |
| Recuperación de contraseña | No implementada |
| Verificación de email | No implementada |
| Paginación en listados | No implementada |
| Filtros avanzados (precio, zona) | Solo búsqueda por texto |
| Mapa con geolocalización | No implementado |
| Calificación de propiedades | No implementada |
| Reportes / exportación PDF | No implementado |
| Tests automatizados | tests.py sin contenido |
| Seguridad producción | DEBUG=True, secret key expuesta |
| Logging / auditoría | No implementado |

---

## 9. PANTALLAS Y PLANTILLAS

| Plantilla | Descripción |
|-----------|-------------|
| `index.html` | Catálogo público de propiedades con buscador, modales y botones de acción |
| `login.html` | Formulario de inicio de sesión |
| `register.html` | Formulario de registro de usuario |
| `dashboard.html` | Panel principal con secciones diferenciales por rol |
| `propiedad_form.html` | Formulario de alta/edición de propiedad |
| `conversaciones.html` | Listado de conversaciones activas |
| `conversacion_detalle.html` | Chat con historial de mensajes |

### Recursos CDN
- Bootstrap 5.3.0 (CSS + JS)
- Font Awesome 6.4.0
- Google Fonts: Plus Jakarta Sans

---

## 10. CONSIDERACIONES TÉCNICAS

### 10.1 Seguridad
- Passwords hasheados con PBKDF2 (Django default)
- Migración automática de passwords legacy
- CSRF protection activo en todos los formularios
- Sesiones gestionadas por Django
- **⚠️ DEBUG = True en producción potencial**
- **⚠️ SECRET_KEY expuesta en el repositorio**
- **⚠️ Sin HTTPS en desarrollo**
- **⚠️ Autenticación de base de datos sin contraseña**

### 10.2 Rendimiento
- Sin paginación (posible problema con muchos registros)
- Consultas sin optimización (`select_related` solo en favoritos)
- Sin caché
- Archivos estáticos servidos por Django (no recomendado en producción)

### 10.3 Base de datos
- Sin constraints FK a nivel BD (`db_constraint=False`)
- MariaDB Strict Mode no activado (warning presente)
- Migraciones aplicadas correctamente (8 migraciones)

### 10.4 Dependencias no utilizadas
- `djangorestframework` 3.16.1 → Instalado, no en `INSTALLED_APPS`
- `django-cors-headers` 4.9.0 → Instalado, no en `INSTALLED_APPS` ni `MIDDLEWARE`

---

## 11. REQUISITOS PARA EJECUCIÓN

### 11.1 Local (desarrollo)
```bash
# Activar entorno virtual
.\env\Scripts\activate

# Aplicar migraciones
python manage.py migrate

# Iniciar servidor
python manage.py runserver
```

### 11.2 Requisitos
- Python 3.11+
- MySQL 8+ corriendo en localhost
- Usuario `root` sin contraseña en MySQL
- Base de datos `tocancipa_propiedades` creada
- Tablas existentes con datos (o ejecutar migraciones)

### 11.3 Posible archivo requirements.txt
```
Django==4.2.10
mysqlclient==2.2.8
Pillow==12.1.1
django-jazzmin==3.0.4
djangorestframework==3.16.1
django-cors-headers==4.9.0
```

---

## 12. DATOS EXISTENTES (AL 20/05/2026)

| Tabla | Registros |
|-------|-----------|
| Roles | 3 |
| Usuarios | ~85 |
| Inmuebles | ~37 |
| Comisiones | — |
| Favoritos | — (vacío) |
| HistorialBusqueda | — (vacío) |
| Conversaciones | — (vacío) |
| Mensajes | — (vacío) |
| auth_user (Django) | 1 (superusuario `root`) |

### Usuarios de prueba principales
| Email | Rol | Contraseña |
|-------|-----|------------|
| `admin@tocancipa.com` | SuperAdmin | `admin123` |
| `carlos.admin@gmail.com` | Admin | — |
| `juan.perez@email.com` | Admin | — |
| `marta.prop@outlook.com` | Cliente | — |
| `root` (Django superuser) | SuperAdmin | (la que se definió en createsuperuser) |

---

## 13. FLUJO DE USUARIO TÍPICO

```
Visitante
  ├── Ve propiedades en "/"
  ├── Busca por sector (se guarda historial si está logueado)
  ├── Cotiza (modal con precios + comisión)
  ├── Se registra ("/register/") → rol Cliente
  └── Inicia sesión ("/login/")

Cliente autenticado
  ├── Marca favoritos ❤️ en propiedades
  ├── "Estoy interesado" → crea conversación
  ├── "Solicitar visita" → crea conversación con mensaje de visita
  ├── Dashboard: publica/edita sus propiedades
  ├── Dashboard: ve favoritos
  ├── Dashboard: ve conversaciones
  └── Chatea con asesores

Admin / SuperAdmin
  ├── Dashboard: ve todas las propiedades y estadísticas
  ├── Cambia estado de conversaciones
  ├── Responde mensajes
  └── Django Admin: gestión completa de datos
```

---

## 14. RECOMENDACIONES

1. **Producción**: Desactivar DEBUG, cambiar SECRET_KEY, configurar HTTPS
2. **Seguridad**: Establecer contraseña de MySQL, configurar validadores de contraseña
3. **Rendimiento**: Agregar paginación a listados de propiedades y conversaciones
4. **API**: Activar Django REST Framework para crear API consumible desde móvil
5. **Tests**: Implementar tests unitarios y de integración
6. **Documentación**: No existe README ni documentación de usuario
7. **Estáticos**: Migrar CSS/JS de CDN a archivos locales para producción
8. **CORS**: Configurar si se planea consumir desde frontend separado
9. **Almacenamiento**: Migrar a S3 o servicio cloud para imágenes en producción
