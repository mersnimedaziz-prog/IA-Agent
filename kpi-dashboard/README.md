# Agent IA Delivery KPI Dashboard

Projet de stage basé sur :

- Angular 21
- FastAPI
- Docker
- GitHub Actions CI/CD
- KPI Dashboard
- Analyse Jira
- Chatbot local de données Jira

---

# Fonctionnalités principales

## KPI mensuel

- Upload fichiers Jira mensuels
- Validation structure Jira
- Détection fichier déjà importé/modifié
- Calcul KPI mensuel
- Historique Results / Targets
- Comparaison Result vs Target
- Diagrammes mensuels

## Analyses détaillées

- Daily Summary
- Role Summary
- Author Summary

## Gestion multi-fichiers

- Historique des fichiers uploadés
- Sélection fichier source
- Analyse des anciens mois

## Docker

Application conteneurisée avec :

- Backend FastAPI
- Frontend Angular + Nginx
- Docker Compose

## CI/CD

Pipeline GitHub Actions :

- Frontend CI
- Backend CI
- Docker Build Validation

---

# Lancement local

## Backend

```bash
cd backend
uvicorn main:app --reload
```

## Frontend

```bash
cd kpi-dashboard
npm install
ng serve
```

Frontend :

```text
http://localhost:4200
```

Backend :

```text
http://localhost:8000/docs
```

---

# Docker

## Build et lancement

```bash
docker compose up --build
```

Frontend :

```text
http://localhost:4200
```

Backend Swagger :

```text
http://localhost:8000/docs
```

## Arrêt

```bash
docker compose down
```

---

# Tests

## Angular

```bash
ng test
```

## Build Angular

```bash
ng build
```

---

# Auteur

Mohamed Aziz Mersni