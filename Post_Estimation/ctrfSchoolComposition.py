'''
Nash Equilibria on (Un-)Stable Networks

2020
Anton Badev
anton.badev@gmail.com

COUNTERFACTUAL EXPERIMENT CHANGE SCHOOL RACIAL COMPOSITION
Input files:
    Data/ctrfSchoolComposition.data
    parameterSetup.csv
    1000draws_posterior.csv
Output files:
    {scratchdir}/ctrfSchoolComposition.data
Note Data/ctrfSchoolComposition.data is preped by 
    i. DataPrep/inhm-04-Python-ctrf-schoolComposition.do (STATA)
    ii. Estimation/prep_data_ctrfSchoolComposition.py
'''


import os,sys,csv,multiprocessing,functools
from pathlib import Path
from datetime import datetime
import time
import numpy as np
import pandas as pd
import scipy.io as sio
import pickle
from tqdm import tqdm

from libsetups import state2pickle
from libsetups import setupdirs
from libccp import ccp2intercept
from libccp import dccp2coeff
from libccp import dlogccp2coeff
from libtheta import theta2param
from libpotential import deltaPotentialCwrap
from libpotential import potentialCwrap
from libposteriors import posteriorStats
from libnets import stateStats
from libnets import homophily
from libkCD import gen_kCD
#from libkCD import gen_kCD_fixG
from libkCD import pmf_k

DO_PARALLEL = True
NUM_WORKERS = 12


def sim_state(num_nets, 
                attr,
                I9,
                data_a, 
                data_g, 
                size_nets, 
                vec_numsim_kCD, 
                thetastar_draws, 
                theta_setup,
                sampleinfo, 
                sample_k,
                mcJump,
                numsim,
                filename,
                jscid):
    
    simdata=[]
    jattr = (attr[jscid]).copy() #fresh copy for each scenario
    jI9 = I9[jscid]
    
    nn  = int(size_nets[jscid])
    jkk = sample_k[jscid]
    nmc_state = vec_numsim_kCD[jscid]
    
    sim_a=np.zeros([numsim+1, nn])
    sim_g=np.zeros([numsim+1, nn, nn])
    sim_a[0,:]   = np.copy(data_a[jscid])
    sim_g[0,:,:] = np.copy(data_g[jscid]) 
    
    # (1) Model
    jA = np.copy(data_a[jscid])
    jG = np.copy(data_g[jscid])
    for js in range(numsim):
        thetastar=(thetastar_draws.iloc[js]).to_numpy()
        [vv,ww,h,phi1,phi2,psi,qhat] = theta2param(thetastar,jattr,theta_setup,sampleinfo)
        np.random.seed(js*num_nets+jscid+2026642028)
        [jG1,jA1,p_th1_s1,p_th1_s0] = gen_kCD(vv,ww,h,phi1,phi2,psi,qhat,jI9,
                                              nn,jkk,mcJump,nmc_state,
                                              jG,jA)
                   
        sim_a[js+1,:]   = jA1
        sim_g[js+1,:,:] = jG1
        
        #Multiple setups: v0 with reset & v1 without
        #jG=np.copy(jG1)
        #jA=np.copy(jA1)
    simdata.append([np.copy(sim_a), np.copy(sim_g), jscid])


    columnnames  = ['scid','sim','netsize','race',
                    'prev', 'density', 'avgDeg', 'minDeg', 'maxDeg', 'AGA', 'IAGIA', 'tri',
                    'HI','CHI','FSI']
    stats_ctrfSchool = pd.DataFrame(data=np.zeros([(numsim+1),15],dtype=float),columns=columnnames)
    for s in range(numsim+1):
        A=sim_a[s] #subdimensional array
        G=sim_g[s] #subdimensional array
        n=len(A)
               
        race=np.mean(jattr.race.to_numpy(float),dtype=float)
        stats_ctrfSchool.iloc[s,0:4] = np.array([jscid,s,n,race])
        stats_ctrfSchool.iloc[s,4:15]= np.array(stateStats(G,A,n)[:-1] + homophily(G,A,n,True))
        
    return stats_ctrfSchool

def main():
    ## Setup
    [systime0,pyfilename,pyfiledir,homedir,currentdir,scratchdir,hostname,sysname]=setupdirs()
    filename=scratchdir+'/'+pyfilename+'-'+systime0.strftime("%Y-%m-%d-%H:%M:%S")
    filename=scratchdir+'/'+pyfilename
    print(80*'*')
    print(f'hostname={hostname} (OS={sysname})')
    print(f'start={systime0.strftime("%Y-%m-%d-%H:%M:%S")}\npyfilename={pyfilename}\ncurrentdir={currentdir}\nscratchdir={scratchdir}')
    print(f'filename ={filename}')
    print(80*'*')
     
    ## Load data.
    with open(currentdir+'/../Data/ctrfSchoolComposition.data', 'rb') as filehandle:
        [num_nets, size_nets, attr, data_a, data_g]=pickle.load(filehandle)
    sampleinfo=[num_nets, size_nets]
    sample_k = [pmf_k(jn) for jn in size_nets]
    I9 = [(jattr.grade>8.1).to_numpy(np.float) for jattr in attr]
    
    ## Parameter setup.
    theta_setup     = pd.read_csv(currentdir+'/../Estimation/priors/parameterSetup.csv')
    estimatesfile   ='/../Estimation/estimates/1000draws_posterior.csv'
    thetastar_draws = pd.read_csv(currentdir+estimatesfile)

    ## Size MC for state (inner loop).
    vec_numsim_kCD = np.ones(num_nets,dtype=int)*20000

    numsim = 1000
    mcJump = 0.05 # Probability of large jumps for the MCMC.

    np.random.seed(2026642028)
    
    sim_state_args = [num_nets, attr, I9, data_a, data_g, size_nets, vec_numsim_kCD,
                    thetastar_draws, theta_setup, sampleinfo, sample_k, mcJump, numsim, filename]
    sim_state_wrapper = functools.partial(sim_state,*sim_state_args)
    if DO_PARALLEL:
        pool = multiprocessing.Pool(processes=NUM_WORKERS)
    if not DO_PARALLEL:
        ctrfData = [sim_state_wrapper(jjscid)
                   for jjscid in range(num_nets)]
                  #for jjscid in tqdm(range(num_net),'scid')]
    else:
        ctrfData = pool.map(sim_state_wrapper,range(num_nets))
    

    #ctrfPriceSim
    #   [scid]
    #       [simdata,simdataFixedNet,simdataPEoff,simdataNoPE]
    #           [sim_a, sim_g, jprice, jscid]

    ctrfData=pd.concat(ctrfData,ignore_index=True) #all scids in one df
    with open(filename+'.data', 'wb') as filehandle:
        pickle.dump([ctrfData,numsim,num_nets, size_nets, attr, data_a, data_g], filehandle)
    print(f'{pyfilename} saved {filename}')

if __name__ == '__main__':
    main()
