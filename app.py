"""
Application Streamlit - Mon Coach Triathlon IA
Analyse des données Strava avec feedback sarcastique par GPT-5-nano
"""

import streamlit as st
import pandas as pd
import re
import os
from openai import OpenAI
from dotenv import load_dotenv
import plotly.express as px
import requests
from datetime import datetime
import time
import subprocess

# Configuration de la page
st.set_page_config(
    page_title="Mon Coach Triathlon IA",
    page_icon="🏃",
    layout="wide"
)

# Titre principal
st.title("🏃 Mon Coach Triathlon IA")
st.markdown("---")

# Importer les fonctions d'analyse depuis le script original
# (On va les copier ici pour simplifier, ou on pourrait les importer)
from analyse_strava import (
    parser_donnees_strava,
    calculer_temps_par_semaine,
    comparer_activites,
    generer_feedback_coach
)

# ===== OAUTH FLOW FUNCTIONS =====

def obtenir_redirect_uri():
    """Obtient l'URL de redirection de manière cohérente"""
    try:
        # Essayer d'obtenir depuis les secrets
        redirect_uri = st.secrets.get("REDIRECT_URI", None)
    except:
        redirect_uri = None

    # Si pas dans les secrets, utiliser localhost par défaut
    if not redirect_uri:
        redirect_uri = "http://localhost:8501"

    # Normaliser l'URL (éviter les boucles OAuth dues aux mismatchs)
    redirect_uri = redirect_uri.strip()
    # Forcer https en production (Streamlit Cloud)
    if redirect_uri.startswith("http://") and "localhost" not in redirect_uri:
        redirect_uri = redirect_uri.replace("http://", "https://", 1)
    # Ajouter le schéma si absent
    if not redirect_uri.startswith(("http://", "https://")):
        redirect_uri = f"https://{redirect_uri}"
    # Supprimer le slash final pour cohérence
    redirect_uri = redirect_uri.rstrip("/")

    return redirect_uri


def generer_url_autorisation_strava():
    """Génère l'URL d'autorisation OAuth Strava"""
    try:
        client_id = st.secrets["STRAVA_CLIENT_ID"]
        redirect_uri = obtenir_redirect_uri()

        # Construire l'URL d'autorisation
        auth_url = (
            f"https://www.strava.com/oauth/authorize?"
            f"client_id={client_id}&"
            f"response_type=code&"
            f"redirect_uri={redirect_uri}&"
            f"approval_prompt=force&"
            f"scope=activity:read_all"
        )
        return auth_url
    except KeyError as e:
        st.error(f"❌ Configuration manquante : {e}")
        return None


def echanger_code_contre_token(code):
    """Échange le code d'autorisation contre un access_token"""
    try:
        client_id = st.secrets["STRAVA_CLIENT_ID"]
        client_secret = st.secrets["STRAVA_CLIENT_SECRET"]
        redirect_uri = obtenir_redirect_uri()

        url = "https://www.strava.com/oauth/token"
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri  # IMPORTANT: Doit être identique à l'autorisation
        }

        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()

        data = response.json()
        return {
            "access_token": data.get("access_token"),
            "refresh_token": data.get("refresh_token"),
            "expires_at": data.get("expires_at"),
            "athlete": data.get("athlete")
        }
    except requests.exceptions.RequestException as e:
        response = getattr(e, "response", None)
        status_code = response.status_code if response is not None else None
        response_text = response.text if response is not None else "N/A"

        # Message clair pour la limite d'athlètes connectés (Strava 403)
        if status_code == 403 and "athlete" in response_text.lower():
            st.error("❌ Erreur 403 : limite d'athlètes connectés dépassée.")
            st.info(
                "💡 Strava limite le nombre d'athlètes connectés pour les apps en mode développement. "
                "Déconnecte des comptes de test ou demande une augmentation de quota dans Strava."
            )
        else:
            st.error(f"❌ Erreur lors de l'échange du code : {e}")
            st.error(f"Détails de l'erreur : {response_text}")
        return None
    except Exception as e:
        st.error(f"❌ Erreur inattendue : {e}")
        return None


def rafraichir_access_token(refresh_token):
    """Rafraîchit l'access_token avec un refresh_token"""
    try:
        client_id = st.secrets["STRAVA_CLIENT_ID"]
        client_secret = st.secrets["STRAVA_CLIENT_SECRET"]

        url = "https://www.strava.com/oauth/token"
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }

        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()

        data = response.json()
        return {
            "access_token": data.get("access_token"),
            "refresh_token": data.get("refresh_token"),
            "expires_at": data.get("expires_at")
        }
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erreur lors du rafraîchissement du token : {e}")
        return None
    except Exception as e:
        st.error(f"❌ Erreur inattendue : {e}")
        return None


# ===== GESTION DU CALLBACK OAUTH =====

