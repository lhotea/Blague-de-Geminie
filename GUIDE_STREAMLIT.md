# 🏃 Guide d'utilisation - Mon Coach Triathlon IA

## 🚀 Comment lancer l'application

### Étape 1 : Installer les dépendances

Si ce n'est pas déjà fait, installe toutes les dépendances :

```bash
pip install -r requirements.txt
```

### Étape 2 : Lancer l'application Streamlit

Dans le terminal, depuis le dossier du projet, tape :

```bash
streamlit run app.py
```

### Étape 3 : Utiliser l'application

1. **Ouvre ton navigateur** : Streamlit va automatiquement ouvrir une page dans ton navigateur (généralement à l'adresse `http://localhost:8501`)

2. **Colle tes données Strava** : Dans la zone de texte, colle tes données Strava (format export ou CSV)

3. **Clique sur "Analyser"** : Le bouton va analyser tes données et afficher :
   - Les statistiques principales (Volume total, Course, Ski, etc.)
   - Un graphique de répartition des sports
   - Le message sarcastique du coach GPT-5-nano

4. **Consulte les détails** : Clique sur "Détails supplémentaires" pour voir plus d'informations

## 📝 Format des données

L'application accepte deux formats :

### Format Strava export (recommandé)
```
Ski nordiquedim. 04/01/2026Vom Bahnhof hei5:041,13 km11 m1
Course à piedjeu. 01/01/2026Left my legs in 2025 🙈1:48:0814,60 km140 m24
```

### Format CSV simple
```
2024-01-15, Course à pied, 1h30, 15km
2024-01-16, Ski de fond, 2h00, 20km
```

## ⚙️ Configuration

Assure-toi d'avoir un fichier `.env` avec ta clé API OpenAI :

```
OPENAI_API_KEY=sk-ta-cle-api-ici
```

## 🛑 Arrêter l'application

Pour arrêter l'application, appuie sur `Ctrl+C` dans le terminal.

## 💡 Astuces

- L'application se met à jour automatiquement quand tu modifies le code
- Tu peux partager l'URL avec d'autres personnes sur ton réseau local
- Les données ne sont pas sauvegardées, elles restent dans ta session
