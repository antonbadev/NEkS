'''
Nash Equilibria on (Un-)Stable Networks

2020
Anton Badev
anton.badev@gmail.com

Migrate data from Stata to PY for estimation
Sample constists of schools with 100+ students
Input files:
    attr.csv
    edges.csv
Output files:
    estimation_top8_100plus.data
Note (check) the folder structure:
    datadir
    estimationdatadir
'''

import numpy as np
import pandas as pd
import pickle


def main():
    
    ## 100 PLUS STUDENTS ------------------------------------------------
    datadir='../Data/'
    estimation_sample = [7,8,9,12,13,14,15,16]
    
    # ATTRIBUTES
    df_attr = pd.read_csv(datadir+'/attr.csv').sort_values(by=['netid', 'id'])
    df_attr= df_attr[df_attr.netid.isin(estimation_sample)] # subsample
    # reindex
    for j,jnetid in enumerate(estimation_sample):
        df_attr.loc[df_attr.netid==jnetid,'netid']=j+1
    # list of panda df for each net
    attr = [jnet_attr[1] for jnet_attr in df_attr.groupby('netid')]
    for j in range(len(attr)):
        attr[j].index=attr[j].id-1
    # list of numpy 2d arrays [n,1] ready for matrix algebra
    data_a = [jnet_attr.tobacco.to_numpy().astype(np.float) for jnet_attr in attr]
    size_nets = [jnet_attr.shape[0] for jnet_attr in attr]
    num_nets  = df_attr.netid.nunique()

    # EDGES
    df_edges = pd.read_csv(datadir+'/edges.csv')
    df_edges.columns=df_edges.columns.str.replace(" ","")
    df_edges = df_edges.sort_values(by=['netid', 'id'])
    df_edges = df_edges[df_edges.netid.isin(estimation_sample)] #subsample
    # reindex
    for j,jnetid in enumerate(estimation_sample):
        df_edges.loc[df_edges.netid==jnetid,'netid']=j+1
    
    data_g=[None]*num_nets
    for jnet,jnet_edges in df_edges.groupby('netid'):
        nn=size_nets[jnet-1] #netid coincides with net index
        G=np.zeros((nn,nn), dtype=float)
        id1=jnet_edges.id.to_numpy()-1
        id2=jnet_edges.nominee.to_numpy()-1
        G[id1,id2]=1
        data_g[jnet-1]=G

    with open(datadir+'/estimation_top8_100plus.data', 'wb') as filehandle:
        pickle.dump([num_nets, size_nets, attr, data_a, data_g], filehandle)    


    ## SYNTHETIC DATA
    # TOP 8 100 PLUS STUDENTS ------------------------------------------------
    datadir='../Data/'
    with open(datadir+'/estimation_top8_100plus.data', 'rb') as filehandle:
        [num_nets, size_nets, attr, data_a, data_g]=pickle.load(filehandle)
        
    varlist=['sex', 'grade', 'race', 'black', 'income', 'price','hhsmokes', 'mom_ed', 'tobacco']
    for jnet, jattr in enumerate(attr):
        print(f'netid = {jnet:2d}, size = {size_nets[jnet]:3d}')
        for j,jvar in enumerate(varlist):
            np.random.shuffle(jattr[jvar].to_numpy())
        jattr['black']=(jattr['race']==1).to_numpy(dtype=int)
        data_a[jnet]=jattr['tobacco'].to_numpy(dtype=float)
            
    with open(datadir+'/synthetic_data.data', 'wb') as filehandle:
        pickle.dump([num_nets, size_nets, attr, data_a, data_g], filehandle)    
        


if __name__ == '__main__':
    main()