# Vérifier si on revient d'une autorisation OAuth (code dans l'URL)
if "code" in st.query_params:
    code = st.query_params["code"]

    with st.spinner("🔐 Authentification en cours..."):
        # Échanger le code contre un access_token
        token_data = echanger_code_contre_token(code)

        if token_data and token_data.get("access_token"):
            # Stocker les tokens dans session_state
            st.session_state["strava_access_token"] = token_data["access_token"]
            st.session_state["strava_refresh_token"] = token_data["refresh_token"]
            st.session_state["strava_expires_at"] = token_data["expires_at"]
            st.session_state["strava_athlete"] = token_data.get("athlete", {})
            st.session_state["strava_connected"] = True

            # Nettoyer l'URL (enlever le code)
            st.query_params.clear()
            st.success("✅ Connexion réussie !")
            st.rerun()
        else:
            st.error("❌ Impossible de se connecter à Strava")
            st.query_params.clear()

# ===== END OAUTH FLOW =====

# Fonction pour obtenir un access_token Strava (DEPRECATED - keeping for backward compatibility)
def obtenir_access_token_strava():
    """Obtient un access_token frais depuis Strava en utilisant le refresh_token"""
    try:
        client_id = st.secrets["STRAVA_CLIENT_ID"]
        client_secret = st.secrets["STRAVA_CLIENT_SECRET"]
        refresh_token = st.secrets["STRAVA_REFRESH_TOKEN"]
        
        url = "https://www.strava.com/oauth/token"
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return data.get("access_token")
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erreur lors de l'obtention du token : {e}")
        return None
    except KeyError as e:
        st.error(f"❌ Secret manquant dans st.secrets : {e}")
        return None
    except Exception as e:
        st.error(f"❌ Erreur inattendue : {e}")
        return None


# Fonction pour obtenir l'access_token actif (depuis session ou refresh)
def obtenir_access_token_actif():
    """Obtient un access_token actif, rafraîchit si nécessaire"""
    # Vérifier si on a un token en session
    if "strava_access_token" in st.session_state and "strava_expires_at" in st.session_state:
        # Vérifier si le token est toujours valide
        current_time = int(time.time())
        expires_at = st.session_state["strava_expires_at"]

        # Si le token expire dans moins de 5 minutes, le rafraîchir
        if current_time < (expires_at - 300):
            return st.session_state["strava_access_token"]

        # Token expiré ou proche de l'expiration, le rafraîchir
        if "strava_refresh_token" in st.session_state:
            with st.spinner("🔄 Rafraîchissement du token..."):
                token_data = rafraichir_access_token(st.session_state["strava_refresh_token"])

                if token_data and token_data.get("access_token"):
                    st.session_state["strava_access_token"] = token_data["access_token"]
                    st.session_state["strava_refresh_token"] = token_data["refresh_token"]
                    st.session_state["strava_expires_at"] = token_data["expires_at"]
                    return token_data["access_token"]

    return None


# Fonction pour récupérer les activités Strava
def recuperer_activites_strava(access_token, per_page=50):
    """Récupère les activités depuis l'API Strava"""
    try:
        url = "https://www.strava.com/api/v3/athlete/activities"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"per_page": per_page}

        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        return response.json()
    except requests.exceptions.RequestException as e:
        response = getattr(e, "response", None)
        status_code = response.status_code if response is not None else None
        response_text = response.text if response is not None else "N/A"

        if status_code == 403 and "athlete" in response_text.lower():
            st.error("❌ Erreur 403 : limite d'athlètes connectés dépassée.")
            st.info(
                "💡 Strava limite le nombre d'athlètes connectés pour les apps en mode développement. "
                "Déconnecte des comptes de test ou demande une augmentation de quota."
            )
        else:
            st.error(f"❌ Erreur lors de la récupération des activités : {e}")
            st.error(f"Détails de l'erreur : {response_text}")
        return None
    except Exception as e:
        st.error(f"❌ Erreur inattendue : {e}")
        return None


# Fonction météo avec cache
@st.cache_data(ttl=86400)  # Cache pour 24h
def get_weather_history(lat, lon, date):
    """
    Récupère les données météo historiques depuis Open-Meteo
    Retourne : temp_max, precipitation, windspeed_max
    """
    try:
        # Convertir la date en format YYYY-MM-DD
        if isinstance(date, pd.Timestamp):
            date_str = date.strftime('%Y-%m-%d')
        elif isinstance(date, str):
            date_str = date.split('T')[0] if 'T' in date else date
        else:
            date_str = str(date).split(' ')[0]
        
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": date_str,
            "end_date": date_str,
            "daily": "temperature_2m_max,precipitation_sum,windspeed_10m_max",
            "timezone": "auto"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        daily = data.get("daily", {})
        
        if daily and len(daily.get("temperature_2m_max", [])) > 0:
            return {
                "temp_max": daily["temperature_2m_max"][0],
                "precipitation": daily["precipitation_sum"][0],
                "windspeed_max": daily["windspeed_10m_max"][0]
            }
        else:
            return None
    except Exception as e:
        return None


