"""
Script d'analyse des données Strava
Analyse le volume d'entraînement et détecte les risques de surcharge
Génère un feedback sarcastique avec GPT-5-nano
"""

import pandas as pd
from datetime import datetime
import re
import os
from collections import defaultdict
from openai import OpenAI
from dotenv import load_dotenv
import streamlit as st


def parser_donnees_strava(texte_brut):
    """
    Parse le texte brut des données Strava et retourne un DataFrame pandas.
    
    Supporte trois formats :
    1. Format tabulé : "Nordic Ski\tSun, 1/4/2026\tTitre\t5:04\t1.13 km\t11 m"
    2. Format simple : "2024-01-15, Course à pied, 1h30, 15km"
    3. Format Strava export : "Ski nordiquedim. 04/01/2026Titre1:04:221,13 km11 m"
    """
    lignes = texte_brut.strip().split('\n')
    donnees = []
    
    for ligne in lignes:
        ligne = ligne.strip()
        if not ligne or ligne.startswith('#'):
            continue
        
        # Essayer d'abord le format tabulé (nouveau format)
        donnee = parser_format_tabule(ligne)
        if donnee:
            donnees.append(donnee)
            continue
        
        # Ensuite, essayer le format Strava export (plus complexe)
        donnee = parser_format_strava_export(ligne)
        if donnee:
            donnees.append(donnee)
            continue
        
        # Enfin, essayer le format simple (CSV)
        donnee = parser_format_simple(ligne)
        if donnee:
            donnees.append(donnee)
    
    return pd.DataFrame(donnees)


def parser_format_tabule(ligne):
    """
    Parse le format tabulé (séparé par des tabulations) :
    "Nordic Ski\tSun, 1/4/2026\tTitre\t5:04\t1.13 km\t11 m\t..."
    """
    # Vérifier si la ligne contient des tabulations
    if '\t' not in ligne:
        return None
    
    parties = ligne.split('\t')
    
    # On a besoin d'au moins : Activité, Date, Durée
    if len(parties) < 4:
        return None
    
    activite = parties[0].strip()
    date_str = parties[1].strip()
    # parties[2] = titre (on l'ignore)
    duree_str = parties[3].strip()
    # Extraire la distance (peut contenir plusieurs parties séparées par des tabulations)
    distance_str = None
    if len(parties) > 4:
        # Prendre seulement la partie distance (avant le prochain tabulation ou espace significatif)
        distance_raw = parties[4].strip()
        # Extraire la distance avec son unité (km ou m)
        match_dist = re.search(r'([\d\s,\.]+)\s*(km|m)', distance_raw)
        if match_dist:
            distance_str = match_dist.group(0).strip()  # Prendre "1,725 m" ou "1.13 km"
    
    # Parser la date (format "Sun, 1/4/2026" ou "Wed, 12/31/2025")
    # Enlever le jour de la semaine et la virgule
    date_clean = re.sub(r'^[A-Za-z]+,?\s*', '', date_str).strip()
    
    try:
        # Essayer différents formats de date
        # Format M/D/YYYY
        date = pd.to_datetime(date_clean, format='%m/%d/%Y')
    except:
        try:
            # Essayer format D/M/YYYY
            date = pd.to_datetime(date_clean, format='%d/%m/%Y')
        except:
            try:
                # Essayer format automatique
                date = pd.to_datetime(date_clean)
            except:
                return None
    
    # Conversion de la durée (format "5:04" ou "1:38:52")
    duree_heures = parser_duree_strava(duree_str)
    
    # Conversion de la distance
    distance_km = None
    if distance_str and distance_str != '0 km' and distance_str != '0 m':
        # Format "1.13 km" ou "1,725 m" ou "1 725 m"
        # Chercher d'abord les km
        match_km = re.search(r'([\d\s,\.]+)\s*km', distance_str)
        if match_km:
            distance_val = match_km.group(1).replace(' ', '').replace(',', '.')
            try:
                distance_km = float(distance_val)
            except:
                pass
        else:
            # Chercher les mètres
            match_m = re.search(r'([\d\s,\.]+)\s*m', distance_str)
            if match_m:
                distance_val_raw = match_m.group(1).replace(' ', '')
                # Détecter si la virgule est un séparateur de milliers (1,725) ou décimal (1,72)
                # Si format "X,XXX" (virgule suivie de 3 chiffres), c'est un séparateur de milliers
                if re.match(r'\d+,\d{3}$', distance_val_raw):
                    # Séparateur de milliers : "1,725" -> 1725
                    distance_val = distance_val_raw.replace(',', '')
                else:
                    # Séparateur décimal : "1,72" -> 1.72
                    distance_val = distance_val_raw.replace(',', '.')
                try:
                    distance_km = float(distance_val) / 1000.0
                except:
                    pass
    
    # Normaliser le nom de l'activité
    activite_normalisee = activite
    if 'Nordic Ski' in activite or 'Ski' in activite:
        activite_normalisee = 'Ski nordique'
    elif 'Run' in activite:
        activite_normalisee = 'Course à pied'
    elif 'Swim' in activite:
        activite_normalisee = 'Natation'
    elif 'Weight Training' in activite:
        activite_normalisee = 'Entraînement aux poids'
    elif 'Workout' in activite:
        activite_normalisee = 'Entraînement'
    
    return {
        'Date': date,
        'Activité': activite_normalisee,
        'Durée (h)': duree_heures,
        'Distance (km)': distance_km
    }


