import streamlit as st
import folium as fo
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import xarray as xr
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib import cm
import altair as alt

    
#Chargement des données 
data=pd.read_csv("data/data_agri_bat3.csv", sep=",")
#data['time']=pd.to_datetime(data['time'])
print (data.dtypes)

#transformation de la colonne time en datetime
#data['time']=pd.to_datetime(data['time'])
class_color=['#D0D3D4','#21618C', '#3498DB', '#85C1E9', '#32CD42', '#FFE333', '#FFA533', '#FF3342']
classes=['Nan','Extremement humide','Très humide','Modèrement humide','Humidité normale','Modèrement sec','Très sec','Extremement sec']


#class_color={'A':'#D0D3D4','B':'#21618C', 'C':'#3498DB', 'D':'#85C1E9', 'E':'#32CD42', 'F':'#FFE333', 'G':'#FFA533', 'H':'#FF3342'}
#Regroupement des données en fonction de la classe et le mois
#data_cross=pd.crosstab( data['time'], data['class_sm'], normalize="index").sort_index(axis=0,ascending=True)

vis_sm=(alt
    .Chart(data, title="Humidité des sols nécessaire à l'agriculture")
    .transform_calculate(classes=f"-indexof({classes}, datum.class_sm)")
    .mark_bar()
    .encode(
       x=alt.X('time:N').title(None),
       y=alt.Y('count(class_sm)').stack("normalize").title(" % du territoire"), 
       color=alt.Color('class_sm:N', sort=classes).scale( range=class_color).title(None),
       order="classes:N"
    )
)
#Affichage des données 
#st.title("Impact de la sécheresse sur l'agriculture et les batiments")
st.altair_chart(vis_sm, use_container_width=True)

vis_usm=(alt
    .Chart(data, title="Indice d'humidité uniforme des sols")
    .transform_calculate(classes=f"-indexof({classes}, datum.class_usm)")
    .mark_bar()
    .encode(
       x=alt.X('time:N').title(None),
       y=alt.Y('count(class_usm)').stack("normalize").title(" % du territoire"), 
       color=alt.Color('class_usm:N', sort=classes).scale( range=class_color).title(None),
       order="classes:N"
    )
)

st.altair_chart(vis_usm, use_container_width=True)