# Fonction pour enrichir un DataFrame avec les données météo
def enrichir_avec_meteo(df, activites_strava=None, df_csv_original=None):
    """
    Enrichit un DataFrame avec les données météo
    - Si activites_strava est fourni, utilise les coordonnées de l'API Strava
    - Sinon, cherche les colonnes lat/lon dans df_csv_original ou df
    """
    if df.empty:
        return df
    
    # Ajouter les colonnes météo
    df['Température (°C)'] = None
    df['Précipitations (mm)'] = None
    df['Vitesse vent (km/h)'] = None
    
    # Préparer la barre de progression
    progress_bar = st.progress(0)
    status_text = st.empty()
    total = len(df)
    
    for numeric_idx, (df_idx, row) in enumerate(df.iterrows()):
        lat = None
        lon = None
        date = row['Date']
        
        # Si on a les données brutes Strava, utiliser les coordonnées de l'API
        if activites_strava and numeric_idx < len(activites_strava):
            start_latlng = activites_strava[numeric_idx].get("start_latlng")
            if start_latlng and len(start_latlng) == 2:
                lat, lon = start_latlng[0], start_latlng[1]
        
        # Sinon, chercher dans le DataFrame original CSV si disponible
        if (lat is None or lon is None) and df_csv_original is not None and numeric_idx < len(df_csv_original):
            csv_row = df_csv_original.iloc[numeric_idx]
            # Chercher les colonnes de coordonnées
            for col in df_csv_original.columns:
                col_lower = col.lower()
                if 'lat' in col_lower and 'lon' not in col_lower and 'lng' not in col_lower:
                    lat_val = csv_row.get(col)
                    if pd.notna(lat_val):
                        lat = float(lat_val) if isinstance(lat_val, (int, float, str)) else None
                elif ('lon' in col_lower or 'lng' in col_lower) and 'lat' not in col_lower:
                    lon_val = csv_row.get(col)
                    if pd.notna(lon_val):
                        lon = float(lon_val) if isinstance(lon_val, (int, float, str)) else None
                elif 'start_latlng' in col_lower or 'start_lat_lng' in col_lower:
                    # Peut être une liste [lat, lon]
                    val = csv_row.get(col)
                    if isinstance(val, list) and len(val) == 2:
                        lat, lon = float(val[0]), float(val[1])
                    elif isinstance(val, str):
                        # Essayer de parser "[lat, lon]" ou "lat,lon"
                        match = re.search(r'\[?\s*([\d\.-]+)\s*,\s*([\d\.-]+)\s*\]?', val)
                        if match:
                            lat, lon = float(match.group(1)), float(match.group(2))
        
        # Sinon, chercher dans le DataFrame parsé lui-même
        if lat is None or lon is None:
            for col in df.columns:
                col_lower = col.lower()
                if 'lat' in col_lower and 'lon' not in col_lower and 'lng' not in col_lower:
                    lat_val = row.get(col)
                    if pd.notna(lat_val):
                        lat = float(lat_val) if isinstance(lat_val, (int, float, str)) else None
                elif ('lon' in col_lower or 'lng' in col_lower) and 'lat' not in col_lower:
                    lon_val = row.get(col)
                    if pd.notna(lon_val):
                        lon = float(lon_val) if isinstance(lon_val, (int, float, str)) else None
        
        # Si on a des coordonnées, récupérer la météo
        if lat is not None and lon is not None and pd.notna(lat) and pd.notna(lon):
            weather = get_weather_history(lat, lon, date)
            if weather:
                df.at[df_idx, 'Température (°C)'] = weather['temp_max']
                df.at[df_idx, 'Précipitations (mm)'] = weather['precipitation']
                df.at[df_idx, 'Vitesse vent (km/h)'] = weather['windspeed_max']
        
        # Mettre à jour la barre de progression
        progress = (numeric_idx + 1) / total
        progress_bar.progress(progress)
        status_text.text(f"Récupération météo : {numeric_idx + 1}/{total} activités")
    
    progress_bar.empty()
    status_text.empty()
    
    return df


# Fonction pour convertir les données Strava API en format texte
def strava_api_to_text_format(activites):
    """Convertit les données de l'API Strava en format texte pour le parser"""
    lignes = []
    
    for activite in activites:
        # Date
        date_str = activite.get("start_date_local", "")
        if date_str:
            # Convertir "2024-01-15T18:30:00Z" en "2024-01-15"
            date = date_str.split("T")[0]
        else:
            continue
        
        # Type d'activité
        type_activite = activite.get("type", "")
        if not type_activite:
            continue
        
        # Normaliser le type d'activité
        type_map = {
            "Run": "Course à pied",
            "Ride": "Vélo",
            "NordicSki": "Ski nordique",
            "AlpineSki": "Ski alpin",
            "Swim": "Natation",
            "Walk": "Marche",
            "Hike": "Randonnée",
            "Workout": "Entraînement",
            "WeightTraining": "Entraînement aux poids"
        }
        activite_nom = type_map.get(type_activite, type_activite)
        
        # Durée (moving_time en secondes)
        moving_time = activite.get("moving_time", 0)
        if moving_time:
            hours = moving_time // 3600
            minutes = (moving_time % 3600) // 60
            seconds = moving_time % 60
            if hours > 0:
                duree = f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                duree = f"{minutes}:{seconds:02d}"
        else:
            continue
        
        # Distance (en mètres, convertir en km)
        distance_m = activite.get("distance", 0)
        distance = ""
        if distance_m and distance_m > 0:
            if distance_m >= 1000:
                distance = f"{distance_m / 1000:.2f} km"
            else:
                distance = f"{int(distance_m)} m"
        
        # Créer la ligne
        ligne = f"{date}, {activite_nom}, {duree}"
        if distance:
            ligne += f", {distance}"
        lignes.append(ligne)
    
    return '\n'.join(lignes)