def parser_format_strava_export(ligne):
    """
    Parse le format Strava export :
    "Ski nordiquedim. 04/01/2026Titre1:04:221,13 km11 m"
    """
    # Pattern pour extraire : Activité, jour, date, titre, durée, distance, dénivelé
    # Les jours de la semaine en français
    jours = r'(dim\.|lun\.|mar\.|mer\.|jeu\.|ven\.|sam\.)'
    
    # Pattern pour la date DD/MM/YYYY
    pattern_date = r'(\d{2}/\d{2}/\d{4})'
    
    # Pattern pour la durée H:MM:SS ou MM:SS
    pattern_duree = r'(\d{1,2}:\d{2}:\d{2}|\d{1,2}:\d{2})'
    
    # Pattern pour la distance (X,XX km ou X XXX m)
    pattern_distance = r'([\d\s,]+)\s*(km|m)'
    
    # Extraire l'activité (avant le jour)
    match_jour = re.search(jours, ligne)
    if not match_jour:
        return None
    
    activite = ligne[:match_jour.start()].strip()
    
    # Extraire la date
    match_date = re.search(pattern_date, ligne)
    if not match_date:
        return None
    
    date_str = match_date.group(1)
    
    # Extraire la durée
    match_duree = re.search(pattern_duree, ligne)
    if not match_duree:
        return None
    
    duree_str = match_duree.group(1)
    
    # Extraire la distance (chercher après la durée)
    distance_km = None
    
    # Trouver la position de la fin de la durée pour chercher la distance après
    duree_end_pos = match_duree.end()
    ligne_apres_duree = ligne[duree_end_pos:]
    
    # Chercher d'abord les km (priorité) - format: "1,13 km" ou "22,69 km"
    # S'assurer qu'il n'y a pas de ":" juste avant (pour éviter de capturer la durée)
    match_km = re.search(r'(?<!:)([\d\s,]+)\s*km', ligne_apres_duree)
    if match_km:
        distance_val = match_km.group(1).replace(' ', '').replace(',', '.')
        # Ignorer si c'est "0" (pas de distance)
        try:
            distance_num = float(distance_val)
            if distance_num > 0:
                distance_km = distance_num
        except:
            pass
    else:
        # Sinon chercher les mètres - format: "1 725 m" ou "1900 m"
        # Le 'm' doit être suivi d'un espace, d'un chiffre (dénivelé) ou fin de ligne
        match_m = re.search(r'(?<!:)([\d\s,]+)\s*m(?:\s+\d|\s|$)', ligne_apres_duree)
        if match_m:
            distance_val = match_m.group(1).replace(' ', '').replace(',', '.')
            try:
                distance_num = float(distance_val)
                if distance_num > 0:
                    distance_km = distance_num / 1000.0
            except:
                pass
    
    # Conversion de la date
    try:
        date = pd.to_datetime(date_str, format='%d/%m/%Y')
    except:
        return None
    
    # Conversion de la durée
    duree_heures = parser_duree_strava(duree_str)
    
    return {
        'Date': date,
        'Activité': activite,
        'Durée (h)': duree_heures,
        'Distance (km)': distance_km
    }


