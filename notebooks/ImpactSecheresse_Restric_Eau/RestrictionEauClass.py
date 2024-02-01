import pandas as pd
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from datetime import date, timedelta
import plotly.io as pio
from unidecode import unidecode
import re
import os


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
        self.end_date = date.today().replace(day=1)
        self.start_date = (self.end_date.today() - timedelta(days=365*2)).strftime("%Y-%m-%d")

    def load_restriction_data(self, year, dataset_id):
        """
        Loads water restriction data for a specific year from a given dataset ID.
        Parameters:
            year (int): The year for which to load data.
            dataset_id (dict): Dictionary mapping years to dataset IDs.
        """
        arrete_url = f"https://www.data.gouv.fr/fr/datasets/r/{dataset_id[year]}"
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
        """
        Loads data about alert zones in communes from the specified URL.
        Parameters:
            zone_alerte_commune_url (str): URL to the CSV file containing zone alert data.
        """
        df_zone_alerte_commune = pd.read_csv(zone_alerte_commune_url)
        self.dict_id_zone_to_code_commune = df_zone_alerte_commune.set_index('id_zone')['code_commune'].to_dict()

    def clean_restriction_data(self, year):
        """
        Cleans and preprocesses restriction data for a specific year.
        Parameters:
            year (int): The year for which the data is being cleaned.
        """
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

    def build_restriction_data(self, dataset_id):
        years = range(self.end_date.year-2, self.end_date.year)
        data_list = []
        for year in years:
            self.load_restriction_data(year, dataset_id)
            self.clean_restriction_data(year)
            data_list.append(self.df_restriction[year])
        self.all_restriction_data = pd.concat(data_list).reset_index(drop=True)
        self.all_restriction_data.drop_duplicates(inplace=True)

    def _validate_and_clean_data(self):
        """Validates and cleans the initial water restriction data."""
        valid_start_date, valid_end_date = pd.Timestamp('2010-01-01'), pd.Timestamp('2025-01-01')
        self.num_niveau_to_nom_niveau = self.all_restriction_data.set_index('numero_niveau')['nom_niveau'].to_dict()
        self.all_restriction_data.dropna(subset=['debut_validite_arrete', 'fin_validite_arrete'], inplace=True)
        self.all_restriction_data = self.all_restriction_data.query(
            "`debut_validite_arrete` >= @self.start_date and `debut_validite_arrete` <= @self.end_date and " +
            "`fin_validite_arrete` >= @self.start_date and `fin_validite_arrete` <= @self.end_date"
        ).reset_index(drop=True)

    def _expand_date_ranges(self):
        """Expands date ranges into individual rows for each day."""
        dateranges = self.all_restriction_data.apply(
            lambda row: pd.date_range(row['debut_validite_arrete'], row['fin_validite_arrete']), axis=1
        ).explode().reset_index(name='date')
        self.all_restriction_data = pd.merge(dateranges, self.all_restriction_data, left_on='index', right_index=True).drop(columns=['index'])

    def _map_and_merge_data(self, filter_per_departement):
        """Maps and merges additional data based on department filtering."""
        if filter_per_departement:
            self.all_restriction_data['code_insee'] = self.all_restriction_data['id_zone'].map(
                self.dict_id_zone_to_code_commune).fillna(np.nan)
            self.all_restriction_data = pd.merge(
                self.all_restriction_data, self.df_corres_commune_insee, on='code_insee', how='inner'
            ).drop_duplicates().groupby(['departement', 'date'])['numero_niveau'].max().reset_index()

    def _aggregate_and_restructure_data(self):
        """Aggregates data by year and month, and restructures the DataFrame."""

        self.all_restriction_data['date'] = self.all_restriction_data['date'].apply(lambda x: x.strftime("%Y-%m") if pd.notnull(x) else x) #if filter_per_month else self.all_restriction_data['date'].strftime("%Y")
        self.all_restriction_data.drop_duplicates(inplace=True)

        grouping_cols = ['date', 'numero_niveau']
        count_col = 'nbre_de_departement_arrete_par_mois' #if filter_per_month else 'nbre_de_departement_arrete_par_annee'

        self.all_restriction_data = self.all_restriction_data.groupby(grouping_cols)['departement']\
            .count().reset_index(name=count_col)

        self.all_restriction_data['nom_niveau'] = self.all_restriction_data['numero_niveau']\
            .map(self.num_niveau_to_nom_niveau).fillna(np.nan)
        self._filter_recent_data()

    def _filter_recent_data(self):
        """Filters the data for the most recent year."""
        end_date = date.today().replace(day=1)
        one_year_before = end_date - timedelta(days=365)
        end_date = end_date.strftime("%Y-%m")
        one_year_before = one_year_before.strftime("%Y-%m")
        self.all_restriction_data = self.all_restriction_data.query(
            "`date` >= @one_year_before and `date` <= @end_date"
        ).reset_index(drop=True)


    def _save_data_to_csv(self):
        """Saves the processed data to a CSV file."""
        output_filename = os.path.abspath("./data/restriction_data.csv")
        try:
            self.all_restriction_data.to_csv(output_filename, index=False)
            print(f"Data saved successfully in {output_filename}")
        except Exception as e:
            print(f"Error saving data to CSV: {e}")

    def clean_all_restriction_data(self, filter_per_departement=True, filter_per_month=False):
        """Cleans and processes the water restriction data."""
        self._validate_and_clean_data()
        self._expand_date_ranges()
        self._map_and_merge_data(filter_per_departement)
        self._aggregate_and_restructure_data()
        self._save_data_to_csv()


    def process(self, filter_per_month, path_corres_commune_insee, dataset_id,
                zone_alerte_commune_url):
        """Processes the water restriction data from raw data to final CSV output."""

        self.build_restriction_data(dataset_id=dataset_id)
        self.load_clean_corres_commune_insee(path=path_corres_commune_insee)
        self.load_zone_alerte_commune_data(zone_alerte_commune_url)
        self.clean_all_restriction_data(filter_per_month=filter_per_month)

    def plot_restriction_secheresse_data(self, pluviometrie_mois=None, nappes_mois=None):

        couleurs = ['#bca12b', '#feb24c', '#fc4e2a', '#b10026']
        niveaux = ['Vigilance', 'Alerte', 'Alerte renforcée', 'Crise']
        couleur_map = {niveaux[idx]: couleurs[idx] for idx in [0, 1, 2, 3]}

        # Créez un graphique combiné
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        for niveau in self.all_restriction_data['nom_niveau'].unique():
            df_niveau = self.all_restriction_data[self.all_restriction_data['nom_niveau'] == niveau]
            fig.add_trace(
                go.Bar(
                    x=df_niveau['date'],
                    y=df_niveau['nbre_de_departement_arrete_par_mois'],
                    name=niveau,
                    marker_color=couleur_map[niveau]
                ),
                secondary_y=False,
            )

        if not pluviometrie_mois.empty:
            if all(column in pluviometrie_mois.columns for column in ['annee', 'mois']):
                pluviometrie_mois['date'] = pd.to_datetime(
                    pluviometrie_mois['annee'].astype(str) + '-' + pluviometrie_mois['mois'].astype(str),
                    format='%Y-%m')
                pluviometrie_mois.drop(['annee', 'mois'], axis=1, inplace=True)
            fig.add_trace(
                go.Scatter(
                    x=pluviometrie_mois['date'],
                    y=pluviometrie_mois['valeur'],
                    name='Pluviométrie',
                    text=pluviometrie_mois['niveau_pluviométrie'],
                    hoverinfo='text+y',
                    mode='lines+markers',
                    marker_color="blue"
                ),
                secondary_y=True,
            )

        if not nappes_mois.empty:
            if all(column in nappes_mois.columns for column in ['annee', 'mois']):
                nappes_mois['date'] = pd.to_datetime(
                    nappes_mois['annee'].astype(str) + '-' + nappes_mois['mois'].astype(str), format='%Y-%m')
                nappes_mois.drop(['annee', 'mois'], axis=1, inplace=True)
            fig.add_trace(
                go.Scatter(
                    x=nappes_mois['date'],
                    y=nappes_mois['valeur'],
                    name="Nappes d'eau",
                    text=nappes_mois['niveau_nappes'],
                    hoverinfo='text+y',
                    mode='lines+markers',
                    marker_color="green"
                ),
                secondary_y=True,
            )

        fig.update_layout(
            title=f"Nombre de départements avec arrêtés par mois et par niveau de restriction combiné avec la pluviométrie <br>et la nappes d'eau",
            xaxis_title='Mois',
            yaxis_title='Nombre de Départements avec Arrêtés',
        )

        fig.update_yaxes(title_text='Pluviométrie', secondary_y=True)

        fig.show()

        # Save the figure
        image_filename = f'./images/retriction_secheresse.pdf'
        print(f"Sauvegarde du graphique dans {image_filename}")
        pio.write_image(fig, image_filename)
