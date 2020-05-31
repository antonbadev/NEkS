/* Compute the potential CPP code */
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <numpy/arrayobject.h>


/* Undirected version */
void compute_potential_cpp(
        double* V,      // 1
        double* W,      // 2
        double  h,     // 3        
        double  ph1,     // 3
        double  ph2,     // 3
        double  psi,     // 3
        double  qhat,   // 4
        double* I9,     // 5
        double* G,      // 6
        double* A,      // 7
        int     n,      // 8
        double* pout){

    /* Declarations */
    double p;
    double sumA;
    double fof,tri;
    double deg_i,sum_deg_i,sum_deg_i_sq;
    int i, j, l;
    
/* pointer arithmetics
 * always test
 * from matlab a(r+1,c+1) = a[r+c*nrow]**/
    p=0;
    fof=0;
    tri=0;
    sumA=0;
    deg_i=0;
    sum_deg_i=0;
    sum_deg_i_sq=0;
    for(i = 0; i < n; i++)
    {
        sumA+=A[i];
        p+= V[i]*A[i];
        for(j = (i+1); j < n; j++)
        {
            p = p + W[i*n+j]*G[i*n+j]  \
                  + ph1*G[i*n+j]*A[i]*A[j] \
                  + ph2*G[i*n+j]*(1-A[i])*(1-A[j]);
            
            for(l= (j+1); l < n; l++)
            {
                //fof += I9[i]*I9[j]*I9[l] *( G[i*n+j]*G[j*n+l] + G[i*n+j]*G[i*n+l] + G[j*n+l]*G[i*n+l] );
                tri += I9[i]*I9[j]*I9[l] * G[i*n+j]*G[j*n+l]*G[i*n+l];
            }
            
        }
    }
    
    for(i = 0; i < n; i++)
    {
        deg_i=0;
        for(j = 0; j < n; j++)
        {
            deg_i+=G[i*n+j];
        }
        sum_deg_i += I9[i]*deg_i;
        sum_deg_i_sq += I9[i]*deg_i*deg_i;
    }
    
    
    pout[0]=p + 0.5*psi*(sum_deg_i_sq + sum_deg_i) + qhat*tri + h*sumA*(sumA-1)*0.5;
    return;
}    




/* GATEWAY FUNCTION */
static PyObject* compute_potential(PyObject* self, PyObject* args){
    double* VV = NULL;    //1
    double* WW = NULL;    //2
    double h;             //3
    double phi1;           //4
    double phi2;           //4
    double psi;           //4
    double qhat;          //5
    double* I9g = NULL;   //6
    double* GG = NULL;    //7
    double* AA = NULL;    //8
    int nn;               //9
    double pout;

    PyArrayObject* npy_VV;
    PyArrayObject* npy_WW;
    PyArrayObject* npy_I9g;
    PyArrayObject* npy_GG;
    PyArrayObject* npy_AA;

    import_array()

    if(!PyArg_ParseTuple(args,"O!O!dddddO!O!O!i",
					       &PyArray_Type,
					       &npy_VV,         //1
					       &PyArray_Type,
					       &npy_WW,         //2
					       &h,              //3
					       &phi1,            //4
                           &phi2,            //4
					       &psi,            //4
					       &qhat,           //5
					       &PyArray_Type,
					       &npy_I9g,        //6
					       &PyArray_Type,
					       &npy_GG,         //7
					       &PyArray_Type,
					       &npy_AA,         //8
					       &nn))            //9
        return NULL;
  
    VV = npy_VV->data;
    WW = npy_WW->data;
    I9g= npy_I9g->data;
    GG = npy_GG->data;
    AA = npy_AA->data;
    
    pout=0.0;
    compute_potential_cpp(VV,WW,h,phi1,phi2,psi,qhat,I9g,GG,AA,nn,&pout);

    return Py_BuildValue("d",pout);
}


static PyMethodDef methods[] = {
  {"compute_potential",compute_potential,METH_VARARGS,"Compute Potential State."},
  {NULL,NULL,0,NULL} // Sentinel.
};


static struct PyModuleDef module = {
  PyModuleDef_HEAD_INIT,
  "compute_potential",
  NULL,
  -1,
  methods
};


PyMODINIT_FUNC PyInit_compute_potential(void){
  return PyModule_Create(&module);
}
