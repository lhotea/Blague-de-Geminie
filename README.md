# 🤣 Script de Blague avec OpenAI

Un script Python super simple pour demander à l'IA de raconter des blagues !

## 📚 Explication Simple (comme si tu avais 10 ans)

### Qu'est-ce qu'on fait ici ?

Imagine que tu veux parler à un robot super intelligent qui peut raconter des blagues. Ce script Python, c'est comme un téléphone qui te permet d'appeler ce robot et de lui demander une blague !

### Les étapes en langage simple :

1. **Importer les outils** : On dit à Python "j'ai besoin de ces outils pour parler à l'API"
   - `os` : pour lire les secrets (comme les mots de passe)
   - `openai` : c'est la bibliothèque qui sait comment parler à OpenAI

2. **Se connecter** : On donne notre clé secrète (comme un mot de passe) pour prouver qu'on a le droit d'utiliser l'API

3. **Demander une blague** : On envoie un message au robot qui dit "Raconte-moi une blague !"

4. **Recevoir et afficher** : Le robot nous répond avec une blague, et on l'affiche à l'écran !

## 🚀 Comment utiliser ce script

### Étape 1 : Installer Python
Assure-toi d'avoir Python installé sur ton ordinateur.

### Étape 2 : Installer la bibliothèque OpenAI
Ouvre un terminal et tape :
```bash
pip install openai
```

### Étape 3 : Obtenir une clé API
1. Va sur https://platform.openai.com/
2. Crée un compte ou connecte-toi
3. Va dans "API Keys" (Clés API)
4. Crée une nouvelle clé et copie-la (elle ressemble à : `sk-...`)

### Étape 4 : Configurer ta clé API

**Sur Mac/Linux :**
Ouvre un terminal et tape :
```bash
export OPENAI_API_KEY="ta-clé-api-ici"
```

**Sur Windows :**
Ouvre PowerShell et tape :
```powershell
$env:OPENAI_API_KEY="ta-clé-api-ici"
```

⚠️ **Important** : Remplace `"ta-clé-api-ici"` par ta vraie clé API !

### Étape 5 : Lancer le script
Dans le terminal, va dans le dossier du projet et tape :
```bash
python blague.py
```

## 🎯 Résultat attendu

Tu devrais voir quelque chose comme :
```
🤖 Je demande une blague à l'ordinateur intelligent...

😄 Voici la blague :
Pourquoi les plongeurs plongent-ils toujours en arrière et jamais en avant ?
Parce que sinon ils tombent dans le bateau !
```

## 💡 Pour aller plus loin

Tu peux modifier le message dans le script pour demander :
- Des blagues sur un thème spécifique
- Des blagues plus longues
- Des devinettes
- Etc.

Amuse-toi bien ! 🎉