def parser_format_simple(ligne):
    """Parse le format simple CSV : Date, Activité, Durée, Distance"""
    parties = [p.strip() for p in ligne.split(',')]
    
    if len(parties) < 3:
        return None
        
    date_str = parties[0]
    activite = parties[1]
    duree_str = parties[2]
    distance_str = parties[3] if len(parties) > 3 else None
    
    # Conversion de la durée
    # Essayer d'abord parser_duree, puis parser_duree_strava si ça échoue
    duree_heures = parser_duree(duree_str)
    if duree_heures == 0.0 and ':' in duree_str:
        # Si parser_duree n'a pas fonctionné et qu'il y a des ':', essayer parser_duree_strava
        duree_heures = parser_duree_strava(duree_str)
    
    # Conversion de la distance
    distance_km = parser_distance(distance_str) if distance_str else None
    
    # Conversion de la date
    try:
        date = pd.to_datetime(date_str)
    except:
        return None
        
    return {
        'Date': date,
        'Activité': activite,
        'Durée (h)': duree_heures,
        'Distance (km)': distance_km
    }


def parser_duree_strava(duree_str):
    """Convertit une durée au format Strava (H:MM:SS ou MM:SS) en heures décimales"""
    parties = duree_str.split(':')
    
    if len(parties) == 3:  # H:MM:SS
        heures = int(parties[0])
        minutes = int(parties[1])
        secondes = int(parties[2])
        return heures + minutes / 60.0 + secondes / 3600.0
    elif len(parties) == 2:  # MM:SS
        minutes = int(parties[0])
        secondes = int(parties[1])
        return minutes / 60.0 + secondes / 3600.0
    
    return 0.0


def parser_duree(duree_str):
    """Convertit une durée (ex: '1h30', '2h00', '45min') en heures décimales"""
    duree_str = duree_str.lower().strip()
    
    # Pattern pour "1h30" ou "2h00"
    match_h_min = re.match(r'(\d+)h\s*(\d+)?', duree_str)
    if match_h_min:
        heures = int(match_h_min.group(1))
        minutes = int(match_h_min.group(2)) if match_h_min.group(2) else 0
        return heures + minutes / 60.0
    
    # Pattern pour "45min" ou "30min"
    match_min = re.match(r'(\d+)\s*min', duree_str)
    if match_min:
        return int(match_min.group(1)) / 60.0
    
    # Pattern pour "2.5" (heures décimales)
    try:
        return float(duree_str)
    except:
        return 0.0


def parser_distance(distance_str):
    """Convertit une distance en km (ex: '15km', '10.5km')"""
    distance_str = distance_str.lower().strip()
    match = re.match(r'([\d.]+)\s*km', distance_str)
    if match:
        return float(match.group(1))
    try:
        return float(distance_str)
    except:
        return None


def calculer_temps_par_semaine(df):
    """Calcule le temps total de sport par semaine"""
    if df.empty:
        return pd.DataFrame()
    
    # Ajouter une colonne semaine
    df['Semaine'] = df['Date'].dt.to_period('W')
    
    # Grouper par semaine et sommer les durées
    temps_semaine = df.groupby('Semaine')['Durée (h)'].sum().reset_index()
    temps_semaine.columns = ['Semaine', 'Temps total (h)']
    
    return temps_semaine


