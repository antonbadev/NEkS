'''
Nash Equilibria on (Un-)Stable Networks

2020
Anton Badev
anton.badev@gmail.com

Appendix parametrization and re-parametrization
ccp2intercept(ccpin, moreinfo)
dccp2coeff(dccpin, intercept, more_info)
dlogccp2coeff(dlogccpin, intercept, more_info)

'''


import numpy as np

# ccp2intercept(ccpin, moreinfo)
# dccp2coeff(dccpin, intercept, more_info)
# dlogccp2coeff(dlogccpin, intercept, more_info)

def ccp2intercept(ccpin, more_info):
    """ ccp=exp(intercept)/(1+exp(intercept))"""
    eps=1e-14
    lb=0
    ub=1
    if ccpin < lb+eps or ccpin > ub-eps:
        print(f'ccp2intercept: {more_info} {ccpin} not in ({lb},{ub}).')
        ccpin = np.clip(ccpin, a_min=lb+eps, a_max=ub-eps)
    intercept  = np.log(ccpin) - np.log(1.0-ccpin)        
    return float(intercept)


def dccp2coeff(dccpin, intercept, more_info):
    """
    ccp2-ccp1 = dccpin in ppt (divided by 100)
    ccp2 = exp(intercept+x)/(1+exp(intercept+x))
    ccp1 = exp(intercept)/(1+exp(intercept))
    That is ccp1 is the baseline probability
    while x is the coeff in front of a dummy
    with certain marginal effect (dccp)
    """
    eps=1e-14
    lb = -np.exp(intercept)/(1.0+np.exp(intercept))
    ub = 1.0/(1.0+np.exp(intercept))
    if dccpin < lb+eps or dccpin > ub-eps:
        print(f'dccp2coeff: {more_info} {dccpin} not in ({lb},{ub}); {intercept}.')
        dccpin = np.clip(dccpin, a_min=lb+eps, a_max=ub-eps) #correct the proposal

    tt1 = 1.0+dccpin*(1.0+1/np.exp(intercept))
    tt2 = 1.0-dccpin*(1.0+np.exp(intercept))
    coeff = np.log(tt1)-np.log(tt2)
    return float(coeff)


def dlogccp2coeff(dlogccpin, intercept, more_info):
    ## Returns the coefficient in front of a dummy,
    ##   given the intercept and the marginal effect dLogCCP in PERCENTS
    ##   from the CCP induced by the intercept
    eps=1e-14
    lb = -1.0
    ub = 1.0/np.exp(intercept)
    if dlogccpin < lb+eps or dlogccpin > ub-eps:
        print(f'dlogccp2coeff: {more_info} {dlogccpin} not in ({lb},{ub}); {intercept}.')
        dlogccpin = np.clip(dlogccpin, a_min=lb+eps, a_max=ub-eps) #correct the proposal
    tt1 = 1.0+dlogccpin
    tt2 = 1.0-dlogccpin*np.exp(intercept)
    coeff = np.log(tt1)-np.log(tt2)
    return float(coeff)


def check_libccp(n,degree):
    v0=ccp2intercept(degree/(n-1),'check_libccp')
    ccp0=np.exp(v0)/(1+np.exp(v0))
    print(f'Check ccp2intercept({degree/(n-1):5.3f})={v0:5.3f}; ccp={ccp0:5.4}')
    
    dccpin=0.20#ppt
    dummy1=dccp2coeff(dccpin, v0, 'check_libccp')
    ccp1=np.exp(v0+dummy1)/(1+np.exp(v0+dummy1)) 
    print(f'Check dccp2coeff({dccpin:5.3f} ppt)={dummy1:5.3f}; ccp={ccp1:5.4}')
    dccpin=-0.02#ppt
    dummy1=dccp2coeff(dccpin, v0, 'check_libccp')
    ccp1=np.exp(v0+dummy1)/(1+np.exp(v0+dummy1)) 
    print(f'Check dccp2coeff({dccpin:5.3f} ppt)={dummy1:5.3f}; ccp={ccp1:5.4}')
    dccpin=-0.00#ppt
    dummy1=dccp2coeff(dccpin, v0, 'check_libccp')
    ccp1=np.exp(v0+dummy1)/(1+np.exp(v0+dummy1)) 
    print(f'Check dccp2coeff({dccpin:5.3f} ppt)={dummy1:5.3f}; ccp={ccp1:5.4}')
