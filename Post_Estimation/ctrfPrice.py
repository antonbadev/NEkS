'''
Nash Equilibria on (Un-)Stable Networks

2020
Anton Badev
anton.badev@gmail.com

COUNTERFACTUAL EXPERIMENT CHANGE TOBACCO PRICE (AS A RESULT OF EXCISE TAX)
Input files:
    estimation_top8_100plus.data
    parameterSetup.csv
    1000draws_posterior.csv
    parameterSetupFixedNet.csv
    1000draws_posteriorFixedNet.csv
    parameterSetupNoNetData.csv
    1000draws_posteriorNoNetData.csv
Output files:
    ctrfPrice.data (in scratchdir)
Note different estimation scenarios
    i. model    
    ii. fixed (exogenous) networks
    iii. model without netowork data, i.e. no local PE
'''


import os,sys,csv
import multiprocessing,functools
from datetime import datetime
import time
import numpy as np
import pandas as pd
import pickle

from libsetups import setupdirs
from libtheta import theta2param
from libnets import stateStats
from libnets import homophily
from libkCD import gen_kCD
from libkCD import gen_kCD_fixG
from libkCD import pmf_k


DO_PARALLEL = True
NUM_WORKERS = 36

def Jcpu2JscidJctrf(jcpu,nscid,nctrf):
    jscid=int(float(jcpu)/float(nctrf))
    jctrf=int(jcpu - jscid*nctrf)
    return jscid,jctrf

def JscidJctrf2Jcpu(jscid,jctrf,nscid,nctrf):
    return jscid*nctrf+jctrf



