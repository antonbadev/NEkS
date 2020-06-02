'''
Nash Equilibria on (Un-)Stable Networks

2020
Anton Badev
anton.badev@gmail.com

COUNTERFACTUAL EXPERIMENT SPILLOVERS FROM A SMALL SCALE INTERVENTION 
Input files:
    estimation_top8_100plus.data
    parameterSetup.csv
    1000draws_posterior.csv
    parameterSetupFixedNet.csv
    1000draws_posteriorFixedNet.csv
    parameterSetupNoNetData.csv
    1000draws_posteriorNoNetData.csv
Output files:
    ctrfSpillovers_scid_1.data
    ctrfSpillovers_scid_7.data
Note run twice changing line 240
Two schools with median high smoking rates
    i. target_scid=1
    ii. target_scid=7
'''

import os,sys,csv
import multiprocessing,functools
from datetime import datetime
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
NUM_WORKERS = 30 #>= num scenarios spills


def Jcpu2JscidJctrf(jcpu,nscid,nctrf):
    jscid=int(float(jcpu)/float(nctrf))
    jctrf=int(jcpu - jscid*nctrf)
    return jscid,jctrf

def JscidJctrf2Jcpu(jscid,jctrf,nscid,nctrf):
    return jscid*nctrf+jctrf

def get_stats(sim_a,sim_g,jattr,more_info):
    [jscid,jctrf,n,numsim] = more_info
    
    
    columnnames  = ['scid','ctrf','sim','netsize',
                    'prev', 'density', 'avgDeg', 'minDeg', 'maxDeg', 'AGA', 'IAGIA', 'tri',
                    'HI','CHI','FSI']
    ncol = len(columnnames)
    statsout = pd.DataFrame(data=np.zeros([(numsim+1),ncol],dtype=float),columns=columnnames)
    for s in range(numsim+1):
        A=sim_a[s] #subdimensional array
        G=sim_g[s] #subdimensional array
        
        statsout.iloc[s,0:4] = np.array([jscid,jctrf,s,n])
        statsout.iloc[s,4:ncol]= np.array(stateStats(G,A,n)[:-1] + homophily(G,A,n,True))
        
    return statsout.copy()
    
def sim_state_spills(
        num_nets,
        grid_nnosmoke,
        jattr0,
        I9,
        jA0, 
        jG0, 
        size_nets, 
        vec_numsim_kCD, 
        thetastar_draws, 
        thetastarFixedNet_draws, 
        thetastarNoNetData_draws,
        theta_setup,
        theta_setupFixedNet, 
        theta_setupNoNetData,
        sampleinfo, 
        sample_k,
        mcJump,
        numsim,
        jcpu):
    
    nscid=num_nets
    nctrf=3
    [jscid,jctrf] = Jcpu2JscidJctrf(jcpu,nscid,nctrf)
    
    jI9 = I9[jscid].copy()
    nn  = int(size_nets[jscid])
    nnosmoke = np.round(nn*grid_nnosmoke[jscid]).astype(int)
    jkk = sample_k[jscid]
    nmc_state = vec_numsim_kCD[jscid]
    jA = np.copy(jA0)
    jG = np.copy(jG0)
    
    # Endog net
    sim_a=np.zeros([numsim+1, nn])
    sim_g=np.zeros([numsim+1, nn, nn])
    sim_a[0,:]   = np.copy(jA)
    sim_g[0,:,:] = np.copy(jG)
    
    print(jcpu, jscid, jctrf)
    
    # MODEL
    if jctrf==0:
        for js in range(numsim):
            np.random.seed(js+2026642028)
            ids_nosmoke= np.sort(np.random.permutation(nn)[:nnosmoke])
            jattr = jattr0.copy() #fresh copy for each scenario
            jA = np.copy(jA0)
            jG = np.copy(jG0)
            jA[ids_nosmoke]=0
        
            if thetastar_draws.loc[js,'vPrice']>0:
                jattr.loc[ids_nosmoke,'price']=-1e12
                #jattr.price[jattr.id.isin(ids_nosmoke)] without index=id-1
            else:
                jattr.loc[ids_nosmoke,'price']=1e12
