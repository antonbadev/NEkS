import numpy as np
import pandas as pd
import pickle
from collections import namedtuple

from libccp import ccp2intercept
from libccp import dccp2coeff
from libccp import dlogccp2coeff

def theta2param(thetain, jnet_data_attr, theta_setup, sampleinfo):
    """ 
    theta to matrix of parameters
    transformation needed for quick computing of P and deltaP
    -- thetain : numpy 1d array (nparam,)
    -- jnet_data_attr : pandas df 
        (sorted by id), price, income, hhsmokes, mom_ed, sex, grade, black
    -- theta_setup : pandas df (read from xls file)
        (sorted by No ) Label, Description, PriorMean, PriorSD, PropSD, FlagInclude
    -- sampleifno : [num_nets, size_nets] -- list with info for the entire sample
        needed to scale qhat (tri)
    """
    ## Prep matrix coeff which depend on theta and attributes data
    ##   vh enters  a'VH a
    ##   ww enters  1' W.*G 1
    ##   mm enters  (m/2) 1' GG' 1
    ##   phi enters (phi/2) a' GG' a + (1-a)' GG' (1-a)
    ##   dd enters  (G1)' (G1)

    ## data_attr comes from STATA
    ## outsheet scid age sex male race black grade income 
    ## price price_level tax hhsmokes mom_hs mom_co mom_ed

    ## Num nodes.
    nn = jnet_data_attr.shape[0]
    theta_labels = theta_setup.Label[theta_setup.FlagInclude==1].tolist()

    ## Default values.
    v0       = 0.0
    vPrice   = 0.0
    vIncome  = 0.0
    vMale    = 0.0
    vMomEd   = 0.0
    vHhSm    = 0.0
    vGrade9p = 0.0
    vBlack   = 0.0
    
    diffgrade1 = 0.0
    diffgrade2 = 0.0
    diffsex    = 0.0
    diffrace   = 0.0
    diffracebl = 0.0 # Default value is diffRaceBL=diffRace
    
    hh  = 0
    phi1= 0
    phi2= 0
    psi = 0
    qhat= 0
    
    [num_nets, size_nets] = sampleinfo
    scaletheta = namedtuple('scaletheta', ['fof','tri'])
    scaletheta.fof=np.average(size_nets)
    scaletheta.tri=np.average(size_nets)

    w0     = ccp2intercept(3.50/(nn-1),'friends') #needed for Fixed Net & No net data
    w0base = w0 # reference point for the other parameters
    for jth in range(thetain.shape[0]):
        jthlabel = theta_labels[jth]
        if jthlabel == 'v0':
            v0 = ccp2intercept(thetain[jth],'v0') # 1
        elif jthlabel == 'vPrice':
            vPrice = thetain[jth] # 2
        elif jthlabel == 'vIncome':
            vIncome = thetain[jth] # data ln(1+income) # 2
        elif jthlabel == 'vMomEd':
            vMomEd = dccp2coeff(thetain[jth],v0,'mom ed') # 3
        elif jthlabel == 'vHHsmokes':
            vHhSm = dccp2coeff(thetain[jth],v0,'hh smokes') # 4
        # jth=jth+1;  vMale = dccp2coeff(thetain[jth],v0,'male') # 5
        # Note the correction v0/2. Blacks are usually with good attributes
        # eg momeduc=1,hhsmoke=0,high income. In essence their intercept is
        # higher. Since v0<0 (vecause baseline smoking <0.5), this is the
        # correct way to account for ppt MORE than the baseline
        elif jthlabel == 'vMale':
            vMale = dccp2coeff(thetain[jth],v0/2,'vMale') # 6
        elif jthlabel == 'vGrade9p':
            vGrade9p = dccp2coeff(thetain[jth],v0/2,'grade9p') # 6
        elif jthlabel == 'vBlack':
            vBlack = dccp2coeff(thetain[jth],v0/4,'black') # 6
        elif jthlabel == 'hh':
            hh = dccp2coeff(thetain[jth]/(nn*0.3),v0,'30prc') # 7

        ## B. friendships
        elif jthlabel == 'w0':
            w0 = ccp2intercept(thetain[jth]/(nn-1),'friends') # 1
            #w0base = w0 # update reference  
        elif jthlabel == 'diffSex':
            diffsex = dlogccp2coeff(thetain[jth],w0base,'sex') # 2
        elif jthlabel == 'diffGrade':
            diffgrade1 = dlogccp2coeff(thetain[jth],w0base,'grade adjacent') # 3
        #elif jthlabel == 'diffGrade2':
        #    diffgrade2 = dlogccp2coeff(thetain[jth],w0,'grade non-adjacent') # 4
        elif jthlabel == 'diffRace':
            diffrace = dlogccp2coeff(thetain[jth],w0base,'race   ') # 5
        elif jthlabel == 'psi':
            psi = dlogccp2coeff(thetain[jth],w0base,'fof') # 8 scales n^3
            psi = psi*((scaletheta.fof/float(nn))**1)
        elif jthlabel == 'qq9p':
            qhat = dlogccp2coeff(thetain[jth],w0base,'tri') # 8 scales n^3
            #qhatHALFth=qhat
            #qhat = dlogccp2coeff(3*thetain[jth],w0,'qq') # 8 scales n^3
            #qhat0=qhat
            #qhat = qhat*scaletheta.tri/float(nn)
            qhat = qhat*((scaletheta.tri/float(nn))**1)
            #print(f' th={thetain[jth]:5.4f},w0={w0:5.4f},qhatHALFth={qhatHALFth:5.4f},qhat0={qhat0:5.4f},qhat={qhat:5.4f}')

        ## C. Both
        elif jthlabel == 'phi1':
            phi1 = dccp2coeff(thetain[jth],(v0+w0base)/2,'-mc phi 1-' );
            # thetain[jth]
            # (v0+w0)/2
            # phi
        elif jthlabel == 'phi2':
            phi2 = dccp2coeff(thetain[jth],(v0+w0base)/2,'-mc phi 2-' );

        diffracebl = diffrace
    
    ## Preparation.
    # vv = np.zeros([nn,1])
    vv = (v0*np.ones([nn])+
          vPrice*jnet_data_attr.price.to_numpy()+
          vIncome*jnet_data_attr.income.to_numpy()+
          vMomEd*jnet_data_attr.mom_ed.to_numpy()+
          vHhSm*jnet_data_attr.hhsmokes.to_numpy()+
          vMale*(2-jnet_data_attr.sex.to_numpy())+
          vGrade9p*(jnet_data_attr.grade.to_numpy()>8)+
          vBlack*jnet_data_attr.black.to_numpy())
    #vh = np.diag(vv)+np.tril(np.ones([nn,nn]),-1)*hh

