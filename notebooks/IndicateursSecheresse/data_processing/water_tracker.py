from base_standard_index import BaseStandardIndex
from datetime import date, timedelta, datetime
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import pickle
import requests
from tqdm import tqdm

class WaterTracker():
    def __init__(self, api_key):
        self.api_key = api_key
        self.data_folder = "data/"
        self.timeseries_folder = self.data_folder+"timeseries/"
        self.df_stations = pd.read_csv(f"{self.data_folder}df_stations.csv")
        self.mapping_indicateur_column = {"pluviométrie":"dryness-meteo", 
                                          "nappes": "dryness-groundwater", 
                                          "nappes profondes": "dryness-groundwater-deep"
                                          }
        self.mapping_indicateur_indicateur_standardise = {"pluviométrie":"spi", 
                                                          "nappes": "spli", 
                                                          "nappes profondes": "spli"
                                                          }
        self.levels_colors = ["#da442c", "#f28f00", "#ffdd55", "#6cc35a", "#30aadd", "#1e73c3", "#286172"]
        self.timeseries = {}
        self.timeseries_computed = {}
        self.standardized_indicator_means_last_year = {}
        self.aggregated_standardized_indicator_means_last_year = {}
        self.levels = { -1.78        : "Très bas",
                        -0.84        : "Bas",
                        -0.25        : "Modérément bas",
                         0.25        : "Autour de la normale",
                         0.84        : "Modérément haut",
                         1.28        : "Haut",
                         float('inf'): "Très haut"
                      }
        self.mapping_indicator_names = {"dryness-meteo":"rain-level",
                                        "dryness-groundwater":"water-level-static",
                                        "dryness-groundwater-deep":"water-level-static",
                                        }
        
        # Some stations have strange values, we get rid off them
        self.black_listed_station_ids = [1951]


    def download_stations_data(self):
        stations_data = {}
        for i in tqdm(range(1,96)):
            stations_data[i] = self.download_departement_data(str(i).rjust(2,"0"))

        # data[20] is None
        del stations_data[20]

        return stations_data  

    def download_departement_data(self, departement_code):
        headers = {'accept': 'application/json', 'Authorization': f'Bearer {self.api_key}'}
        params = {'with':'geometry;indicators.state.type;locations.type;locations.indicators.state.type'}
        
        try:
            response = requests.get(f'https://api.emi.imageau.eu/app/departments/{departement_code}', params=params, headers=headers)
        except Exception as e:
            print(e)
            return
        else:
            if response.status_code == 200:
                return dict(response.json())
            else:
                return None 

    def build_stations_data(self):
        """
        Call this function to create the df_stations.csv file storing all data about stations that are needed for further computations (timeseries, computation of standardized indicators, plots)
        """
        stations_data = self.stations_data()
        res = []
        for departement_code in stations_data.keys():
            for station in stations_data[departement_code]["data"]["locations"]:
                data = {"departement_code" : departement_code,
                        "id": station["id"],
                        'bss_code': station["bss_code"],
                        'name': station["name"],
                        'bss_code': station["bss_code"],
                        "indicators": [indicator["state"]["type"]["name"] for indicator in station["indicators"]],
                    }
                res.append(data)
        df_stations = pd.DataFrame(res)
        df_stations = pd.concat([df_stations, pd.get_dummies(df_stations["indicators"].explode()).groupby(level=0).sum()], axis=1).drop("indicators", axis=1)
        output_filename = "./data/df_stations.csv"
        print(f"Sauvegarde des données des stations dans {output_filename}")
        df_stations.to_csv(output_filename, index=False)
    

    def download_timeseries_station(self, location_id, start_date, end_date):

        headers = {'accept': 'application/json', 'Authorization': f'Bearer {self.api_key}'}
        params = {'location_id': str(location_id), 'from': start_date, 'to': end_date}
        
        try:
            response = requests.get('https://api.emi.imageau.eu/app/data', params=params, headers=headers)
        except Exception as e:
            print(e)
            return
        else:
            if response.status_code == 200:
                return dict(response.json())
            else:
                return None

    def download_all_timeseries(self):
        """
        Call this function to query the API and download/update the timeseries for all stations.
        The file df_stations.csv must be created first with self.build_stations_data()
        """
        start_date = "1970-01-01"
        today = datetime.today().strftime('%Y-%m-%d')
        df = pd.read_csv("./data/df_stations.csv")
        cpt = 0
        n = len(df)
        for i, row in df.iterrows():
            station_id = row["id"]
            if station_id not in self.black_listed_station_ids:
                cpt+=1
                print(f"{100*cpt/n}%", end="\r")
                if row["dryness-meteo"]==1 or row["dryness-groundwater-deep"]==1 or row["dryness-groundwater"]==1:
                    
                    filename = f"./data/timeseries/{station_id}.csv"
                    
                    if not os.path.isfile(filename):
                        d = self.download_timeseries_station(station_id, start_date, today)
                        if row["dryness-meteo"]==1:
                            timeseries = pd.DataFrame(d[self.mapping_indicator_names["dryness-meteo"]])[["date","value"]]
                        elif row["dryness-groundwater-deep"]==1 or row["dryness-groundwater"]==1:
                            timeseries = pd.DataFrame(d[self.mapping_indicator_names["dryness-groundwater-deep"]])[["date","value"]]
                        else:
                            pass
                        timeseries["date"] = pd.to_datetime(timeseries["date"])
                        timeseries = timeseries.drop_duplicates()
                        #timeseries = timeseries.set_index("date")
                        timeseries.to_csv(filename)

                    else:
                        timeseries_init = pd.read_csv(filename)
                        timeseries_init["date"] = pd.to_datetime(timeseries_init["date"])
                        # Download data from the last date only
                        #next_date = timeseries_init.index[0].to_pydatetime()+timedelta(days=1)
                        next_date = (timeseries_init["date"].max().to_pydatetime()+timedelta(days=1)).date()
                        #print(loc_id, next_date, today)
                        d = self.download_timeseries_station(station_id, next_date, today)
                        #print(d)
                        if row["dryness-meteo"]==1:
                            indicator_name = self.mapping_indicator_names["dryness-meteo"]
                        elif row["dryness-groundwater-deep"]==1:
                            indicator_name = self.mapping_indicator_names["dryness-groundwater-deep"]
                        elif row["dryness-groundwater"]==1:
                            indicator_name = self.mapping_indicator_names["dryness-groundwater"]
                        else:
                            print("ERREUR")

                        if len(d[indicator_name]) > 0:
                            timeseries = pd.DataFrame(d[indicator_name])[["date","value"]]
                            timeseries["date"] = pd.to_datetime(timeseries["date"])
                            timeseries = timeseries.drop_duplicates()
                            #timeseries = timeseries.set_index("date")

                            timeseries_final = pd.concat([timeseries_init, timeseries], axis=0)
                            timeseries_final.to_csv(filename)


    def column_from_indicateur(self, indicateur):
        if indicateur in self.mapping_indicateur_column.keys():
            return self.mapping_indicateur_column[indicateur]
        else:
            print("Problème: l'indicateur doit être pluviométrie, nappes, ou nappes profondes")
            return None
    
    def load_timeseries(self):
        self.timeseries = pickle.load(open(f"{self.data_folder}timeseries.pkl", "rb"))
    
    
    def load_timeseries_computed(self):
        self.timeseries_computed = pickle.load(open(f"{self.data_folder}timeseries_computed.pkl", "rb"))

    
    def load_standardized_indicator_means_last_year(self):
        self.standardized_indicator_means_last_year = pickle.load(open(f"{self.data_folder}standardized_indicator_means_last_year.pkl", "rb"))


    def load_aggregated_standardized_indicator_means_last_year(self):
        self.aggregated_standardized_indicator_means_last_year = pickle.load(open(f"{self.data_folder}aggregated_standardized_indicator_means_last_year.pkl", "rb"))


    def load_timeseries_from_files(self, indicateur, min_number_years=15):
        column = self.column_from_indicateur(indicateur)
        if column is None:
            return None
        
        ids = self.df_stations[self.df_stations[column]==1]["id"].values
        self.timeseries[indicateur] = {}
        print(f"Chargement des chroniques pour l'indicateur {indicateur}")
        for station_id in tqdm(ids) :
            if station_id not in self.black_listed_station_ids:
                timeseries = pd.read_csv(f"{self.timeseries_folder}{station_id}.csv")
                timeseries["date"] = pd.to_datetime(timeseries["date"])
                
                if (timeseries["date"].max() - timeseries["date"].min()).days/365 >= (min_number_years+1):
                    start_date = (date.today()-timedelta(days=min_number_years*365)).strftime("%Y-%m-%d")
                    timeseries = timeseries[timeseries["date"]>=start_date]
                    timeseries = timeseries.set_index("date")
                    self.timeseries[indicateur][station_id] = timeseries
        print(f"Terminé")

    def save_data(self, data, filename):
        print(f"Saving into {filename}")
        pickle.dump(data, open(filename, "wb"))
    
    def save_timeseries(self):
        print(f"Saving timeseries into {self.data_folder}timeseries.pkl")
        pickle.dump(self.timeseries, open(f"{self.data_folder}timeseries.pkl", "wb"))

    def save_timeseries_computed(self):
        print(f"Saving timeseries_computed into {self.data_folder}timeseries_computed.pkl")
        pickle.dump(self.timeseries_computed, open(f"{self.data_folder}timeseries_computed.pkl", "wb"))
    
    def save_standardized_indicator_means_last_year(self):
        print(f"Saving standardized_indicator_means_last_year into {self.data_folder}standardized_indicator_means_last_year.pkl")
        pickle.dump(self.standardized_indicator_means_last_year, open(f"{self.data_folder}standardized_indicator_means_last_year.pkl", "wb"))
    
    def save_aggregated_standardized_indicator_means_last_year(self):
        print(f"Saving aggregated_standardized_indicator_means_last_year into {self.data_folder}aggregated_standardized_indicator_means_last_year.pkl")
        pickle.dump(self.aggregated_standardized_indicator_means_last_year, open(f"{self.data_folder}aggregated_standardized_indicator_means_last_year.pkl", "wb"))

    def save(self):
        """
        Save all the data that are stored
        """
        self.save_timeseries()
        self.save_timeseries_computed()
        self.save_standardized_indicator_means_last_year()
        self.save_aggregated_standardized_indicator_means_last_year()
        
        
    def load(self):
        """
        Loads all the data that are stored
        """
        print(f"Chargement des chroniques (timeseries) depuis {self.data_folder}timeseries.pkl")
        self.timeseries = pickle.load(open(f"{self.data_folder}timeseries.pkl", "rb"))

        print(f"Chargement des chroniques des indicateurs (timeseries_computed) depuis {self.data_folder}timeseries_computed.pkl")
        self.timeseries_computed = pickle.load(open(f"{self.data_folder}timeseries_computed.pkl", "rb"))

        print(f"Chargement des indicateurs standardisés sur 1 an (standardized_indicator_means_last_year) depuis {self.data_folder}standardized_indicator_means_last_year.pkl")
        self.standardized_indicator_means_last_year = pickle.load(open(f"{self.data_folder}standardized_indicator_means_last_year.pkl", "rb"))

        print(f"Chargement des données agrégées (aggregated_standardized_indicator_means_last_year) depuis {self.data_folder}aggregated_standardized_indicator_means_last_year.pkl")
        self.aggregated_standardized_indicator_means_last_year = pickle.load(open(f"{self.data_folder}aggregated_standardized_indicator_means_last_year.pkl", "rb"))


    def aggregate_standardized_indicator_means_last_year(self, indicateur):
        self.aggregated_standardized_indicator_means_last_year[indicateur] = { month: {level:0  for level in range(len(self.levels.keys()))} for month in range(12)}
        print(self.aggregated_standardized_indicator_means_last_year)
        for station_id, data in self.standardized_indicator_means_last_year[indicateur].items():
            if station_id not in self.black_listed_station_ids:
                for month, level in data.items():
                    self.aggregated_standardized_indicator_means_last_year[indicateur][month][level] += 1

    def compute_standardized_indicator_values(self, indicateur, freq="M", scale = 3):
        print("Calcul des indicateurs standardisés par mois")
        self.standardized_indicator_means_last_year[indicateur] = {}
        self.timeseries_computed[indicateur] = {}

        standardized_indicator = self.mapping_indicateur_indicateur_standardise[indicateur]
        end_date = date.today().replace(day=1)
        one_year_before = (end_date.today()-timedelta(days=365)).strftime("%Y-%m-%d")
        

        for station_id, timeseries in tqdm(self.timeseries[indicateur].items()):
            if station_id not in self.black_listed_station_ids:
                timeseries = self.clean_timeseries(timeseries)
                
                standardized_indicator_computer = BaseStandardIndex()
                timeseries_computed = standardized_indicator_computer.calculate(df=timeseries,
                                                                                date_col='date', 
                                                                                precip_cols='value',
                                                                                indicator=standardized_indicator, 
                                                                                freq=freq, 
                                                                                scale=scale, # rolling sum over 3 month
                                                                                fit_type="mle", 
                                                                                dist_type="gam",
                                                                                )
                
                timeseries_computed.columns = ["date", f"roll_{scale}{freq}", standardized_indicator]
                self.timeseries_computed[indicateur][station_id] = timeseries_computed

                timeseries_tmp = timeseries_computed[timeseries_computed["date"] >= one_year_before]
                
                d = dict(timeseries_tmp[standardized_indicator].groupby(timeseries_tmp['date'].dt.month).mean().apply(lambda x: self.standardized_indicator_to_level_code(x)))
                dd = {k-1:v for k,v in d.items()}
                self.standardized_indicator_means_last_year[indicateur][station_id] = dd

    def plot_counts_france(self, indicateur):
        """
        Plots the BRGM representation of the proportions of stations in France for each dryness levels month by month since 1 year.
        Returns also the corresponding dataframe
        """
        print(f"Création du graphique pour {indicateur}")
        standardized_indicator = self.mapping_indicateur_indicateur_standardise[indicateur]
        df_levels = pd.DataFrame(self.aggregated_standardized_indicator_means_last_year[indicateur]).transpose().reset_index()
        df_levels.columns = ["Mois"] + [x for x in self.levels.values()]
        dict_months ={  0: "Janvier",
                        1: "Février",
                        2: "Mars",
                        3: "Avril",
                        4: "Mai",
                        5: "Juin",
                        6: "Juillet",
                        7: "Août",
                        8: "Septembre",
                        9: "Octobre",
                        10: "Novembre",
                        11: "Décembre",
                        }
        # Add years after months in dict_months
        today = date.today()
        current_year = today.year
        last_year = current_year-1
        last_month = today.month-1
        for month, name in dict_months.items():
            if month<last_month:
                dict_months[month] = f"{name} {current_year}"
            else:
                dict_months[month] = f"{name} {last_year}"

        df_levels["Mois"]= df_levels["Mois"].replace(dict_months)
        
        # Shift rows to display the last month on the right of the graph
        df_levels = df_levels.reindex(index=np.roll(df_levels.index,12-(date.today().replace(day=1).month-1)))
        df_values = df_levels.drop("Mois", axis=1)
        df_values = df_values.div(df_values.sum(axis=1), axis=0)*100
        df_levels = pd.concat([df_levels["Mois"], df_values], axis=1)

        ax = df_levels.plot.bar(x="Mois",
                                stacked=True,
                                title=f"{indicateur.capitalize()} : répartition de la sécheresse depuis 1 an",
                                color=self.levels_colors,
                                grid=False,
                                )
        plt.yticks(range(0,101,10))
        plt.xlabel("")
        plt.ylabel("Proportion des stations (%)")
        #plt.tick_params(labelright=True)
        
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(reversed(handles), reversed(labels), loc='upper left',bbox_to_anchor=(1.0, 0.5))
        fig = ax.get_figure()
        fig.autofmt_xdate(rotation=45)
        image_filename = f'./images/{indicateur}.pdf'
        print(f"Sauvegarde du graphique dans {image_filename}")
        fig.savefig(image_filename, bbox_inches='tight')
        return df_levels

    def standardized_indicator_to_level_code(self, standardized_indicator_value):
        for i, (k, v) in enumerate(self.levels.items()):
            if standardized_indicator_value < k:
                return i

    def process(self, indicateur):
        """
        Loads the timeseries
        indicateur = "pluviométrie", "nappe", "nappe profonde"
        """
        
        self.load_timeseries_from_files(indicateur=indicateur, min_number_years=15)
        self.compute_standardized_indicator_values(indicateur=indicateur, freq="M", scale=3)
        self.save_timeseries_computed()
        self.save_standardized_indicator_means_last_year()
        self.aggregate_standardized_indicator_means_last_year(indicateur=indicateur)
        self.save_aggregated_standardized_indicator_means_last_year()

    def test(self, indicateur, id_station):
        freq="M"
        scale = 3
        end_date = date.today().replace(day=1)
        one_year_before = (end_date.today()-timedelta(days=365)).strftime("%Y-%m-%d")
        timeseries = pd.read_csv(f"./data/timeseries/{id_station}.csv")#self.timeseries[indicateur][id_station]
        timeseries = self.clean_timeseries(timeseries)
        standardized_indicator = self.mapping_indicateur_indicateur_standardise[indicateur]
    
        timeseries = timeseries.reset_index()
        timeseries = timeseries.drop_duplicates(subset="date")
        #print(timeseries["value"].tolist())
        print(timeseries["value"].describe())
        standardized_indicator_computer = BaseStandardIndex()
        timeseries_computed = standardized_indicator_computer.calculate(df=timeseries,
                                                                        date_col='date', 
                                                                        precip_cols='value',
                                                                        indicator=standardized_indicator, 
                                                                        freq=freq, 
                                                                        scale=scale, # rolling sum over 3 month
                                                                        fit_type="mle", 
                                                                        dist_type="gam",
                                                                        )
        
        timeseries_computed.columns = ["date", f"roll_{scale}{freq}", standardized_indicator]
        #self.timeseries_computed[indicateur][id_station] = timeseries_computed

        timeseries_tmp = timeseries_computed[timeseries_computed["date"] >= one_year_before]
        #print(timeseries["value_scale_3"].tolist())
        #print(list(timeseries_computed["spli"].values))
        print(timeseries_computed.describe())
        d = dict(timeseries_tmp[standardized_indicator].groupby(timeseries_tmp['date'].dt.month).mean().apply(lambda x: self.standardized_indicator_to_level_code(x)))
        dd = {k-1:v for k,v in d.items()}
        print(dd)
        #self.standardized_indicator_means_last_year[indicateur][id_station] = dd

    def clean_timeseries(self, timeseries):
        """
        Remove outliers, duplicated dates and set all values to positive values
        """
        df = timeseries.copy()
        df = df.reset_index()
        df = df.drop_duplicates(subset="date")
        df["value"] = df["value"].apply(abs)
        col="value"
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3- Q1
        c = 2
        min_t = Q1 - c*IQR
        max_t = Q3 + c*IQR
        df["outlier"] = (df[col].clip(lower = min_t,upper=max_t) != df[col])
        return df[~df["outlier"]].drop("outlier",axis=1)