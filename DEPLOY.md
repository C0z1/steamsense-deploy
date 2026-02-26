# 🚀 Guía de Deploy — SteamSense

## Costos
| Servicio | Plan | Costo |
|---|---|---|
| Vercel (frontend) | Hobby | **$0/mes** |
| Render (backend) | Free | **$0/mes** |
| Render Persistent Disk | 1 GB | **~$0.25/mes** |
| **Total** | | **~$0.25/mes** |

---

## Opción A — Probar en local con Docker (antes del deploy real)

### 1. Configurar variables de entorno
```bash
cp .env.example .env
# Edita .env con tus API keys reales
```

### 2. Levantar todo
```bash
docker compose up --build
```
Espera el mensaje `SteamSense API lista` (~2 min la primera vez).

### 3. Verificar
```bash
curl http://localhost:8000/health
# Abre http://localhost:3000 en el navegador
```

### 4. Poblar datos (primer uso)
```bash
curl -X POST "http://localhost:8000/sync/top?top_n=100"
# Espera 2 min...
curl -X POST "http://localhost:8000/sync/predictions?limit=200"
```

### Comandos útiles
```bash
docker compose down             # Parar todo
docker compose logs backend     # Ver logs del backend
docker compose restart backend  # Reiniciar solo backend
```

---

## Opción B — Deploy en Render + Vercel (producción)

### Paso 1 — Subir a GitHub
```bash
git init && git add . && git commit -m "initial"
git remote add origin https://github.com/tu-usuario/steamsense.git
git push -u origin main
```
⚠️ Verifica que `.env` NO aparece en el commit (está en .gitignore).

### Paso 2 — Backend en Render
1. render.com → New → Web Service → conecta tu repo
2. Render detecta `render.yaml` automáticamente
3. En **Environment Variables** del dashboard agrega manualmente:
   - `STEAM_API_KEY` = tu key
   - `ITAD_API_KEY` = tu key  
   - `JWT_SECRET` = cadena aleatoria larga
   - `CORS_ORIGINS` = (lo agregas después con la URL de Vercel)
   - `FRONTEND_URL` = (ídem)
4. Deploy → copia tu URL: `https://steamsense-backend.onrender.com`

### Paso 3 — Frontend en Vercel
1. vercel.com → New Project → importa el mismo repo
2. Root Directory: `frontend`
3. Environment Variables: `NEXT_PUBLIC_API_URL` = `https://steamsense-backend.onrender.com`
4. Deploy → copia tu URL: `https://steamsense-xxx.vercel.app`

### Paso 4 — Conectar ambos
Vuelve a Render y agrega:
- `CORS_ORIGINS` = `https://steamsense-xxx.vercel.app`
- `FRONTEND_URL` = `https://steamsense-xxx.vercel.app`

Haz Manual Deploy en Render para aplicar.

### Paso 5 — Poblar datos en producción
```bash
BASE=https://steamsense-backend.onrender.com
curl -X POST "$BASE/sync/top?top_n=100"
# Espera 2 min...
curl -X POST "$BASE/sync/predictions?limit=200"
```

---

## ⚠️ Tip: evitar el sleep de Render Free
El backend duerme tras 15 min sin tráfico (tarda ~30s en despertar).
Solución gratis: crea un monitor en uptimerobot.com apuntando a
`https://steamsense-backend.onrender.com/health` cada 10 minutos.
