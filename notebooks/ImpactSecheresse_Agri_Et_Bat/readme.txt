Projet Water-Tracker
Sous-projet: Visualisation de l'impact de la sécheresse sur l'agriculture et les Batiments

Description: 
L'objet de ce projet est de fournir des visualisations pour mesurer l'impact de la sécheresse sur l'agriculture d'une part et sur les batiments d'autre part. 
Pour ce faire des indicateurs ont été identifiés. 
Au niveau de  l'agriculture, l'indice d'humidité des sols a été retenu ( voir description dans la documentation)
Au niveau des batiments, l'indice d'humidité uniforme a été retenu ( voir description dans la documentation)

Composition du dossier projet
"ressources": Contient la documentation utile pour comprendre les indicateurs identifiés
"data": Contient les données extraites d'ERA 5 ( API cds) ainsi que le fichier csv qui archive ces données une fois traitées
"data_2023": Contient les données extraites d'ERA 5 pour l'année 2023
"cds_lib.py": Code python pour l'extraction des données depuis l'API 'cds'
"traitement.py": Code python pour le traitement des données brutes extraites de l'API cds 
"Visualisation_sm": code python pour la visualisation de l'humidité des sols ( indicateur d'impact de la sécheresse sur l'agriculture)