def generer_feedback_coach(stats):
    """
    Génère un feedback sarcastique et drôle avec GPT-5-nano
    basé sur les statistiques d'entraînement
    """
    # Charger la clé API depuis .env
    #load_dotenv()
    # api_key = os.getenv("OPENAI_API_KEY")
    # Remplace l'ancienne ligne client = OpenAI(api_key="sk-...") par :
    # 

    api_key = st.secrets["OPENAI_API_KEY"]
    client = OpenAI(api_key=api_key)
    
    # Préparer le prompt avec les stats
    prompt = f"""Analyse ces statistiques d'entraînement et rédige un message de feedback court (3-4 phrases max) pour l'athlète.

Statistiques :
- Volume total d'entraînement : {stats['volume_total']:.2f} heures
- Course à pied : {stats['volume_course']:.2f} heures
- Ski de fond/nordique : {stats['volume_ski']:.2f} heures
- Nombre d'activités : {stats['nb_activites']}
- Durée moyenne par activité : {stats['duree_moyenne']:.2f} heures
- Distance totale : {stats.get('distance_totale', 0):.2f} km
- Semaines en surcharge (>10h) : {stats['semaines_surcharge']}

Sois TRÈS sarcastique, drôle, avec de l'humour piquant. Utilise des métaphores, des comparaisons amusantes. Sois direct mais constructif. Mentionne les points forts et les points à améliorer de manière humoristique et mémorable."""

    try:
        print("\n🤖 Demande de feedback au coach GPT...")
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un coach de triathlon ultra-sarcastique, drôle et direct. Tu donnes des feedbacks TRÈS courts (2-3 phrases max), percutants, avec beaucoup d'humour piquant, des métaphores amusantes et des comparaisons drôles. Sois comme un coach qui dit la vérité avec humour, sans être méchant mais en étant mémorable et drôle. Utilise un ton décontracté et familier."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_completion_tokens=5000
        )
        
        feedback = response.choices[0].message.content
        return feedback
    except Exception as e:
        print(f"❌ Erreur lors de la génération du feedback : {e}")
        return None


def comparer_activites(df, activite1='Course à pied', activite2='Ski de fond'):
    """Compare le volume de deux activités"""
    if df.empty:
        return None, None
    
    # Normaliser les noms d'activités (insensible à la casse)
    df['Activité_normalisée'] = df['Activité'].str.lower().str.strip()
    
    # Patterns pour reconnaître les variantes d'activités
    # Course à pied : "course", "running", "jog"
    pattern_course = r'course|running|jog'
    
    # Ski : "ski de fond", "ski nordique", "ski"
    # Utilisation de groupes non-capturants (?:...) pour éviter les warnings
    pattern_ski = r'ski\s*(?:de\s*fond|nordique)?|nordique'
    
    # Calculer le volume total pour chaque activité
    volume1 = df[df['Activité_normalisée'].str.contains(pattern_course, na=False, regex=True)]['Durée (h)'].sum()
    volume2 = df[df['Activité_normalisée'].str.contains(pattern_ski, na=False, regex=True)]['Durée (h)'].sum()
    
    return volume1, volume2


