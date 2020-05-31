'''
Nash Equilibria on (Un-)Stable Networks

2020
Anton Badev
anton.badev@gmail.com

Setups
'''

import os,sys
from pathlib import Path
from datetime import datetime
import time
import pickle
import numpy as np
import pandas as pd


def  setupdirs():
    hostname=os.uname().nodename
    sysname=os.uname().sysname #Linux vs OSX?
    systime0=datetime.now()
    pyfilename=(sys.argv[0][:-3]).split('/')[-1]
    currentdir=os.getcwd()+'/'
    pyfiledir=currentdir.split('/')[-2]
    homedir='/home/anton/'
    if sysname=='Darwin':
        homedir='/Users/anton/'
    scratchdir=homedir+'Scratch/'+currentdir[len(homedir):]
    os.system('mkdir -p '+scratchdir)
    #print(f'({hostname}:{sysname}) start={systime0.strftime("%Y-%m-%d-%H:%M:%S")}\npyfilename={pyfilename}\ncurrentdir={currentdir}\nscratchdir={scratchdir}')
    return  systime0,pyfilename,pyfiledir,homedir,currentdir,scratchdir,hostname,sysname

    
def  state2pickle(filename,GG,AA):
    id1, id2=np.nonzero(GG)
    edges = pd.DataFrame({'id': id1[:], 'nominee': id2})
    nodes = AA
    with open(filename+'.data', 'wb') as filehandle:
        pickle.dump([nodes, edges], filehandle)
       
    print(f'State saved in {filename}')
    return


def  state2csv(filename,GG,AA,attr,flag_attr):
    id1, id2=np.nonzero(GG)
    edges = pd.DataFrame({'id': id1[:], 'nominee': id2})
    edges.to_csv(path_or_buf=filename+'_edges.csv', index = None, header=True)

    if flag_attr:
        attr.sort_values('id', inplace=True, ascending=True)
        attr['smoke']=AA.astype(int)
    else:
        attr = pd.DataFrame({'id': range(len(AA)), 'smoke' : AA.astype(int)})
    attr.to_csv(path_or_buf=filename+'_attr.csv', index = None, header=True)
       
    print(f'State saved in {filename} _edges and _attr csv-s')
    return    