#        if thetastar_draws.loc[js,'vIncome']>0:
#            jattr.loc[ids_nosmoke[jscid],'income']=-1e12
#        else:
#            jattr.loc[ids_nosmoke[jscid],'income']=1e12
    
            thetastar=(thetastar_draws.iloc[js]).to_numpy()
            [vv,ww,h,phi1,phi2,psi,qhat] = theta2param(thetastar,jattr,theta_setup,sampleinfo)
            np.random.seed(js+2026642028)
            [jG1,jA1,p_th1_s1,p_th1_s0] = gen_kCD(vv,ww,h,phi1,phi2,psi,qhat,jI9,
                                                  nn,jkk,mcJump,nmc_state,
                                                  jG,jA)
            sim_a[js+1,:]   = jA1.copy()
            sim_g[js+1,:,:] = jG1.copy()
    # EXOG (FIXED) NET
    elif jctrf==1:
        for js in range(numsim):
            np.random.seed(js+2026642028)
            ids_nosmoke= np.sort(np.random.permutation(nn)[:nnosmoke])
            jattr = jattr0.copy() #fresh copy for each scenario
            jA = np.copy(jA0)
            jG = np.copy(jG0)
            jA[ids_nosmoke]=0
        
            if thetastar_draws.loc[js,'vPrice']>0:
                jattr.loc[ids_nosmoke,'price']=-1e12
                #jattr.price[jattr.id.isin(ids_nosmoke)] without index=id-1
            else:
                jattr.loc[ids_nosmoke,'price']=1e12
#        if thetastar_draws.loc[js,'vIncome']>0:
#            jattr.loc[ids_nosmoke[jscid],'income']=-1e12
#        else:
#            jattr.loc[ids_nosmoke[jscid],'income']=1e12

            thetastarFixedNet      = (thetastarFixedNet_draws.iloc[js]).to_numpy()
            [vv,ww,h,phi1,phi2,psi,qhat] = theta2param(thetastarFixedNet,jattr,theta_setupFixedNet,sampleinfo)
            np.random.seed(js+2026642028)
            [jG1,jA1,p_th1_s1,p_th1_s0] = gen_kCD_fixG(vv,ww,h,phi1,phi2,psi,qhat,jI9,
                                                  nn,jkk,mcJump,nmc_state,
                                                  jG,jA)
            sim_a[js+1,:]   = jA1.copy()
            sim_g[js+1,:,:] = jG1.copy()
    # C NO NET DATA
    elif jctrf==2:
        for js in range(numsim):
            np.random.seed(js+2026642028)
            ids_nosmoke= np.sort(np.random.permutation(nn)[:nnosmoke])
            jattr = jattr0.copy() #fresh copy for each scenario
            jA = np.copy(jA0)
            jG = np.copy(jG0)
            jA[ids_nosmoke]=0
        
            if thetastar_draws.loc[js,'vPrice']>0:
                jattr.loc[ids_nosmoke,'price']=-1e12
                #jattr.price[jattr.id.isin(ids_nosmoke)] without index=id-1
            else:
                jattr.loc[ids_nosmoke,'price']=1e12
