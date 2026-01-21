# Migration vers OAuth Multi-Utilisateurs

## 🎯 Objectif

L'application a été transformée pour supporter l'authentification multi-utilisateurs via OAuth, permettant à chaque utilisateur de se connecter avec son propre compte Strava (mode SaaS).

## 📋 Changements Principaux

### Avant (Mono-utilisateur)
- ❌ Utilisait un `STRAVA_REFRESH_TOKEN` unique dans les secrets
- ❌ Tous les utilisateurs voyaient les mêmes données (celles du propriétaire)
- ❌ Pas de vraie authentification utilisateur

### Après (Multi-utilisateurs)
- ✅ Authentification OAuth individuelle pour chaque utilisateur
- ✅ Chaque utilisateur voit ses propres activités Strava
- ✅ Tokens stockés dans `st.session_state` (sécurisé, par session)
- ✅ Auto-rafraîchissement des tokens expirés
- ✅ Déconnexion propre

## 🔧 Configuration

### 1. Secrets Streamlit Requis

Dans `.streamlit/secrets.toml` (local) ou Streamlit Cloud secrets:

```toml
# OpenAI API
OPENAI_API_KEY = "sk-..."

# Strava OAuth
STRAVA_CLIENT_ID = "123456"
STRAVA_CLIENT_SECRET = "abc123def456..."

# URL de redirection (optionnel, par défaut: localhost:8501)
REDIRECT_URI = "http://localhost:8501"  # En local
# REDIRECT_URI = "https://your-app.streamlit.app"  # En production
```

### 2. Configuration de l'Application Strava

1. Va sur https://www.strava.com/settings/api
2. Crée une nouvelle application ou modifie une existante
3. Configure les **Authorization Callback Domains**:
   - Pour le développement local: `localhost`
   - Pour la production: `your-app.streamlit.app`
4. Note ton **Client ID** et **Client Secret**

### 3. Secrets à Supprimer

⚠️ **IMPORTANT**: Supprime `STRAVA_REFRESH_TOKEN` de tes secrets, il n'est plus utilisé.

## 🔐 Flux OAuth Implémenté

```
┌─────────────┐
│  Utilisateur │
└──────┬──────┘
       │ 1. Clique "Se connecter avec Strava"
       ▼
┌─────────────────────────────────────────┐
│ Redirection vers Strava OAuth           │
│ (avec client_id, redirect_uri, scope)   │
└──────┬──────────────────────────────────┘
       │ 2. Utilisateur autorise l'app
       ▼
┌─────────────────────────────────────────┐
│ Strava redirige vers ton app avec CODE  │
└──────┬──────────────────────────────────┘
       │ 3. App détecte le code dans l'URL
       ▼
┌─────────────────────────────────────────┐
│ Échange CODE contre ACCESS_TOKEN        │
│ via POST à /oauth/token                 │
└──────┬──────────────────────────────────┘
       │ 4. Stockage dans st.session_state
       ▼
┌─────────────────────────────────────────┐
│ Token stocké, URL nettoyée              │
│ Utilisateur connecté ✅                 │
└─────────────────────────────────────────┘
```

## 📝 Fonctions Principales Ajoutées

