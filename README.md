# 🏃 Mon Coach Triathlon IA

Une application Streamlit intelligente qui analyse vos données d'entraînement Strava et vous fournit un feedback sarcastique et motivant grâce à l'IA GPT-5-nano!

## ✨ Fonctionnalités

### 🔐 Authentification Multi-Utilisateurs (OAuth)
- **Connexion Strava sécurisée** : Chaque utilisateur se connecte avec son propre compte Strava
- **Gestion automatique des tokens** : Auto-rafraîchissement des tokens expirés
- **Sessions isolées** : Chaque utilisateur voit uniquement ses propres données
- **Déconnexion propre** : Nettoyage sécurisé de la session

### 📊 Analyse des Données
- **Import automatique depuis Strava** : Récupération de vos 50 dernières activités via l'API
- **Import de fichiers** : Support CSV et Excel avec détection automatique du format
- **Parseurs multi-formats** : Compatible avec différents exports de données Strava
- **Enrichissement météo** : Ajout automatique des données météo historiques (température, précipitations, vent)

### 📈 Statistiques et Visualisations
- Volume total d'entraînement (heures)
- Répartition par sport (Course à pied, Ski de fond, etc.)
- Nombre d'activités et durée moyenne
- Distance totale parcourue
- Analyse par semaine avec détection de surcharge (>10h/semaine)
- Graphiques interactifs (Plotly)

### 🤖 Coach IA Sarcastique
- **Feedback personnalisé** : Analyse de vos stats avec humour piquant
- **Chat interactif** : Posez des questions à votre coach IA sur vos entraînements
- **Conseils motivants** : Recommandations constructives avec une touche d'humour

## 🚀 Installation

### Prérequis
- Python 3.8+
- Compte Strava
- Clé API OpenAI
- Application Strava OAuth configurée

### Installation des dépendances
```bash
pip install -r requirements.txt
```

### Configuration des Secrets

#### En Local
Crée un fichier `.streamlit/secrets.toml`:
```toml
# OpenAI API
OPENAI_API_KEY = "sk-..."

# Strava OAuth
STRAVA_CLIENT_ID = "123456"
STRAVA_CLIENT_SECRET = "abc123def456..."

# URL de redirection (optionnel)
REDIRECT_URI = "http://localhost:8501"
```

#### Configuration de l'App Strava
1. Va sur https://www.strava.com/settings/api
2. Crée une nouvelle application
3. Configure les **Authorization Callback Domains**:
   - Pour le développement local: `localhost`
   - Pour la production: `your-app.streamlit.app`
4. Note ton **Client ID** et **Client Secret**

## 🎯 Utilisation

### Lancer l'Application
```bash
streamlit run app.py
```

### Workflow Utilisateur

1. **Connexion**
   - Clique sur "Se connecter avec Strava"
   - Autorise l'application à accéder à tes activités
   - Tu es redirigé automatiquement vers l'app

2. **Récupération des Données**
   - Option A: Clique sur "Récupérer mes activités" pour importer depuis Strava
   - Option B: Upload un fichier CSV/Excel avec tes données

3. **Analyse**
   - Consulte tes statistiques détaillées
   - Découvre la répartition de tes sports
   - Analyse l'évolution hebdomadaire
   - Reçois un feedback sarcastique de ton coach IA

4. **Chat Interactif**
   - Pose des questions à ton coach
   - Reçois des conseils personnalisés
   - Analyse plus en détail tes performances

## 📁 Structure du Projet

```
Blague-de-Geminie/
├── app.py                          # Application Streamlit principale
├── analyse_strava.py               # Fonctions d'analyse et parseurs
├── blague.py                       # Script de test OpenAI simple
├── get_token.py                    # Script legacy (obsolète)
├── requirements.txt                # Dépendances Python
├── Dockerfile                      # Image Docker de l'app
├── docker-compose.yml              # Orchestration Docker locale
├── .dockerignore                   # Fichiers exclus du build Docker
├── .env.example                    # Template des variables d'environnement
├── ENV_EXAMPLE.txt                 # Exemple de configuration (legacy)
├── OAUTH_MIGRATION.md             # Guide de migration OAuth
├── GUIDE_STREAMLIT.md             # Guide Streamlit
├── tests/                          # Suite de tests
│   ├── test_analyse_strava.py     # Tests des parseurs (54 tests)
│   ├── test_openai_integration.py # Tests OpenAI (17 tests)
│   └── README.md                  # Documentation des tests
└── .streamlit/
    └── secrets.toml               # Configuration locale (gitignored)
```

## 🧪 Tests

### Lancer les Tests
```bash
# Tous les tests
pytest tests/

# Avec couverture
pytest tests/ --cov=analyse_strava --cov-report=term-missing

# Tests spécifiques
pytest tests/test_analyse_strava.py -v
pytest tests/test_openai_integration.py -v
```

