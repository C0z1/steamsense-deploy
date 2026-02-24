# Deploy (steamsense-deploy)

⚠️ Este deploy se hace **solo desde la copia** `steamsense-deploy`.  
El proyecto original `steamsense` queda intacto.

## Repositorio Git (para Render + Vercel)

1. **Crear un repositorio nuevo en GitHub** (mismo usuario que uses, ej. `steamsense-deploy`).
   - No inicialices con README, .gitignore ni licencia.

2. **Subir este código** (si aún no lo hiciste):

   ```bash
   cd steamsense-deploy
   git remote add origin https://github.com/<TU_USUARIO>/<NOMBRE_REPO>.git
   git push -u origin main
   ```

   Si ya añadiste un `origin` distinto, cámbialo:

   ```bash
   git remote set-url origin https://github.com/<TU_USUARIO>/<NOMBRE_REPO>.git
   git push -u origin main
   ```

3. **Conectar en Render**: Dashboard → New → Web Service → conectar el repo de GitHub → elegir este repositorio.

4. **Conectar en Vercel**: Import Git Repository → elegir el mismo repositorio → Root Directory = `frontend`.

---

## Frontend (Next.js) → Vercel

- **Root Directory**: `frontend`
- **Framework preset**: Next.js

### Variables de entorno (Vercel)

- **`NEXT_PUBLIC_API_URL`** = `https://<tu-backend>.onrender.com`

Notas:
- El frontend **ya no tiene fallback a `localhost`**. Si no configuras `NEXT_PUBLIC_API_URL`, el build/runtime fallará.

## Backend (FastAPI) → Render

Crear un **Web Service (Python)**.

- **Root Directory**: `backend`
- **Build command**: `pip install -r requirements.txt`
- **Start command**:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Variables de entorno (Render)

Mínimas recomendadas:

- **`ENV`** = `production`
- **`JWT_SECRET`** = (un secreto largo)
- **`STEAM_API_KEY`** = (Steam Web API key)
- **`FRONTEND_URL`** = `https://<tu-frontend>.vercel.app`
- **`CORS_ORIGINS`** = `https://<tu-frontend>.vercel.app`

Opcionales (pero útiles):
- **`ITAD_API_KEY`** = (IsThereAnyDeal API key)
- **`DUCKDB_PATH`** = ruta a DuckDB en un disco persistente (recomendado)

#### DuckDB en Render (recomendado)

Si quieres que la DB persista entre deploys/restarts:

- Agrega un **Disk** en Render (ej. montado en `/var/data`)
- Configura:
  - `DUCKDB_PATH=/var/data/steamsense.duckdb`

## CORS (requisito)

El backend ya usa `CORS_ORIGINS` (separado por comas) y lo aplica en `main.py`.

Ejemplo:

- `CORS_ORIGINS=https://<tu-frontend>.vercel.app,https://<tu-dominio-custom.com>`

## Verificación (producción)

- El frontend **NO** debe usar `localhost` (solo `NEXT_PUBLIC_API_URL`).
- Endpoints deben responder con token JWT válido:
  - `GET /me/library`
  - `GET /me/wishlist`
  - `GET /me/recommendations`

## Steam Login (OpenID)

- `/auth/steam` ahora construye el callback usando el **dominio real del backend** (`request.base_url`), para que funcione en Render sin hardcodear `localhost`.
- El redirect post-login se hace a `FRONTEND_URL` (env var).

