import pandas as pd
import os
import json
import numpy as np



current_directory = os.path.dirname(os.path.abspath(__file__))
correspondance = os.path.join(current_directory, 'data', 'correspondance.csv')
data = pd.read_csv(correspondance, sep=";")
data = data[["Code INSEE", "geo_point_2d", "Commune"]]

# Conserver les coordonnées json de chaques code insee
data['coord_json'] = data['geo_point_2d'].apply(lambda x: {"latitude": x.split(',')[0], "longitude": x.split(',')[1]})

# Lire le fichier villes.csv (les données qui changent)
villes = os.path.join(current_directory, 'data', 'villes.csv')
data_ville = pd.read_csv(villes, encoding='latin1', sep = ";")

# Ajouter un 0 devant les codes INSEE qui ont exactement 4 caractères
data_ville['insee'] = data_ville['insee'].apply(lambda x: x.zfill(5) if len(x) == 4 else x)

# Joindre les deux csv selon le code insee
data_merged = pd.merge(data_ville, data[['Code INSEE', 'coord_json', "Commune"]], left_on='insee', right_on='Code INSEE', how='left')

# Reformater les coordonnées json pour bien les conserver
def reformater_coord_json(coord_dict):
    if pd.isna(coord_dict):  # Vérifier si la valeur est NaN
        return np.nan
    reformatted_coord_dict = {
        "latitude": float(coord_dict['latitude']),
        "longitude": float(coord_dict['longitude'])
    }
    return json.dumps(reformatted_coord_dict)
data_merged['coord_json'] = data_merged['coord_json'].apply(reformater_coord_json)

# Reformater les coordonnées json pour ceux hors France (n'ayant pas de code INSEE)
def reformater_coord_json(coord_json):
    coord_json = coord_json.strip('[]').split(',')
    return '{"latitude":'+coord_json[0]+', "longitude":'+coord_json[1]+'}'

# Modifier les coordonnées json pour les personnes hors france ( à partir du code insee)
data_merged['coord_json'] = data_merged.apply(lambda row: reformater_coord_json(row['insee']) if row['insee'].startswith('[') else row['coord_json'], axis=1)

#ajout des colonnes parents (leur sosa)
data_merged['papa'] = data_merged['sosa'] * 2
data_merged['maman'] = data_merged['sosa'] * 2 + 1

# Colonnes finales conservées dans villes_cartes (pour être sur la carte)
data_final = data_merged[["sosa", "coord_json", "insee", "qui", "papa", "maman", "Commune"]]

# Enregistrement automatique au même endroit (attention écrase l'ancien fichier !)
villes_carte = os.path.join(current_directory, 'data', 'villes_carte.csv')
data_final.to_csv(villes_carte, index=False, sep =";")
print("C'est tout bon, le changement a bien été effectué dans villes_carte.csv !")