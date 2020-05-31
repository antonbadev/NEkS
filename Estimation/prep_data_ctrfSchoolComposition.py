'''
Nash Equilibria on (Un-)Stable Networks

2020
Anton Badev
anton.badev@gmail.com

Migrate data from Stata to PY for ctrf school composition
Input files:
    attr-ctrfSchoolComposition.csv
    edges-ctrfSchoolComposition.csv
Output files:
    ctrfSchoolComposition.data
Note (check) the folder structure:
    datadir
    estimationdatadir
'''

import os,sys,csv
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
import scipy.io as sio
import pickle



def main():
    
    datadir='../Data/'
    estimationdatadir='../Data/'
    
    attr_df = pd.read_csv(datadir+'/attr-ctrfSchoolComposition.csv').sort_values(by=['netid', 'id'])
    attr = [jattr for j,jattr in attr_df.groupby('netid')]
    num_nets  = attr_df.netid.nunique()
    size_nets = [jattr.shape[0] for jattr in attr]
    data_a    = [jattr.tobacco.to_numpy().astype(np.float) for jattr in attr]
    
    
    edges_df = pd.read_csv(datadir+'/edges-ctrfSchoolComposition.csv')
    edges_df.columns = edges_df.columns.str.replace(" ","")
    edges_df = edges_df.sort_values(by=['netid', 'id'])
    data_g=[None]*num_nets
    for j,jedges in edges_df.groupby('netid'):
        nn=size_nets[j-1] #netid coincides with net index
        G=np.zeros((nn,nn), dtype=float)
        id1=jedges.id.to_numpy()-1
        id2=jedges.nominee.to_numpy()-1
        G[id1,id2]=1
        data_g[j-1]=G
        
    with open(estimationdatadir+'/ctrfSchoolComposition.data', 'wb') as filehandle:
        pickle.dump([num_nets, size_nets, attr, data_a, data_g], filehandle)    


if __name__ == '__main__':
    main()

