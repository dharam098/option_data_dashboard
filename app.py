import requests
from requests.adapters import HTTPAdapter, Retry
import json
import pandas as pd
from pandas import json_normalize
import time
from time import localtime, strftime
from datetime import datetime
import streamlit as st
import numpy as np
import plotly.express as px



symbol_list = ['NIFTY', 'BANKNIFTY', 'FINNIFTY']


d={}
for symbol in symbol_list:
    d[f"time_{symbol}"] = [0]
    d[f"max_pain_{symbol}"] = [0]
    d[f"pcr_{symbol}"] = [0]
live_data = pd.DataFrame(d)



session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
session.mount('http://', HTTPAdapter(max_retries=retries))


def get_option_chain_dic(symbol):
    urlheader = {
    "authority": "www.nseindia.com",
    "scheme":"https"
    }

    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    data = session.get(url)#, headers=urlheader)
    # data2 = data.decode('utf-8')
    oc={}
    if (data):
        oc = json.loads(data.text)
   

    return oc




def get_max_pain(cee, pee):
    # merge ce and pe data
    cp = cee.iloc[:, [0,4]].merge(pee.iloc[:, [0,4]], on ='strikePrice', how = 'outer').sort_values(by='strikePrice').reset_index(drop=True)
    cp.columns = ['SP', 'OI_CE', 'OI_PE']
    
    cp['loss'] = 0

    #calculate loss and get max pain
    for i in cp.index:
        ce_loss = ((cp.iloc[i, 0] -cp.iloc[:i, 0])*cp.iloc[:i, 1]).sum()
        pe_loss = ((cp.iloc[i+1:, 0]-cp.iloc[i,0])*cp.iloc[i+1:,2]).sum()
        cp.iloc[i, 3]= ce_loss+pe_loss
    max_pain = cp.iloc[cp['loss'].idxmin(), 0]
    return cp, max_pain



def last_max_pain_value(symbol, exp_index=0):
    global live_data
    try:
        #get dict
        oc=get_option_chain_dic(symbol)
        current_time = strftime("%d-%b-%Y %H:%M:%S", localtime())
        record_time = datetime.strptime(oc['records']['timestamp'].split(' ')[-1], '%H:%M:%S').time()
        #read dict

        exp_dates = oc['records']['expiryDates']
        exp = exp_dates[exp_index]
        df = pd.DataFrame(oc['records']['data'])
        ce = pd.DataFrame(df['CE'].dropna().to_list())
        pe = pd.DataFrame(df['PE'].dropna().to_list())
        cee = ce[ce['expiryDate']==exp].reset_index(drop=True)
        pee = pe[pe['expiryDate']==exp].reset_index(drop=True)
        #calculations
        pcr = (pee.iloc[:,4].sum()/cee.iloc[:,4].sum()).round(4)
        cp, max_pain = get_max_pain(cee,pee)
    except:
        return [live_data[f"time_{symbol}"].iloc[-1],live_data[f"max_pain_{symbol}"].iloc[-1], live_data[f"pcr_{symbol}"].iloc[-1]]

    return [record_time , max_pain, pcr]




st.set_page_config(
    page_title = 'Real-Time Data Science Dashboard',
    page_icon = '✅',
    layout = 'wide'
)

st.title("MAX PAIN AND PCR")

placeholder = st.empty()


while True: 
    
    l=[]
    for symbol in symbol_list:
        l = l+ last_max_pain_value(symbol) 
    live_data.loc[len(live_data)] = l
    
    with placeholder.container():
        # create three columns
        kpi1, kpi2, kpi3 = st.columns(3)

        # fill in those three columns with respective metrics or KPIs 
        kpi1.metric(label="NIFTY", value=live_data['max_pain_NIFTY'].iloc[-1], delta = str(live_data['pcr_NIFTY'].iloc[-1]))
        kpi2.metric(label="BANKNIFTY", value=live_data['max_pain_BANKNIFTY'].iloc[-1], delta = str(live_data['pcr_BANKNIFTY'].iloc[-1]))
        kpi3.metric(label="FINNIFTY", value=live_data['max_pain_FINNIFTY'].iloc[-1],delta =  str(live_data['pcr_FINNIFTY'].iloc[-1]))

        # create two columns for charts 
        fig_col1, fig_col2 = st.columns(2)
        # fig_col1, fig_col2, fig_col3 = st.columns(3)
        with fig_col1:
            st.markdown("### NIFTY")
            fig = px.line(live_data.iloc[1:], y = 'max_pain_NIFTY', x = 'time_NIFTY',  markers=True)#'time_NIFTY')
            st.write(fig)
        with fig_col2:
            st.markdown("### BANKNIFTY")
            fig2 = px.line(live_data.iloc[1:], y = 'max_pain_BANKNIFTY', x = 'time_BANKNIFTY',  markers=True)#'time_BANKNIFTY')
            st.write(fig2)

        fig_col3, fig_col4 = st.columns(2)
        
        with fig_col3:
            st.markdown("### FINNIFTY")
            fig3 = px.line(live_data.iloc[1:], y = 'max_pain_FINNIFTY', x = 'time_FINNIFTY',  markers=True)#'time_FINNIFTY')
            st.write(fig3)
        with fig_col4:    
            st.markdown("### HISTORY")
            st.dataframe(live_data.iloc[1:].tail(10).reset_index(drop=True))
            time.sleep(20)
    #placeholder.empty()
