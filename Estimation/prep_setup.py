from distutils.core import setup, Extension
import numpy

modules = [Extension('compute_delta_potential',
                     sources=['compute_delta_potential.c'],
                     include_dirs=[numpy.get_include()]),
          Extension('compute_potential',
                     sources=['compute_potential.c'],
                     include_dirs=[numpy.get_include()])]
setup(ext_modules=modules)
