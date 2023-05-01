#!/usr/bin/bash

# deactivate the conda environment, if there is one.
if [ -z $CONDA_DEFAULT_ENV ]; then
    conda deactivate
fi

# activate the geoprocess-env environment 
source geoprocess-env/bin/activate
# run the script
python municipal_limits_geoprocess.py