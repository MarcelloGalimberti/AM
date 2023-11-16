#!/usr/bin/env python
# coding: utf-8



import pandas as pd
import streamlit as st
import plotly.express as px
import numpy as np



st.set_page_config(layout="wide")

url_immagine = 'https://github.com/MarcelloGalimberti/Sentiment/blob/main/Ducati_red_logo.png?raw=true'

col_1, col_2 = st.columns([1, 6])

with col_1:
    st.image(url_immagine, width=150)

with col_2:
    st.title('Analisi fabbisogno e WIP Albero Motore')

######## CARICAMENTO DATI


st.header('Caricamento dati | Fabbisogno', divider='red')

uploaded_MD_04 = st.file_uploader("Carica MD 04 (EXPORT_MD04.XLSX)")
if not uploaded_MD_04:
    st.stop()
df_MD04=pd.read_excel(uploaded_MD_04, parse_dates=True)


url_codici_AM = 'https://github.com/MarcelloGalimberti/AM/blob/main/Codici%20AM.xlsx?raw=True'
df_codici_AM=pd.read_excel(url_codici_AM)

# st.write('MD 04',df_MD04 ) # poi togliere


####### PROCESSA DATI - MD 04
df_MD04 = df_MD04[['Materiale','Date pianif.','Fabb.']]
lista_finiti = list(df_codici_AM['Assieme con bielle'])
df_MD04_finiti = df_MD04[df_MD04['Materiale'].isin(lista_finiti)]
df_MD04_finiti['Fabb.']=df_MD04_finiti['Fabb.'].apply(lambda x: x*(-1))
df_MD04_finiti = df_MD04_finiti[df_MD04_finiti['Fabb.']>0]
df_MD04_finiti['Data'] = df_MD04_finiti['Date pianif.'].dt.to_period('M')

pvt_2 = pd.pivot_table(df_MD04_finiti,
                      index='Data',
                      columns='Materiale',
                      values='Fabb.',
                      aggfunc='sum').fillna(0)

materiali = list(pvt_2.columns)

###### GRAFICO E TABELLA
fig = px.bar(pvt_2, pvt_2.index.strftime("%Y-%m") , materiali,template='plotly_dark', title='Fabbisogno finiti')
st.plotly_chart(fig, use_container_width=True)


#fig.show()

st.write ('Tabella fabbisogni', pvt_2)

###### WIP
st.header('Caricamento dati | WIP', divider='red')

##### CARICAMENTO DATI
op = st.file_uploader("Carica COOIS Operazioni (EXPORT_COOIS_ODP_OPERAZIONI.XLSX)")
if not op:
    st.stop()
df_op=pd.read_excel(op, parse_dates=True)#,dtype={'Ordine': int}) #np.int32

tes = st.file_uploader("Carica COOIS Testata (EXPORT_COOIS_ODP_TESTATA.XLSX)")
if not tes:
    st.stop()
df_tes=pd.read_excel(tes, parse_dates=True)#,dtype={'Ordine': int})

#st.write(df_tes)

url_modello_albero = 'https://github.com/MarcelloGalimberti/AM/blob/main/Modello_Albero.xlsx?raw=True'

df_mod = pd.read_excel(url_modello_albero)

url_modello_isole = 'https://github.com/MarcelloGalimberti/AM/blob/main/Codifica%20isole.xlsx?raw=True'

df_isole = pd.read_excel(url_modello_isole)


##### PROCESSA DATI
lista_alberi = list(df_mod['AM'])

df_op = df_op[['Ordine','Operazione','Centro di lavoro','Oper. testo breve','Dt.eff.inizio esec.','Stato sistema','Qtà ott. conf. (MEINH)']]


df_tes = df_tes[['Ordine','Cd. materiale']] # testata ordine


df_0 = df_op.merge(df_tes, how = 'left', left_on='Ordine',right_on='Ordine') # prende il materiale
df_1 = df_0[df_0['Cd. materiale'].isin(lista_alberi)] # filtra per codici albero rilevanti (esclusi ricambi, obsoleti e phase out)

lista_stati = ['CONF COTA RIL. STMP','CONF COTA RIL.','RIL. STMP','RIL.','CONP COTA RIL. STMP', 'CONP COTA RIL.',
              'CONF RIL.']


df_2 = df_1[df_1['Stato sistema'].isin(lista_stati)]
df_3 = df_2.merge(df_mod, how = 'left', left_on='Cd. materiale',right_on='AM')
df_4 = df_3.merge(df_isole, how = 'left', left_on=['Centro di lavoro','Oper. testo breve'], right_on=['CdL','Oper. testo breve'])
df_4.drop(columns=['Stato sistema','AM','CdL','Chiave'], inplace=True)
df_4.rename(columns={'Cd. materiale':'Materiale','Versione semplificata':'Isola','Qtà ott. conf. (MEINH)':'Qty_confermata'}, inplace=True)
df_4 = df_4[(df_4['Centro di lavoro']!='COSTO') & (df_4['Centro di lavoro']!='50000')]


df_raw = df_4.copy()

df_raw=df_raw[df_raw['Dt.eff.inizio esec.'].notnull()]

df_max = df_raw.groupby(['Ordine']).max()
df_max.reset_index(inplace=True)
df_max = df_max[['Ordine','Dt.eff.inizio esec.','Operazione']]

df_wip = df_max.merge(df_raw, left_on=['Ordine', 'Dt.eff.inizio esec.','Operazione'],right_on=['Ordine', 'Dt.eff.inizio esec.','Operazione'])

pvt_wip = pd.pivot_table(df_wip, index='Isola', columns='Materiale', values = 'Qty_confermata',aggfunc='sum',
                       ).fillna(0)

pvt_wip_table = pd.pivot_table(df_wip, index=['Isola','Ordine'], columns='Materiale', values = 'Qty_confermata',aggfunc='sum',
                       margins = True, margins_name='Totale').fillna(0)


articolo = list(pvt_wip.columns)

##### GRAFICI

st.write('WIP totale = ', df_wip.Qty_confermata.sum())

fig_wip = px.bar(pvt_wip , articolo ,template='plotly_dark', height = 800, title='WIP Alberi motore')
st.plotly_chart(fig_wip, use_container_width=True)



#fig_wip.show()

#st.write(pvt_wip_table)



