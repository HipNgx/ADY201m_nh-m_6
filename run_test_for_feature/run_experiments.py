from pathlib import Path
import os
os.environ['OMP_NUM_THREADS'] = '4'
os.environ['OPENBLAS_NUM_THREADS'] = '4'
import json, hashlib, time, sys, warnings, platform, subprocess
import numpy as np
import pandas as pd
import sklearn, xgboost
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler, SplineTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score, f1_score, precision_score, recall_score, accuracy_score
from sklearn.exceptions import ConvergenceWarning
from xgboost import XGBClassifier
from threadpoolctl import threadpool_limits

sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parent.parent
OUT=Path(__file__).resolve().parent
INPUT=ROOT/'on_going2/Ongoing2_5_file_dau_vao'
OUT.mkdir(parents=True,exist_ok=True)
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode('utf-8').split('\0')
initial={p:digest(ROOT/p) for p in tracked if p and not p.startswith(OUT.name + '/')}
(OUT/'source_hashes_before.json').write_text(json.dumps(initial,indent=2),encoding='utf-8')
source=INPUT/'data/cleaned_cdc2015_keep_duplicates.csv'
meta=json.loads((INPUT/'split_metadata.json').read_text(encoding='utf-8'))
assert digest(source)==meta['data_sha256']
all_data=pd.read_csv(source)
manifest=pd.read_csv(INPUT/'split_manifest.csv')
assert len(all_data)==len(manifest)==116662
assert np.array_equal(manifest.row_id,np.arange(len(all_data)))
assert manifest.groupby('group_id').split.nunique().max()==1
train_manifest=manifest.loc[manifest.split.eq('train')].copy()
assert train_manifest.groupby('group_id').cv_fold.nunique().max()==1
df=all_data.iloc[train_manifest.row_id].copy().reset_index(drop=True)
del all_data
assert len(df)==93329
y=df.pop('Diabetes_binary').to_numpy(dtype=int)
assert y.sum()==10192
F=list(df.columns)
folds=train_manifest.cv_fold.to_numpy()
ids=train_manifest.row_id.to_numpy()
group_ids=train_manifest.group_id.to_numpy()
unique=~pd.DataFrame(np.column_stack([df.to_numpy(),y])).duplicated().to_numpy()
original=df.copy()
df['AgeBMI']=(df.Age*5+17)*df.BMI
df['BPCholState']=2*df.HighBP+df.HighChol
df['LowEducationLowIncome']=((df.Education<=3)&(df.Income<=3)).astype(int)
df['PoorHealthDiffWalk']=((df.GenHlth>=4)&(df.DiffWalk==1)).astype(int)
df['AnyMentHlth']=(df.MentHlth>0).astype(int)
df['AnyPhysHlth']=(df.PhysHlth>0).astype(int)
df['LogMentHlth']=np.log1p(df.MentHlth)
df['LogPhysHlth']=np.log1p(df.PhysHlth)
df['AgeBMIGrid']=(df.Age-3)*4+np.select([df.BMI<18.5,df.BMI<25,df.BMI<30],[0,1,2],default=3)
df['EducationIncomeState']=(df.Education-1)*8+df.Income-1
derived=['AgeBMI','BPCholState','LowEducationLowIncome','PoorHealthDiffWalk']
compact=['HighBP','HighChol','BMI','Stroke','HeartDiseaseorAttack','PhysActivity','GenHlth','MentHlth','PhysHlth','DiffWalk','Age','Education','Income']
replacement=['Stroke','HeartDiseaseorAttack','PhysActivity','GenHlth','MentHlth','PhysHlth']+derived
specs=[]
def add(key,label,cols,kind,**extra):
    assert len(cols)==len(set(cols))
    specs.append(dict(key=key,label=label,columns=cols,kind=kind,**extra))
add('full21','21 biến gốc',F,'reference')
add('compact13','13 biến của nhóm',compact,'reference')
add('replacement10','10 biến của nhóm',replacement,'reference')
add('expanded25','21 gốc cộng cả 4 biến mới',F+derived,'reference')
parents={'AgeBMI':['Age','BMI'],'BPCholState':['HighBP','HighChol'],'LowEducationLowIncome':['Education','Income'],'PoorHealthDiffWalk':['DiffWalk']}
for c in derived:
    add('add_'+c,'21 gốc cộng '+c,F+[c],'add')
    add('replace_'+c,'Thay '+', '.join(parents[c])+' bằng '+c,[x for x in F if x not in parents[c]]+[c],'replace')
for c in ['AgeBMI','LowEducationLowIncome','PoorHealthDiffWalk']:
    add('restore10_'+c,'Bộ 10 khôi phục '+', '.join(parents[c]),[x for x in replacement if x!=c]+parents[c],'restore')
