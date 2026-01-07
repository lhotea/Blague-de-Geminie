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

# Zone de texte pour coller les données
st.subheader("📋 Colle tes données Strava ici")
donnees_texte = st.text_area(
    "Copie-colle tes données Strava (format export ou CSV)",
    height=200,
    placeholder="Exemple:\nSki nordiquedim. 04/01/2026Vom Bahnhof hei5:041,13 km11 m1\nCourse à piedjeu. 01/01/2026Left my legs in 2025 🙈1:48:0814,60 km140 m24"
)

# Bouton Analyser
if st.button("🔍 Analyser", type="primary", use_container_width=True):
    if not donnees_texte.strip():
        st.error("⚠️ Veuillez coller tes données Strava avant d'analyser.")
    else:
        with st.spinner("Analyse en cours..."):
            # Parser les données
            df = parser_donnees_strava(donnees_texte)
            
            if df.empty:
                st.error("❌ Aucune donnée valide trouvée. Vérifie le format de tes données.")
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
