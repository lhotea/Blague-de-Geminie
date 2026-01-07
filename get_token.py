import requests

# REMPLACE CES 2 VALEURS PAR LES TIENNES
client_id = '189101'
client_secret = 'a6c7d177fa58ff5447fd04db396b9dd7a5341183'

# 1. Générer l'URL d'autorisation
print("--- ÉTAPE 1 : AUTORISATION ---")
url = f"http://www.strava.com/oauth/authorize?client_id={client_id}&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=activity:read_all"
print(f"Clique sur ce lien (ou copie-le dans ton navigateur) :\n{url}")

# 2. L'utilisateur doit coller le code
print("\nUne fois autorisé, tu seras redirigé vers une page qui échouera (localhost).")
print("Regarde l'URL dans la barre d'adresse. Elle ressemblera à : http://localhost/exchange_token?state=&code=CE_CODE_ICI&scope=...")
code = input("Copie et colle le code (la partie après code= et avant &scope) ici : ")

# 3. Échanger le code contre les tokens
print("\n--- ÉTAPE 2 : ÉCHANGE ---")
payload = {
    'client_id': client_id,
    'client_secret': client_secret,
    'code': code,
    'grant_type': 'authorization_code'
}

response = requests.post("https://www.strava.com/oauth/token", data=payload)
data = response.json()

if 'refresh_token' in data:
    print("\n✅ SUCCÈS ! Voici ton Refresh Token (garde-le précieusement) :")
    print(data['refresh_token'])
else:
    print("\n❌ Erreur :", data)
