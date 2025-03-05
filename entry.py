import pandas as pd
import streamlit as st
import boto3 
from io import StringIO

session = boto3.Session(
    aws_access_key_id=st.secrets["aws"]["access_key"],
    aws_secret_access_key=st.secrets["aws"]["secret_access_key"]
)
s3 = session.client('s3')
#Read all observatios necessary columns with provided datatypes for efficiency
all_obs_dtypes = {
    'SUBNATIONAL1_CODE': 'string',
    'SPECIES_CODE': 'string',
    'Year':'category'
}

#Get file from S3
response = s3.get_object(Bucket='feederwatch-dashboard', Key='observation_data_oh.csv')
csv_content = response['Body'].read().decode('utf-8')
all_obs_data = StringIO(csv_content)

all_obs = pd.read_csv(
    all_obs_data,#'observation_data.csv',
    dtype=all_obs_dtypes,
    usecols=['SUBNATIONAL1_CODE','HOW_MANY', 'SPECIES_CODE','Year','LATITUDE','LONGITUDE']
)
ohio_obs = all_obs.loc[all_obs['SUBNATIONAL1_CODE'] == "US-OH"]

#Only keep records where HOW_MANY is not null for analysis
#Then convert to int for efficiency
ohio_obs.dropna(subset=['HOW_MANY'], inplace=True)
ohio_obs['HOW_MANY'] = ohio_obs['HOW_MANY'].astype('int64')

#Read in species translation table
species_translation_dtypes = {
    'species_code': 'string',
    'american_english_name': 'string',
}
#Get file from s3
response = s3.get_object(Bucket='feederwatch-dashboard', Key='species_translation.csv')
csv_content = response['Body'].read().decode('utf-8')
species_translation_data = StringIO(csv_content)

species_translation = pd.read_csv(
    species_translation_data,#'species_translation.csv',
    dtype=species_translation_dtypes,
    usecols=['species_code','american_english_name']
)


#Merge dataframes
ohio_obs = pd.merge(ohio_obs, species_translation, how="inner", left_on="SPECIES_CODE",right_on="species_code")

ohio_obs.info()

#Get yearly counts for all birds
yearly_counts = ohio_obs.groupby(['Year', 'american_english_name'], as_index=False)['HOW_MANY'].sum()
top_10_count = ohio_obs.groupby('american_english_name', as_index=False)['HOW_MANY'].sum()
top_10_count = top_10_count.sort_values(by='HOW_MANY', ascending=False)
top_10_count = top_10_count.head(10)

#Filter yearly counts by top 10 list
filtered_yearly_counts = yearly_counts[yearly_counts['american_english_name'].isin(top_10_count['american_english_name'])]
filtered_yearly_counts = filtered_yearly_counts.sort_values(by=['american_english_name', 'Year'], 
                                   ascending=[True, False])

st.title("Feeder Watch Ohio")
st.caption("Compiled from data publicly available via Cornell's Feeder Watch")
st.caption("https://feederwatch.org/explore/raw-dataset-requests/")

st.header("Top 10 Birds Year Over Year", divider=True)
#View Top 10 Counts by year
#st.dataframe(filtered_yearly_counts)
st.bar_chart(
    filtered_yearly_counts,
    x="american_english_name",
    y=["HOW_MANY"],
    color="Year",
    stack=False,
    
    x_label='Bird Name',
    y_label='Observation Count'
)


st.header("Observation Count Trends", divider=True)

observations_by_year = ohio_obs.groupby(['Year'], as_index=False)['HOW_MANY'].sum()
observations_by_year['delta'] = observations_by_year['HOW_MANY'].pct_change() * 100
observations_by_year['delta'] = observations_by_year['delta'].round(0).astype('float')  # Keeps NaN values if needed

count_2021 = observations_by_year.loc[observations_by_year['Year'] == '2021', 'HOW_MANY'].values[0]
change_2021 = observations_by_year.loc[observations_by_year['Year'] == '2021', 'delta'].values[0]
count_2022 = observations_by_year.loc[observations_by_year['Year'] == '2022', 'HOW_MANY'].values[0]
change_2022 = observations_by_year.loc[observations_by_year['Year'] == '2022', 'delta'].values[0]
count_2023 = observations_by_year.loc[observations_by_year['Year'] == '2023', 'HOW_MANY'].values[0]
change_2023 = observations_by_year.loc[observations_by_year['Year'] == '2023', 'delta'].values[0]
count_2024 = observations_by_year.loc[observations_by_year['Year'] == '2024', 'HOW_MANY'].values[0]
change_2024 = observations_by_year.loc[observations_by_year['Year'] == '2024', 'delta'].values[0]
a, b = st.columns(2)
c, d = st.columns(2)

a.metric("2021",count_2021 , change_2021, border=True)
b.metric("2022",count_2022 , change_2022, border=True)

c.metric("2023",count_2023 , change_2023, border=True)
d.metric("2024",count_2024 , change_2024, border=True)





st.header("Sighting Hot Spots", divider=True)
hot_spot_counts = ohio_obs.groupby(['LATITUDE', 'LONGITUDE'], as_index=False)['HOW_MANY'].sum()
st.map(hot_spot_counts, latitude="LATITUDE", longitude="LONGITUDE",size='HOW_MANY')