# 🔍 Guide de Diagnostic OAuth Strava

## Problème: "Max challenge attempts exceeded"

Ce message de Strava indique généralement un problème de configuration OAuth. Voici comment le résoudre :

---

## ✅ Checklist de Configuration

### 1. Vérifier ton Application Strava

Va sur https://www.strava.com/settings/api

#### A. Authorization Callback Domain
**CRITIQUE**: Ce champ doit contenir UNIQUEMENT le domaine, PAS l'URL complète.

❌ **INCORRECT:**
```
http://localhost:8501
https://localhost:8501
localhost:8501
```

✅ **CORRECT:**
```
localhost
```

Pour la production :
```
your-app.streamlit.app
```

#### B. Vérifier tes Identifiants
- **Client ID** : Doit être un nombre (ex: 123456)
- **Client Secret** : Une longue chaîne alphanumérique

---

### 2. Vérifier tes Secrets Streamlit

#### Fichier: `.streamlit/secrets.toml`

```toml
# Strava OAuth
STRAVA_CLIENT_ID = "123456"  # ⚠️ DOIT être entre guillemets même si c'est un nombre
STRAVA_CLIENT_SECRET = "abc123def456..."

# URL de redirection (DOIT correspondre à ton environnement)
REDIRECT_URI = "http://localhost:8501"  # En local
# REDIRECT_URI = "https://your-app.streamlit.app"  # En production
```

⚠️ **IMPORTANT:**
- `STRAVA_CLIENT_ID` doit être une chaîne (entre guillemets), pas un nombre
- `REDIRECT_URI` doit être l'URL EXACTE de ton app (avec http:// ou https://)

---

### 3. Configuration Strava - Étapes Détaillées

#### Étape 1: Accéder aux Paramètres API
1. Va sur https://www.strava.com/settings/api
2. Si tu n'as pas d'application, clique sur "Create an App"
3. Si tu as déjà une app, clique sur ton app pour la modifier

#### Étape 2: Remplir les Champs

**Application Name:**
```
Mon Coach Triathlon IA
```

**Category:**
```
Training
```

**Club:**
```
(Laisser vide)
```

**Website:**
```
http://localhost:8501
```
(ou ton URL de production)

**Authorization Callback Domain:** ⚠️ **LE PLUS IMPORTANT**
```
localhost
```

Pour plusieurs domaines (local + production), sépare par des virgules :
```
localhost,your-app.streamlit.app
```

**Application Description:**
```
Application d'analyse d'entraînement avec IA
```

#### Étape 3: Sauvegarder
- Clique sur "Update" ou "Create"
- Note ton **Client ID** et **Client Secret**

---

## 🔧 Tests de Diagnostic

### Test 1: Vérifier l'URL d'Autorisation Générée

Ajoute ce code temporairement dans `app.py` (avant le bouton OAuth) :

```python
# CODE DE DEBUG - À RETIRER APRÈS TEST
if st.checkbox("🔍 Afficher l'URL OAuth (debug)"):
    auth_url = generer_url_autorisation_strava()
    if auth_url:
        st.code(auth_url)
        st.info(f"Redirect URI utilisé: {obtenir_redirect_uri()}")
```

Vérifie que :
- Le `client_id` est correct
- Le `redirect_uri` correspond EXACTEMENT à ton environnement
- L'URL est valide (pas de caractères bizarres)

### Test 2: Vérifier les Secrets

Ajoute ce code temporairement :

```python
# CODE DE DEBUG - À RETIRER APRÈS TEST
if st.checkbox("🔍 Vérifier les secrets (debug)"):
    try:
        client_id = st.secrets["STRAVA_CLIENT_ID"]
        st.success(f"✅ STRAVA_CLIENT_ID trouvé: {client_id}")

        client_secret = st.secrets.get("STRAVA_CLIENT_SECRET", "NON TROUVÉ")
        st.success(f"✅ STRAVA_CLIENT_SECRET: {'Trouvé (' + client_secret[:10] + '...)' if client_secret != 'NON TROUVÉ' else 'NON TROUVÉ'}")

        redirect_uri = obtenir_redirect_uri()
        st.success(f"✅ REDIRECT_URI: {redirect_uri}")
    except Exception as e:
        st.error(f"❌ Erreur: {e}")
```

---

## 🐛 Solutions aux Problèmes Courants

### Problème 1: "Max challenge attempts exceeded"

**Causes possibles:**
1. ❌ Authorization Callback Domain contient l'URL complète au lieu du domaine seul
2. ❌ Le `redirect_uri` dans le code ne correspond pas à la config Strava
3. ❌ Trop de tentatives de connexion rapides

**Solutions:**
1. ✅ Configure "localhost" (PAS "http://localhost:8501") dans Authorization Callback Domain
2. ✅ Vérifie que `REDIRECT_URI` dans secrets.toml est correct
3. ✅ Attends 5-10 minutes avant de réessayer
4. ✅ Efface les cookies de ton navigateur pour Strava
5. ✅ Utilise une fenêtre de navigation privée

