'''
Nash Equilibria on (Un-)Stable Networks

2020
Anton Badev
anton.badev@gmail.com

VISUALS COUNTERFACTUAL SCHOOL COMPOSITION
    -A- Table summary results of the conterfactual experiment
    -B- Table pairwise tests on the overall smoking prevalence: equality of distribution & equality of means
    -C- Plot of the distribution of overall smoking under different scenarios

Input files:
    {scratchdir}/ctrfSchoolComposition.data
Output files:
    table_ctrfSchoolComposition.tex
    table_ctrfSchoolComposition_tests.tex
    ctrfSchoolComposition_OverallSmoking.pdf
Note output in texdir
'''



import numpy as np
import pandas as pd
import pickle
from scipy import stats
from sklearn.neighbors import KernelDensity
import matplotlib.pyplot as plt

from libsetups import setupdirs



def weighted_average_bygroup(dfin,data_col,weight_col,by_col):
    df=dfin.copy()
    df['_data_times_weight'] = df[data_col]*df[weight_col]#/float((df[weight_col].sum())
    df['_weight_where_notnull'] = df[weight_col]*pd.notnull(df[data_col])
    g = df.groupby(by_col)
    result = g['_data_times_weight'].sum() / g['_weight_where_notnull'].sum()
    del df['_data_times_weight'], df['_weight_where_notnull']
    return result

def weighted_average(df,data_col,weight_col):
    result = np.average(df[data_col].to_numpy(float),axis=None,weights=df[weight_col].to_numpy(float))
    #result = df[data_col]*df[weight_col].astype(float)).sum()/float(df[weight_col].sum())
    return result

def weightedmean_meanCtrfPrice(df,varname):
    result = np.average(df[varname].to_numpy(float),axis=0,weights=df['netsize'].to_numpy(float))
    return result