def sim_ctrfPrice_jscid_jctrf(
        num_nets, 
        attr, 
        I9,
        data_a, 
        data_g, 
        size_nets, 
        vec_numsim_kCD, 
        thetastars,
        theta_setups,
        sampleinfo,
        sample_k,
        gridDeltaPrice,
        mcJump,
        numsim,
        filename,
        cpuinfo,
        jcpu):
    
    [ncpu,nscid,nctrf]=cpuinfo
    [jscid,jctrf]=Jcpu2JscidJctrf(jcpu,nscid,nctrf)
    
    [theta_setupModel, theta_setupRestrictNet, theta_setupFixedNet, theta_setupNoNetData] = theta_setups
    [thetastarModel_draws, thetastarRestrictNet_draws, thetastarFixedNet_draws, thetastarNoNetData_draws] = thetastars

    
    #for jprice,dPrice in enumerate(gridDeltaPrice):
    jprice = jctrf
    #dPrice = gridDeltaPrice[jprice]
    
    print(jcpu, jscid, jctrf)
    #if size_nets[jscid]==max(size_nets):
    #    print(f'Largest school (scid={jscid:2d}, size={size_nets[jscid]:3d}) delta price = {dPrice:3.0f},  {(datetime.now()).strftime("%Y-%m-%d-%H:%M:%S")}')
    
    
    jattr = (attr[jscid]).copy() #fresh copy for each scenario
    jattr.price = jattr.price + gridDeltaPrice[jprice]
    jI9 = I9[jscid]
    nn = int(size_nets[jscid])
    jkk = sample_k[jscid]
    nmc_state = vec_numsim_kCD[jscid]
    
    sim_a=np.zeros([numsim+1, nn])
    sim_g=np.zeros([numsim+1, nn, nn])
    sim_a[0,:]   = np.copy(data_a[jscid])
    sim_g[0,:,:] = np.copy(data_g[jscid]) 
    
    # (1) Model
    #[vv,ww,h,phi,qhat,I9grade] = theta2param(thetastar,jattr,theta_setup,sampleinfo)
    
    jA = np.copy(data_a[jscid])
    jG = np.copy(data_g[jscid])
    for js in range(numsim):
        thetastar              = (thetastarModel_draws.iloc[js]).to_numpy()
        [vv,ww,h,phi1,phi2,psi,qhat] = theta2param(thetastar,jattr,theta_setupModel,sampleinfo)
        np.random.seed(js*num_nets+jscid+2026642028)
        [jG1,jA1,p_th1_s1,p_th1_s0] = gen_kCD(vv,ww,h,phi1,phi2,psi,qhat,jI9,
                            nn,jkk,mcJump,nmc_state,
                            jG,jA)
        sim_a[js+1,:]   = jA1
        sim_g[js+1,:,:] = jG1
        
    simdata=[np.copy(sim_a), np.copy(sim_g), jprice, jscid]
    
    # (2a) Restrict network adjustmens: True estimates but Fixed net
    #[vv,ww,h,phi,qhat,I9grade] = theta2param(thetastarFixedNet,jattr,theta_setupFixedNet,sampleinfo)
    jA = np.copy(data_a[jscid])
    jG = np.copy(data_g[jscid])
    for js in range(numsim):
        thetastar              = (thetastarRestrictNet_draws.iloc[js]).to_numpy()
        [vv,ww,h,phi1,phi2,psi,qhat] = theta2param(thetastar,jattr,theta_setupRestrictNet,sampleinfo)
        np.random.seed(js*num_nets+jscid+2026642028)
        
        [jG1,jA1,p_th1_s1,p_th1_s0] = gen_kCD_fixG(vv,ww,h,phi1,phi2,psi,qhat,jI9,
                                              nn,jkk,mcJump,nmc_state,
                                              jG,jA)
        sim_a[js+1,:]   = jA1
        sim_g[js+1,:,:] = jG1
    
    #Multiple setups: v0 with reset & v1 without
    #jG=np.copy(jG1)
    #jA=np.copy(jA1)
    simdataRestrictNet=[np.copy(sim_a), np.copy(sim_g), jprice, jscid]
    
    
    # (2) Exogenous (fixed) network 
    jA = np.copy(data_a[jscid])
    jG = np.copy(data_g[jscid])
    for js in range(numsim):
        thetastarFixedNet=(thetastarFixedNet_draws.iloc[js]).to_numpy()
        [vv,ww,h,phi1,phi2,psi,qhat] = theta2param(thetastarFixedNet,jattr,theta_setupFixedNet,sampleinfo)
        np.random.seed(js*num_nets+jscid+2026642028)
        
        [jG1,jA1,p_th1_s1,p_th1_s0] = gen_kCD_fixG(vv,ww,h,phi1,phi2,psi,qhat,jI9,
                                              nn,jkk,mcJump,nmc_state,
                                              jG,jA)
        sim_a[js+1,:]   = jA1
        sim_g[js+1,:,:] = jG1
        
    simdataFixedNet=[np.copy(sim_a), np.copy(sim_g), jprice, jscid]
    
    # (3) Model with No Net Data (no local PE)
    #[vv,ww,h,phi,qhat,I9grade] = theta2param(thetastarNoPE,jattr,theta_setupNoPE,sampleinfo)
    
    jA = np.copy(data_a[jscid])
    jG = np.copy(data_g[jscid])
    for js in range(numsim):
        thetastarNoNetData=(thetastarNoNetData_draws.iloc[js]).to_numpy()
        [vv,ww,h,phi1,phi2,psi,qhat] = theta2param(thetastarNoNetData,jattr,theta_setupNoNetData,sampleinfo)
        np.random.seed(js*num_nets+jscid+2026642028)
        [jG1,jA1,p_th1_s1,p_th1_s0] = gen_kCD_fixG(vv,ww,h,phi1,phi2,psi,qhat,jI9,
                                              nn,jkk,mcJump,nmc_state,
                                              jG,jA)
        sim_a[js+1,:]   = jA1
        sim_g[js+1,:,:] = jG1
        
    simdataNoNetData=[np.copy(sim_a), np.copy(sim_g), jprice, jscid]
        
    

    # COMPUTE STATS
    columnnames = ['scid','dprice','sim','netsize']
    for jstats in ['prev', 'density', 'avgDeg', 'minDeg', 'maxDeg', 'AGA', 'IAGIA', 'tri','HI','CHI','FSI']:
        for jctrfLabel in ['Model','RestrictNet','FixedNet','noNetData']:
            columnnames.append(jstats+'-'+jctrfLabel)
    stats_ctrfPrice = pd.DataFrame(data=np.zeros([(numsim+1),48],dtype=float),columns=columnnames)

    for jscenario,ctrfdata in enumerate([simdata,simdataRestrictNet,simdataFixedNet,simdataNoNetData]):
        [sim_a, sim_g, jprice, jscid]=ctrfdata
        for s in range(numsim+1):
            A=sim_a[s] #subdimensional array
            G=sim_g[s] #subdimensional array
            n=len(A)
            stats_ctrfPrice.iloc[s,0:4]=np.array([jscid,jprice,s,n])
            jstats   = np.array(stateStats(G,A,n)[:-1] + homophily(G,A,n,True))
            jcolumns = [j for j in range(jscenario+4,jscenario+44+1,4)]
            stats_ctrfPrice.iloc[s,jcolumns]=jstats
    
    return stats_ctrfPrice #end sim_ctrfPrice_jscid_jctrf


