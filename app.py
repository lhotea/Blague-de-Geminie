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

# Zone d'upload de fichier CSV ou Excel
st.subheader("📁 Charge ton fichier Strava")
uploaded_file = st.file_uploader(
    "Sélectionne un fichier CSV ou Excel contenant tes données Strava",
    type=['csv', 'xlsx'],
    help="Le fichier doit contenir les colonnes : Date, Activité, Durée, Distance (ou format similaire)"
)

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
        if st.button("🔍 Analyser", type="primary", use_container_width=True):
            with st.spinner("Analyse en cours..."):
                # Parser les données
                df = parser_donnees_strava(donnees_texte)
                
                if df.empty:
                    st.error("❌ Aucune donnée valide trouvée. Vérifie le format de ton fichier.")
                else:
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
    except Exception as e:
        st.error(f"❌ Erreur lors de la lecture du fichier : {e}")
        st.info("💡 Assure-toi que ton fichier (CSV ou Excel) contient les colonnes : Date, Activité, Durée, Distance")
