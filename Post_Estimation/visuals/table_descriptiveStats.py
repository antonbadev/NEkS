'''
Nash Equilibria on (Un-)Stable Networks

2020
Anton Badev
anton.badev@gmail.com

DESCRIPTIVE STATS ESTIMATION SAMPLE
Input files:
    estimation_top8_100plus.data
    attr2.csv
Output files:
    table_sampleStats.tex
Note output in texdir
'''

# Create table with descriptive stats for the estimation sample

import os,sys,csv,multiprocessing,functools
import time
import numpy as np
import pandas as pd
import scipy.io as sio
import pickle
from tqdm import tqdm

from libsetups import state2pickle
from libsetups import setupdirs
from libposteriors import posteriorStats
from libnets import netStats
from libnets import stateStats2
from libnets import homophily
from libnets import mixingMat



def weighted_average_bygroup(dfin,data_col,weight_col,by_col):
    df=dfin.copy()
    df['_data_times_weight'] = df[data_col]*df[weight_col]#/float((df[weight_col].sum())
    df['_weight_where_notnull'] = df[weight_col]*pd.notnull(df[data_col])
    g = df.groupby(by_col)
    result = g['_data_times_weight'].sum() / g['_weight_where_notnull'].sum()
    del df['_data_times_weight'], df['_weight_where_notnull']
    return result

def weighted_average(df,data_col,weight_col):
    result = np.average(df[data_col].to_numpy(float),axis=None,weights=df[weight_col].to_numpy(float))
    return result


def main():

    [systime0,pyfilename,pyfiledir,homedir,currentdir,scratchdir,hostname,sysname] = setupdirs()    
    ## Load data.
    with open(currentdir+'/../../Data/estimation_top8_100plus.data', 'rb') as filehandle:
        [num_nets, size_nets, attr, data_a, data_g]=pickle.load(filehandle)
        
    attr2=pd.read_csv(currentdir+'/../../Data/attr2.csv') #extended attr
    # 100 plus
    estimation_sample = [7,8,9,12,13,14,15,16]
    attr2 = attr2[attr2['netid'].isin(estimation_sample)]

    texdir   = currentdir + '/../../TeX/'
    texfile = 'table_sampleStats.tex'

    netid=np.zeros(num_nets)
    prev=np.zeros(num_nets)
    density=np.zeros(num_nets)
    avgDeg=np.zeros(num_nets)
    minDeg=np.zeros(num_nets)
    maxDeg=np.zeros(num_nets)
    AGA=np.zeros(num_nets)
    IAGIA=np.zeros(num_nets)
    tri=np.zeros(num_nets)
    twolinksonly=np.zeros(num_nets)
    twolinksonly2=np.zeros(num_nets)
    HI=np.zeros(num_nets)
    CHI=np.zeros(num_nets)
    FSI=np.zeros(num_nets)
    nn=np.zeros(num_nets)
    ns=np.zeros(num_nets)
    sn=np.zeros(num_nets)
    ss=np.zeros(num_nets)
    for jnet,jattr in enumerate(attr):
        n=size_nets[jnet]
        netid[jnet]=jnet+1
        A=data_a[jnet]
        G=data_g[jnet]
        [prev[jnet],
         density[jnet],
         avgDeg[jnet],
         minDeg[jnet],
         maxDeg[jnet],
         AGA[jnet],
         IAGIA[jnet],
         tri[jnet],
         twolinksonly[jnet],
         twolinksonly2[jnet],
         stateStatsLabels]=stateStats2(G,A,n)
        [HI[jnet],CHI[jnet],FSI[jnet]]=homophily(G,A,n,True)
        [nn[jnet],ns[jnet],sn[jnet],ss[jnet]] = list((mixingMat(G,A.astype(int),n,2).ravel('C')).astype(float))

    data_stats=pd.DataFrame(data=np.column_stack([netid,prev,density,avgDeg,minDeg,maxDeg,AGA,IAGIA,np.multiply(tri,size_nets),twolinksonly,twolinksonly2,HI,CHI,FSI,nn,ns,sn,ss]),
                    dtype=float,
                    columns=['netid','prev','density','avgDeg','minDeg','maxDeg','AGA','IAGIA','tri','twolinks','twolinks2','HI','CHI','FSI','nn','ns','sn','ss'])
    allattr=attr2 #pd.concat(attr)
    
    allattr['male']=(allattr['sex']==1).to_numpy(dtype=float)
    allattr['white']=(allattr['race']==1).to_numpy(dtype=float)
    allattr['as-hi-ot']=(allattr['race']==3).to_numpy(dtype=float)
    
    summary_attr=allattr.groupby('netid').agg(['count','mean'])
    
    var=summary_attr.loc[:,[(      'id', 'count')]].to_numpy()
    texline=f'Students    & {np.sum(var):12.0f} &  {np.min(var):12.0f} & {np.max(var):12.0f} \\\ \n'
    varlabels=['Smoking','Male','Whites','Blacks','As-Hi-Ot','Price','Avg income','Mom edu','HH smokes','Avg friends']
    for j,jvar in enumerate(['tobacco','male','white','black','as-hi-ot','price_level','income_level','mom_ed','hhsmokes','deg']):
        jscidvar=summary_attr.loc[:,[(      jvar, 'mean')]].to_numpy()
        texline+=f'{varlabels[j]:12}  & {np.mean(allattr[jvar]):12.2f} &  {np.min(jscidvar):12.2f} & {np.max(jscidvar):12.2f} \\\ \n'
    
    texsignature=f'% tex created by {pyfilename}.py \n'
    texheader = r'''
\begin{table}[t]
\label{table:descriptive_stats}
\begin{center}
\caption{Descriptive Statistics for the estimation sample}
\begin{tabular}{lccc}
\hline \hline
              & Overall & Min      & Max   \\ \hline
'''
    texfooter = r'''
\hline
\end{tabular}
\label{table:descriptive_stats}
\end{center}
\fignotetitle{Note:} \fignotetext{The final sample contains students from 8 high schools. Min and max are reported at a school level.}
\end{table}
'''
    
    texcontent = texsignature + texheader + texline + texfooter
    with open(texdir+texfile,'w') as f:
        f.write(texcontent)


if __name__ == '__main__':
    main()