#        if thetastar_draws.loc[js,'vIncome']>0:
#            jattr.loc[ids_nosmoke[jscid],'income']=-1e12
#        else:
#            jattr.loc[ids_nosmoke[jscid],'income']=1e12
                
            thetastarNoNetData     = (thetastarNoNetData_draws.iloc[js]).to_numpy()
            [vv,ww,h,phi1,phi2,psi,qhat] = theta2param(thetastarNoNetData,jattr,theta_setupNoNetData,sampleinfo)
            np.random.seed(js+2026642028)
            [jG1,jA1,p_th1_s1,p_th1_s0] = gen_kCD_fixG(vv,ww,h,phi1,phi2,psi,qhat,jI9,
                                                      nn,jkk,mcJump,nmc_state,
                                                      jG,jA)
            sim_a[js+1,:]   = jA1.copy()
            sim_g[js+1,:,:] = jG1.copy()
        
    more_info   = [jscid,jctrf,nn,numsim]
    jctrfSpills = get_stats(sim_a,sim_g,jattr0,more_info)
    
    return jctrfSpills


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
    with open(currentdir+'/../Data/estimation_top8_100plus.data', 'rb') as filehandle:
        [num_nets, size_nets, attr, data_a, data_g]=pickle.load(filehandle)
    sampleinfo=[num_nets, size_nets]
    sample_k = [pmf_k(jn) for jn in size_nets]
    I9 = [(jattr.grade>8.1).to_numpy(np.float) for jattr in attr]
    
    ## Parameter setup.
    theta_setup     = pd.read_csv(currentdir+'/../Estimation/priors/parameterSetup.csv')
    estimatesfile   ='/../Estimation/estimates/1000draws_posterior.csv'
    thetastar_draws = pd.read_csv(currentdir+estimatesfile)
    
    #Fixed net
    theta_setupFixedNet = pd.read_csv(currentdir+'/../Estimation/priors/parameterSetupFixedNet.csv')
    estimatesfile='/../Estimation/estimates/1000draws_posteriorFixedNet.csv'
    thetastarFixedNet_draws = pd.read_csv(currentdir+estimatesfile)
    
    #No Net Data (no local PE)
    theta_setupNoNetData = pd.read_csv(currentdir+'/../Estimation/priors/parameterSetupNoNetData.csv')
    estimatesfile='/../Estimation/estimates/1000draws_posteriorNoNetData.csv'
    thetastarNoNetData_draws = pd.read_csv(currentdir+estimatesfile)
    
    nctrf=3 # Model, Fixed net, No net data

    ## Size MC for state (inner loop).
    vec_numsim_kCD = np.ones(num_nets,dtype=int)*20000
    
    numsim = 1000
    mcJump = 0.05 # Probability of large jumps for the MCMC.

    grid_nnosmoke=[0, 0.03, 0.05, 0.10, 0.20, 0.30, 0.50]
    lengrid=len(grid_nnosmoke)
    target_scid=1 #1,7 medium size/medium-high smoking for representative experiements
    # netid	prev
    # 1 0.44654088050314467
    # 7	0.4397590361445783
    
    # Prep synthetic sample
    num_nets  = lengrid
    n         = size_nets[target_scid]
    size_nets = [n]*num_nets
    sampleinfo= [num_nets, size_nets]
    sample_k  = [pmf_k(jn) for jn in size_nets]
    jattr     = attr[target_scid]
    jattr.index=jattr.id-1 #to be able to subset on ids
    I9 = [(jattr.grade>8.1).to_numpy(np.float)]*num_nets
    jA = data_a[target_scid].copy()
    jG = data_g[target_scid].copy()
    vec_numsim_kCD = np.ones(num_nets,dtype=int)*20000
    print(f'Target scid = {target_scid:3.0f} ({n})')


    sim_state_args = [num_nets, grid_nnosmoke, jattr, I9, jA, jG, size_nets, vec_numsim_kCD,
                      thetastar_draws, thetastarFixedNet_draws, thetastarNoNetData_draws,
                      theta_setup, theta_setupFixedNet, theta_setupNoNetData, sampleinfo, sample_k,
                      mcJump, numsim]
    sim_state_wrapper = functools.partial(sim_state_spills,*sim_state_args)
    if DO_PARALLEL:
        pool = multiprocessing.Pool(processes=NUM_WORKERS)
    if not DO_PARALLEL:
        result = [sim_state_wrapper(jcpu) for jcpu in range(num_nets*nctrf)]
                  #for jjscid in tqdm(range(num_net),'scid')]
    else:
        result = pool.map(sim_state_wrapper,range(num_nets*nctrf))

    ctrfSpills = pd.concat(result,ignore_index=True)
    filename   = filename+f'_scid_{target_scid}.data'
    with open(filename, 'wb') as filehandle:
        pickle.dump([ctrfSpills,numsim,grid_nnosmoke,num_nets,size_nets,jattr,jA,jG,target_scid], filehandle)
    print(f'{pyfilename} saved {filename}')



    
    # ctrfSpillsData,ctrfSpillsData_fixednet,ctrfSpillsData_noNet=list(zip(*result))
    # ctrfSpills        =pd.concat(ctrfSpillsData)
    # ctrfSpillsFixedNet=pd.concat(ctrfSpillsData_fixednet)
    # ctrfSpillsNoNet   =pd.concat(ctrfSpillsData_noNet)
    # filename = filename+f'_scid_{target_scid}.data'
    # with open(filename, 'wb') as filehandle:
    #     pickle.dump([ctrfSpills,ctrfSpillsFixedNet,ctrfSpillsNoNet,numsim,grid_nnosmoke,num_nets,size_nets,jattr,jA,jG,target_scid], filehandle)
    # print(f'{pyfilename} saved {filename}')

if __name__ == '__main__':
    main()



    
