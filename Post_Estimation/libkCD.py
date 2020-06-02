import numpy as np
from libpotential import deltaPotentialCwrap
from libpotential import potentialCwrap
#from libpotential import potentialF95wrap


# Returns sample with size 30
def pmf_k(n):
    sample_k      = 2*np.ones(30,dtype=np.int32)
    sample_k[0:10]= np.floor(np.linspace(3,0.9*n,10)).astype(np.int32)
    return sample_k
    

def gen_kCD(vv, ww, h, phi1, phi2, psi, qhat, I9, 
            nn, kkin, mcJump, nmc,
            G0, A0):
    """
    Markov chain from the model via kCD 
    * mcJump prob large jumps inverting G and A
    * large k acceptance is less likely 
    """
    
    ## Random variables
    #(a) meetings i
    veci = (np.random.randint(0,nn,[nmc])).astype(np.int32)
    #(b) meeting dimensions
    nkk = kkin.shape[0] #kkin sample for dimensions of k
    if nkk>1:
        veck = kkin[np.random.randint(0,nkk,[nmc])]
    else:
        veck = np.ones([nmc])*kkin
    veck = veck.astype(np.int32)
    #(c) proposal mode
    proposal = np.random.uniform(0,1,[nmc])
    #(d) accept
    lnaccept = np.log(np.random.uniform(0,1,[nmc]))
            
    ## Prep the data.
    G = np.copy(G0)
    A = np.copy(A0)
    p = potentialCwrap(vv,ww,h,phi1,phi2,psi,qhat,I9,G,A,nn)
    p0= np.copy(p)

    ## Initializations & misc
    dP = 0
    p1 = 0
    lnPbar = 0
    index_set = np.arange(nn)

    for ss in range(nmc):
        ## Draw a meeting i,jset.
        ihat = veci[ss]
        k    = veck[ss]
        feasible_jj = index_set[ihat!=index_set]
        jj = feasible_jj[np.random.permutation(nn-1)[:k-1]]
        
        ## Propose.
        if proposal[ss]<mcJump:
            G1 = 1-G
            np.fill_diagonal(G1,0)
            A1 = 1-A
            p1 = potentialCwrap(vv,ww,h,phi1,phi2,psi,qhat,I9,G1,A1,nn)
        else:
            A1 = np.copy(A)
            G1 = np.copy(G)
            G1[ihat,jj] = np.random.binomial(1,0.5,[k-1]).astype(np.float64)
            G1[jj,ihat] = G1[ihat,jj].T
            A1[ihat]    = np.random.binomial(1,0.5,1).astype(np.float64)

            dP = deltaPotentialCwrap(vv,ww,h,phi1,phi2,psi,qhat,I9,G,G1,A,A1,ihat,nn)
            p1 = p+dP
            
        lnPbar = p1-p
        if lnaccept[ss]<lnPbar or lnPbar>0:
            A = A1
            G = G1
            p = np.copy(p1)

    return G,A,p,p0



def gen_kCD_fixG(vv, ww, h, phi1, phi2, psi, qhat, I9, 
            nn, kkin, mcJump, nmc,
            G0, A0):
    """
    Markov chain from the model via kCD 
    * mcJump prob large jumps inverting G and A
    * large k acceptance is less likely 
    """
    
    ## Random variables
    #(a) meetings i
    veci = (np.random.randint(0,nn,[nmc])).astype(np.int32)
    #(b) meeting dimensions
    nkk = kkin.shape[0] #kkin sample for dimensions of k
    if nkk>1:
        veck = kkin[np.random.randint(0,nkk,[nmc])]
    else:
        veck = np.ones([nmc])*kkin
    veck = veck.astype(np.int32)
    #(c) proposal mode
    proposal = np.random.uniform(0,1,[nmc])
    #(d) accept
    lnaccept = np.log(np.random.uniform(0,1,[nmc]))
            
    ## Prep the data.
    G = np.copy(G0)
    A = np.copy(A0)
    p = potentialCwrap(vv,ww,h,phi1,phi2,psi,qhat,I9,G,A,nn)
    p0= np.copy(p)
    TempG1= np.copy(G) #only for fixed G
    G1    = np.copy(G) #only for fixed G
    
    ## Initializations & misc
    dP = 0
    p1 = 0
    lnPbar = 0
    index_set = np.arange(nn)

    for ss in range(nmc):
        ## Draw a meeting i,jset.
        ihat = veci[ss]
        k    = veck[ss]
        feasible_jj = index_set[ihat!=index_set]
        jj = feasible_jj[np.random.permutation(nn-1)[:k-1]]
        
        ## Propose.
        if proposal[ss]<mcJump:
            #G1 = 1-G
            #np.fill_diagonal(G1,0)
            A1 = 1-A
            p1 = potentialCwrap(vv,ww,h,phi1,phi2,psi,qhat,I9,G1,A1,nn)
        else:
            A1 = np.copy(A)
            #G1 = np.copy(G)
            #keep this draw to maintain parallel randomness with other estiamtion scenarios
            TempG1[ihat,jj] = np.random.binomial(1,0.5,[k-1]).astype(np.float64) 
            #G1[jj,ihat] = G1[ihat,jj].T
            A1[ihat]    = np.random.binomial(1,0.5,1).astype(np.float64)

            dP = deltaPotentialCwrap(vv,ww,h,phi1,phi2,psi,qhat,I9,G,G1,A,A1,ihat,nn)
            p1 = p+dP
            
        lnPbar = p1-p
        if lnaccept[ss]<lnPbar or lnPbar>0:
            A = A1
            #G = G1
            p = np.copy(p1)

    return G,A,p,p0



