# Interface : choix entre upload de fichier ou connexion Strava
st.subheader("📊 Choisis ta méthode d'import")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📁 Upload de fichier")
    uploaded_file = st.file_uploader(
        "Sélectionne un fichier CSV ou Excel",
        type=['csv', 'xlsx'],
        help="Le fichier doit contenir les colonnes : Date, Activité, Durée, Distance (ou format similaire)",
        key="file_uploader"
    )

with col2:
    st.markdown("### 🔗 Connexion Strava")

    # Vérifier si l'utilisateur est déjà connecté
    if st.session_state.get("strava_connected", False):
        # Afficher l'info de l'athlète connecté
        athlete = st.session_state.get("strava_athlete", {})
        athlete_name = athlete.get("firstname", "Athlète")
        st.success(f"✅ Connecté en tant que **{athlete_name}**")

        # Bouton pour récupérer les activités
        if st.button("📥 Récupérer mes activités", type="primary", use_container_width=True):
            with st.spinner("Récupération des activités..."):
                # Obtenir un access_token actif
                access_token = obtenir_access_token_actif()

                if access_token:
                    activites = recuperer_activites_strava(access_token, per_page=50)

                    if activites:
                        st.success(f"✅ {len(activites)} activités récupérées")

                        # Convertir en format texte
                        donnees_texte = strava_api_to_text_format(activites)

                        # Stocker dans session_state pour l'analyse
                        st.session_state['donnees_strava'] = donnees_texte
                        st.session_state['activites_strava_brutes'] = activites
                        st.session_state['nb_activites_strava'] = len(activites)
                        st.rerun()
                    else:
                        st.error("❌ Impossible de récupérer les activités")
                else:
                    st.error("❌ Token expiré, veuillez vous reconnecter")
                    st.session_state["strava_connected"] = False
                    st.rerun()

        # Bouton de déconnexion
        if st.button("🚪 Se déconnecter", use_container_width=True):
            # Nettoyer la session
            for key in list(st.session_state.keys()):
                if key.startswith("strava_"):
                    del st.session_state[key]
            st.rerun()

    else:
        # Générer l'URL d'autorisation OAuth
        auth_url = generer_url_autorisation_strava()

        if auth_url:
            st.info("👤 Connecte-toi avec ton compte Strava pour accéder à tes activités")
            # Afficher le lien OAuth (même onglet)
            if hasattr(st, "link_button"):
                st.link_button("🔐 Se connecter avec Strava", auth_url, type="primary")
            else:
                st.markdown(
                    f'<a href="{auth_url}" target="_self" '
                    f'style="display: inline-block; padding: 0.5rem 1rem; '
                    f'background-color: #FC4C02; color: white; text-decoration: none; '
                    f'border-radius: 0.25rem; font-weight: 600; text-align: center; '
                    f'width: 100%;">🔐 Se connecter avec Strava</a>',
                    unsafe_allow_html=True
                )
            st.caption("Tu seras redirigé vers Strava pour autoriser l'accès à tes activités.")

            # Aide de dépannage
            with st.expander("🔧 Problème de connexion ? (Lire si erreur)"):
                st.markdown("""
                ### ⚠️ Erreur "Max challenge attempts exceeded" ?

                **Causes principales:**
                1. **Authorization Callback Domain mal configuré sur Strava**
                   - Doit être: `localhost` (PAS `http://localhost:8501`)
                   - Va sur https://www.strava.com/settings/api
                   - Vérifie le champ "Authorization Callback Domain"

                2. **Redirect URI incorrect dans les secrets**
                   - Doit être: `http://localhost:8501` (URL complète)
                   - Vérifie `.streamlit/secrets.toml`

                3. **Trop de tentatives rapides**
                   - Attends 5-10 minutes avant de réessayer
                   - Efface les cookies de ton navigateur
                   - Utilise une fenêtre de navigation privée

                ### ✅ Configuration Correcte

                **Sur Strava (https://www.strava.com/settings/api):**
                ```
                Authorization Callback Domain: localhost
                ```

                **Dans .streamlit/secrets.toml:**
                ```toml
                STRAVA_CLIENT_ID = "123456"
                STRAVA_CLIENT_SECRET = "ton_secret"
                REDIRECT_URI = "http://localhost:8501"
                ```

                ### 🔍 Debug Info
                """)

                # Afficher les informations de debug
                try:
                    client_id = st.secrets.get("STRAVA_CLIENT_ID", "NON CONFIGURÉ")
                    redirect_uri = obtenir_redirect_uri()
                    st.code(f"""
Client ID: {client_id}
Redirect URI: {redirect_uri}
URL OAuth générée:
{auth_url}
                    """)
                    st.info("📖 Guide complet: Consulte le fichier `STRAVA_OAUTH_DEBUG.md`")
                except Exception as e:
                    st.error(f"Erreur lors de la lecture de la config: {e}")
        else:
            st.error("❌ Configuration OAuth manquante")
            st.warning("Vérifie que STRAVA_CLIENT_ID et STRAVA_CLIENT_SECRET sont dans tes secrets")

