FROM python:3.11-slim

# Métadonnées
LABEL maintainer="Arnaud Lhote"
LABEL description="Blague de Geminie - Analyse Strava avec IA"

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Répertoire de travail
WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY . .

# Port par défaut (Railway définit $PORT dynamiquement)
ENV PORT=8501
EXPOSE 8501

# Commande de démarrage (utilise $PORT pour Railway)
CMD streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
