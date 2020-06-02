'''
Nash Equilibria on (Un-)Stable Networks

2020
Anton Badev
anton.badev@gmail.com

The model is estimated under various estimation scenarios.
-A- Plot of the posterior distribution of the price parameter
estimated under different scenarios (see table estimates)
-B- Table pairwise tests on the distribution of price parameter:
equality of distribution & equality of means

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
    fig_posterior_price.pdf
    table_posterior_price_tests.tex
Note output in texdir
'''

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from libsetups import state2pickle
from libsetups import setupdirs
from sklearn.neighbors import KernelDensity
from scipy import stats



def main():
    [systime0,pyfilename,pyfiledir,homedir,currentdir,scratchdir,hostname,sysname]=setupdirs()
    estimatesdir = scratchdir+'/../../Estimation/'
    texdir   = currentdir + '/../../TeX/'
    texfile  = 'table_posterior_price_tests.tex'
    graphdir = texdir
    graphfile = 'fig_posterior_price.pdf'
    
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
    
    models_labels   =[ 'Model','Fixed net','No net data', 'No PE', 'No tri', 'No cost']
    price_range     = np.linspace(-0.015, 0.005, 100)[:, np.newaxis]#adds axis to 1d to make it 2d array
    posteriorsPrice = pd.DataFrame(columns=models_labels)
    
    fig, axs = plt.subplots()
    linestyles = ['r-', 'g--', 'b-.', '*k:', ':',':']
    linewidths = [2,2,2,2,2,2]
    
    for jp, posterior in enumerate(posteriors):
    
        theta_post=pd.read_csv(estimatesdir+posterior+'.csv')
        numobs=np.sum((theta_post.iloc[:,0]>0).to_numpy())
        print(numobs)
        burnin=np.floor(0.2*numobs).astype(int)
        price = theta_post.loc[burnin:numobs,'vPrice'][:, np.newaxis].copy()
        posteriorsPrice[models_labels[jp]]=price[:,0]
        kde = KernelDensity(kernel='gaussian', bandwidth=0.0003).fit(price)
        log_dens = kde.score_samples(price_range)
        axs.plot(price_range, np.exp(log_dens), linestyles[jp],linewidth=linewidths[jp], label="{0}".format(models_labels[jp]))
    
    
    axs.legend(loc='upper left')
    axs.set_xlim(np.min(price_range), np.max(price_range))
    xmarks=[i for i in np.linspace(np.min(price_range),np.max(price_range),5)]
    plt.xticks(xmarks,rotation=45)
    axs.spines['right'].set_visible(False)
    axs.spines['top'].set_visible(False)
    axs.spines['left'].set_visible(False)
    axs.set_yticklabels([])
    axs.set_yticks([])
    
    plt.savefig(graphdir+graphfile, dpi=300)
    
    
    # -B- Test equal distribution/equal mean ---------------------------------
    nmodels=len(models_labels)
    p1=np.zeros([nmodels,nmodels])
    p2=np.zeros([nmodels,nmodels])
    for j in range(nmodels):
        for jj in range(nmodels):
            rvs1=posteriorsPrice.iloc[:,j].to_numpy()
            rvs2=posteriorsPrice.iloc[:,jj].to_numpy()
            [t, p1[j,jj]]=stats.ttest_ind(rvs1,rvs2, equal_var = False)
    
            #rvs1=posteriorsPrice.iloc[:,j].to_numpy()
            #rvs2=posteriorsPrice.iloc[:,jj].to_numpy()
            [t, p2[j,jj]]=stats.ks_2samp(rvs1,rvs2)


    texsignature=f'% tex created by {pyfilename}.py \n'
    texheader = r'''
    \begin{table}[!h]
    \caption{Pairwise tests of the posteriors for the price parameter under different estimation scenarios}
    \label{table:ctrf-posteriorPrice-tests}
    \begin{center}
    \begin{tabular}{lccccccc}
    Estimation & \multirow{2}{*}{Model} & \multirow{2}{*}{Fixed net}&\multirow{2}{*}{No net data}&\multirow{2}{*}{No PE}&\multirow{2}{*}{No tri}&\multirow{2}{*}{No cost} \\
    scenarios &  \\ \hline \hline
    '''
    #grid_policy=range(0,60,10)
    table_ctrf=''
    for r,model in enumerate(models_labels):
        texline= f'{model:12}'
        for c in range(r+1):
            texline = texline + f' & {p1[r,c]:4.2f} ({p2[r,c]:4.2f})'        
        table_ctrf = table_ctrf + texline + r' \\' + ' \n'
        
    texfooter = r'''
    \hline
    \end{tabular}
    \end{center}
    \fignotetitle{Note:} \fignotetext{
    Each cell compares the posterior distribution of the parameter price between a pair of estimation scenarios.
    The two p-values are from testing a hypothesis of equal means and from testing a hypothesis of equal distributions
    (two-sample Kolmogorov-Smirnov test).}
    \end{table}
    '''
    
    texcontent = texsignature + texheader + table_ctrf + texfooter
    with open(texdir+texfile,'w') as f:
         f.write(texcontent)
         


     
if __name__ == '__main__':
    main()
