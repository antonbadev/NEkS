'''
Nash Equilibria on (Un-)Stable Networks

2020
Anton Badev
anton.badev@gmail.com

Draw a sample of 1000 from the posterior
Used in counterfactuals, fit etc
Input files:
    posterior.csv
    posteriorFixedNet.csv
    posteriorNoNetData.csv
    posteriorNoPE.csv
    posteriorNoTri.csv
    posteriorNoCost.csv
Output files:
    1000draws_XXX.csv
Note (check) the folder structure:
    currentdir
    scratchdir
    posteriorsdir
    estimatesdir
'''

import numpy as np
import pandas as pd
from libsetups import setupdirs
from libposteriors import posteriorSample


def main():
    [systime0,pyfilename,pyfiledir,homedir,currentdir,scratchdir,hostname,sysname]=setupdirs()

    posteriorsdir=scratchdir
    estimatesdir =currentdir+'estimates/'
    
    posteriors=[    
        'posterior',
        'posteriorFixedNet',
        'posteriorNoNetData',
        'posteriorNoPE',
        'posteriorNoTri',
        'posteriorNoCost'
    ]


    ndraws=1000
    np.random.seed(2026642028)
    

    for jp, posterior in enumerate(posteriors):
        try:
            theta_post=pd.read_csv(posteriorsdir+posterior+'.csv')
        except:
            print(f'Not found {posteriorsdir+posterior}')
            continue
        theta_draws = posteriorSample(theta_post,0.2,ndraws)

        estimates=f'{ndraws}'+'draws_'+posterior.split('-')[0]
        print(f'posterior={posterior} --> estimates={estimates}')

        theta_draws.to_csv(estimatesdir+estimates+'.csv', encoding='utf-8', index=False)
    
        if jp==0:
            #theta_setup         = pd.read_csv(currentdir+'priors/parameterSetup.csv')
            theta_setupFixedNet = pd.read_csv(currentdir+'priors/parameterSetupFixedNet.csv')
            varlist  = theta_setupFixedNet.Label[theta_setupFixedNet.FlagInclude==1].tolist()
            theta_draws[varlist].to_csv(estimatesdir+estimates+'RestrictNet.csv', encoding='utf-8', index=False)

if __name__ == '__main__':
    main()

