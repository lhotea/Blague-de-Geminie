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

# Fonction pour obtenir un access_token Strava
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
        st.error(f"❌ Erreur lors de la récupération des activités : {e}")
        return None
    except Exception as e:
        st.error(f"❌ Erreur inattendue : {e}")
        return None


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
    if st.button("🔐 Connexion Strava Directe", type="primary", use_container_width=True):
        with st.spinner("Connexion à Strava en cours..."):
            # Obtenir l'access_token
            access_token = obtenir_access_token_strava()
            
            if access_token:
                st.success("✅ Connexion réussie !")
                
                # Récupérer les activités
                with st.spinner("Récupération des activités..."):
                    activites = recuperer_activites_strava(access_token, per_page=50)
                
                if activites:
                    st.success(f"✅ {len(activites)} activités récupérées")
                    
                    # Convertir en format texte
                    donnees_texte = strava_api_to_text_format(activites)
                    
                    # Stocker dans session_state pour l'analyse
                    st.session_state['donnees_strava'] = donnees_texte
                    st.session_state['nb_activites_strava'] = len(activites)
                    st.rerun()
                else:
                    st.error("❌ Impossible de récupérer les activités")
            else:
                st.error("❌ Impossible de se connecter à Strava")

# Fonction réutilisable pour afficher l'analyse
def afficher_analyse(donnees_texte, source="fichier"):
    """Affiche l'analyse complète des données"""
    with st.spinner("Analyse en cours..."):
        # Parser les données
        df = parser_donnees_strava(donnees_texte)
        
        if df.empty:
            st.error("❌ Aucune donnée valide trouvée.")
            return
        
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
        st.plotly_chart(fig, use_container_width=True)
        
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
            st.plotly_chart(fig_pie, use_container_width=True)
        with col2:
            st.markdown("### 📊 Détails")
            for _, row in activites_df_pourcent.iterrows():
                st.metric(
                    label=row['Activité'],
                    value=f"{row['Durée (heures)']:.1f} h",
                    delta=f"{row['Pourcentage']:.1f}%"
                )
        
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
                st.dataframe(temps_semaine, use_container_width=True)


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
        st.dataframe(df_csv.head(5), use_container_width=True)
        
        # Convertir en format texte pour le parser
        donnees_texte = csv_to_text_format(df_csv)
        
        # Bouton Analyser
        if st.button("🔍 Analyser", type="primary", use_container_width=True, key="analyze_file"):
            afficher_analyse(donnees_texte, source="fichier")
    except Exception as e:
        st.error(f"❌ Erreur lors de la lecture du fichier : {e}")
        st.info("💡 Assure-toi que ton fichier (CSV ou Excel) contient les colonnes : Date, Activité, Durée, Distance")
