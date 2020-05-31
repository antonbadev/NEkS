Nash Equilibria on (Un)Stable Networks
Anton Badev (antonbadev.net)

Replication files
2020 February

A. DATA PREP
Stata files in folder DataPrep
000-setup.do
inhm-01.do
inhm-02.do
inhm-03.do
inhm-04-Python.do
inhm-04-Python-ctrf-schoolComposition.do

B. ESTIMATION
Notes:
i. Libraries
libXXX.py
compute_XXX.so
ii. Priors
Folder Estimation/priors
iii. Python installation
Python 3.6 (conda create -n py36 python=3.6)

B.1. Preparation
prep_data.py
prep_data_ctrfSchoolComposition.py
prep_setup.py

B.2. Bayesian estimation
B.2.1. Specification with tobacco price
Six estimation scenarios
posterior.py
posteriorFixedNet.py
posteriorNoPE.py
PosteriorNoNetData.py
posteriorNoTri.py
posteriorNoCost.py

B.2.2. Specification with income/allowances
Six estimation scenarios
income-posterior.py
income-posteriorFixedNet.py
income-posteriorNoPE.py
income-PosteriorNoNetData.py
income-posteriorNoTri.py
income-posteriorNoCost.py

C.POST ESTIMATION
C.1. Sample 1000 draws from the posterior distributions
prep_estimates.py
prep_income_estimates.py

C.2. Counterfactuals (including simulations for model fit)
Folder Post_Estimation
ctrfPrice.py
ctrfSchoolComposition.py
ctrfSchoolComposition_income.py
ctrfSpillovers.py
ctrfSpillovers_income.py

D. VISUALS
Folder Post_Estimation
Folder TeX contains all output files
table_descriptiveStats.py
table_estimates.py
table_estimates_income.py
table_fit.py
table_ctrfPrice.py
table_ctrfSpills.py
visuals_postriorPrice.py
visuals_ctrfSchoolComposition.py
visuals_ctrfSchoolComposition_income.py