def main():
    [systime0,pyfilename,pyfiledir,homedir,currentdir,scratchdir,hostname,sysname] = setupdirs()
    ctrfDir = scratchdir
    ctrfFile= '/../ctrfSchoolComposition.data' #20000 MCMC kCD
    with open(ctrfDir+ctrfFile, 'rb') as filehandle:
        [ctrfData,numsim,num_nets, size_nets, attr, data_a, data_g]=pickle.load(filehandle)
    texdir   = currentdir + '/../../TeX/'
    texfile  = 'table_ctrfSchoolComposition.tex'
    texfile2 = 'table_ctrfSchoolComposition_tests.tex'
    graphdir = texdir
    graphfile= 'ctrfSchoolComposition_OverallSmoking.pdf'
    
    # -A- table policy effects
    ctrfData['policy'] = np.floor(ctrfData['scid'].to_numpy(float)/float(2)) 
    ctrfData.scid[(ctrfData.sim==0)]=ctrfData.scid[(ctrfData.sim==0)] - num_nets #this is data
    meanCtrfData=ctrfData.groupby(['scid']).mean().reset_index()
    meanCtrfData['sctype'] = np.where(meanCtrfData['scid']%2==0, 'White', 'Black')
    tmp=meanCtrfData.loc[meanCtrfData.scid>=0,['policy','scid','sctype','prev']]
    texdf=tmp.pivot(index='policy', columns='sctype', values='prev')
    texdf['Total']=(texdf['White']+texdf['Black'])/2
    
    texsignature=f'% tex created by {pyfilename}.py \n'
    texheader = r'''
    \begin{table}[t!]
    \caption{Predicted Smoking Prevalence following Same-race Students Cap}
    \label{table:ctrf-schoolcomposition}
    \begin{center}
    \begin{tabular}{cccc}
    Same-race & School & School & Overall \\
    cap ($\%$) & White  & Black   & \\ \hline \hline
    '''
    grid_policy=range(0,60,10)
    table_ctrf=''
    for r in range(len(grid_policy)):
        texline= f'{grid_policy[r]:3.0f}'
        for j,c in enumerate(texdf.columns):
            texline = texline + f' & {100*texdf.loc[r,c]:4.1f}'        
        table_ctrf = table_ctrf + texline + r' \\' + ' \n'
        
    texfooter = r'''
    \hline
    \end{tabular}
    \end{center}
    \fignotetitle{Note:} \fignotetext{A cap of $x\%$ same-race students is implemented with a swap of $(100-x)\%$ students. 
    The last column shows the predicted changes in overall smoking under different same-race caps. 
    The policy induces statistically significant changes in the overall smoking as suggested by 
    the statistical tests in appendix D.}
    \end{table}
    '''
    
    texcontent = texsignature + texheader + table_ctrf + texfooter
    with open(texdir+texfile,'w') as f:
         f.write(texcontent)
         
    # -B- Test equal distribution/equal mean ---------------------------------
    tmp=ctrfData.loc[ctrfData.scid>=0,['policy','scid','prev','sim']]
    tmp['sctype'] = np.where(tmp['scid']%2==0, 'White', 'Black')
    tmp['ii']     = tmp['policy']*1000000 + tmp['sim']
    tmp2=tmp.pivot(index='ii', columns='sctype', values=['policy','sim','prev'])
    tmp2['pr']=(tmp2[('prev', 'White')]+tmp2[('prev', 'Black')])/2
    tmp2['po']=tmp2[('policy', 'White')]
    tmp2['s']=tmp2[('sim', 'White')]
    tmp3=tmp2[[('po',''),('s',''),('pr','')]]
    tmp3.columns=['policy','sim','prev']
    prevDistrib=tmp3.pivot(index='sim', columns='policy', values='prev')
    
    p1=np.zeros([prevDistrib.shape[1],prevDistrib.shape[1]])
    p2=np.zeros([prevDistrib.shape[1],prevDistrib.shape[1]])
    for j in range(prevDistrib.shape[1]):
        for jj in range(prevDistrib.shape[1]):
            rvs1=prevDistrib.iloc[:,j].to_numpy()
            rvs2=prevDistrib.iloc[:,jj].to_numpy()
            [t, p1[j,jj]]=stats.ttest_ind(rvs1,rvs2, equal_var = False)
    
            rvs1=prevDistrib.iloc[:,j].to_numpy()
            rvs2=prevDistrib.iloc[:,jj].to_numpy()
            [t, p2[j,jj]]=stats.ks_2samp(rvs1,rvs2)

    texheader = r'''
    \begin{table}[!h]
    \caption{Pairwise tests of the response of the overall smoking to same-race caps}
    \label{table:ctrf-schoolcomposition-tests}
    \begin{center}
    \begin{tabular}{cccccccc}
    Same-race & \multirow{2}{*}{0} & \multirow{2}{*}{10}&\multirow{2}{*}{20}&\multirow{2}{*}{30}&\multirow{2}{*}{40}&\multirow{2}{*}{50} \\
    cap ($\%$) &  \\ \hline \hline
    '''
    grid_policy=range(0,60,10)
    table_ctrf=''
    for r in range(len(grid_policy)):
        texline= f'{grid_policy[r]:3.0f}'
        for c in range(r+1):
            texline = texline + f' & {p1[r,c]:4.2f} ({p2[r,c]:4.2f})'        
        table_ctrf = table_ctrf + texline + r' \\' + ' \n'
        
    texfooter = r'''
    \hline
    \end{tabular}
    \end{center}
    \fignotetitle{Note:} \fignotetext{Each cell examines the change in overall prevelance between a pair of scenarios (same-race caps).
    The two p-values are from testing a hypothesis of equal means and from testing a hypothesis of equal distributions
    (two-sample Kolmogorov-Smirnov test). 
    For example, both tests cannot reject the null (of equal means and equal distributions) 
    of the overall smoking between a same-race cap of 40\% and a same-race cap of 50\% (p-value $0.37 (0.95)$).
    For all other cases the policy induces statistically significant changes in the overall smoking.}
    \end{table}
    '''
    
    texcontent = texsignature + texheader + table_ctrf + texfooter
    with open(texdir+texfile2,'w') as f:
         f.write(texcontent)





    # -C- Plot selected distribution of overall prevalences--------------------
    models_labels      =[ '0%','10%','20%','30%','40%','50%']
    prev_range = np.linspace(0.05, 0.35, 100)[:, np.newaxis]#adds axis to 1d to make it 2d array
    
    fig, axs = plt.subplots()
    linestyles = ['r-', 'g--', 'b:', '*k:', ':']
    linewidths = [2,2,2,2,2]
    
    
    for j,jj in enumerate([0,3,5]):
        x=prevDistrib.iloc[:,jj][:, np.newaxis]#.to_numpy()
        kde = KernelDensity(kernel='gaussian', bandwidth=0.01).fit(x)
        log_dens = kde.score_samples(prev_range)
        axs.plot(prev_range, np.exp(log_dens), linestyles[j],linewidth=linewidths[j], label="{0}".format(models_labels[jj]))
    
    axs.legend(loc='upper right')
    #ax.plot(X[:, 0], -0.005 - 0.01 * np.random.random(X.shape[0]), '+k')
    axs.set_xlim(np.min(prev_range), np.max(prev_range))
    #axs.tick_params(axis='y', bottom='off', top='off', labelbottom='off', right='off', left='off', labelleft='off')
    #axs.axes.get_yaxis().set_visible(False)
    xmarks=[i for i in np.linspace(np.min(prev_range),np.max(prev_range),5)]
    plt.xticks(xmarks,rotation=0)
    axs.spines['right'].set_visible(False)
    axs.spines['top'].set_visible(False)
    axs.spines['left'].set_visible(False)
    axs.set_yticklabels([])
    axs.set_yticks([])
    
    plt.savefig(graphdir+graphfile, dpi=300)
    print(f'Saving graph in {graphdir+graphfile}')










     
if __name__ == '__main__':
    main()