def analyser_donnees_strava(texte_brut):
    """
    Fonction principale d'analyse des données Strava
    """
    print("=" * 60)
    print("ANALYSE DES DONNÉES STRAVA")
    print("=" * 60)
    print()
    
    # Parser les données
    df = parser_donnees_strava(texte_brut)
    
    if df.empty:
        print("❌ Aucune donnée valide trouvée dans le texte fourni.")
        return
    
    print(f"✅ {len(df)} activité(s) chargée(s)")
    print(f"   Période : {df['Date'].min().date()} → {df['Date'].max().date()}")
    print()
    
    # 1. Temps total par semaine
    print("-" * 60)
    print("1. TEMPS TOTAL PAR SEMAINE")
    print("-" * 60)
    temps_semaine = calculer_temps_par_semaine(df)
    
    if not temps_semaine.empty:
        for _, row in temps_semaine.iterrows():
            semaine_str = str(row['Semaine'])
            temps_total = row['Temps total (h)']
            print(f"   Semaine {semaine_str}: {temps_total:.2f} heures")
            
            # Alerte si > 10h
            if temps_total > 10:
                print(f"   ⚠️  ATTENTION SURCHARGE : Planifie une semaine de repos")
        print()
    else:
        print("   Aucune donnée par semaine disponible")
        print()
    
    # 2. Comparaison Course à pied vs Ski de fond
    print("-" * 60)
    print("2. COMPARAISON COURSE À PIED vs SKI DE FOND")
    print("-" * 60)
    volume_course, volume_ski = comparer_activites(df)
    
    print(f"   Course à pied : {volume_course:.2f} heures")
    print(f"   Ski de fond   : {volume_ski:.2f} heures")
    
    if volume_course > volume_ski:
        diff = volume_course - volume_ski
        print(f"   → Course à pied en tête de {diff:.2f} heures")
    elif volume_ski > volume_course:
        diff = volume_ski - volume_course
        print(f"   → Ski de fond en tête de {diff:.2f} heures")
    else:
        print(f"   → Volumes équilibrés")
    print()
    
    # 3. Volume total et alerte globale
    print("-" * 60)
    print("3. VOLUME TOTAL")
    print("-" * 60)
    volume_total = df['Durée (h)'].sum()
    print(f"   Volume total : {volume_total:.2f} heures")
    
    if volume_total > 10:
        print()
        print("   ⚠️  ATTENTION SURCHARGE : Planifie une semaine de repos")
    else:
        print(f"   ✅ Volume raisonnable (< 10h)")
    print()
    
    # 4. Statistiques détaillées
    print("-" * 60)
    print("4. STATISTIQUES DÉTAILLÉES")
    print("-" * 60)
    print(f"   Nombre total d'activités : {len(df)}")
    duree_moyenne = df['Durée (h)'].mean()
    print(f"   Durée moyenne par activité : {duree_moyenne:.2f} heures")
    print(f"   Durée maximale : {df['Durée (h)'].max():.2f} heures")
    print(f"   Durée minimale : {df['Durée (h)'].min():.2f} heures")
    
    distance_totale = None
    if 'Distance (km)' in df.columns and df['Distance (km)'].notna().any():
        distance_totale = df['Distance (km)'].sum()
        print(f"   Distance totale : {distance_totale:.2f} km")
    
    print()
    print("=" * 60)
    
    # 5. Feedback du coach GPT
    print()
    print("-" * 60)
    print("5. FEEDBACK DU COACH")
    print("-" * 60)
    
    # Compter les semaines en surcharge
    semaines_surcharge = 0
    if not temps_semaine.empty:
        semaines_surcharge = len(temps_semaine[temps_semaine['Temps total (h)'] > 10])
    
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
    feedback = generer_feedback_coach(stats)
    
    if feedback:
        print()
        print("💬 Message du coach :")
        print()
        print(feedback)
        print()
    else:
        print("   ⚠️  Impossible de générer le feedback")
    
    print("=" * 60)


# Exemple d'utilisation
if __name__ == "__main__":
    import sys
    
    # Si un fichier est fourni en argument, on le lit
    if len(sys.argv) > 1:
        fichier = sys.argv[1]
        try:
            with open(fichier, 'r', encoding='utf-8') as f:
                texte_donnees = f.read()
            print(f"📁 Lecture du fichier : {fichier}\n")
            analyser_donnees_strava(texte_donnees)
        except FileNotFoundError:
            print(f"❌ Erreur : Le fichier '{fichier}' n'existe pas.")
        except Exception as e:
            print(f"❌ Erreur lors de la lecture du fichier : {e}")
    else:
        # Sinon, on utilise les données d'exemple
        exemple_donnees = """
        2024-01-15, Course à pied, 1h30, 15km
        2024-01-16, Ski de fond, 2h00, 20km
        2024-01-17, Course à pied, 1h00, 10km
        2024-01-18, Ski de fond, 2h30, 25km
        2024-01-20, Course à pied, 2h00, 20km
        2024-01-22, Ski de fond, 3h00, 30km
        """
        
        print("💡 Mode démo avec données d'exemple")
        print("   Pour utiliser tes propres données :")
        print("   python3 analyse_strava.py mes_donnees.txt\n")
        
        analyser_donnees_strava(exemple_donnees)
