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
        .reset_index()
        )
    #print(data_df)

    #transformation du dataframe en geodataframe (lon,lat en géométry de type point)
    data_gdf = gpd.GeoDataFrame(
        data_df, geometry=gpd.points_from_xy(data_df.lon, data_df.lat), crs="EPSG:4326"
    )
    #print(data_gdf)

    #Chargement des limites de la France Métropolitaine
    limite_france=gpd.read_file("metropole.geojson").to_crs(epsg=4326)
    #print(limite_france)

    #Selection des données sur la France 
    data_gdf_france = gpd.sjoin(data_gdf, limite_france, predicate='within')
    #print(data_gdf_france)

    return data_gdf_france

#Archivage des données traitées dans un fichier csv
def archive_cds(geodata):
    if os.path.isfile('data/archive2.csv'):
        geodata.to_csv('data/archive2.csv', header=False, mode='a')
    else:
        geodata.to_csv('data/archive2.csv', mode='a')


def data_init_csv():
    #Initialisation des données avec les 10 dernières années
    with ZipFile('data/download.zip') as myzip:
        list_file=myzip.namelist()

    for file in list_file :
        gdf=cds_to_gdf('data/'+ file)
        archive_cds(gdf)

def data_2023_csv():
    #Initialisation des données avec les 10 dernières années
    with ZipFile('data_2023/download.zip') as myzip:
        list_file=myzip.namelist()

    for file in list_file :
        gdf=cds_to_gdf('data_2023/'+ file)
        archive_cds(gdf)

data_init_csv()
data_2023_csv()