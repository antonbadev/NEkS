'''
Nash Equilibria on (Un-)Stable Networks

2020
Anton Badev
anton.badev@gmail.com

Compute varous stats from the posteriors
'''



import numpy as np
import pandas as pd

def posteriorStats(posteriorDraws,nparams,significance):
    """ 
    Return posterior stats
    posteriorDraws pandas dataframe
    nparams int
    significance int \in [1,99]"""
    # Sanitation
    if posteriorDraws.shape[1]!=nparams:
        print(f'libposteriors.posteriorStats: posterior.shape[1]!=nparams.')
        return -1
    if significance<1 or significance>99:
        print(f'libposteriors.posteriorStats: significance level not in [1,99]')
        return -1

    mean  = np.zeros(nparams)
    median= np.zeros(nparams)
    cs_lb = np.zeros(nparams)
    cs_ub = np.zeros(nparams)
    for jtheta in range(nparams):
        sample_theta_j = posteriorDraws.iloc[:,jtheta].to_numpy()
        mean[jtheta]   = np.mean(sample_theta_j)
        median[jtheta] = np.percentile(sample_theta_j,0.5,interpolation='lower')
        lb=np.zeros(100-significance)
        ub=np.zeros(100-significance)
        length_credible_set=np.zeros(100-significance)

        for joffset in range(100-significance):
            lb[joffset] = np.percentile(sample_theta_j, joffset, interpolation='lower')
            ub[joffset] = np.percentile(sample_theta_j, joffset+significance, interpolation='lower')
            length_credible_set[joffset] = np.absolute(ub[joffset]-lb[joffset])
        indx_min_length_credible_set = np.where(length_credible_set == np.amin(length_credible_set))[0][0]
        cs_lb[jtheta] = lb[indx_min_length_credible_set]
        cs_ub[jtheta] = ub[indx_min_length_credible_set]

    return mean, median, cs_lb, cs_ub


def posteriorStats_short(posteriorDraws,nparams):
    """ 
    Return posterior stats
    posteriorDraws pandas dataframe
    nparams int
    significance int \in [1,99]"""
    # Sanitation
    if posteriorDraws.shape[1]!=nparams:
        print(f'libposteriors.posteriorStats: posterior.shape[1]!=nparams.')
        return -1

    mean  = np.zeros(nparams)
    median= np.zeros(nparams)
    for jtheta in range(nparams):
        sample_theta_j = posteriorDraws.iloc[:,jtheta].to_numpy()
        mean[jtheta]   = np.mean(sample_theta_j)
        median[jtheta] = np.percentile(sample_theta_j,0.5,interpolation='lower')

    return mean, median


def posterior_significance(posteriorDraws,nparams):
    """ 
    Return posterior stats
    posteriorDraws pandas dataframe
    nparams int
    significance int \in [1,99]"""
    # Sanitation
    if posteriorDraws.shape[1]!=nparams:
        print(f'libposteriors.posteriorStats: posterior.shape[1]!=nparams.')
        return -1

    stars = ['']*nparams
    significance=[90,95,99] # Order is important
    significance_symbol=[(k+1)*'*' for k in range(len(significance))]
    cs_lb =np.zeros([len(significance),nparams])
    cs_ub =np.zeros([len(significance),nparams])
    for k in range(len(significance)):
        [mean, median, cs_lb[k,:], cs_ub[k,:]] = posteriorStats(posteriorDraws,nparams,significance[k])
    stars = ['']*nparams
    for jparam in range(nparams):
        for k in range(len(significance)):
            #print(k)
            if cs_lb[k,jparam]*cs_ub[k,jparam]>0:
                stars[jparam] = significance_symbol[k]
        
    return stars

def posteriorSample(posteriorDraws,burnin,nsample):
    """
    Draw subsample of nsample from the posterior Draws
    discarding (first) burin fraction of the sample.
    """
    
    [ndraws,nparams]=posteriorDraws.shape

    posteriorDrawsClean = posteriorDraws.iloc[int(burnin*ndraws):]
    ndrawsClean = posteriorDrawsClean.shape[0]-1
    #sampleIndex = np.sort(np.random.permutation(ndrawsClean)[:nsample])
    sampleIndex = (np.random.permutation(ndrawsClean)[:nsample])
    posteriorSampleOut = posteriorDrawsClean.iloc[sampleIndex].copy()
    return posteriorSampleOut
    
    
    
    