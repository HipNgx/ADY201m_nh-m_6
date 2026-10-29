from pathlib import Path
import json, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score, roc_auc_score
sys.stdout.reconfigure(encoding='utf-8')
P=Path(__file__).resolve().parent
protocol=json.loads((P/'protocol.json').read_text(encoding='utf-8'))
metrics=pd.read_csv(P/'fold_metrics.csv')
summary=pd.read_csv(P/'summary.csv')
for spec in protocol['experiments']:
 for model in ['LR','XGB']:
  pred=np.load(P/(spec['key']+'__'+model+'__oof.npz'))
  assert len(pred['row_id'])==93329 and len(np.unique(pred['row_id']))==93329
  for fold in range(5):
   mask=pred['fold']==fold;a=pred['y'][mask];p=pred['probability'][mask];b=p>0.5
   row=metrics[(metrics.Experiment==spec['key'])&(metrics.Model==model)&(metrics.Fold==fold)].iloc[0]
   checks=dict(AP=average_precision_score(a,p),F1=f1_score(a,b),Precision=precision_score(a,b),Recall=recall_score(a,b),AUC=roc_auc_score(a,p))
   assert all(np.isclose(v,row[k],atol=1e-12) for k,v in checks.items())
print('Independent recheck passed: 56 OOF files / 280 fold rows')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold'})
colors={'LR':'#21618c','XGB':'#ba5a17'}
keys=['full21','compact13','replacement10','expanded25','spline_bmi','age_bmi_grid','education_income_state']
labels=['21 biến gốc','13 biến của nhóm','10 biến của nhóm','21 gốc + 4 mới','Spline BMI','Tuổi × nhóm BMI','Học vấn × thu nhập']
fig,axes=plt.subplots(1,2,figsize=(10.5,4.4),sharey=True)
for ax,model in zip(axes,['LR','XGB']):
 d=summary[summary.Model.eq(model)].set_index('Experiment').loc[keys]
 yy=np.arange(len(keys))
 ax.errorbar(d.AP_mean,yy,xerr=d.AP_std,fmt='o',color=colors[model],ecolor='#b8bec7',capsize=3)
 for i,v in enumerate(d.AP_mean):ax.annotate(f'{v:.4f}',(v,i),xytext=(5,6),textcoords='offset points',fontsize=8)
 ax.axvline(d.loc['full21','AP_mean'],color='#888888',ls='--',lw=1)
 ax.set(yticks=yy,yticklabels=labels,xlim=(.375,.44),xlabel='AP trung bình qua 5 fold',title='Logistic Regression' if model=='LR' else 'XGBoost')
 ax.grid(axis='x',alpha=.2)
axes[0].invert_yaxis();fig.tight_layout();fig.savefig(P/'overview_ap.png',dpi=180,bbox_inches='tight');plt.close(fig)
keys=[x['key'] for x in protocol['experiments'] if x['kind']=='drop']
labels=[x.removeprefix('drop_') for x in keys]
fig,ax=plt.subplots(figsize=(9.7,3.9));yy=np.arange(len(keys))
for model,offset in [('LR',-.13),('XGB',.13)]:
 d=summary[summary.Model.eq(model)].set_index('Experiment').loc[keys]
 ax.scatter(d.Delta_AP_mean,yy+offset,label=model,color=colors[model],s=35)
ax.axvline(0,color='#777777',lw=1);ax.set(yticks=yy,yticklabels=labels,xlabel='Thay đổi AP trung bình so với 21 gốc',xlim=(-.0035,.0038))
ax.invert_yaxis();ax.grid(axis='x',alpha=.2);ax.legend(loc='lower right',frameon=False);fig.tight_layout();fig.savefig(P/'drop_one_ap.png',dpi=180,bbox_inches='tight');plt.close(fig)

all_data={'protocol':protocol,'verification':json.loads((P/'verification.json').read_text()),'folds':pd.read_csv(P/'fold_counts.csv').to_dict('records'),'summary':summary.to_dict('records'),'metrics':metrics.fillna('').to_dict('records'),'independent_oof_recheck':True}
(P/'report_data.json').write_text(json.dumps(all_data,ensure_ascii=False,indent=2),encoding='utf-8')
for model in ['LR','XGB']:
 d=summary[summary.Model.eq(model)].set_index('Experiment')
 print('\n',model,'restore vs 10')
 for key in ['restore10_AgeBMI','restore10_LowEducationLowIncome','restore10_PoorHealthDiffWalk']:
  print(key,'AP delta',d.loc[key,'AP_mean']-d.loc['replacement10','AP_mean'],'F1 delta',d.loc[key,'F1_mean']-d.loc['replacement10','F1_mean'])
 print('base',d.loc['full21',['AP_mean','F1_mean','Recall_mean','Precision_mean']].to_dict())
 print('spline',d.loc['spline_bmi',['AP_mean','F1_mean','Delta_AP_mean','Delta_F1_mean','Delta_AP_std','AP_unique_mean','Delta_AP_unique_mean']].to_dict())
