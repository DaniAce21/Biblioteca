# Sistema de Biblioteca — versión completa, comentada y corregida

## Descripción

Proyecto web desarrollado con Django y Python para gestionar una biblioteca.
Incluye autenticación, registro por pasos, recuperación de contraseña, gestión
CRUD de libros, autores, editoriales y lectores, préstamos, devoluciones y
solicitudes.

## Características principales

- Registro de lectores dividido en pasos.
- Inicio de sesión con redirección según el tipo de usuario.
- Recuperación de contraseña con token de Django.
- Dashboard administrativo.
- Dashboard para lectores.
- Gestión de libros.
- Consulta de información desde Open Library.
- Gestión de autores y editoriales.
- Gestión de lectores.
- Registro y control de préstamos.
- Registro histórico de devoluciones.
- Solicitudes de préstamos realizadas por lectores.
- Solicitudes de incorporación de nuevos libros.
- Edición de teléfono y dirección del lector.
- Interfaz oscura con negro, blanco, grises y rojo.
- Bootstrap 5 y Bootstrap Icons.
- CSS y JavaScript separados de las plantillas.
- Código Python, HTML, CSS y JavaScript documentado con comentarios.

## Estructura

```text
biblioteca/
├── manage.py
├── db.sqlite3
├── requirements.txt
├── README.md
│
├── biblioteca/
│   ├── settings.py
│   ├── urls.py
│   ├── validators.py
│   ├── asgi.py
│   └── wsgi.py
│
└── biblioteca_app/
    ├── admin.py
    ├── apps.py
    ├── forms.py
    ├── models.py
    ├── urls.py
    ├── views.py
    ├── migrations/
    ├── templates/
    ├── static/
    └── management/
```

## Recuperación de contraseña

La pantalla inicial se encuentra en:

`biblioteca_app/templates/biblioteca_app/auth/password/password_reset.html`

La ruta `/password-reset/` muestra esta pantalla y la ruta
`/password-reset/request/` procesa el correo y genera el enlace.

## Base de datos incluida

La base `db.sqlite3` incluida en este ZIP ya contiene la migración
`0009_lector_telefono_direccion`, incluyendo las columnas `Telefono` y
`Direccion` en la tabla `LECTOR`.

## Instalación

1. Crear un entorno virtual:

```powershell
python -m venv .venv
```

2. Activarlo en PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

3. Instalar dependencias:

```powershell
pip install -r requirements.txt
```

4. Verificar el proyecto:

```powershell
python manage.py check
```

5. Aplicar migraciones pendientes:

```powershell
python manage.py migrate
```

6. Iniciar el servidor:

```powershell
python manage.py runserver
```

## Usuario administrador

La base de datos incluida conserva los usuarios que estaban registrados en la
versión de trabajo. No se debe asumir una contraseña nueva; utilizar las
credenciales existentes o crear un nuevo superusuario con:

```powershell
python manage.py createsuperuser
```

## Comentarios del código

Los archivos principales están organizados por secciones. Las funciones y
bloques importantes explican qué reciben, qué procesan y qué resultado
producen. Las migraciones conservan sus operaciones generadas por Django y
solo incluyen documentación introductoria.

## Nota de seguridad

`DEBUG=True` y el `SECRET_KEY` incluido son adecuados únicamente para el
entorno académico/local. Antes de publicar el sistema en producción deben
cambiarse la clave secreta, DEBUG y la configuración de correo y seguridad.

## Autenticación de dos factores (2FA)

Las nuevas cuentas de lector deben completar la configuración de 2FA durante el registro.
El sistema utiliza TOTP, por lo que es compatible con Google Authenticator, Microsoft Authenticator
y otras aplicaciones que generen códigos de seis dígitos.

Después de instalar las dependencias, ejecuta las migraciones:

```powershell
python -m pip install -r requirements.txt
python manage.py migrate
```

Durante el registro se solicitarán también el número de teléfono y la dirección.

> En desarrollo, el código QR se genera directamente desde Django y no se envía por SMS.


## Búsqueda de libros con Open Library

Se incorporó una función de backend para consultar libros externos mediante
la API Search de Open Library. El endpoint requiere autenticación de lector:

`GET /lector/open-library/search/?q=nombre_del_libro`

La respuesta devuelve título, autor, editorial, año de publicación, ISBN,
portada, clave Open Library, enlace externo y si el título ya existe en el
catálogo local. La futura interfaz del lector podrá utilizar estos datos para
mostrar resultados visuales y permitir seleccionar un libro antes de enviar
la solicitud de adquisición.

## Configuración y ejecución

1. Clona este repositorio
2. Instala las dependencias: pip install -r requirements.txt
3. Copia .env.example a .env y configura las variables:
   - SECRET_KEY: clave secreta de Django
   - DEBUG: True para desarrollo / False para producción
   - ALLOWED_HOSTS: lista separada por comas
4. Aplica migraciones: python manage.py migrate
5. Crea superusuario: python manage.py createsuperuser
6. Ejecuta el servidor: python manage.py runserver

## Nota de seguridad

SECRET_KEY y DEBUG se configuran mediante variables de entorno. Nunca commitees tu archivo .env. Usa .env.example como plantilla.