def main():
    ## Setup
    [systime0,pyfilename,pyfiledir,homedir,currentdir,scratchdir,hostname,sysname]=setupdirs()
    filename=scratchdir+'/'+pyfilename
    print(80*'*')
    print(f'hostname={hostname} (OS={sysname})')
    print(f'start={systime0.strftime("%Y-%m-%d-%H:%M:%S")}\npyfilename={pyfilename}\ncurrentdir={currentdir}\nscratchdir={scratchdir}')
    print(f'filename ={filename}')
    print(80*'*')
    
    ## Load data.
    with open(currentdir+'/../Data/estimation_top8_100plus.data', 'rb') as filehandle:
        [num_nets, size_nets, attr, data_a, data_g]=pickle.load(filehandle)
    sampleinfo=[num_nets, size_nets]
    sample_k = [pmf_k(jn) for jn in size_nets]
    I9 = [(jattr.grade>8.1).to_numpy(np.float) for jattr in attr]
    
    ## Parameter setup.
    # Model
    # Restricted net (true coeff but agents restrected from adjusting, FixedNet priors)
    # Fixed net
    # No Net Data (no local PE)
    priors_dir    = currentdir+'/../Estimation/priors/'
    estimates_dir = currentdir+'/../Estimation/estimates/'
    setup_files     = ['parameterSetup','parameterSetupFixedNet','parameterSetupFixedNet','parameterSetupNoNetData']
    estimates_files = ['1000draws_posterior','1000draws_posteriorRestrictNet','1000draws_posteriorFixedNet','1000draws_posteriorNoNetData']
    theta_setups  = [pd.read_csv(priors_dir+jfile+'.csv') for jfile in setup_files]
    thetastars    = [pd.read_csv(estimates_dir+jfile+'.csv') for jfile in estimates_files]
    
   
    ## Size MC for state (inner loop).
    vec_numsim_kCD = np.ones(num_nets,dtype=int)*20000

    numsim = 1000
    mcJump = 0.05 # Probability of large jumps for the MCMC.
    np.random.seed(2026642028)
    
    gridDeltaPrice=[float(x*220/11) for x in range(0, 9)]
    nctrf   = len(gridDeltaPrice)
    nscid   = num_nets
    cpuinfo = [NUM_WORKERS,nscid,nctrf]
    
    sim_args = [num_nets, attr, I9, data_a, data_g, size_nets, vec_numsim_kCD,
                    thetastars, theta_setups, sampleinfo, sample_k,
                    gridDeltaPrice, mcJump, numsim, filename, cpuinfo]
    sim_wrapper = functools.partial(sim_ctrfPrice_jscid_jctrf,*sim_args)
    if DO_PARALLEL:
        pool = multiprocessing.Pool(processes=NUM_WORKERS)
    if not DO_PARALLEL:
        ctrfPriceData = [sim_wrapper(jcpu) for jcpu in range(num_nets*nctrf)]
    else:
        ctrfPriceData = pool.map(sim_wrapper,range(num_nets*nctrf))
    ctrfPriceData = pd.concat(ctrfPriceData,ignore_index=True) #all scids in one df
    

    with open(filename+'.data', 'wb') as filehandle:
        pickle.dump([ctrfPriceData,numsim,gridDeltaPrice,num_nets, size_nets, attr, data_a, data_g], filehandle)
    print(f'{pyfilename} saved {filename} at {(datetime.now()).strftime("%Y-%m-%d-%H:%M:%S")}')

if __name__ == '__main__':
    main()
