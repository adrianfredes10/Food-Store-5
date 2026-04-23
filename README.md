# FoodStore

E-commerce gourmet (FastAPI + SQLModel + React/Vite).

**Repositorio:** [github.com/adrianfredes10/Food-Store-5](https://github.com/adrianfredes10/Food-Store-5)

**Base de datos:** el proyecto usa **PostgreSQL** como motor principal (conexión vía `DATABASE_URL` con esquema `postgresql+psycopg2://...` y driver `psycopg2-binary`). La sección [Desarrollo con SQLite](#desarrollo-con-sqlite) es solo una alternativa opcional para desarrollo local; para entrega y entornos reales se espera **PostgreSQL**.

## Setup

1. **Clonar** el repositorio: `git clone https://github.com/adrianfredes10/Food-Store-5.git`

2. **Backend**
   - Entrar en `backend/`.
   - Instalar dependencias Python (elegí una opción):
     - Desde la **raíz** del repo: `pip install -r requirements.txt` (archivo pedido en la entrega del parcial), **o**
     - Desde `backend/`: `pip install -e ".[dev]"` (instala el paquete editable + herramientas de test).
   - Copiar variables de entorno: crear `.env` a partir de `backend/.env.example` y completar al menos `DATABASE_URL` y `JWT_SECRET_KEY`.
   - Para **PostgreSQL** (entrega): crear la base y usuario, poner `DATABASE_URL=postgresql+psycopg2://...`, y aplicar migraciones:
     - `alembic upgrade head`
   - Cargar datos iniciales (roles, estados, admin, catálogo demo si hace falta):
     - `python -m app.db.seed`
   - Levantar la API (desde `backend/`):
     - `uvicorn app.main:app --reload --host 127.0.0.1 --port 8008`

3. **Frontend**
   - `cd frontend`
   - `npm install`
   - Configurar `frontend/.env` si hace falta (p. ej. `VITE_API_BASE_URL` apuntando al backend).
   - `npm run dev` y abrir la URL que muestre Vite (típicamente http://localhost:5173).

### Primera migración con Alembic (autogenerate)

Si agregás o cambiás modelos y necesitás una nueva revisión, desde `backend/` con `DATABASE_URL` y `JWT_SECRET_KEY` cargados:

```bash
alembic revision --autogenerate -m "initial_schema"
```

Ese comando compara `SQLModel.metadata` con el estado real de la base y genera un script en `alembic/versions/`. Revisá el diff antes de commitear. Luego:

```bash
alembic upgrade head
```

**Nota:** En el repo ya existe una migración inicial (`initial_schema`) compatible con el modelo actual; para un entorno nuevo con PostgreSQL alcanza con `alembic upgrade head` sin volver a autogenerar.

## Desarrollo con SQLite (opcional, no reemplaza PostgreSQL)

Si `DATABASE_URL` apunta a `sqlite:///...`, al arrancar la API el bootstrap ejecuta `create_all` y las semillas (no hace falta Alembic para arrancar, aunque podés usarlo igual). Es cómodo para pruebas locales; **no** es el motor objetivo del proyecto.

## Video de demostración

[Video Food-Store — Google Drive](https://drive.google.com/file/d/15jIlgIpQI47_CmBz1d7gDS2YAWO9AHfg/view?usp=sharing)

## Checklist

Ver [CHECKLIST.md](./CHECKLIST.md)
