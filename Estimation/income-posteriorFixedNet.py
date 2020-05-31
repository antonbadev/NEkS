'''
Nash Equilibria on (Un-)Stable Networks

2020
Anton Badev
anton.badev@gmail.com

Bayesian estimation Fixed Networks scenario
Input files:
    estimation_top8_100plus.data (high schools enrolled 100+ students)
    income-parameterSetupFixedNet.csv
Output files:
    income-posteriorFixedNet.csv
Note (check) the folder structure:
    homedir
    currentdir
    pyfiledir
    scratchdir
'''

import os,sys,csv,multiprocessing,functools
from pathlib import Path
from datetime import datetime
import time
import numpy as np
import pandas as pd
import scipy.io as sio
import pickle

from libsetups import state2pickle
from libsetups import setupdirs
from libpotential import deltaPotentialCwrap
from libpotential import potentialCwrap
#from libpotential import potentialF95wrap
from libtheta import theta2param
from libkCD import gen_kCD_fixG
from libkCD import pmf_k

DO_PARALLEL = True
NUM_WORKERS = 12


def run_sim(num_net, 
            nets_inhm_attr,
            I9, 
            nets_a, 
            nets_g, 
            vec_size_net, 
            vec_nmc_state, 
            theta0, 
            theta1, 
            theta_setup,
            sampleinfo,
            sample_k,
            mcJump,
            filename,
            jsim,
            jscid):
    
    
    np.random.seed(jsim*num_net+jscid+2026642028)
    
    jattr = nets_inhm_attr[jscid]
    jI9 = I9[jscid]
    jA = nets_a[jscid]
    jG = nets_g[jscid]
    nn = int(vec_size_net[jscid])
    jkk = sample_k[jscid]
    nmc_state = vec_nmc_state[jscid]
    [vv,ww,h,phi1,phi2,psi,qhat] = theta2param(theta1,jattr,theta_setup,sampleinfo)
    [jG1,jA1,p_th1_s1,p_th1_s0] = gen_kCD_fixG(vv,ww,h,phi1,phi2,psi,qhat,jI9,
                                nn,jkk,mcJump,nmc_state,
                                jG,jA)
    ## Could be more efficient.
    [vv,ww,h,phi1,phi2,psi,qhat] = theta2param(theta0,jattr,theta_setup,sampleinfo)
    p_th0_s1 = potentialCwrap(vv,ww,h,phi1,phi2,psi,qhat,jI9,jG1,jA1,nn)
    p_th0_s0 = potentialCwrap(vv,ww,h,phi1,phi2,psi,qhat,jI9,jG,jA,nn)

#    if jsim>0 and jsim%5000==0:
#        state2pickle(filename+'-kCD-state--scid-'+str(jscid+1).zfill(2)+'--sim-'+str(jsim+1).zfill(6),jG1,jA1)
#        #print(f'Saving {posteriorfile}')

    p_dTh_s1 = p_th1_s1-p_th0_s1
    p_dTh_s0 = p_th1_s0-p_th0_s0
    return (p_dTh_s0-p_dTh_s1)#,mcstats


