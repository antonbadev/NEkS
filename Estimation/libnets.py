'''
Nash Equilibria on (Un-)Stable Networks

2020
Anton Badev
anton.badev@gmail.com

Compute varous network stats
Note the references
'''


import numpy as np
import pandas as pd


# homophily(G,T,n,flagSymmetric)
# mixingMat(G,TT,n,ntypes)
# netStats(G,n,flagTri), netStats2(G,n,flagTri)
# nodeStats(G,n,flagTri)
# stateStats(G,A,n), stateStats2(G,A,n)

def homophily(G,T,n,flagSymmetric):
    """ 
    T \in {0,1} int
    Return three homphily indices:
    a. Homophily index
    b. Coleman homophily index
    c. Freeman segregation index
    
    (a.) H_\tau (https://web.stanford.edu/~jacksonm/racialhomophily.pdf)
    Homophily type \tau
    total number of links of type tau = same type links + tau linked to non-tau (divide by number of taus for avg)
    H\tau = same type links / total links of tau (compare to size of tau in the population)
 
    (b.) C_\tau
    https://www.le.ac.uk/economics/research/RePEc/lec/leecon/dp16-05.pdf
    re-normalization of H relative to W_\tau the relative size of the group in the population
    (H - W_\tau)/(1- W_\tau) 
    """
    
    homophilyLabels=['Homophily','Coleman','Freeman']
    numlinks = np.sum(G, axis=None, dtype=float) #axis=None - sum all elements
    if flagSymmetric:
        numlinks = numlinks/float(2)
    numpossiblelinks = n*(n-1)/2;

    numlinks_typetau = np.matmul(np.matmul(T,G),T)
    IT = np.ones(n,dtype=float) - T
    numlinks_crosstype =  np.matmul(np.matmul(IT,G),T)
    if flagSymmetric:
        numlinks_typetau = numlinks_typetau/float(2)
        numlinks_crosstype = numlinks_crosstype/float(2)


    numtypetau = np.sum(T,axis=None,dtype=float)
    proptypetau= numtypetau/float(n)
    density= numlinks/numpossiblelinks
    Enumlinks_crosstype = float(numtypetau*(n-numtypetau)*density)

    
    H=numlinks_typetau/numlinks
    C=0
    if proptypetau<1:
        C=(H-proptypetau)/(float(1)-proptypetau)
    F=0
    if Enumlinks_crosstype>0:
        F=(Enumlinks_crosstype - numlinks_crosstype)/Enumlinks_crosstype

    return H,C,F


def mixingMat(G,TT,n,ntypes):
    """ 
    Mixing between the categories in A
    T - integer \in{0,1,2 ...}
    """
    
    uniquetypes = np.unique(TT)
    mat_indicators_type=np.zeros([n,ntypes],dtype=int)
    for j,jtype in np.ndenumerate(uniquetypes):
        mat_indicators_type[:,j] = ((TT==j).astype(int)).reshape(n,1)
    mm = np.matmul(np.matmul(mat_indicators_type.T,G),mat_indicators_type)
    
    return mm


def netStats(G,n,flagTri):
    """ 
    Compute network statistics
    G : numpy 2d array (G symmetric, diag=0)
    nn : int
    flagExtended : int
    """
    
    statsLabels=['Density',
                 'Avg deg',
                 'Min deg',
                 'Max deg',
                 'Tri/n']
               
    degreeDistribution = np.sum(G, axis=1, dtype=float)
    avgDeg = np.average(degreeDistribution, axis=0)
    minDeg = np.min(degreeDistribution,axis=0)
    maxDeg = np.max(degreeDistribution,axis=0)
    density = np.sum(degreeDistribution, axis=0, dtype=float)/float(n*(n-1))
    tri=-1
    if flagTri:
        tri = np.trace(np.matmul(np.matmul(G,G),G))/float(6*n)

    return density, avgDeg, minDeg, maxDeg, tri, statsLabels