add('day_flags','21 gốc cộng 2 cờ có ngày sức khỏe kém',F+['AnyMentHlth','AnyPhysHlth'],'representation')
add('log_days','21 gốc với log1p hai biến số ngày',[x for x in F if x not in ['MentHlth','PhysHlth']]+['LogMentHlth','LogPhysHlth'],'representation')
add('spline_bmi','21 gốc với spline BMI',F,'representation',spline=True)
add('age_bmi_grid','21 gốc cộng tổ hợp tuổi và nhóm BMI',F+['AgeBMIGrid'],'representation')
add('education_income_state','21 gốc cộng tổ hợp học vấn và thu nhập',F+['EducationIncomeState'],'representation')
removed=[x for x in F if x not in compact]
assert len(removed)==8
for c in removed: add('drop_'+c,'21 gốc bỏ riêng '+c,[x for x in F if x!=c],'drop')
assert len(specs)==28

domains={'Age':list(range(3,9)),'Education':list(range(1,7)),'Income':list(range(1,9)),'GenHlth':list(range(1,6))}
nominal_domains={'BPCholState':list(range(4)),'AgeBMIGrid':list(range(24)),'EducationIncomeState':list(range(48))}
numeric_names=['BMI','MentHlth','PhysHlth','AgeBMI','LogMentHlth','LogPhysHlth']
def preprocessor(spec,linear):
    cols=spec['columns']; pieces=[]
    numeric=[c for c in numeric_names if c in cols and not(c=='BMI' and spec.get('spline'))]
    if numeric: pieces.append(('numeric',StandardScaler() if linear else 'passthrough',numeric))
    if spec.get('spline'):
        # Quantile knots learned using the fit fold only. No interaction terms.
        spline=Pipeline([('basis',SplineTransformer(n_knots=5,degree=3,knots='quantile',include_bias=False,extrapolation='linear')),('scale',StandardScaler())])
        pieces.append(('bmi_spline',spline,['BMI']))
    ords=[c for c in domains if c in cols]
    if ords: pieces.append(('ordinal',OneHotEncoder(categories=[domains[c] for c in ords],drop='first',handle_unknown='error',sparse_output=False) if linear else 'passthrough',ords))
    noms=[c for c in nominal_domains if c in cols]
    if noms: pieces.append(('nominal',OneHotEncoder(categories=[nominal_domains[c] for c in noms],drop='first',handle_unknown='error',sparse_output=False),noms))
    rest=[c for c in cols if c not in numeric+ords+noms and not(c=='BMI' and spec.get('spline'))]
    if rest:pieces.append(('binary','passthrough',rest))
    return ColumnTransformer(pieces,remainder='drop')

protocol=dict(project_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
    source_sha256=digest(source),manifest_sha256=digest(INPUT/'split_manifest.csv'),seed=42,
    train_rows=len(df),train_positive=int(y.sum()),unique_train_rows=int(unique.sum()),
    validation='Existing five group-stratified Train folds; Test excluded from fitting, scoring and selection',
    caveat='EDA and hypotheses were informed by all Train; these are development checks, not independent confirmation; no nested selection or significance claim',
    training='keep duplicates only; no resampling; fold-specific balanced class weights; original ordinals one-hot for LR and ordered integers for XGB; nominal derived states one-hot for both',
    threshold='probability > 0.5',primary_metric='Average precision; F1 at fixed 0.5 is secondary; paired delta uses identical validation folds',
    dedup_sensitivity='Validation only: one occurrence per original 21 features plus target; training remains keep duplicates',
    models={'LR':dict(C=1.0,solver='lbfgs',max_iter=1500,class_weight='balanced',random_state=42),
            'XGB':dict(n_estimators=100,max_depth=6,learning_rate=0.1,n_jobs=4,random_state=42,eval_metric='logloss',tree_method='hist',scale_pos_weight='fold n0/n1')},
    software=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,sklearn=sklearn.__version__,xgboost=xgboost.__version__),
    experiments=specs)
(OUT/'protocol.json').write_text(json.dumps(protocol,ensure_ascii=False,indent=2),encoding='utf-8')
counts=[]
for fold in range(5):
    tr=folds!=fold;va=~tr
    assert not set(group_ids[tr])&set(group_ids[va])
    counts.append(dict(fold=fold,fit_rows=int(tr.sum()),fit_positive=int(y[tr].sum()),validation_rows=int(va.sum()),validation_positive=int(y[va].sum()),unique_validation=int((va&unique).sum())))
