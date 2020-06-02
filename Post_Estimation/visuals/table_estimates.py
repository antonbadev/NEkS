'''
Nash Equilibria on (Un-)Stable Networks

2020
Anton Badev
anton.badev@gmail.com

The model is estimated under various estimation scenarios.
Collect all estimates in a table

Input files:
    parameterSetup.csv
    parameterSetupFixedNet.csv
    parameterSetupNoNetData.csv
    parameterSetupNoPE.csv
    parameterSetupNoTri.csv
    parameterSetupNoCost.csv
    posterior.csv
    posteriorFixedNet.csv
    posteriorNoNetData.csv
    posteriorNoPE.csv
    posteriorNoTri.csv
    posteriorNoCost.csv
Output files:
    table_estimates.tex
Note output in texdir
'''


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from libsetups import state2pickle
from libsetups import setupdirs
from libposteriors import posteriorStats
from libposteriors import posterior_significance


[systime0,pyfilename,pyfiledir,homedir,currentdir,scratchdir,hostname,sysname] = setupdirs()
estimatesdir = scratchdir+'/../../Estimation/'
priorsdir    = currentdir+'/../../Estimation/priors/'
texdir       = currentdir + '/../../TeX/'
texfile      = 'table_estimates.tex'

paramSetups=[
    'parameterSetup',
    'parameterSetupFixedNet',
    'parameterSetupNoNetData',
    'parameterSetupNoPE',
    'parameterSetupNoTri',
    'parameterSetupNoCost'
    ]
posteriors=[    
    'posterior',
    'posteriorFixedNet',
    'posteriorNoNetData',
    'posteriorNoPE',
    'posteriorNoTri',
    'posteriorNoCost'
    ]


models_labels      =[ 'Model','Fixed net','No net data', 'No PE', 'No tri','No costs']
models_column_order=[ 'No net data', 'Fixed net', 'No PE', 'No costs', 'No tri','Model']
table_estimates    =pd.DataFrame(columns=['vars', 'precision','description'])


for jp, posterior in enumerate(posteriors):

    theta_post=pd.read_csv(estimatesdir+posterior+'.csv')
    varnames=theta_post.columns.values.tolist()
    numobs=np.sum((theta_post.iloc[:,0]>0).to_numpy())
    nparams=theta_post.shape[1]
    print(numobs,nparams)
    burnin=np.floor(0.2*numobs).astype(int)
    theta_post= theta_post.iloc[burnin:numobs].copy()

    paramSetup=paramSetups[jp]
    theta_setup = pd.read_csv(priorsdir+paramSetup+'.csv')
    if jp==0:
        nparams_fullmodel=nparams
        varnames_fullmodel=varnames
        
        table_estimates['vars']=varnames
        table_estimates['vars']=table_estimates['vars'].astype(str)
        table_estimates=table_estimates.set_index('vars')
        table_estimates['description']=list(theta_setup.Description[theta_setup.FlagInclude==1])
        table_estimates['description']=table_estimates['description'].astype(str)
        table_estimates['precision']=3
        table_estimates.loc['vPrice','precision']=4
    thetahat=theta_post.mean() #series.to_numpy()
    significance = posterior_significance(theta_post,nparams)
    table_estimates[models_labels[jp]]='--'
    table_estimates[models_labels[jp]]=table_estimates[models_labels[jp]].astype(str)
    for jparam, param in enumerate(varnames):
        #print(jparam,significance[jparam])
        jhat = np.around(thetahat[jparam],decimals=table_estimates.precision.loc[param])
        table_estimates.loc[param,models_labels[jp]]='$'+jhat.astype('str')+'^{'+significance[jparam]+'}$'


# Prepping the tex file    
estimates_smoking=''
for jparam in range(7):
    texline=str(jparam+1).rjust(3, ' ') + ' &' + table_estimates.loc[varnames_fullmodel[jparam],'description'].ljust(40, ' ')
    for jp, model in enumerate(models_column_order):
        jestimate = table_estimates.loc[varnames_fullmodel[jparam],model]
        texline = texline + ' &' + jestimate.rjust(14, ' ')
        #print(texline)
    estimates_smoking=estimates_smoking + texline + r' \\' + ' \n'

estimates_network=''
for jparam in range(7,nparams_fullmodel):
    texline=str(jparam+1).rjust(3, ' ') + ' &' + table_estimates.loc[varnames_fullmodel[jparam],'description'].ljust(40, ' ')
    for jp, model in enumerate(models_column_order):
        jestimate = table_estimates.loc[varnames_fullmodel[jparam],model]
        texline = texline + ' &' + jestimate.rjust(14, ' ') 
    estimates_network=estimates_network + texline + r' \\' + ' \n'

texsignature=f'% tex created by {pyfilename}.py \n'
texheader = r'''
\begin{table}[t!]
\begin{center}
\caption{Parameter estimates (posterior means)} \label{tab:estimates}
\hspace*{-1cm}
\begin{small}
\begin{tabular}{llcccccc}
\hline \hline
\multicolumn{4}{c}{\textit{Utility of smoking}}  \\
   & Parameter   & No Net Data   & Fixed Net   & No PE   & No Cost  & No Tri   & Model  \\ \hline
'''

texmid = r'''
\\
\multicolumn{4}{c}{\textit{Utility of friendships}} \\
  & Parameter  & No Net Data  & Fixed Net  & No PE  & No Cost & No Tri  & Model  \\ \hline
'''

texfooter = r'''
\\ \hline
\end{tabular}%
\end{small}
\end{center}
\fignotetitle{Note:} \fignotetext{MP stands for the estimated marginal probability in percentage points and MP$\%$ for estimated marginal probability in percent, relative to the baseline probability. The posterior sample contains $10^5$ simulations before discarding the first $20\%$. The shortest $90/95/99\%$ credible sets not including zero is indicated by $^{*}$/$^{**}$/$^{***}$ respectively.}
\end{table}
'''

texcontent = texsignature + texheader + estimates_smoking + texmid + estimates_network + texfooter
with open(texdir+texfile,'w') as f:
     f.write(texcontent)
     
     