def netStats2(G,n,flagTri):
    """ 
    Compute network statistics
    G : numpy 2d array (G symmetric, diag=0)
    nn : int
    flagExtended : int
    """
    
    statsLabels=['Density',
                 'Avg deg',
                 'Min deg',
                 'Max deg',
                 'Tri/n',
                 'Two links/n']
               
    degreeDistribution = np.sum(G, axis=1, dtype=float)
    avgDeg = np.average(degreeDistribution, axis=0)
    minDeg = np.min(degreeDistribution,axis=0)
    maxDeg = np.max(degreeDistribution,axis=0)
    density = np.sum(degreeDistribution, axis=0, dtype=float)/float(n*(n-1))
    tri=-1
    twolinksonly=-1
    twolinksonly2=-1
    if flagTri:
        G2 = np.matmul(G,G)
        tri = np.trace(np.matmul(G2,G))/float(6*n)
        IG  = np.ones([n,n],dtype=float)-G
        np.fill_diagonal(IG,0) #modifies in place
        twolinksonly2 = np.trace(np.matmul(G2,IG))/float(2*n)
        np.fill_diagonal(G2,0) #modifies in place
        twolinksonly=(G2.sum()/2-3*tri*n)/float(n)


    return density, avgDeg, minDeg, maxDeg, tri, twolinksonly, twolinksonly2, statsLabels


def nodeStats(G,n,flagSymmetric):
    """ 
    Node-level network stats (returns df)
    G : numpy 2d array (G symmetric, diag=0)
    nn : int
    flagExtended : int
    """
    
    statsLabels=['Degree',
                 'Two-links',
                 'Tri']

    if flagSymmetric:
        deg = np.matmul(G,np.ones(n,dtype=float))
        G2  = np.matmul(G,G)
        np.fill_diagonal(G2,0) #modifies in place
        twolinks=G2.sum(axis=1)
        tri=np.diag(np.matmul(G2,G))*0.5

    stats=pd.DataFrame(data=np.column_stack([deg,twolinks,tri]),dtype=int,columns=statsLabels)

    return stats



def stateStats(G,A,n):
    """ 
    Return statistics on the state
    posteriorDraws pandas dataframe
    nparams int
    significance int \in [1,99]"""
    
    stateStatsLabels=['Prev',
                      'Density',
                      'Avg deg',
                      'Min deg',
                      'Max deg',
                      'a_ig_{ij,ji}a_j/n',
                      '(1-a_i)g_{ij,ji}(1-a_j)/n',
                      'Tri/n']
    [density,avgDeg,minDeg,maxDeg,tri,statsLabels] = netStats(G,n,True)
    
    prev=np.average(A)
    IA = np.ones(n,dtype=float)-A
    AGA = np.matmul(np.matmul(A,G),A)/float(n)
    IAGIA = np.matmul(np.matmul(IA,G),IA)/float(n)
    
    return prev, density, avgDeg, minDeg, maxDeg, AGA, IAGIA, tri, stateStatsLabels

def stateStats2(G,A,n):
    """ 
    Return statistics on the state
    posteriorDraws pandas dataframe
    nparams int
    significance int \in [1,99]"""
    
    stateStatsLabels=['Prev',
                      'Density',
                      'Avg deg',
                      'Min deg',
                      'Max deg',
                      'a_ig_{ij,ji}a_j/n',
                      '(1-a_i)g_{ij,ji}(1-a_j)/n',
                      'Tri/n',
                      'Two links/n']
    [density,avgDeg,minDeg,maxDeg,tri,twolinks,twolinks2,statsLabels] = netStats2(G,n,True)
    
    prev=np.average(A)
    IA = np.ones(n,dtype=float)-A
    AGA = np.matmul(np.matmul(A,G),A)/float(n)
    IAGIA = np.matmul(np.matmul(IA,G),IA)/float(n)
    
    return prev, density, avgDeg, minDeg, maxDeg, AGA, IAGIA, tri, twolinks, twolinks2, stateStatsLabels