pd.DataFrame(counts).to_csv(OUT/'fold_counts.csv',index=False)
metrics_path=OUT/'fold_metrics.csv'
rows=pd.read_csv(metrics_path).to_dict('records') if metrics_path.exists() else []
done={(r['Experiment'],r['Model'],int(r['Fold'])) for r in rows}
started=time.monotonic()
for spec in specs:
    for model_name in ['LR','XGB']:
        oof=np.full(len(df),np.nan);dimensions=[]
        save_path=OUT/(spec['key']+'__'+model_name+'__oof.npz')
        if save_path.exists() and all((spec['key'],model_name,f) in done for f in range(5)):continue
        for fold in range(5):
            tr=folds!=fold;va=~tr
            start=time.monotonic()
            if model_name=='LR':model=LogisticRegression(**protocol['models']['LR'])
            else:
                params=protocol['models']['XGB'].copy();params['scale_pos_weight']=float((y[tr]==0).sum()/y[tr].sum())
                model=XGBClassifier(**params)
            pipe=Pipeline([('preprocess',preprocessor(spec,model_name=='LR')),('model',model)])
            with warnings.catch_warnings(record=True) as caught,threadpool_limits(limits=4):
                warnings.simplefilter('always',ConvergenceWarning)
                pipe.fit(df.loc[tr,spec['columns']],y[tr])
                prob=pipe.predict_proba(df.loc[va,spec['columns']])[:,1]
            assert np.isfinite(prob).all()
            oof[va]=prob
            dim=pipe.named_steps['preprocess'].transform(df.loc[va,spec['columns']].iloc[:1]).shape[1]
            dimensions.append(dim)
            masks={'all':np.ones(len(prob),dtype=bool),'unique':unique[va]}
            result=dict(Experiment=spec['key'],Label=spec['label'],Kind=spec['kind'],Model=model_name,Fold=fold,InputColumns=len(spec['columns']),EncodedColumns=dim,FitSeconds=time.monotonic()-start,Warnings=' | '.join(str(w.message) for w in caught))
            for view,mask in masks.items():
                a=y[va][mask];p=prob[mask];pred=(p>0.5).astype(int)
                for name,val in dict(AP=average_precision_score(a,p),AUC=roc_auc_score(a,p),F1=f1_score(a,pred),Precision=precision_score(a,pred,zero_division=0),Recall=recall_score(a,pred),Accuracy=accuracy_score(a,pred)).items():result[name+('_unique' if view=='unique' else '')]=val
            rows=[r for r in rows if not(r['Experiment']==spec['key'] and r['Model']==model_name and int(r['Fold'])==fold)]
            rows.append(result)
            pd.DataFrame(rows).to_csv(metrics_path,index=False,encoding='utf-8-sig')
            print(f"[{len(rows):03}/280] {spec['key']} {model_name} fold{fold}: AP={result['AP']:.4f} F1={result['F1']:.4f} time={result['FitSeconds']:.1f}s",flush=True)
        assert np.isfinite(oof).all()
        np.savez_compressed(save_path,row_id=ids,y=y,fold=folds,probability=oof,unique=unique)

metrics=pd.DataFrame(rows)
assert len(metrics)==280 and not metrics.duplicated(['Experiment','Model','Fold']).any()
baseline=metrics[metrics.Experiment=='full21'].set_index(['Model','Fold'])
for metric in ['AP','F1','Recall','Precision','AP_unique','F1_unique']:
    metrics['Delta_'+metric]=[getattr(r,metric)-baseline.loc[(r.Model,r.Fold),metric] for r in metrics.itertuples()]
metrics.to_csv(metrics_path,index=False,encoding='utf-8-sig')
summary=[]
for (exp,model),g in metrics.groupby(['Experiment','Model'],sort=False):
    row=dict(Experiment=exp,Label=g.Label.iloc[0],Kind=g.Kind.iloc[0],Model=model,InputColumns=int(g.InputColumns.iloc[0]),EncodedColumns=int(g.EncodedColumns.iloc[0]),FitSeconds=float(g.FitSeconds.sum()))
    for metric in ['AP','AUC','F1','Precision','Recall','Accuracy','AP_unique','F1_unique','Delta_AP','Delta_F1','Delta_AP_unique','Delta_F1_unique']:
        row[metric+'_mean']=float(g[metric].mean());row[metric+'_std']=float(g[metric].std(ddof=1))
    row['AP_wins_vs21']=int((g.Delta_AP>0).sum());row['F1_wins_vs21']=int((g.Delta_F1>0).sum())
    summary.append(row)
pd.DataFrame(summary).to_csv(OUT/'summary.csv',index=False,encoding='utf-8-sig')
after={p:digest(ROOT/p) for p in initial}
assert initial==after,'Project content changed during experiments'
(OUT/'source_hashes_after.json').write_text(json.dumps(after,indent=2),encoding='utf-8')
report=dict(status='passed',experiments=28,models=2,folds=5,fits=280,metrics_rows=len(metrics),warnings_count=int(metrics.Warnings.fillna('').str.len().gt(0).sum()),project_files_unchanged=True,tracked_files_checked=len(initial),test_scored=False,elapsed_seconds=time.monotonic()-started)
(OUT/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2),flush=True)
