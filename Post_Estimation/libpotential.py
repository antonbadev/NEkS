import numpy as np
import pandas as pd
import scipy.io as sio
#import pickle
#from tqdm import tqdm

from compute_delta_potential import compute_delta_potential
from compute_potential import compute_potential
# from libfpotential import compute_delta_potential_f95
# from libfpotential import compute_potential_f95

# Setup C
# python prep_setup build
# export PYTHONPATH="PATH-TO-CYTHON"
# Setup F
# f2py -c libfpotential.f95 -m libfpotential 

def deltaPotentialCwrap(vv,ww,h,phi1,phi2,psi,qhat,I9,G,G1,A,A1,ihat,nn):
    dP = compute_delta_potential(
            vv.ravel('C'),
            ww.ravel('C'),
            h,
            phi1,
            phi2,
            psi,
            qhat,
            I9.ravel('C'),
            G.ravel('C'),
            G1.ravel('C'),
            A.ravel('C'),
            A1.ravel('C'),
            ihat,
            nn)
    return dP


def potentialCwrap(vv,ww,h,phi1,phi2,psi,qhat,I9,G,A,nn):
    p = compute_potential(
        vv.ravel('C'),
        ww.ravel('C'),
        h,
        phi1,
        phi2,
        psi,
        qhat,
        I9.ravel('C'),
        G.ravel('C'),
        A.ravel('C'),
        nn)
    return p

    
# def deltaPotentialF95wrap(vv,ww,h,phi,psi,qhat,I9,G,G1,A,A1,ihat,nn):
#     dP=compute_delta_potential_f95(
#         vv.ravel('C'),
#         ww.ravel('C'),
#         h,
#         phi,
#         psi,
#         qhat,
#         I9.ravel('C'),
#         G.ravel('C'),
#         G1.ravel('C'),
#         A.ravel('C'),
#         A1.ravel('C'),
#         ihat,
#         nn)
#     return dP

# def potentialF95wrap(vv,ww,h,phi,psi,qhat,I9,G,A,nn):
#     p = compute_potential_f95(
#         vv.ravel('C'),
#         ww.ravel('C'),
#         h,
#         phi,
#         psi,
#         qhat,
#         I9.ravel('C'),
#         G.ravel('C'),
#         A.ravel('C'),
#         nn)
#     return p




def deltaPotential(vv,ww,h,phi,psi,qhat,I9,G,G1,A,A1,ihat,nn): #(vh,ww,phi,I9,qhat,ihat,G,G1,A,A1,nn):
    ## Delta utility agent i

    sumA=np.sum(A,dtype=float)
    dA =A1[ihat]-A[ihat]
    dGi=G1[ihat,:]-G[ihat,:]
    dU = vv[ihat]*dA
    dU += dA*(sumA-A[ihat])*h
    dU += np.matmul(dGi,ww[:,ihat])
    
    In1 = np.ones([nn],dtype=float)
#    dU += phi*A1[ihat]*np.matmul(G1[ihat,:],A1) - phi*A[ihat]*np.matmul(G[ihat,:],A)
#    dU += phi*(1.0 - A1[ihat])*np.matmul(G1[ihat,:],(In1 - A1)) - phi*(1.0 - A[ihat])*np.matmul(G[ihat,:],(In1 - A))

    dU += phi*A1[ihat]*np.dot(G1[ihat,:],A1) - phi*A[ihat]*np.dot(G[ihat,:],A)
    dU += phi*(1.0 - A1[ihat])*np.dot(G1[ihat,:],(In1 - A1)) - phi*(1.0 - A[ihat])*np.dot(G[ihat,:],(In1 - A))
    
    #print(phi*(1 - A1[i])*np.matmul(G1[i,:],(In1 - A1)) - phi*(1 - A[i])*np.matmul(G[i,:],(In1 - A)))
    #print(phi)

    if I9[ihat]>0.5:
        #Option A
#        N_i  = np.nonzero(np.multiply(I9,G[:,ihat].reshape(-1,1))>0.5)[0].tolist() #note the reshape of the slicing
#        N_i1 = np.nonzero(np.multiply(I9,G1[:,ihat].reshape(-1,1))>0.5)[0].tolist()
#        tri=0
#        tri1=0
#        for j1 in N_i:
#            for j2 in N_i:
#                tri+=G[j1,j2] #*I9[j1]*I9[j2] #np.multiply(I9
#                #print(G[ihat,j1],G[ihat,j2])
#        for j1 in N_i1:
#            for j2 in N_i1:
#                tri1+=G1[j1,j2] #*I9[j1]*I9[j2] #I9[j1]*I9[j2]
#        dTri = (tri1-tri)/2
        #Option B
        GiI9 =np.multiply(I9,G[ihat,:]) #1D array
        G1iI9=np.multiply(I9,G1[ihat,:])#1D array
        #print(GiI9.ndim,GiI9.shape)
        dTri = 0.5*(np.dot(np.matmul(G1iI9,G1),G1iI9) - np.dot(np.matmul(GiI9,G),GiI9))
#        print(I9.shape,G[ihat,:].shape,A.shape,(np.matmul(G1iI9,G1)).shape,G1iI9.shape,(np.dot(np.matmul(G1iI9,G1),G1iI9)).shape)
#        time.sleep(50)
#        print('dU+=',dTri,qhat)
        dU = dU + dTri*qhat #Note dTri, qhat, and dU are all different shapes
#        print('du0',dU.shape)
#        print('dU+=',dTri,qhat)
#    print('du-',dU.shape)
    return dU #ndarray

def potential(vh,ww,phi,psi,qhat,I9,G,A,nn):
    ## Potential
    
    PPP = np.dot(A,np.matmul(vh,A))
    #print((np.dot(A,np.matmul(vh,A))).shape)
    PPP += 0.5*(np.multiply(ww,G)).sum()
    PPP += 0.5*phi*np.dot(A,np.matmul(G,A))
    PPP += 0.5*phi*np.dot((1-A),np.matmul(G,(1-A)))
    G9g = np.copy(G)
    notG9=I9<0.5
    G9g[notG9,:]=0
    G9g[:,notG9]=0
    PPP +=qhat*np.trace(np.matmul(np.matmul(G9g,G9g),G9g))/6.0
    return PPP #ndarray
#    PPP = np.dot(np.transpose(A),np.matmul(vh,A))
#    #print((np.dot(A,np.matmul(vh,A))).shape)
#    PPP += 0.5*(np.multiply(ww,G)).sum()
#    PPP += 0.5*phi*np.matmul(np.transpose(A),np.matmul(G,A))
#    PPP += 0.5*phi*np.matmul((1-np.transpose(A)),np.matmul(G,(1-A)))
#    G9g = np.copy(G)
#    notG9=I9<0.5
#    G9g[notG9,:]=0
#    G9g[:,notG9]=0
#    PPP +=qhat*np.trace(np.matmul(np.matmul(G9g,G9g),G9g))/6.0






#Check
#G9g=np.array([[0, 1, 1], [1, 0, 1], [1, 1, 0]])
#Path2_G9g = np.matmul(G9g,G9g)
#Path3_G9g = np.matmul(Path2_G9g,G9g)
#numTri=np.trace(Path3_G9g)/6.0

