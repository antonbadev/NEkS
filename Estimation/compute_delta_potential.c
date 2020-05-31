/*
 * Compute the change of utility of i
 */
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <numpy/arrayobject.h>


/* Undirecteda version */
double compute_delta_potential_cpp(
        double* V,      /* 1 */
        double* W,      /* 2 */
        double  h,      /* 3 */        
        double  ph1,     /* 4 */
        double  ph2,     /* 4 */
        double  psi,     /* 4 */
        double  qhat,   /* 5 */
        double* I9,     /* 6 */
        double* G0,     /* 7 */
        double* G1,     /* 8 */
        double* A0,     /* 9 */
        double* A1,     /* 10 */
        int     iin,    /* 11 */
        int     n){     /* 12 */

    /* Declarations */
    double dU,dA,sumA0,dFof,ff,dTri,tt;
    double deg0_j,deg1_j,deg0_i,deg1_i, cost;
    int i, j, l;
    
/* pointer arithmetics (test!)
 * Python & C both in row major form/order
 * w(r,c) = a[r*ncol+c]
 */

    i=iin; //Python=C indexing (Matlab starts from 1) iin-1
    dA = A1[i]-A0[i];
    dU = V[i]*dA;
    cost = 0;
    deg0_j=0;
    deg1_j=0;
    deg0_i=0;
    deg1_i=0;

    sumA0 =0;
    for(j = 0; j < n; j++)
    {
        sumA0 += A0[j];
        deg0_i+= G0[i*n+j];
        deg1_i+= G1[i*n+j];

        dU = dU + W[i*n+j]*G1[i*n+j]              \
                + ph1*G1[i*n+j]*A1[i]*A1[j]        \
                + ph2*G1[i*n+j]*(1-A1[i])*(1-A1[j])\
                - W[i*n+j]*G0[i*n+j]              \
                - ph1*G0[i*n+j]*A0[i]*A0[j]        \
                - ph2*G0[i*n+j]*(1-A0[i])*(1-A0[j]);
        
        deg0_j=0;
        deg1_j=0;
        for(l = 0; l < n; l++)
        {
            deg0_j+= G0[j*n+l];
            deg1_j+= G1[j*n+l];
        }
        
        cost+= I9[j]*( G1[i*n+j]*deg1_j - G0[i*n+j]*deg0_j );
         
    }
    dU+= h*dA*(sumA0 - A0[i]);
    cost+= 0.5*I9[i]*(deg1_i*deg1_i - deg0_i*deg0_i + deg1_i - deg0_i);
    dU+= psi*cost;






    //dFof=0;
    //ff=0;
    dTri=0;
    tt=0;
    if (I9[i]>0.5)
    {
        for(j = 0; j < n; j++)
        {
            for(l = (j+1); l < n; l++)
            {
                if ((i==j) || (i==l))
                {
                    continue;
                }
                tt = G1[i*n+j]*G1[j*n+l]*G1[i*n+l] - G0[i*n+j]*G0[j*n+l]*G0[i*n+l];
                dTri += tt*I9[j]*I9[l];
                
                //ff  = G1[i*n+j]*G1[j*n+l] - G0[i*n+j]*G0[j*n+l];
                //ff += G1[i*n+j]*G1[i*n+l] - G0[i*n+j]*G0[i*n+l];
                //ff += G1[j*n+l]*G1[i*n+l] - G0[j*n+l]*G0[i*n+l];
                //dFof += ff*I9[j]*I9[l];
                                
            }
        }
    //dU+= dFof*psi;
    dU+= dTri*qhat;
//    dU+= round(dTri)*qhat;
    }

    return dU;
}

/* GATEWAY FUNCTION */
static PyObject* compute_delta_potential(PyObject* self, PyObject* args){
  double* VV = NULL;
  double* WW = NULL;
  double  h;
  double  phi1;
  double  phi2;
  double  psi;
  double  qhat;
  double* I9g = NULL;
  double* GG0 = NULL;
  double* GG1 = NULL;
  double* AA0 = NULL;
  double* AA1 = NULL;
  int     ii;
  int     nn;
  double  pout;

  PyArrayObject* npy_VV;
  PyArrayObject* npy_WW;
  PyArrayObject* npy_I9g;
  PyArrayObject* npy_GG0;
  PyArrayObject* npy_GG1;
  PyArrayObject* npy_AA0;
  PyArrayObject* npy_AA1;
	
  import_array()

  if(!PyArg_ParseTuple(args,"O!O!dddddO!O!O!O!O!ii",
					   &PyArray_Type,
  					   &npy_VV,
					   &PyArray_Type,
					   &npy_WW,
					   &h,
					   &phi1,
                       &phi2,
					   &psi,
					   &qhat,
					   &PyArray_Type,
					   &npy_I9g,
					   &PyArray_Type,
  					   &npy_GG0,
					   &PyArray_Type,
					   &npy_GG1,
					   &PyArray_Type,
					   &npy_AA0,
					   &PyArray_Type,
					   &npy_AA1,
					   &ii,
					   &nn))
      return NULL;

  VV = npy_VV->data;
  WW = npy_WW->data;
  I9g = npy_I9g->data;
  GG0 = npy_GG0->data;
  GG1 = npy_GG1->data;
  AA0 = npy_AA0->data;
  AA1 = npy_AA1->data;
    
  pout = 0.0;
  pout = compute_delta_potential_cpp(VV,WW,h,phi1,phi2,psi,qhat,I9g,GG0,GG1,AA0,AA1,ii,nn);

  return Py_BuildValue("d",pout);
}

static PyMethodDef methods[] = {
  {"compute_delta_potential",compute_delta_potential,METH_VARARGS,"Delta Utility/Potential."},
  {NULL,NULL,0,NULL} // Sentinel.
};


static struct PyModuleDef module = {
  PyModuleDef_HEAD_INIT,
  "compute_delta_potential",
  NULL,
  -1,
  methods
};


PyMODINIT_FUNC PyInit_compute_delta_potential(void){
  return PyModule_Create(&module);
}