def gen_kCD_fixednet_old(vv, ww, h, phi, qhat, I9, 
            nn, kkin, mcJump, nmc,
            G0, A0):
    """
    Markov chain from the model via kCD 
    * mcJump prob large jumps inverting G and A
    * large k acceptance is less likely 
    """
    lnaccept = np.log(np.random.uniform(0,1,[nmc]))
    lnPaccept = 0
    
    ## Prep i in meetings.
    veci = np.random.randint(0,nn,[nmc])

    ## Prep the data.
    G = np.copy(G0)
    A = np.copy(A0)

#    p = potential(vh,ww,phi,I9,qhat,G,A,nn)
    
    p = compute_potential(vv.ravel('C'),
                        ww.ravel('C'),
                        h,
                        phi,
                        qhat,
                        I9.ravel('C'),
                        G.ravel('C'),
                        A.ravel('C'),
                        nn)
    p0=np.copy(p)

    ## Prep meeting dimensions.
    nkk = kkin.shape[0]
    if nkk>1:
        kk = kkin[np.random.randint(0,nkk,[nmc])]
    else:
        kk = np.ones([nmc])*kkin
    kk = kk.astype(np.int32)

    ## Miscellanea.
    index_set = np.arange(nn)
    acceptlog = np.zeros([nmc])
    #for ss in tqdm(range(nmc),'nmc'):
    for ss in range(nmc):
        ## Draw a meeting i,jset.
        ihat = int(veci[ss])
        feasible_jj = index_set[ihat!=index_set]
        jj = feasible_jj[np.random.permutation(nn-1)[:kk[ss]-1]]
        
        ## Propose.
        if np.random.uniform()<mcJump:
            #G1 = 1-G
            #np.fill_diagonal(G1,0)
            G1=G
            A1 = 1-A
#            p1 = potential(vh,ww,phi,I9,qhat,G1,A1,nn)

            p1 = compute_potential(vv.ravel('C'),
                                ww.ravel('C'),
                                h,
                                phi,
                                qhat,
                                I9.ravel('C'),
                                G1.ravel('C'),
                                A1.ravel('C'),
                                nn)

#            print(p1)
#            if np.absolute(p1-p1cpp)/p1>0.000000001:
#                print(f'sim {ss} CPP {p1cpp} Py {p1} Diff {p1cpp-p1}')
        else:
            A1 = np.copy(A)
#            G1 = np.copy(G)
#            G1[ihat,jj] = (np.random.uniform(0,1,[kk[ss]-1])<0.5).astype(np.float64)
#            G1[jj,ihat] = G1[ihat,jj].T
            G1=G
            A1[ihat] = float(np.random.uniform(0,1)<0.5)


#            #Next 4 lines change the parameters 
#            #to illustrate precision discrepancies 
#            vh=vh*0
#            ww= np.ones([nn,nn])*0.2; np.fill_diagonal(ww,0)
#            phi=0#.1 #phi*0 #?
#            qhat=0 #qhat*0 #no problem

            
   
            dP=0
            dP = compute_delta_potential(
                    vv.ravel('C'),
                    ww.ravel('C'),
                    h,
                    phi,
                    qhat,
                    I9.ravel('C'),
                    G.ravel('C'),
                    G1.ravel('C'),
                    A.ravel('C'),
                    A1.ravel('C'),
                    ihat,
                    nn)
            
