# Climate Challenge - Team Pluto 

This repository contains the implementation and results of all algorithms mentioned in the paper.
A quick overview:

- The `material` folder contains the original and pre-processed data
- The `Classic_Approach.ipynb` contains the code for the classic algorithm and the `classic_results.csv` contains the 
according results. `classic_results.pickle` contains the flight paths in full detail and can be loaded into the
`Classic_Approach.ipynb` for better visualization.
- The OR Tools related code lies in `or_tools.py` and in `ortools_cost_function.py`. The results can be seen in 
`results_ortools`.
- The `src` folder together with the pip file and requirements contain the code related to the D-WAVE setup.