# Fonction réutilisable pour afficher l'analyse
def afficher_analyse(donnees_texte, source="fichier"):
    """Affiche l'analyse complète des données"""
    with st.spinner("Analyse en cours..."):
        # Parser les données
        df = parser_donnees_strava(donnees_texte)
        
        if df.empty:
            st.error("❌ Aucune donnée valide trouvée.")
            return
        
        # Enrichir avec les données météo si disponibles
        activites_strava_brutes = None
        df_csv_original = None
        if source == "strava" and 'activites_strava_brutes' in st.session_state:
            activites_strava_brutes = st.session_state['activites_strava_brutes']
        elif source == "fichier" and 'df_csv_original' in st.session_state:
            df_csv_original = st.session_state['df_csv_original']
        
        # Enrichir avec la météo
        st.info("🌤️ Enrichissement des données avec la météo...")
        df = enrichir_avec_meteo(df, activites_strava_brutes, df_csv_original)
        
        # Calculer les statistiques
        volume_total = df['Durée (h)'].sum()
        volume_course, volume_ski = comparer_activites(df)
        temps_semaine = calculer_temps_par_semaine(df)
        duree_moyenne = df['Durée (h)'].mean()
        
        distance_totale = None
        if 'Distance (km)' in df.columns and df['Distance (km)'].notna().any():
            distance_totale = df['Distance (km)'].sum()
        
        # Compter les semaines en surcharge
        semaines_surcharge = 0
        if not temps_semaine.empty:
            semaines_surcharge = len(temps_semaine[temps_semaine['Temps total (h)'] > 10])
        
        # Afficher les stats en gros
        st.markdown("---")
        st.subheader("📊 Statistiques")
        
        # Créer des colonnes pour les stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("⏱️ Volume Total", f"{volume_total:.1f} h")
        
        with col2:
            st.metric("🏃 Course à pied", f"{volume_course:.1f} h")
        
        with col3:
            st.metric("⛷️ Ski de fond", f"{volume_ski:.1f} h")
        
        with col4:
            st.metric("📈 Activités", f"{len(df)}")
        
        # Graphique de répartition
        st.markdown("---")
        st.subheader("📊 Répartition des sports")
        
        # Préparer les données pour le graphique
        activites_df = df.groupby('Activité')['Durée (h)'].sum().reset_index()
        activites_df.columns = ['Activité', 'Durée (heures)']
        activites_df = activites_df.sort_values('Durée (heures)', ascending=False)
        
        # Créer le graphique bar chart
        fig = px.bar(
            activites_df,
            x='Activité',
            y='Durée (heures)',
            title="Volume d'entraînement par activité",
            labels={'Durée (heures)': 'Durée (heures)', 'Activité': 'Activité'},
            color='Durée (heures)',
            color_continuous_scale='Blues'
        )
        fig.update_layout(
            xaxis_tickangle=-45,
            height=400,
            showlegend=False
        )
        st.plotly_chart(fig, width='stretch')
        
        # Graphique en camembert pour la répartition en pourcentage
        st.markdown("---")
        st.subheader("🥧 Répartition par type de sport")
        
        # Calculer les pourcentages
        activites_df_pourcent = activites_df.copy()
        total_heures = activites_df_pourcent['Durée (heures)'].sum()
        activites_df_pourcent['Pourcentage'] = (activites_df_pourcent['Durée (heures)'] / total_heures * 100).round(1)
        
        # Créer le graphique en camembert
        fig_pie = px.pie(
            activites_df_pourcent,
            values='Durée (heures)',
            names='Activité',
            title="Répartition des entraînements par type de sport",
            hole=0.3,  # Donut chart pour un look plus moderne
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_pie.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>%{value:.1f} heures<br>%{percent}<extra></extra>'
        )
        fig_pie.update_layout(
            height=400,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.05
            )
        )
        
        # Afficher le graphique en camembert avec un tableau récapitulatif
        col1, col2 = st.columns([2, 1])
        with col1:
            st.plotly_chart(fig_pie, width='stretch')
        with col2:
            st.markdown("### 📊 Détails")
            for _, row in activites_df_pourcent.iterrows():
                st.metric(
                    label=row['Activité'],
                    value=f"{row['Durée (heures)']:.1f} h",
                    delta=f"{row['Pourcentage']:.1f}%"
                )
        
        # Graphique de dispersion Température vs Performance
        if 'Température (°C)' in df.columns and df['Température (°C)'].notna().any():
            st.markdown("---")
            st.subheader("🌡️ Impact de la température sur la performance")
            
            # Calculer la vitesse (km/h) ou pace (min/km) pour chaque activité
            df_scatter = df.copy()
            df_scatter['Vitesse (km/h)'] = None
            df_scatter['Pace (min/km)'] = None
            
            for idx, row in df_scatter.iterrows():
                if pd.notna(row.get('Distance (km)')) and pd.notna(row.get('Durée (h)')):
                    distance_km = row['Distance (km)']
                    duree_h = row['Durée (h)']
                    if distance_km > 0 and duree_h > 0:
                        # Vitesse en km/h
                        vitesse = distance_km / duree_h
                        df_scatter.at[idx, 'Vitesse (km/h)'] = vitesse
                        # Pace en min/km
                        pace = (duree_h * 60) / distance_km
                        df_scatter.at[idx, 'Pace (min/km)'] = pace
            
            # Filtrer les données avec température et vitesse valides
            df_meteo = df_scatter[
                (df_scatter['Température (°C)'].notna()) & 
                (df_scatter['Vitesse (km/h)'].notna())
            ].copy()
            
            if not df_meteo.empty:
                # Créer le graphique de dispersion
                fig_scatter = px.scatter(
                    df_meteo,
                    x='Température (°C)',
                    y='Vitesse (km/h)',
                    color='Activité',
                    size='Distance (km)',
                    hover_data=['Date', 'Précipitations (mm)', 'Vitesse vent (km/h)'],
                    title="Performance vs Température",
                    labels={
                        'Température (°C)': 'Température maximale (°C)',
                        'Vitesse (km/h)': 'Vitesse moyenne (km/h)',
                        'Distance (km)': 'Distance (km)'
                    },
                    trendline="ols"  # Ligne de tendance
                )
                fig_scatter.update_layout(
                    height=500,
                    showlegend=True
                )
                st.plotly_chart(fig_scatter, width='stretch')
                
                # Statistiques sur l'impact de la température
                if len(df_meteo) > 1:
                    correlation = df_meteo['Température (°C)'].corr(df_meteo['Vitesse (km/h)'])
                    st.info(f"📊 **Corrélation température-performance :** {correlation:.3f}")
                    if correlation < -0.3:
                        st.success("✅ Tu performes mieux quand il fait froid !")
                    elif correlation > 0.3:
                        st.warning("⚠️ Tu performes mieux quand il fait chaud.")
                    else:
                        st.info("ℹ️ Pas de corrélation claire entre température et performance.")
            else:
                st.warning("⚠️ Pas assez de données météo pour créer le graphique.")
        
        # Message du coach
        st.markdown("---")
        st.subheader("💬 Message du Coach")
        
        # Préparer les stats pour GPT
        stats = {
            'volume_total': volume_total,
            'volume_course': volume_course,
            'volume_ski': volume_ski,
            'nb_activites': len(df),
            'duree_moyenne': duree_moyenne,
            'distance_totale': distance_totale if distance_totale else 0,
            'semaines_surcharge': semaines_surcharge
        }
        
        # Générer le feedback
        with st.spinner("🤖 Le coach réfléchit..."):
            feedback = generer_feedback_coach(stats)
        
        if feedback:
            # Afficher dans un encadré bien visible
            st.info(f"💬 **Coach GPT-5-nano :**\n\n{feedback}")
        else:
            st.warning("⚠️ Impossible de générer le feedback. Vérifie ta clé API dans le fichier .env")
        
        # Détails supplémentaires (optionnel, en expander)
        with st.expander("📋 Détails supplémentaires"):
            st.write(f"**Période :** {df['Date'].min().date()} → {df['Date'].max().date()}")
            st.write(f"**Durée moyenne par activité :** {duree_moyenne:.2f} heures")
            st.write(f"**Durée maximale :** {df['Durée (h)'].max():.2f} heures")
            st.write(f"**Durée minimale :** {df['Durée (h)'].min():.2f} heures")
            if distance_totale:
                st.write(f"**Distance totale :** {distance_totale:.2f} km")
            st.write(f"**Semaines en surcharge (>10h) :** {semaines_surcharge}")
            
            if not temps_semaine.empty:
                st.write("\n**Temps par semaine :**")
                st.dataframe(temps_semaine, width='stretch')
        
        # Stocker le DataFrame dans session_state pour le chatbot
        st.session_state['df_analyse'] = df
        st.session_state['analyse_complete'] = True