#            dP = deltaPotential(vh,ww,phi,I9,qhat,ihat,G,G1,A,A1,nn)
#            print(f'delta P CPP/Py {dP} : {dPpy} : {np.absolute(dP-dPpy)}.')
            p1 = p+dP

        lnPaccept = p1-p
        if lnaccept[ss]<lnPaccept or lnPaccept>0:
            A = A1
            G = G1
            p = np.copy(p1)

    return G,A,p,p0


def gen_kCD_checks(vv, ww, h, phi, psi, qhat, I9, 
            nn, kkin, mcJump, nmc,
            G0, A0):
    """
    Markov chain from the model via kCD 
    * mcJump prob large jumps inverting G and A
    * large k acceptance is less likely 
    """
    
    
    ## Prep meetings
    veci = (np.random.randint(0,nn,[nmc])).astype(np.int32)
    nkk = kkin.shape[0] #kkin sample for dimensions of k
    if nkk>1:
        veck = kkin[np.random.randint(0,nkk,[nmc])]
    else:
        veck = np.ones([nmc])*kkin
    veck = veck.astype(np.int32)
            
    ## Prep the data.
    G = np.copy(G0)
    A = np.copy(A0)
    p = potentialCwrap(vv,ww,h,phi,psi,qhat,I9,G,A,nn)
    p0= np.copy(p)

    ## Draw acceptance
    lnaccept = np.log(np.random.uniform(0,1,[nmc]))
    
    ## Miscellanea & inits.
    index_set = np.arange(nn)
    dP = 0
    p1 = 0
    lnPbar = 0
    

    for ss in range(nmc):
        ## Draw a meeting i,jset.
        ihat = veci[ss]
        k    = veck[ss]
        feasible_jj = index_set[ihat!=index_set]
        jj = feasible_jj[np.random.permutation(nn-1)[:k-1]]
        
        ## Propose.
        if np.random.uniform()<mcJump:
            G1 = 1-G
            np.fill_diagonal(G1,0)
            A1 = 1-A
            p1 = potentialCwrap(vv,ww,h,phi,psi,qhat,I9,G1,A1,nn)
        else:
            A1 = np.copy(A)
            G1 = np.copy(G)
            G1[ihat,jj] = (np.random.uniform(0,1,[k-1])<0.5).astype(np.float64)
            G1[jj,ihat] = G1[ihat,jj].T
            A1[ihat] = float(np.random.uniform(0,1)<0.5)
            
            #            #CHECK SYMMETRIC
#            if np.any(np.abs(G1-G1.T) > 0.5):
#                print('Proposal not symmetric')


#            #Next 4 lines change the parameters 
#            #to illustrate precision discrepancies 
#            vv=vv*0
            #vv=np.ones(nn)*0.2
#            if np.sum(np.iscomplex(vv))>0:
#                print('Complex')
#            if np.isnan(np.sum(vv))>0:
#                print('NA')
#                
#            ww= np.ones([nn,nn])*1.0; np.fill_diagonal(ww,0)
#            ww= np.ones([nn,nn])*0; np.fill_diagonal(ww,0)
#            h=0.1
#            phi=1 #phi*0 #?
#            psi=1
#            qhat=1 #qhat*0 #no problem
            
            #G1=G
            #A1=A

            dP = deltaPotentialCwrap(vv,ww,h,phi,psi,qhat,I9,G,G1,A,A1,ihat,nn)
            p1 = p+dP


#            p1_check    =   potentialCwrap(vv,ww,h,phi,psi,qhat,I9,G1,A1,nn)
#            p0_check    =   potentialCwrap(vv,ww,h,phi,psi,qhat,I9,G,A,nn)
#            if abs(dP-(p1_check-p0_check))>1e-12:
#                print(f'dP={dP:10.4f} , p1check-p0check={p1_check-p0_check:10.4f}, error={dP-(p1_check-p0_check):10.8f}')
#                
#                if (abs(np.trace(G0)) + abs(np.trace(G1)))>1e-12:
#                    print(f'Trace 0/1 = {np.trace(G0)}, {np.trace(G1)}')
#                #print(f'P1={p1:10.4f} , P1check={p1_check:10.4f},  dP={dP:10.4f}/dPP={p1_check-p0_check:10.4f}, error={abs(p1-p1_check):10.4f}')
            



            
        lnPbar = p1-p
        if lnaccept[ss]<lnPbar or lnPbar>0:
            A = A1
            G = G1
            p = np.copy(p1)

    return G,A,p,p0