### Problème 2: "Redirect URI mismatch"

**Causes:**
- Le `redirect_uri` utilisé lors de l'échange du code ne correspond pas à celui de l'autorisation

**Solution:**
- Assure-toi que `REDIRECT_URI` est identique entre :
  - La fonction `generer_url_autorisation_strava()`
  - La fonction `echanger_code_contre_token()`
  - Cette fonctionnalité est maintenant gérée automatiquement par `obtenir_redirect_uri()`

### Problème 3: "Invalid client"

**Causes:**
- Client ID ou Client Secret incorrect

**Solution:**
- Re-vérifie tes identifiants sur https://www.strava.com/settings/api
- Copie-colle avec soin (pas d'espaces)
- Assure-toi que les valeurs sont entre guillemets dans secrets.toml

---

## 🧪 Procédure de Test Complète

### Étape 1: Nettoyer l'État
```bash
# Supprime le cache Streamlit
rm -rf .streamlit/cache

# Efface les cookies Strava dans ton navigateur
# Utilise une fenêtre de navigation privée
```

### Étape 2: Vérifier la Configuration Strava
1. Va sur https://www.strava.com/settings/api
2. Vérifie "Authorization Callback Domain" = `localhost`
3. Note ton Client ID et Client Secret

### Étape 3: Vérifier les Secrets
```toml
# .streamlit/secrets.toml
STRAVA_CLIENT_ID = "123456"  # ⚠️ Entre guillemets
STRAVA_CLIENT_SECRET = "ton_secret_ici"
REDIRECT_URI = "http://localhost:8501"  # URL complète
```

### Étape 4: Redémarrer l'App
```bash
# Tue le processus Streamlit
# Relance
streamlit run app.py
```

### Étape 5: Tester la Connexion
1. Clique sur "Se connecter avec Strava"
2. Tu devrais être redirigé vers Strava
3. Connecte-toi avec tes identifiants Strava
4. Clique sur "Authorize" (Autoriser)
5. Tu devrais être redirigé vers ton app
6. Ton nom devrait s'afficher

---

## 📊 URLs de Référence

### URLs Importantes
- **Page de login Strava:** https://www.strava.com/login
- **Paramètres API:** https://www.strava.com/settings/api
- **Documentation OAuth:** https://developers.strava.com/docs/authentication/

### Format des URLs OAuth

**URL d'autorisation (générée automatiquement):**
```
https://www.strava.com/oauth/authorize?
  client_id=123456&
  response_type=code&
  redirect_uri=http://localhost:8501&
  approval_prompt=force&
  scope=activity:read_all
```

**URL de callback (après autorisation):**
```
http://localhost:8501?
  code=abc123def456&
  scope=read,activity:read_all
```

---

## 🔐 Vérification de Sécurité

### Checklist de Sécurité
- [ ] `STRAVA_CLIENT_SECRET` n'est PAS dans le code source
- [ ] `.streamlit/secrets.toml` est dans `.gitignore`
- [ ] Les secrets ne sont PAS committés dans git
- [ ] Authorization Callback Domain est correctement configuré
- [ ] L'app utilise HTTPS en production

---

## 💡 Conseils

### En Développement Local
- Utilise toujours `http://localhost:8501` (pas `http://127.0.0.1:8501`)
- Configure `localhost` dans Authorization Callback Domain
- Redémarre l'app après avoir modifié les secrets

### En Production (Streamlit Cloud)
- Change `REDIRECT_URI` pour l'URL publique de ton app
- Ajoute le domaine dans Authorization Callback Domain sur Strava
- Teste le flux OAuth complet en production

---

## 🆘 Besoin d'Aide ?

Si le problème persiste après avoir suivi ce guide :

1. **Active le mode debug** avec les codes fournis ci-dessus
2. **Capture d'écran** de :
   - La configuration de ton app Strava
   - Les messages d'erreur dans l'app
   - L'URL OAuth générée
3. **Vérifie les logs** de la console du navigateur (F12)
4. **Essaie en navigation privée** pour éliminer les problèmes de cache

---

## ✅ Configuration Finale Vérifiée

Une fois que tout fonctionne, ta configuration devrait ressembler à :

**Strava API Settings:**
```
Application Name: Mon Coach Triathlon IA
Authorization Callback Domain: localhost
Client ID: 123456
Client Secret: [ton_secret]
```

**`.streamlit/secrets.toml`:**
```toml
STRAVA_CLIENT_ID = "123456"
STRAVA_CLIENT_SECRET = "ton_secret_ici"
REDIRECT_URI = "http://localhost:8501"
OPENAI_API_KEY = "sk-..."
```

**Flux attendu:**
1. Clique "Se connecter avec Strava" ✅
2. Redirection vers Strava ✅
3. Login Strava ✅
4. Autorisation ✅
5. Retour sur l'app avec ton nom affiché ✅
6. Récupération des activités ✅

---

**Si tout est configuré correctement, l'erreur "Max challenge attempts exceeded" devrait disparaître !**