#    I9grade = ((jnet_data_attr.grade>8.1).to_numpy(dtype=float))#.astype(np.float)#.reshape(-1,1)
#    II9=np.matmul(I9grade,I9grade.T)
    #print('shape----------',I9grade.shape)
    #time.sleep(10)
    
#    not_9grade = ~I9grade #np.ones(nn,1)
#    q = np.ones([nn,nn,nn])
#    q[not_9grade,:,:] = 0
#    q[:,not_9grade,:] = 0
#    q[:,:,not_9grade] = 0
#    q = np.zeros([nn,nn,nn])
#    q[I9grade,I9grade,I9grade] = 1
#    for i in range(nn):
#        q[i,i,:]=0
#        q[i,:,i]=0
#        q[:,i,i]=0
#    qq = q*qhat


    ## Prep W.
    ww = np.zeros([nn,nn])+w0
    np.fill_diagonal(ww,0)
    wsex = (np.zeros([2,2])+
            diffsex*(np.tril(np.ones([2,2]),-1)+
                     np.triu(np.ones([2,2]),1)))
    wrace = (np.zeros([3,3])+
             diffracebl*(np.tril(np.ones([3,3]),-1)-np.tril(np.ones([3,3]),-2))+
             diffracebl*(np.triu(np.ones([3,3]),1)-np.triu(np.ones([3,3]),2))+
             diffrace*(np.tril(np.ones([3,3]),-2)+np.triu(np.ones([3,3]),2)))
    wgrade = (np.zeros([6,6])+
              diffgrade1*(np.tril(np.ones([6,6]),-1)+np.triu(np.ones([6,6]),1))+
              diffgrade2*(np.tril(np.ones([6,6]),-2)+np.triu(np.ones([6,6]),2)))

    ## Sex,grade,race.
    ind_i = jnet_data_attr.sex.to_numpy()
    ind_i = np.expand_dims(ind_i,axis=-1)
    ind_i = np.tile(ind_i,[1,nn])
    ind_j = jnet_data_attr.sex.to_numpy()
    ind_j = np.expand_dims(ind_j,axis=0)
    ind_j = np.tile(ind_j,[nn,1])
    ww += wsex[ind_i-1,ind_j-1]

    ind_i = (jnet_data_attr.grade-6).to_numpy()
    ind_i = np.expand_dims(ind_i,axis=-1)
    ind_i = np.tile(ind_i,[1,nn])
    ind_j = (jnet_data_attr.grade-6).to_numpy()
    ind_j = np.expand_dims(ind_j,axis=0)
    ind_j = np.tile(ind_j,[nn,1])
    ww += wgrade[ind_i-1,ind_j-1]
    
    ind_i = jnet_data_attr.race.to_numpy()
    ind_i = np.expand_dims(ind_i,axis=-1)
    ind_i = np.tile(ind_i,[1,nn])
    ind_j = jnet_data_attr.race.to_numpy()
    ind_j = np.expand_dims(ind_j,axis=0)
    ind_j = np.tile(ind_j,[nn,1])
    ww += wrace[ind_i-1,ind_j-1]
    
    #DEBUG
    #qq=q*0 ###############################################################################
    #phi=1
    #phi=np.round(phi,decimals=2)
    #phi=0.25
#    vv=vv*0
#    ww=ww*0
#    hh=0
#    phi=0
#    qhat=0
#    psi=1
    return vv,ww,hh,phi1,phi2,psi,qhat

def theta2thetaRestrictedNet(thetastar, theta_setup, theta_setupFixedNet):
    """ 
    theta estiamted via the ful model to 
    thetaRestrictednet that goes with theta_setupFixedNet
    """
    theta_labels         = theta_setup.Label[theta_setup.FlagInclude==1].to_numpy()
    theta_labelsFixedNet = theta_setupFixedNet.Label[theta_setupFixedNet.FlagInclude==1].tolist()

    thetastarRestrictedNet=np.zeros(len(theta_labelsFixedNet),dype=float)
    for j,jlabel in enumerate(theta_labelsFixedNet):
        thetastarRestrictedNet[j]=thetastar[jlabel==theta_labels]

    return thetastarRestrictedNet


