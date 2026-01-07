# Script pour raconter une blague avec OpenAI
# C'est comme demander à un robot intelligent de nous faire rire !

import os
from openai import OpenAI
from dotenv import load_dotenv

# Étape 1 : On charge les variables d'environnement depuis le fichier .env
# C'est comme ouvrir un coffre-fort où on garde nos secrets
load_dotenv()

# Étape 2 : On récupère la clé API de façon sécurisée
# On cherche d'abord dans le fichier .env, puis dans les variables d'environnement système
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("❌ Erreur : Clé API non trouvée !")
    print("💡 Astuce : Crée un fichier .env avec ta clé API :")
    print("   OPENAI_API_KEY=sk-ta-cle-api-ici")
    exit(1)

client = OpenAI(api_key=api_key)

# Étape 3 : On demande à l'API de nous raconter une blague
print("🤖 Je demande une blague à l'ordinateur intelligent...")
print()

try:
    # Étape 4 : On envoie notre demande (on appelle ça un "prompt")
    response = client.chat.completions.create(
        model="gpt-5-nano",  # C'est le nom du robot intelligent qu'on utilise
        messages=[
            {
                "role": "user",  # C'est nous qui posons la question
                "content": "Raconte-moi une blague drôle et courte sur le sujet du sport!"  # Notre question
            }
        ],
        max_completion_tokens=5000  # On limite la longueur de la réponse
        # Note : GPT-5-nano utilise des "reasoning tokens" pour réfléchir avant de répondre
        # Il faut donc prévoir assez de tokens pour le raisonnement ET la réponse
        # GPT-5-nano utilise beaucoup de tokens pour réfléchir, donc on en met assez !
    )

    # Étape 5 : On récupère la blague et on l'affiche
    blague = response.choices[0].message.content
    
    if blague and blague.strip():
        print("😄 Voici la blague :")
        print(blague)
    else:
        print("⚠️ La réponse est vide.")
        print("💡 Astuce : GPT-5-nano utilise des tokens pour 'réfléchir' avant de répondre.")
        print("   Si tous les tokens sont utilisés pour le raisonnement, il n'en reste plus pour la réponse !")
        print("   Solution : augmente 'max_completion_tokens' dans le script.")
    
except Exception as e:
    print("❌ Oups ! Il y a eu une erreur :")
    print(f"   Type d'erreur : {type(e).__name__}")
    print(f"   Message : {e}")
    print("\n💡 Astuce : Vérifie que ta clé API est correcte et configurée.")