def sim_state_spills_old(
        num_nets,
        grid_nnosmoke,
        jattr0,
        I9,
        jA0, 
        jG0, 
        size_nets, 
        vec_numsim_kCD, 
        thetastar_draws, 
        thetastarFixedNet_draws, 
        thetastarNoNetData_draws,
        theta_setup,
        theta_setupFixedNet, 
        theta_setupNoNetData,
        sampleinfo, 
        sample_k,
        mcJump,
        numsim,
        jscid):
    
    jI9 = I9[jscid].copy()
    nn  = int(size_nets[jscid])
    nnosmoke = np.round(nn*grid_nnosmoke[jscid]).astype(int)
    jkk = sample_k[jscid]
    nmc_state = vec_numsim_kCD[jscid]
    jA = np.copy(jA0)
    jG = np.copy(jG0)
    
    # Endog net
    sim_a=np.zeros([numsim+1, nn])
    sim_g=np.zeros([numsim+1, nn, nn])
    sim_a[0,:]   = np.copy(jA)
    sim_g[0,:,:] = np.copy(jG)
    # Fixed net
    sim_a_fixG=np.zeros([numsim+1, nn])
    sim_g_fixG=np.zeros([numsim+1, nn, nn])
    sim_a_fixG[0,:]   = np.copy(jA)
    sim_g_fixG[0,:,:] = np.copy(jG)
    # No net data
    sim_a_noNet=np.zeros([numsim+1, nn])
    sim_g_noNet=np.zeros([numsim+1, nn, nn])
    sim_a_noNet[0,:]   = np.copy(jA)
    sim_g_noNet[0,:,:] = np.copy(jG) 
    for js in range(numsim):
        np.random.seed(js+2026642028)
        ids_nosmoke= np.sort(np.random.permutation(nn)[:nnosmoke])
        jattr = jattr0.copy() #fresh copy for each scenario
        jA = np.copy(jA0)
        jG = np.copy(jG0)
        jA[ids_nosmoke]=0
    
    
        if thetastar_draws.loc[js,'vPrice']>0:
            jattr.loc[ids_nosmoke,'price']=-1e12
            #jattr.price[jattr.id.isin(ids_nosmoke)] without index=id-1
        else:
            jattr.loc[ids_nosmoke,'price']=1e12
#        if thetastar_draws.loc[js,'vIncome']>0:
#            jattr.loc[ids_nosmoke[jscid],'income']=-1e12
#        else:
#            jattr.loc[ids_nosmoke[jscid],'income']=1e12
        # A MODEl        
        thetastar=(thetastar_draws.iloc[js]).to_numpy()
        [vv,ww,h,phi1,phi2,psi,qhat] = theta2param(thetastar,jattr,theta_setup,sampleinfo)
        np.random.seed(js+2026642028)
        [jG1,jA1,p_th1_s1,p_th1_s0] = gen_kCD(vv,ww,h,phi1,phi2,psi,qhat,jI9,
                                              nn,jkk,mcJump,nmc_state,
                                              jG,jA)
        sim_a[js+1,:]   = jA1.copy()
        sim_g[js+1,:,:] = jG1.copy()
        
        # B FIXED (EXOG) NET
        thetastarFixedNet      = (thetastarFixedNet_draws.iloc[js]).to_numpy()
        [vv,ww,h,phi1,phi2,psi,qhat] = theta2param(thetastarFixedNet,jattr,theta_setupFixedNet,sampleinfo)
        np.random.seed(js+2026642028)
        [jG1,jA1,p_th1_s1,p_th1_s0] = gen_kCD_fixG(vv,ww,h,phi1,phi2,psi,qhat,jI9,
                                              nn,jkk,mcJump,nmc_state,
                                              jG,jA)
        sim_a_fixG[js+1,:]   = jA1.copy()
        sim_g_fixG[js+1,:,:] = jG1.copy()
        
        # C NO NET DATA
        thetastarNoNetData     = (thetastarNoNetData_draws.iloc[js]).to_numpy()
        [vv,ww,h,phi1,phi2,psi,qhat] = theta2param(thetastarNoNetData,jattr,theta_setupNoNetData,sampleinfo)
        np.random.seed(js+2026642028)
        [jG1,jA1,p_th1_s1,p_th1_s0] = gen_kCD_fixG(vv,ww,h,phi1,phi2,psi,qhat,jI9,
                                                  nn,jkk,mcJump,nmc_state,
                                                  jG,jA)
        sim_a_noNet[js+1,:]   = jA1.copy()
        sim_g_noNet[js+1,:,:] = jG1.copy()
        if (jscid==0 and js%10==9):
            print(f'Simulation {js+1} {(datetime.now()).strftime("%Y-%m-%d-%H:%M:%S")}')

        
    more_info=[jscid,nn,numsim]
    jctrfSpills      = get_stats(sim_a,sim_g,jattr0,more_info)
    if (jscid==0):
        print(f'ctrfSpills stats computed {(datetime.now()).strftime("%Y-%m-%d-%H:%M:%S")}')
    jctrfSpills_fixG = get_stats(sim_a_fixG,sim_g_fixG,jattr0,more_info)
    if (jscid==0):
        print(f'ctrfSpills_fixG stats computed {(datetime.now()).strftime("%Y-%m-%d-%H:%M:%S")}')
    jctrfSpills_noNet = get_stats(sim_a_noNet,sim_g_noNet,jattr0,more_info)
    if (jscid==0):
        print(f'ctrfSpills_noNet stats computed {(datetime.now()).strftime("%Y-%m-%d-%H:%M:%S")}')
        
    #print(f'completed scid={jscid}')
        
    return jctrfSpills,jctrfSpills_fixG,jctrfSpills_noNet
