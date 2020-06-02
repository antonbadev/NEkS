'''
Nash Equilibria on (Un-)Stable Networks

2020
Anton Badev
anton.badev@gmail.com

SIMULATE kCD WITH DRAWS FROM THE POSTERIOR TO ASSESS MODEL FIT
Input files:
    estimation_top8_100plus.data
    parameterSetup.csv
    1000draws_posterior.csv
Output files:
    modelFit.data (in scratchdir)
Note NONE
'''

import os,sys,csv,multiprocessing,functools
from pathlib import Path
from datetime import datetime
import time
import numpy as np
import pandas as pd
import pickle
from tqdm import tqdm

from libsetups import state2csv
from libsetups import state2pickle
from libsetups import setupdirs
from libposteriors import posteriorStats
from libtheta import theta2param
from libkCD import gen_kCD
from libkCD import pmf_k

DO_PARALLEL = True
NUM_WORKERS = 8
NCPU = os.cpu_count()

def gen_sample(num_nets, attr, I9, data_a, data_g, size_nets, sampleinfo,
               numsim, vec_numsim_kCD, theta_draws, theta_setup, sample_k, mcJump,
               jscid):
    
    
    flag_largest_scid = size_nets.index(max(size_nets))==jscid
    #for jscid in range(num_nets):
        #print(f'Simulation {js+1} {(datetime.now()).strftime("%Y-%m-%d-%H:%M:%S")}')
        
    jattr = attr[jscid]
    jI9 = I9[jscid]
    jA = data_a[jscid]
    jG = data_g[jscid]
    nn = int(size_nets[jscid])
    jkk = sample_k[jscid]
    numsim_kCD = vec_numsim_kCD[jscid]
    
    sim_a=np.zeros([numsim+1, nn])
    sim_g=np.zeros([numsim+1, nn, nn])
    sim_a[0,:]   = jA
    sim_g[0,:,:] = jG 
    
    np.random.seed(jscid+2026642028)
    for js in range(numsim):
        theta_js=(theta_draws.iloc[js]).to_numpy()
        [vv,ww,h,phi1,phi2,psi,qhat] = theta2param(theta_js,jattr,theta_setup,sampleinfo)
        [jG1,jA1,p_th1_s1,p_th1_s0] = gen_kCD(vv,ww,h,phi1,phi2,psi,qhat,jI9,
                                nn,jkk,mcJump,numsim_kCD,
                                jG,jA)
        #print(f'fine={js:4d} prev={np.mean(jA1):5.4f}/{np.mean(jA):5.4f} density={np.mean(jG1.ravel()):5.4f}/{np.mean(jG.ravel()):5.4f}')

        sim_a[js+1,:]   = np.copy(jA1) #np.copy
        sim_g[js+1,:,:] = np.copy(jG1)
        
        #Multiple setups
        #jG=np.copy(jG1)
        #jA=np.copy(jA1)
        
        if flag_largest_scid and js%10==0: 
            systime_t=datetime.now()
            print(f'Largest scid {jscid:3d} ({size_nets[jscid]:3d}) sim {js:4d}/{numsim:3d} time {systime_t.strftime("%Y-%m-%d-%H:%M:%S")}.')
        
        
    return [sim_a, sim_g, jscid]
        
        
        

def main():
    ## Setup
    [systime0,pyfilename,pyfiledir,homedir,currentdir,scratchdir,hostname,sysname]=setupdirs()
    filename=scratchdir+'/'+pyfilename+'-'+systime0.strftime("%Y-%m-%d-%H:%M:%S")
    filename=scratchdir+'/'+pyfilename

    ## Load data.
    with open(currentdir+'/../Data/estimation_top8_100plus.data', 'rb') as filehandle:
        [num_nets, size_nets, attr, data_a, data_g]=pickle.load(filehandle)
    #data_a=[jnet_data_a.reshape(-1,1) for jnet_data_a in data_a] #reshape as 2D from 1D if needed
    sampleinfo=[num_nets, size_nets]
    sample_k = [pmf_k(jn) for jn in size_nets]
    I9 = [(jattr.grade>8.1).to_numpy(np.float) for jattr in attr]


    ## Posterior & parameter setup.
    theta_setup = pd.read_csv(currentdir+'/../Estimation/priors/parameterSetup.csv')
    theta_draws = pd.read_csv(currentdir+'/../Estimation/estimates/1000draws_posterior.csv')
    numsim = 1000
    varnames=theta_draws.columns.values.tolist()
    numvars=len(varnames)

    print(80*'*')
    print(f'start={systime0.strftime("%Y-%m-%d-%H:%M:%S")}\npyfilename={pyfilename}\ncurrentdir={currentdir}\nscratchdir={scratchdir}')
    print(f'sim file name={filename}')
    print(80*'-')
    print(f'hostname={hostname} (OS={sysname}):')
    print(os.environ.get('PYTHONPATH', '').split(os.pathsep))
    print(sys.path)
    print(80*'*')


    
    ## Size MC for state (inner loop).
    vec_numsim_kCD = np.ones(num_nets,dtype=int)*20000
    mcJump = 0.05 # Probability of large jumps for the MCMC.
    np.random.seed(2026642028)
    #np.random.RandomState(2026642028)
    simdata=[]
    
    if DO_PARALLEL:
        pool = multiprocessing.Pool(processes=NUM_WORKERS)
    
    gen_sample_args = [num_nets, attr, I9, data_a, data_g, size_nets, sampleinfo,
                       numsim, vec_numsim_kCD, theta_draws, theta_setup, sample_k, mcJump]
    gen_sample_wrapper = functools.partial(gen_sample,*gen_sample_args)
    if not DO_PARALLEL:
        simdata = [gen_sample_wrapper(jjscid)
                   for jjscid in range(num_nets)]
                  #for jjscid in tqdm(range(num_net),'scid')]
    else:
        simdata = pool.map(gen_sample_wrapper,range(num_nets))
        

    with open(filename+'.data', 'wb') as filehandle:
        pickle.dump(simdata, filehandle)
    print(f'Saved simdata in {filename}.data')
    print(f'end={datetime.now().strftime("%Y-%m-%d-%H:%M:%S")}')

if __name__ == '__main__':
    main()