def main():
    ## Setup
    [systime0,pyfilename,pyfiledir,homedir,currentdir,scratchdir,hostname,sysname]=setupdirs()
    posteriorfile=scratchdir+'/'+pyfilename+'-'+systime0.strftime("%Y-%m-%d-%H:%M:%S")
    posteriorfile=scratchdir+'/'+pyfilename
    kCDstatefile=scratchdir+'/kCD-states/'+pyfilename+'-'+systime0.strftime("%Y-%m-%d-%H:%M:%S")
    print(80*'*')
    print(f'hostname={hostname} (OS={sysname})')
    print(f'start={systime0.strftime("%Y-%m-%d-%H:%M:%S")}\npyfilename={pyfilename}\ncurrentdir={currentdir}\nscratchdir={scratchdir}')
    print(f'posterior ={posteriorfile}')
    print(80*'*')
     
    ## Load data.
    datadir='../Data/'
    with open(datadir+'/estimation_top8_100plus.data', 'rb') as filehandle:
        [num_nets, size_nets, attr, data_a, data_g]=pickle.load(filehandle)
    #data_a=[jnet_data_a.reshape(-1,1) for jnet_data_a in data_a] #reshape as 2D from 1D if needed
    sampleinfo=[num_nets, size_nets]
    sample_k = [pmf_k(jn) for jn in size_nets]
    I9 = [(jattr.grade>8.1).to_numpy(np.float) for jattr in attr]

    ## Parameter setup.
    theta_setup = pd.read_csv('priors/income-parameterSetupFixedNet.csv')
    theta0      = theta_setup.PriorMean[theta_setup.FlagInclude==1].to_numpy()
    nparams     = len(theta0)
    theta_labels= list(theta_setup.Label[theta_setup.FlagInclude==1])
    
    
    ## Prior.
    mu_prior = theta0
    s1_prior = theta_setup.PriorSD[theta_setup.FlagInclude==1].to_numpy()
    s2_prior = np.diag(s1_prior*s1_prior)
    inv_s2_prior = np.linalg.inv(s2_prior)

    ## Proposal -- random walk.
    mu_prop = np.zeros([nparams,1])
    s1_prop = theta_setup.PropSD[theta_setup.FlagInclude==1].to_numpy()
    s2_prop = np.diag(s1_prop*s1_prop)

    ## Size MC for state (inner loop).
    vec_numsim_kCD = np.clip(np.asarray(size_nets, dtype=int)*150,a_min=None,a_max=15000)

    numsim_theta = 100000
    mcJump = 0.05 # 0.02 Probability of large jumps for the MCMC.

    ## Posterior sample.
    theta_post = pd.DataFrame(data=np.zeros([numsim_theta+1,nparams],dtype=float,order='C'),columns=theta_labels)
    theta_post.iloc[0]= theta0

    ## Plots and logs.
    savefreq  = 5000
    printfreq = 1
    
    np.random.seed(2026642028)
    #np.random.RandomState(2026642028)

    if DO_PARALLEL:
        pool = multiprocessing.Pool(processes=NUM_WORKERS)

    for js in range(numsim_theta):
#        if js%printfreq==0:
#            print(f'Simulation {js+1} {(datetime.now()).strftime("%Y-%m-%d-%H:%M:%S")}')
        theta1 = theta0+np.random.multivariate_normal(mu_prop[:,0],s2_prop)
        
        run_sim_args = [num_nets, attr, I9, data_a, data_g, 
                        size_nets, vec_numsim_kCD, theta0, theta1, 
                        theta_setup, sampleinfo, sample_k, mcJump, kCDstatefile, js]
        run_sim_wrapper = functools.partial(run_sim,*run_sim_args)
        if not DO_PARALLEL:
            result = [run_sim_wrapper(jjscid)
                       for jjscid in range(num_nets)]
                      #for jjscid in tqdm(range(num_net),'scid')]
        else:
            result = pool.map(run_sim_wrapper,range(num_nets))
        
        lnaccept_jnet = result

        lnaccept1 = np.sum(lnaccept_jnet)
        lnaccept2 = -0.5*np.matmul((theta1-mu_prior).reshape(1,nparams),
                                   np.matmul(inv_s2_prior,
                                             (theta1-mu_prior).reshape(nparams,1)))
        lnaccept2 += 0.5*np.matmul((theta0-mu_prior).reshape(1,nparams),
                                   np.matmul(inv_s2_prior,
                                             (theta0-mu_prior).reshape(nparams,1)))
        lnaccept2 = lnaccept2[0,0]
        lnaccept_th = lnaccept1+lnaccept2
        if np.random.uniform(0,1)<lnaccept_th or lnaccept_th>0:
            theta0 = theta1.copy()
        theta_post.iloc[js+1]= theta0
        if (js+1)%savefreq==0:
            print(f'Sim = {js+1:4d}; Saving {posteriorfile}')
            #np.savetxt(posteriorfile+'.csv', theta_post, delimiter=',', fmt='%f',header=theta_header, comments="")
            theta_post.iloc[0:js+2].to_csv(posteriorfile+'.csv', encoding='utf-8', index=False)
            
        


if __name__ == '__main__':
    main()

