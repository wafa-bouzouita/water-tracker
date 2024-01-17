import streamlit as st
import folium as fo
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import xarray as xr
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib import cm
from zipfile import ZipFile
import os
import datetime as dt
from dateutil.relativedelta import relativedelta


    
def cds_to_gdf(path):
    #chargement du fichier NetCDF dans un tableau  xarray
    data=xr.open_dataset(path)

    #transformation des données tableau xarray, en dataframe: time, lon, lat, soil_moisture
    data_df = (data
        # convert to dataframe
        .to_dataframe()
        # convert time and lon/lat to columns
        .reset_index()
        # only select what you want, in case there are bnds etc. in the data
        .loc[:,["time", "lon", "lat", "sm"]]
        # remove duplicates that could be introduced by bnds
        .drop_duplicates()
        # add an index
        
        )
    #print(data_df)

    #transformation du dataframe en geodataframe (lon,lat en géométry de type point)
    data_gdf = gpd.GeoDataFrame(
        data_df, geometry=gpd.points_from_xy(data_df.lon, data_df.lat), crs="EPSG:4326"
    )
    #print(data_gdf)

    #Chargement des limites de la France Métropolitaine
    limite_france=gpd.read_file("data/metropole.geojson").to_crs(epsg=4326)
    #print(limite_france)

    #Chargement de l'occupation des sols en France
    #Land_cover_France=gpd.read_file("data/U2018_CLC2018_V2020_20u1.shp")
    #print(Land_cover_France.index, Land_cover_France.shape)

    #Selection des données sur la France 
    data_gdf_france = gpd.sjoin(data_gdf, limite_france, predicate='within')
    #print(data_gdf_france)

    return data_gdf_france

def humidity_class(val):    
    if   0<= val <15.0:
        return "Extremement sec"
    elif 15.0<= val <30.0:
        return "Très sec"
    elif 30.0 <= val<50.0:
        return "Modèrement sec"
    elif 50.0 <= val<65.0:
        return "Humidité normale"
    elif 65.0 <= val<75.0:
        return "Modèrement humide"
    elif 75.0 <= val<90.0:
        return "Très humide"
    elif 90<= val<100.0:
        return "Extremement humide"
    else:
        return "Nan"
    
#Fonction de calcul de l'indice d'humidité uniforme 
def compute_usm(data_fusm, date):
    
    usm_compute = data_fusm.groupby('geometry').agg(usm=('sm',np.mean))
        
    return usm_compute


#fonction d'Archivage des données traitées
def data_to_csv(geodata, file_name):
    if os.path.isfile('data/'+file_name+'.csv'):
        geodata.to_csv('data/'+file_name+'.csv', header=False, mode='a')
    else:
        geodata.to_csv('data/'+file_name+'.csv', mode='a')


def data_treatment(path,data):  
    gdf=cds_to_gdf('data/'+ file)
    gdf['class_sm']=gdf['sm'].astype(float).apply(humidity_class)
    gdf['u_sm']=None
    gdf['time']=pd.to_datetime(gdf['time']).dt.date
    month=gdf.iloc[0,0]
    print(month)
    data=pd.concat([data, gdf])
    # print(data.head())
    data=compute_uniform_humidity(data,month)
    return data

def compute_all_usm(data):
    data['time']=pd.to_datetime(data['time']).dt.date
    times=data['time'].unique()

    for t in times:   
        date_before_1month = t - relativedelta(months=1)
        date_before_2month = t - relativedelta(months=2)
        
        if (date_before_1month in times) and (date_before_2month in times):  
            data_for_Usm=data[((data['time']==t) | (data['time']==date_before_1month) | (data['time']==date_before_2month))]
            data_t=compute_usm(data_for_Usm,t)    
            data.loc[data['time']==t,'u_sm']=list(map(lambda geom: data_t.loc[geom],data.loc[data['time']==t,'geometry']))         
    return data   



if __name__=='__main__':
    
    #Initialisation du dataframe qui contiendra les données traitées
    data=pd.DataFrame()

    #Chargement des fichiers NetCDF dans un géodataframe et restriction sur la France
    with ZipFile('data/download.zip') as myzip:
        list_file=myzip.namelist()  

    for file in list_file:
        data=pd.concat([data,cds_to_gdf('data/'+ file)])

    #Classification de l'indice d'humidité des sols pour chaque pixel
    data['class_sm']=data['sm'].astype(float).apply(humidity_class)
    
    #Calcul de l'indice d'humidité des sols uniforme pour chaque classe
    data=compute_all_usm(data)

    #Classification de l'indice d'humidité des sols uniforme pour chaque pixel
    data['class_usm']=data['u_sm'].astype(float).apply(humidity_class)

    #Sauvegarde des données traitées dans un fichier csv
    data_to_csv(data,"data_agri_bat3")

