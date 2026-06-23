# Docker setup - Agent IA Delivery

## 1. Copier les fichiers
Copier chaque fichier dans le dossier correspondant :

- docker-compose.yml -> racine stage-ia/
- backend/Dockerfile -> backend/
- backend/.dockerignore -> backend/
- backend/requirements.txt -> backend/ si non existant
- kpi-dashboard/Dockerfile -> kpi-dashboard/
- kpi-dashboard/nginx.conf -> kpi-dashboard/
- kpi-dashboard/.dockerignore -> kpi-dashboard/

## 2. Lancer
Depuis la racine :

```powershell
docker compose up --build
```

Frontend : http://localhost:4200
Backend Swagger : http://localhost:8000/docs

## 3. Arrêter
```powershell
docker compose down
```

## 4. Garder les données
Le volume `./backend/data:/app/data` conserve les fichiers mensuels, audits, JSON et SQLite.
