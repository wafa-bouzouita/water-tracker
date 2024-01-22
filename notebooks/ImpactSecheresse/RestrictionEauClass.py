import pandas as pd
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from datetime import date, timedelta
import plotly.express as px
from unidecode import unidecode
import re


def clean_column_names(column_names):
    # Replace spaces with underscores and remove special characters
    clean_names = [unidecode(re.sub(r'\W+', '', name.replace(' ', '_').lower())) for name in column_names]

    return clean_names


class RestrictionEau():
    def __init__(self):
        self.df_restriction = {}
        self.dict_map_restriction = {"Absence de restriction": "Pas de restriction", "Crise renforcée": "Crise",
                                     "Crise modérée": "Alerte renforcée",
                                     "Arrêt des prélèvements non prioritaires": "Crise",
                                     "Modification du régime hydraulique": "Alerte"}
        self.dict_map_niveau = {"Pas de restriction": 0, "Vigilance": 1, "Alerte": 2, "Alerte renforcée": 3, "Crise": 4}
        self.df_corres_commune_insee = pd.DataFrame()
        self.all_restriction_data = pd.DataFrame()

    def load_restriction_data(self, year, dataset_id_for_year):
        arrete_url = f"https://www.data.gouv.fr/fr/datasets/r/{dataset_id_for_year[year]}"
        self.df_restriction[year] = pd.read_csv(arrete_url, engine='python')

    def load_clean_corres_commune_insee(self, path):
        df_corres_commune_insee = pd.read_csv(path, sep=';')
        # columns selection
        selected_columns = ['Code INSEE', 'Code Postal', 'Commune', 'Département', 'Région']
        df_corres_commune_insee = df_corres_commune_insee[selected_columns]

        # Clean the column names
        df_corres_commune_insee.columns = clean_column_names(df_corres_commune_insee.columns)
        columns = df_corres_commune_insee.columns

        for col in columns:
            df_corres_commune_insee[col] = df_corres_commune_insee[col].str.strip("[]'").astype(str)
            df_corres_commune_insee[col] = df_corres_commune_insee[col].str.strip('"').astype(str)
        self.df_corres_commune_insee = df_corres_commune_insee

    def load_zone_alerte_commune_data(self, zone_alerte_commune_url):
        df_zone_alerte_commune = pd.read_csv(zone_alerte_commune_url)
        self.dict_id_zone_to_code_commune = df_zone_alerte_commune.set_index('id_zone')['code_commune'].to_dict()

    def clean_restriction_data(self, year):
        self.df_restriction[year]['nom_niveau'].replace(self.dict_map_restriction, inplace=True)
        self.df_restriction[year]['numero_niveau'] = self.df_restriction[year]['nom_niveau'].map(
            self.dict_map_niveau).fillna(np.nan)
        self.df_restriction[year].drop_duplicates(inplace=True)
        selected_columns = ['id_arrete', 'id_zone', 'debut_validite_arrete', 'fin_validite_arrete', 'numero_niveau',
                            'nom_niveau']
        self.df_restriction[year] = self.df_restriction[year][selected_columns]
        self.df_restriction[year].dropna(inplace=True)
        for col in ['debut_validite_arrete', 'fin_validite_arrete']:
            self.df_restriction[year][col] = pd.to_datetime(self.df_restriction[year][col], errors='coerce')
        self.df_restriction[year] = self.df_restriction[year][
            self.df_restriction[year].debut_validite_arrete <= self.df_restriction[
                year].fin_validite_arrete]  # to check if we delete or use an other thin

    def build_restriction_data(self, start_year, end_year, dataset_id_for_year):
        years = range(start_year, end_year)
        data_list = []
        for year in years:
            self.load_restriction_data(year, dataset_id_for_year)
            self.clean_restriction_data(year)
            data_list.append(self.df_restriction[year])
        self.all_restriction_data = pd.concat(data_list).reset_index(drop=True)
        self.all_restriction_data.drop_duplicates(inplace=True)

    def clean_all_restriction_data(self, filter_per_departement=True, filter_per_month=False):
        self.num_niveau_to_nom_niveau = self.all_restriction_data.set_index('numero_niveau')['nom_niveau'].to_dict()
        self.all_restriction_data.dropna(subset=['debut_validite_arrete', 'fin_validite_arrete'], inplace=True)
        # Drop rows where the dates are NaT or out of bounds
        self.all_restriction_data = self.all_restriction_data[
            (self.all_restriction_data['debut_validite_arrete'] >= '2010-01-01') & (
                        self.all_restriction_data['debut_validite_arrete'] <= '2025-01-01') & (
                        self.all_restriction_data['fin_validite_arrete'] >= '2010-01-01') & (
                        self.all_restriction_data['fin_validite_arrete'] <= '2025-01-01')]
        self.all_restriction_data = self.all_restriction_data.reset_index(drop=True)
        # Create a new DataFrame with a row for each day in each range
        dateranges = self.all_restriction_data.apply(
            lambda row: pd.date_range(row['debut_validite_arrete'], row['fin_validite_arrete']), axis=1)
        dateranges = dateranges.explode().reset_index(name='date')
        # Merge the expanded dateranges back with the original dataframe
        self.all_restriction_data = pd.merge(dateranges, self.all_restriction_data, left_on='index', right_index=True)
        # Drop the extra 'index' column and any other columns you don't need
        self.all_restriction_data = self.all_restriction_data.drop(columns=['index'])
        self.all_restriction_data.drop_duplicates(inplace=True)
        if filter_per_departement:
            self.all_restriction_data['code_insee'] = self.all_restriction_data['id_zone'].map(
                self.dict_id_zone_to_code_commune).fillna(np.nan)
            ## pk il y a des id_zone qui ont plus qu'une tpe d'alerte par jour! this should be done after concatening all data over years
            self.all_restriction_data = pd.merge(self.all_restriction_data, self.df_corres_commune_insee,
                                                 on='code_insee', how='inner')
            self.all_restriction_data.drop_duplicates(inplace=True)
            self.all_restriction_data = self.all_restriction_data.groupby(['departement', 'date'])[
                'numero_niveau'].max().reset_index()

        self.all_restriction_data.drop_duplicates(inplace=True)
        self.all_restriction_data['annee'] = self.all_restriction_data['date'].dt.year
        if filter_per_month:
            self.all_restriction_data['mois'] = self.all_restriction_data['date'].dt.month
            self.all_restriction_data.drop(columns=['date'], inplace=True)
            self.all_restriction_data.drop_duplicates(inplace=True)
            self.all_restriction_data = self.all_restriction_data.groupby(['annee', 'mois', 'numero_niveau'])[
                'departement'].count().reset_index(name='nbre_de_departement_arrete_par_mois')
        else:
            self.all_restriction_data.drop(columns=['date'], inplace=True)
            self.all_restriction_data.drop_duplicates(inplace=True)
            self.all_restriction_data = self.all_restriction_data.groupby(['annee', 'numero_niveau'])[
                'departement'].count().reset_index(name='nbre_de_departement_arrete_par_annee')

        self.all_restriction_data['nom_niveau'] = self.all_restriction_data['numero_niveau'].map(
            self.num_niveau_to_nom_niveau).fillna(np.nan)

    def process(self, start_year, end_year, filter_per_month, path_corres_commune_insee, dataset_id_for_year,
                zone_alerte_commune_url):
        self.build_restriction_data(start_year=start_year, end_year=end_year, dataset_id_for_year=dataset_id_for_year)
        self.load_clean_corres_commune_insee(path=path_corres_commune_insee)
        self.load_zone_alerte_commune_data(zone_alerte_commune_url)
        self.clean_all_restriction_data(filter_per_month=filter_per_month)

    def plot_only_restriction_data(self, year):

        data = self.all_restriction_data[self.all_restriction_data.annee == year]
        # Create checkboxes for selecting nom_niveau values
        niveaux = data['nom_niveau'].unique()
        niveau_options = [{'label': niveau, 'value': niveau} for niveau in niveaux]

        # Palette de 8 couleurs du clair au foncé
        couleurs = ['#bca12b', '#feb24c', '#fc4e2a', '#b10026']
        couleur_map = {niveaux[idx]: couleurs[idx] for idx in [0, 1, 2, 3]}

        # Create a bar graph
        fig = px.bar(data, x='mois', y='nbre_de_departement_arrete_par_mois',
                     color='nom_niveau', color_discrete_map=couleur_map, barmode='group',
                     title=f"Nombre de départements avec arrêtés par mois et par niveau de restrictionpour l'année {year}")

        # Update layout with titles and axes labels
        fig.update_layout(
            xaxis_title="Année",
            yaxis_title="Nombre de Départements avec Arrêtés",
            legend_title="Niveau de Restriction"
        )

        # Show the figure
        fig.show()

    # def plot_restriction_secheresse_data(self, year):
    #     end_date = date.today().replace(day=1)
    #     one_year_before = (end_date.today() - timedelta(days=365)).strftime("%Y-%m-%d")
    #     data = self.all_restriction_data[cl_month.all_restriction_data.annee == year]
    #     pluviometrie_mois = df_pluviometrie_month[df_pluviometrie_month.annee == year]
    #     nappes_mois = df_nappes_month[df_nappes_month.annee == year]
    #     # Create checkboxes for selecting nom_niveau values
    #     niveaux = cl_year.all_restriction_data['nom_niveau'].unique()
    #     niveau_options = [{'label': niveau, 'value': niveau} for niveau in niveaux]
    #
    #     # Palette de 8 couleurs du clair au foncé
    #     couleurs = ['#bca12b', '#feb24c', '#fc4e2a', '#b10026']
    #     couleur_map = {niveaux[idx]: couleurs[idx] for idx in [0, 1, 2, 3]}
    #     # Créez un graphique combiné
    #     fig = make_subplots(specs=[[{"secondary_y": True}]])
    #
    #     # Ajoutez les barres pour les données de restriction
    #     for niveau in data['nom_niveau'].unique():
    #         df_niveau = data[data['nom_niveau'] == niveau]
    #         fig.add_trace(
    #             go.Bar(
    #                 x=df_niveau['mois'],
    #                 y=df_niveau['nbre_de_departement_arrete_par_mois'],
    #                 name=niveau,
    #                 marker_color=couleur_map[niveau]
    #             ),
    #             secondary_y=False,
    #         )
    #
    #     # Ajoutez la ligne pour les données de pluviométrie
    #     fig.add_trace(
    #         go.Scatter(
    #             x=pluviometrie_mois['mois'],
    #             y=pluviometrie_mois['value'],
    #             name='Pluviométrie',
    #             text=pluviometrie_mois['niveau_pluviometrie'],
    #             hoverinfo='text+y',
    #             mode='lines+markers',
    #             marker_color="blue"
    #         ),
    #         secondary_y=True,
    #     )
    #
    #     # Ajoutez la ligne pour les données de pluviométrie
    #     fig.add_trace(
    #         go.Scatter(
    #             x=nappes_mois['mois'],
    #             y=nappes_mois['value'],
    #             name="Nappes d'eau",
    #             text=nappes_mois['niveau_nappes'],
    #             hoverinfo='text+y',
    #             mode='lines+markers',
    #             marker_color="green"
    #         ),
    #         secondary_y=True,
    #     )
    #
    #     # Mise à jour de la mise en page avec des titres et des labels pour les axes
    #     fig.update_layout(
    #         title=f"Nombre de départements avec arrêtés par mois et par niveau de restriction combiné avec la pluviométrie <br>et la nappes d'eau pour l'année {year}",
    #         xaxis_title='Mois',
    #         yaxis_title='Nombre de Départements avec Arrêtés',
    #     )
    #
    #     fig.update_yaxes(title_text='Pluviométrie', secondary_y=True)
    #
    #     # Affichez le graphique
    #     fig.show()