# Afficher les données Strava si disponibles
if 'donnees_strava' in st.session_state:
    st.info(f"📊 {st.session_state['nb_activites_strava']} activités Strava chargées")
    if st.button("🔍 Analyser les données Strava", type="primary", use_container_width=True):
        afficher_analyse(st.session_state['donnees_strava'], source="strava")

# Fonction pour convertir un DataFrame CSV/Excel en format texte pour le parser
def csv_to_text_format(df_csv):
    """
    Convertit un DataFrame CSV/Excel en format texte que le parser peut comprendre.
    Supporte plusieurs formats :
    - Format standard : Date, Activité, Durée, Distance
    - Format StatsHunters : Date, Type, Moving time (secondes), Distance (m)
    """
    lignes = []
    
    # Détecter si c'est le format StatsHunters
    is_statshunters = 'Moving time' in df_csv.columns and 'Type' in df_csv.columns
    
    for _, row in df_csv.iterrows():
        # Chercher la date dans différentes colonnes possibles
        date = ''
        if 'Date' in df_csv.columns and pd.notna(row.get('Date')):
            date_val = row['Date']
            # Convertir en string, gérer les datetime
            if pd.isna(date_val):
                continue
            if isinstance(date_val, pd.Timestamp):
                # Format date seulement (sans heure) pour le parser
                date = date_val.strftime('%Y-%m-%d')
            else:
                # Si c'est une string avec date et heure, extraire juste la date
                date_str = str(date_val)
                if ' ' in date_str:
                    date = date_str.split(' ')[0]
                else:
                    date = date_str
        
        if not date:
            continue
        
        # Chercher l'activité
        activite = ''
        if is_statshunters:
            # Format StatsHunters : utiliser la colonne "Type"
            if 'Type' in df_csv.columns and pd.notna(row.get('Type')):
                activite = str(row['Type'])
                # Normaliser les noms d'activités StatsHunters
                activite_map = {
                    'Run': 'Course à pied',
                    'Ride': 'Vélo',
                    'NordicSki': 'Ski nordique',
                    'Swim': 'Natation',
                    'InlineSkate': 'Patinage',
                    'Walk': 'Marche',
                    'Hike': 'Randonnée'
                }
                activite = activite_map.get(activite, activite)
        else:
            # Format standard
            for col in ['Activité', 'Activite', 'activité', 'activite', 'Activity Type', 'Type', 'Sport']:
                if col in df_csv.columns and pd.notna(row.get(col)):
                    activite = str(row[col])
                    break
        
        if not activite:
            continue
        
        # Chercher la durée
        duree = ''
        if is_statshunters:
            # Format StatsHunters : "Moving time" est en secondes
            if 'Moving time' in df_csv.columns and pd.notna(row.get('Moving time')):
                seconds = int(row['Moving time'])
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                secs = seconds % 60
                if hours > 0:
                    duree = f"{hours}:{minutes:02d}:{secs:02d}"
                else:
                    duree = f"{minutes}:{secs:02d}"
        else:
            # Format standard
            for col in ['Durée', 'Duree', 'durée', 'duree', 'Durée (h)', 'Duration', 'Time', 'Temps']:
                if col in df_csv.columns and pd.notna(row.get(col)):
                    duree = str(row[col])
                    break
        
        if not duree:
            continue
        
        # Chercher la distance
        distance = ''
        if is_statshunters:
            # Format StatsHunters : "Distance (m)" est en mètres
            if 'Distance (m)' in df_csv.columns and pd.notna(row.get('Distance (m)')):
                distance_m = float(row['Distance (m)'])
                if distance_m > 0:
                    # Convertir en km si > 1000m, sinon garder en m
                    if distance_m >= 1000:
                        distance = f"{distance_m / 1000:.2f} km"
                    else:
                        distance = f"{int(distance_m)} m"
        else:
            # Format standard
            for col in ['Distance', 'distance', 'Distance (km)', 'Distance (m)', 'Distance km', 'Distance m']:
                if col in df_csv.columns and pd.notna(row.get(col)):
                    distance = str(row[col])
                    break
        
        # Créer la ligne au format CSV simple (format que le parser comprend)
        ligne = f"{date}, {activite}, {duree}"
        if distance:
            ligne += f", {distance}"
        lignes.append(ligne)
    
    return '\n'.join(lignes)

