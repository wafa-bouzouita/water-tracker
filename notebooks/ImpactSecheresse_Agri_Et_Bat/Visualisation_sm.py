import streamlit as st
import folium as fo
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import xarray as xr
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib import cm


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
    
#Chargement des données 
data=pd.read_csv("data/archive2.csv", sep=",")
print (data.dtypes)

#transformation de la colonne time en datetime
data['time']=pd.to_datetime(data['time'], format="")

#Classification des valeurs d'indice d'humidite 
data['class_sm']=data['sm'].astype(float).apply(humidity_class)

#Regroupement des données en fonction de la classe et le mois
data_cross=pd.crosstab( data['time'], data['class_sm'], normalize="index").sort_index(axis=0,ascending=False)

#Affichage des données 
st.title("Indice d'humidité des sols")
print (data_cross[:10])
st.bar_chart(data_cross[:10], width=5)