### `generer_url_autorisation_strava()`
Génère l'URL d'autorisation OAuth avec:
- `client_id`
- `redirect_uri` (URL actuelle de l'app)
- `scope=activity:read_all`
- `approval_prompt=force`

### `echanger_code_contre_token(code)`
Échange le code d'autorisation contre un `access_token` et `refresh_token`

### `rafraichir_access_token(refresh_token)`
Rafraîchit un `access_token` expiré

### `obtenir_access_token_actif()`
Retourne un `access_token` valide:
- Utilise le token en session s'il est encore valide
- Rafraîchit automatiquement si expiré dans moins de 5 minutes
- Retourne `None` si pas de token disponible

### Gestion du Callback OAuth
Au chargement de l'app:
1. Vérifie si `code` est présent dans `st.query_params`
2. Si oui, échange le code contre un token
3. Stocke le token dans `st.session_state`
4. Nettoie l'URL avec `st.query_params.clear()`
5. Recharge la page

## 🎨 Changements UI

### Avant Connexion
```
┌────────────────────────────────────┐
│ 🔗 Connexion Strava                │
│                                    │
│ 👤 Connecte-toi avec ton compte    │
│    Strava pour accéder à tes       │
│    activités                       │
│                                    │
│ [🔐 Se connecter avec Strava]      │
│                                    │
│ Tu seras redirigé vers Strava pour │
│ autoriser l'accès à tes activités. │
└────────────────────────────────────┘
```

### Après Connexion
```
┌────────────────────────────────────┐
│ 🔗 Connexion Strava                │
│                                    │
│ ✅ Connecté en tant que John Doe   │
│                                    │
│ [📥 Récupérer mes activités]       │
│                                    │
│ [🚪 Se déconnecter]                │
└────────────────────────────────────┘
```

## 🔒 Sécurité

### Stockage des Tokens
- ✅ Tokens stockés dans `st.session_state` (mémoire, par session)
- ✅ Pas de stockage persistant côté client
- ✅ Tokens effacés à la déconnexion
- ✅ Tokens différents pour chaque utilisateur

### Expiration et Rafraîchissement
- ✅ Auto-vérification de l'expiration avant chaque requête API
- ✅ Rafraîchissement automatique si expiration < 5 minutes
- ✅ Gestion d'erreur si rafraîchissement échoue

### Données Utilisateur
- ✅ Chaque utilisateur voit uniquement ses propres données
- ✅ Pas de mélange de données entre utilisateurs
- ✅ Session isolée par connexion

## 🧪 Tests

### En Local
1. Lance l'app: `streamlit run app.py`
2. Clique sur "Se connecter avec Strava"
3. Autorise l'application sur Strava
4. Vérifie que tu es redirigé vers l'app
5. Vérifie que ton nom d'athlète s'affiche
6. Récupère tes activités
7. Teste la déconnexion

### Tests Multi-Utilisateurs
1. Connecte-toi avec le compte A
2. Récupère les activités
3. Déconnecte-toi
4. Connecte-toi avec le compte B
5. Vérifie que les activités sont différentes

## 📊 Gestion de Session

### Clés de `st.session_state`
```python
# Après connexion OAuth
st.session_state["strava_access_token"]   # Token d'accès actif
st.session_state["strava_refresh_token"]  # Token de rafraîchissement
st.session_state["strava_expires_at"]     # Timestamp d'expiration
st.session_state["strava_athlete"]        # Info de l'athlète (nom, etc.)
st.session_state["strava_connected"]      # Boolean: connecté ou non

# Données d'activités
st.session_state["donnees_strava"]        # Données formatées pour l'analyse
st.session_state["activites_strava_brutes"]  # Données brutes de l'API
st.session_state["nb_activites_strava"]   # Nombre d'activités
```

### Nettoyage à la Déconnexion
```python
# Supprime toutes les clés commençant par "strava_"
for key in list(st.session_state.keys()):
    if key.startswith("strava_"):
        del st.session_state[key]
```

## 🐛 Dépannage

### Problème: "Configuration OAuth manquante"
**Solution**: Vérifie que `STRAVA_CLIENT_ID` et `STRAVA_CLIENT_SECRET` sont dans tes secrets

### Problème: "Redirect URI mismatch"
**Solution**:
1. Vérifie que ton `REDIRECT_URI` dans les secrets correspond exactement à l'URL de ton app
2. Configure le domaine autorisé dans les paramètres de ton app Strava

### Problème: Token expiré immédiatement
**Solution**: Vérifie l'heure système de ton serveur (les timestamps doivent être corrects)

### Problème: L'utilisateur perd sa session au rechargement
**Comportement normal**: Les sessions Streamlit sont volatiles. Si la page est rechargée (F5), la session est perdue et l'utilisateur doit se reconnecter. C'est une limitation de Streamlit, pas un bug.

**Solutions possibles**:
- Utiliser `st.cache_resource` avec des cookies (complexe)
- Implémenter un système de base de données pour stocker les tokens (non recommandé pour la sécurité)
- Accepter ce comportement (recommandé pour une app Streamlit simple)

## 🚀 Déploiement

### Streamlit Cloud
1. Push ton code sur GitHub
2. Va sur https://streamlit.io/cloud
3. Déploie ton app
4. Configure les secrets dans les paramètres de l'app:
   ```toml
   OPENAI_API_KEY = "sk-..."
   STRAVA_CLIENT_ID = "123456"
   STRAVA_CLIENT_SECRET = "abc..."
   REDIRECT_URI = "https://your-app.streamlit.app"
   ```
5. Mets à jour les Authorization Callback Domains sur Strava avec `your-app.streamlit.app`

### Production Checklist
- [ ] Secrets configurés
- [ ] REDIRECT_URI correct dans les secrets
- [ ] Authorization Callback Domain configuré sur Strava
- [ ] Test de connexion fonctionnel
- [ ] Test de déconnexion fonctionnel
- [ ] Test multi-utilisateurs OK

## 📚 Ressources

- [Strava OAuth Documentation](https://developers.strava.com/docs/authentication/)
- [Streamlit Session State](https://docs.streamlit.io/library/api-reference/session-state)
- [Streamlit Query Params](https://docs.streamlit.io/library/api-reference/utilities/st.query_params)

## ✅ Résumé des Avantages

1. **Multi-utilisateurs**: Chaque utilisateur a son propre compte
2. **Sécurité**: Tokens jamais exposés, stockage en mémoire
3. **Simplicité**: Pas besoin de base de données
4. **Scalable**: Support d'un nombre illimité d'utilisateurs
5. **Standard**: Utilise le flux OAuth standard de Strava
6. **Maintenance**: Auto-rafraîchissement des tokens