### Couverture Actuelle
- **71 tests** au total
- **61% de couverture** sur `analyse_strava.py`
- Tests complets des parseurs multi-formats
- Tests mocks de l'API OpenAI
- Tests de gestion d'erreurs

## 🔐 Sécurité

### OAuth Multi-Utilisateurs
- ✅ Tokens stockés dans `st.session_state` (mémoire, par session)
- ✅ Pas de stockage persistant côté client
- ✅ Auto-rafraîchissement des tokens
- ✅ Chaque utilisateur a des données isolées
- ✅ Nettoyage propre à la déconnexion

### Bonnes Pratiques
- 🔒 Ne jamais committer `.streamlit/secrets.toml`
- 🔒 Ne jamais partager tes clés API
- 🔒 Utiliser des variables d'environnement en production
- 🔒 Configurer correctement les domaines autorisés sur Strava

## 📚 Documentation Détaillée

- **[OAUTH_MIGRATION.md](OAUTH_MIGRATION.md)** : Guide complet de migration OAuth
- **[GUIDE_STREAMLIT.md](GUIDE_STREAMLIT.md)** : Guide d'utilisation Streamlit
- **[tests/README.md](tests/README.md)** : Documentation de la suite de tests
- **[ENV_EXAMPLE.txt](ENV_EXAMPLE.txt)** : Exemple de configuration

## 🐳 Déploiement avec Docker

### Prérequis
- Docker et Docker Compose installés

### Configuration

1. **Copie le template de configuration** :
```bash
cp .env.example .env
```

2. **Édite `.env`** avec tes vraies clés :
```env
STRAVA_CLIENT_ID=ton_client_id
STRAVA_CLIENT_SECRET=ton_client_secret
REDIRECT_URI=http://localhost:8501
OPENAI_API_KEY=sk-xxx
```

### Lancement Local avec Docker Compose

```bash
# Build et lancement
docker-compose up --build

# En arrière-plan
docker-compose up -d --build

# Arrêter
docker-compose down
```
→ L'app sera disponible sur http://localhost:8501

### Lancement Manuel avec Docker

```bash
# Build l'image
docker build -t blague-geminie .

# Lancer le container
docker run -p 8501:8501 --env-file .env blague-geminie
```

### Déploiement Cloud avec Docker

Le `Dockerfile` est compatible avec la plupart des plateformes cloud :

| Plateforme | Méthode |
|------------|---------|
| **Railway** | Connecte ton repo GitHub, le Dockerfile est détecté automatiquement |
| **Render** | Crée un "Web Service" et connecte ton repo |
| **Fly.io** | `flyctl launch` puis `flyctl deploy` |
| **Google Cloud Run** | `gcloud run deploy --source .` |
| **Azure Container Apps** | Via Azure CLI ou portail |

**Important** : Configure les variables d'environnement dans l'interface de chaque plateforme (pas le fichier `.env`).

## 🚀 Déploiement sur Streamlit Cloud

> ⚠️ Note : OAuth peut parfois causer des boucles de redirection sur Streamlit Cloud. Le déploiement Docker est plus robuste.

1. Push ton code sur GitHub
2. Va sur https://streamlit.io/cloud
3. Connecte ton repo GitHub
4. Configure les secrets dans les paramètres de l'app
5. Mets à jour `REDIRECT_URI` avec l'URL de ton app
6. Configure les Authorization Callback Domains sur Strava

## 🐛 Dépannage

### Problème: "Configuration OAuth manquante"
**Solution**: Vérifie que `STRAVA_CLIENT_ID` et `STRAVA_CLIENT_SECRET` sont dans tes secrets

### Problème: "Redirect URI mismatch"
**Solution**: Configure le bon domaine dans les paramètres de ton app Strava

### Problème: Token expiré
**Solution**: Déconnecte-toi et reconnecte-toi. Les tokens sont automatiquement rafraîchis normalement.

## 🎨 Captures d'Écran

### Écran de Connexion
Interface simple avec bouton OAuth Strava

### Dashboard Statistiques
Métriques détaillées, graphiques interactifs, feedback IA

### Chat Interactif
Conversation avec le coach IA pour des conseils personnalisés

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésite pas à :
- Signaler des bugs
- Proposer des nouvelles fonctionnalités
- Améliorer la documentation
- Ajouter des tests

## 📜 Licence

Ce projet est fourni tel quel, à des fins éducatives et personnelles.

## 🙏 Remerciements

- [Strava API](https://developers.strava.com/) pour l'accès aux données d'entraînement
- [OpenAI](https://openai.com/) pour l'API GPT-5-nano
- [Streamlit](https://streamlit.io/) pour le framework d'application web
- [Open-Meteo](https://open-meteo.com/) pour les données météo historiques

## 📞 Support

Pour toute question ou problème :
1. Consulte la documentation dans `/docs`
2. Vérifie les issues GitHub existantes
3. Crée une nouvelle issue si nécessaire

---

**Bon entraînement et amuse-toi bien avec ton coach IA sarcastique ! 🏃💨**
