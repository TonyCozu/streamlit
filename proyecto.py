import streamlit as st

import pandas as pd
import geopandas as gpd

import plotly.express as px

import folium
from folium import Marker
from folium.plugins import MarkerCluster
from folium.plugins import HeatMap
from streamlit_folium import folium_static

import math


#
# Configuración de la página
#
st.set_page_config(layout='wide')


#
# TÍTULO Y DESCRIPCIÓN DE LA APLICACIÓN
#

st.title('Programación en SIG. Proyecto: Visualización de datos de Especies')
st.markdown('Esta aplicación presenta visualizaciones tabulares, gráficas y geoespaciales de datos de biodiversidad que siguen el estándar [Darwin Core (DwC)](https://dwc.tdwg.org/terms/).')
st.markdown('El usuario debe seleccionar un archivo CSV basado en el DwC y posteriormente elegir una de las especies con datos contenidos en el archivo. **El archivo debe estar separado por tabuladores**. Este tipo de archivos puede obtenerse, entre otras formas, en el portal de la [Infraestructura Mundial de Información en Biodiversidad (GBIF)](https://www.gbif.org/).')
st.markdown('La aplicación muestra un conjunto de tablas, gráficos y mapas correspondientes a la distribución de la especie en el tiempo y en el espacio.')


#
# ENTRADAS
#

# Carga de datos
archivo_registros_presencia = st.sidebar.file_uploader('Seleccione un archivo CSV que siga el estándar DwC')

# Se continúa con el procesamiento solo si hay un archivo de datos cargado
if archivo_registros_presencia is not None:
    # Carga de registros de presencia en un dataframe
    registros_presencia = pd.read_csv(archivo_registros_presencia, delimiter='\t')
    # Conversión del dataframe de registros de presencia a geodataframe
    registros_presencia = gpd.GeoDataFrame(registros_presencia, 
                                           geometry=gpd.points_from_xy(registros_presencia.decimalLongitude, 
                                                                       registros_presencia.decimalLatitude),
                                           crs='EPSG:4326')

    # Carga de polígonos de Cantones y Provincia
    cantones = gpd.read_file("cantones-crtm05.geojson")
    provincias = gpd.read_file("provincias.geojson")

    # Limpieza de datos
    # Eliminación de registros con valores nulos en la columna 'species'
    registros_presencia = registros_presencia[registros_presencia['species'].notna()]
    # Cambio del tipo de datos del campo de fecha
    registros_presencia["eventDate"] = pd.to_datetime(registros_presencia["eventDate"])

    # Especificación de filtros
    # Especie
    lista_especies = registros_presencia.species.unique().tolist()
    lista_especies.sort()
    filtro_especie = st.sidebar.selectbox('Seleccione la especie', lista_especies)

#
# PROCESAMIENTO
#

    # Filtrado
    registros_presencia = registros_presencia[registros_presencia['species'] == filtro_especie]

    # Cálculo de la cantidad de registros en Cantones
    # "Join" espacial de las capas de ASP y registros de presencia
    cantones_contienen_registros = cantones.sjoin(registros_presencia, how="left", predicate="contains")
    # Conteo de registros de presencia en cada ASP
    cantones_registros = cantones_contienen_registros.groupby("cod_canton").agg(cantidad_registros_presencia = ("gbifID","count"))
    cantones_registros = cantones_registros.reset_index() # para convertir la serie a dataframe

    # Filtrado
    registros_presencia = registros_presencia[registros_presencia['species'] == filtro_especie]

    # Cálculo de la cantidad de registros en Provincias
    # "Join" espacial de las capas de ASP y registros de presencia
    provincias_contienen_registros = provincias.sjoin(registros_presencia, how="left", predicate="contains")
    # Conteo de registros de presencia en cada ASP
    provincias_registros = provincias_contienen_registros.groupby("cod_provin").agg(cantidad_registros_presencia = ("gbifID","count"))
    provincias_registros = provincias_registros.reset_index() # para convertir la serie a dataframe

# Mapas

    # Definición de columnas
    col1, col2 = st.columns(2)

    with col1:
        # Mapa de coropletas de registros de presencia por provincia
        st.header('Mapa de cantidad de registros por Provincia')

        # Capa base
        m = folium.Map(location=[9.6, -84.2], tiles='CartoDB positron', zoom_start=8)
        # Capa de coropletas
        folium.Choropleth(
            name="Cantidad de registros por Provincias",
            geo_data=provincias,
            data=provincias_registros,
            columns=['cod_provin', 'cantidad_registros_presencia'],
            bins=8,
            key_on='feature.properties.codigo',
            fill_color='Reds', 
            fill_opacity=0.5, 
            line_opacity=1,
            legend_name='Cantidad de registros de presencia',
            smooth_factor=0).add_to(m)
        # Control de capas
        folium.LayerControl().add_to(m)        
        # Despliegue del mapa
        folium_static(m)

    with col2:
        # Mapa de coropletas de registros de presencia por canton
        st.header('Mapa de cantidad de registros por Cantón')

        # Capa base
        m = folium.Map(location=[9.6, -84.2], tiles='CartoDB positron', zoom_start=8)
        # Capa de coropletas
        folium.Choropleth(
            name="Cantidad de registros por Cantón",
            geo_data=cantones,
            data=cantones_registros,
            columns=['cod_canton', 'cantidad_registros_presencia'],
            bins=8,
            key_on='feature.properties.codigo',
            fill_color='Reds', 
            fill_opacity=0.5, 
            line_opacity=1,
            legend_name='Cantidad de registros de presencia',
            smooth_factor=0).add_to(m)
        # Control de capas
        folium.LayerControl().add_to(m)        
        # Despliegue del mapa
        folium_static(m)   

    # Mapa de registros de presencia
    st.header('Mapa de registros de presencia')
    st.map(registros_presencia.rename(columns = {'decimalLongitude':'longitude', 'decimalLatitude':'latitude'}))