# Afficher un aperçu si un fichier est chargé
if uploaded_file is not None:
    try:
        # Détecter l'extension du fichier et utiliser la bonne fonction pandas
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'csv':
            # Lire le CSV
            df_csv = pd.read_csv(uploaded_file)
        elif file_extension == 'xlsx':
            # Lire le fichier Excel
            df_csv = pd.read_excel(uploaded_file)
        else:
            st.error(f"❌ Format de fichier non supporté : {file_extension}")
            st.stop()
        
        # Afficher un aperçu
        st.success(f"✅ Fichier chargé : {uploaded_file.name} ({file_extension.upper()})")
        st.markdown("**📊 Aperçu des données (5 premières lignes) :**")
        st.dataframe(df_csv.head(5), width='stretch')
        
        # Convertir en format texte pour le parser
        donnees_texte = csv_to_text_format(df_csv)
        
        # Stocker le DataFrame original pour l'enrichissement météo
        st.session_state['df_csv_original'] = df_csv
        
        # Bouton Analyser
        if st.button("🔍 Analyser", type="primary", use_container_width=True, key="analyze_file"):
            afficher_analyse(donnees_texte, source="fichier")
    except Exception as e:
        st.error(f"❌ Erreur lors de la lecture du fichier : {e}")
        st.info("💡 Assure-toi que ton fichier (CSV ou Excel) contient les colonnes : Date, Activité, Durée, Distance")


