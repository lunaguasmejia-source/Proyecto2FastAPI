# TechGear · Sistema híbrido de catálogo y pedidos

Aplicación web híbrida para una tienda en línea:

- **API (FastAPI + MongoDB Atlas):** administra productos, usuarios y pedidos.
- **Portal web (Django, patrón MVT):** consume la API por HTTP y muestra el catálogo, el login y las compras.

## Despliegues

| Servicio | URL |
|---|---|
| Portal web (Django en Vercel) | https://proyecto2-fast-api.vercel.app/ |
| API (FastAPI en Render) | https://techgear-api-1pnp.onrender.com |
| Documentación Swagger | https://techgear-api-1pnp.onrender.com/docs |
| Estado de la API | https://techgear-api-1pnp.onrender.com/health |

> La API está en el plan gratuito de Render: se "duerme" tras 15 minutos sin uso y la primera petición puede tardar cerca de un minuto. Para una demo, abre primero `/health`.

## Tecnologías

- Python 3, FastAPI, Pydantic, Uvicorn
- MongoDB Atlas (PyMongo)
- Autenticación: JWT (usuarios) y API key (administración desde el servidor)
- Django 5 (plantillas, sesiones), Requests
- Despliegue: Render (API) y Vercel (web)

## Estructura del repositorio

```
.
├── techgear_api/            # Código de FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── security.py      # API key y JWT
│   │   ├── utils.py
│   │   ├── models/          # Esquemas Pydantic (producto, pedido, usuarios)
│   │   └── routers/         # productos, pedidos, usuarios
│   ├── requirements.txt
│   └── .env.example
├── techgear_web/            # Proyecto Django
│   ├── manage.py
│   ├── techgear_web/        # settings, urls
│   ├── store/               # vistas, urls, cliente de la API, decoradores
│   ├── templates/           # plantillas HTML
│   ├── requirements.txt
│   └── .env.example
└── README.md
```

## Roles

| Rol | Qué puede hacer |
|---|---|
| **Cliente** | Ver el catálogo, comprar productos y consultar su historial en "Mis pedidos". |
| **Administrador** | Ver el panel, crear, editar y eliminar productos. No realiza compras. |

El rol se guarda en la colección `usuarios` de MongoDB. Todos los registros nuevos son **cliente**. Para crear un administrador, regístrate normalmente y, en Atlas (colección `usuarios`), cambia el campo `rol` a `administrador`.

En el login se elige "Cliente" o "Administrador", pero el sistema compara esa opción con el rol real guardado en la base de datos.

## Endpoints de la API

| Método | Ruta | Acceso | Descripción |
|---|---|---|---|
| GET | `/health` | Público | Estado de la API y de MongoDB |
| GET | `/productos/` | Público | Lista productos (`?categoria=`, `skip`, `limit`) |
| GET | `/productos/{id}` | Público | Detalle de un producto |
| POST | `/productos/` | API key | Crea un producto |
| PUT | `/productos/{id}` | API key | Actualiza un producto |
| DELETE | `/productos/{id}` | API key | Elimina un producto |
| POST | `/usuarios/registro` | Público | Registra un cliente |
| POST | `/usuarios/login` | Público | Devuelve el token JWT |
| GET | `/usuarios/me` | JWT | Perfil del usuario autenticado |
| POST | `/pedidos/` | JWT | Crea un pedido y descuenta el stock |
| GET | `/pedidos/mios` | JWT | Pedidos del usuario autenticado |
| GET | `/pedidos/{id}` | JWT | Un pedido (solo su dueño o un administrador) |
| GET | `/pedidos/admin/todos` | API key | Todos los pedidos |
| PATCH | `/pedidos/{id}/estado` | API key | Cambia el estado de un pedido |

Códigos principales: `201` creado, `401` sin credenciales o inválidas, `403` sin permiso, `404` no encontrado, `409` conflicto (email repetido o stock insuficiente), `422` datos inválidos.

### Probar en Swagger

1. Abre `/docs`.
2. Para rutas con **JWT**: ejecuta `POST /usuarios/login`, copia el `access_token`, pulsa **Authorize** y pégalo en el campo `HTTPBearer` (sin la palabra `Bearer`).
3. Para rutas con **API key**: pulsa **Authorize** y pega la clave en `APIKeyHeader`.

## Variables de entorno

Nunca subas archivos `.env` al repositorio. Usa los `.env.example` como guía.

### `techgear_api/.env`

| Variable | Descripción |
|---|---|
| `MONGODB_URI` | Cadena de conexión de MongoDB Atlas |
| `MONGODB_DB` | Nombre de la base de datos (`techgear`) |
| `API_KEY` | Clave para las rutas de administración |
| `JWT_SECRET` | Clave para firmar los tokens JWT |
| `JWT_EXPIRE_MINUTES` | Duración del token en minutos (por defecto `60`) |

### `techgear_web/.env`

| Variable | Descripción |
|---|---|
| `API_URL` | URL de la API (`http://127.0.0.1:8000` en local) |
| `API_KEY` | La **misma** clave configurada en la API |
| `SECRET_KEY` | Clave secreta de Django |
| `DEBUG` | `True` en desarrollo, `False` en producción |

Para generar una clave segura:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Ejecutar en local

Necesitas Python 3.12 o superior, una cuenta de MongoDB Atlas y dos terminales.

### 1. API (puerto 8000)

```bash
cd techgear_api
python -m venv venv
source venv/bin/activate        
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Documentación en http://127.0.0.1:8000/docs

En Atlas, agrega tu IP en **Network Access** para poder conectarte.

### 2. Portal web (puerto 8001)

```bash
cd techgear_web
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8001
```

Abre http://127.0.0.1:8001

Si cambias un archivo `.env`, reinicia el servidor correspondiente.

## Despliegue

### API en Render

- **Root Directory:** `techgear_api`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Variables:** `MONGODB_URI`, `MONGODB_DB`, `API_KEY`, `JWT_SECRET`, `JWT_EXPIRE_MINUTES`, `PYTHON_VERSION`
- En Atlas, **Network Access** debe permitir las IP de Render (`0.0.0.0/0` en este taller).

### Web en Vercel

- **Root Directory:** `techgear_web`
- **Variables:** `API_URL` (URL de Render), `API_KEY`, `SECRET_KEY`, `DEBUG=False`
- Las sesiones se guardan en cookies firmadas, porque Vercel no tiene disco persistente.

## Flujo de la aplicación

1. El visitante ve el catálogo. Al pulsar **Comprar**, si no tiene sesión, pasa al login (o al registro) y luego vuelve a la compra.
2. Al iniciar sesión, Django recibe el JWT de la API y lo guarda en la sesión del usuario.
3. El cliente confirma la compra: la API valida el token, descuenta el stock de forma atómica, calcula el total y registra el pedido a nombre del usuario autenticado.
4. El cliente consulta sus compras en **Mis pedidos**.
5. El administrador gestiona los productos desde el **Panel admin**. Django envía la `API_KEY` a la API desde el servidor, sin exponerla al navegador.

## Control de versiones

Todo el trabajo se realizó de forma secuencial en la rama `main`, con commits descriptivos por clase.

| Clase | Contenido |
|---|---|
| 1 | Estructura del repositorio, conexión a MongoDB Atlas y modelos Pydantic |
| 2 | CRUD de productos y endpoints de pedidos en FastAPI, con despliegue en Render |
| 4 | Login con JWT, sesiones y plantillas del catálogo en Django |
| 5 | Compra de productos, historial de pedidos, panel admin completo y rediseño responsive |