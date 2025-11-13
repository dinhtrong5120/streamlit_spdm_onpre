This directory contains the source files required to build the co-simulation model associated with the RSM.

To compile a library for inclusion in a binary FMU - for example with `gcc` - execute:

    gcc -shared -fPIC -o rsm_model.so rsm_fmu_wrapper.c generated/rsm.c -Iinclude
    
from this directory.