# Fonction pour convertir un DataFrame en CSV string pour le contexte IA
def df_to_csv_string(df, max_rows=100):
    """Convertit un DataFrame en string CSV pour le contexte de l'IA"""
    if df.empty:
        return "Aucune donnée disponible."
    
    # Sélectionner les colonnes pertinentes
    colonnes = ['Date', 'Activité', 'Durée (h)', 'Distance (km)']
    if 'Température (°C)' in df.columns:
        colonnes.append('Température (°C)')
    if 'Précipitations (mm)' in df.columns:
        colonnes.append('Précipitations (mm)')
    if 'Vitesse vent (km/h)' in df.columns:
        colonnes.append('Vitesse vent (km/h)')
    
    # Filtrer les colonnes qui existent
    colonnes_existantes = [col for col in colonnes if col in df.columns]
    df_subset = df[colonnes_existantes].copy()
    
    # Limiter le nombre de lignes pour éviter un contexte trop long
    if len(df_subset) > max_rows:
        df_subset = df_subset.head(max_rows)
    
    # Convertir en CSV string
    csv_str = df_subset.to_csv(index=False)
    
    # Ajouter un résumé si on a limité les lignes
    if len(df) > max_rows:
        csv_str += f"\n\n(Note: Affichage des {max_rows} premières activités sur {len(df)} totales)"
    
    return csv_str


# Fonction pour gérer le chatbot
def afficher_chatbot():
    """Affiche le module de chatbot interactif"""
    if 'df_analyse' not in st.session_state or st.session_state.get('analyse_complete', False) == False:
        return
    
    df = st.session_state['df_analyse']
    
    st.markdown("---")
    st.subheader("💬 Coach Assistant - Chat Interactif")
    st.markdown("Pose des questions sur tes entraînements et reçois des conseils personnalisés !")
    
    # Initialiser l'historique du chat
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Afficher l'historique des messages
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Récupérer la question de l'utilisateur
    if prompt := st.chat_input("Pose une question à ton coach..."):
        # Ajouter la question de l'utilisateur à l'historique
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Afficher la question
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Préparer le contexte avec les données
        donnees_csv = df_to_csv_string(df)
        
        # Préparer le system prompt
        system_prompt = f"""Tu es un coach de triathlon expert. Tu as accès aux données d'entraînement suivantes :

{donnees_csv}

Réponds aux questions de l'athlète de manière précise, motivante et un peu sarcastique. Si la réponse nécessite un calcul, fais-le. Utilise les données fournies pour donner des conseils personnalisés."""
        
        # Préparer les messages pour l'API
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Ajouter l'historique (limité aux 10 derniers messages pour éviter les tokens)
        for msg in st.session_state.chat_history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Envoyer la requête à OpenAI
        with st.chat_message("assistant"):
            with st.spinner("Le coach réfléchit..."):
                try:
                    # Récupérer la clé API depuis st.secrets (comme dans analyse_strava.py)
                    api_key = st.secrets["OPENAI_API_KEY"]
                    client = OpenAI(api_key=api_key)
                    
                    response = client.chat.completions.create(
                        model="gpt-5-nano",
                        messages=messages,
                        max_completion_tokens=20000
                    )
                    
                    assistant_response = response.choices[0].message.content
                    
                    # Vérifier si la réponse est vide (comme pour le script de blague)
                    if assistant_response is None or assistant_response.strip() == "":
                        st.warning("⚠️ La réponse du coach est vide.")
                        st.info("💡 GPT-5-nano utilise des tokens pour réfléchir. Si tous les tokens sont utilisés pour le raisonnement, il n'en reste plus pour la réponse.")
                        assistant_response = "Désolé, je n'ai pas pu générer de réponse complète. Peux-tu reformuler ta question de manière plus courte ?"
                    
                    # Afficher la réponse
                    st.markdown(assistant_response)
                    
                    # Ajouter la réponse à l'historique
                    st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
                    
                except Exception as e:
                    error_msg = f"❌ Erreur : {e}"
                    st.error(error_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": error_msg})


# Afficher le chatbot si des données ont été analysées
if st.session_state.get('analyse_complete', False):
    afficher_chatbot()


# Afficher l'horodatage et le commit en bas de page
def get_git_commit():
    """Retourne le hash court du dernier commit si disponible."""
    # Priorité à une variable d'env si définie (déploiement)
    env_commit = os.getenv("GIT_COMMIT")
    if env_commit:
        return env_commit[:7]
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        return commit
    except Exception:
        return "unknown"


st.markdown("---")
build_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
commit_id = get_git_commit()
st.caption(f"🕒 Build time: {build_time} | 🧾 Commit: {commit_id}")
