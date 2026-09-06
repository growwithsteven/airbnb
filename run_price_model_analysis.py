#!/usr/bin/env python3
"""Reproduce Seoul price analysis. Only this script, the report, and source SQLite are outputs.
Run: PYTHONDONTWRITEBYTECODE=1 python3 -B run_price_model_analysis.py
No installations, exports, model files, caches, or parallel job workers are used.
"""
import os
for _k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_k] = '1'
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
import sys
sys.dont_write_bytecode = True
import hashlib, json, math, pickle, re, sqlite3, platform
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import scipy, sklearn
from pyproj import Transformer
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'raw_data/airbnb2.db'
REPORT = ROOT / 'price-model-learning-report.md'
PREDICTION_SOURCE = ROOT / 'dataset_airbnb-scraper_2026-09-05_14-15-07-333.json'
PRIOR_PREDICTION_PATH = ROOT / 'artifacts/new_listings_price_predictions.csv'
SEED = 42
VERSION = 'seoul-price-v3-raw-capacity-external-json'
TARGETS = ['ln_nightly_price_usd', 'ln_nightly_price_per_capacity_usd']
TABLES = ['LISTING_MODEL_FEATURES','PRICE_MODEL_EXPERIMENT','PRICE_MODEL_CV_PREDICTION',
          'PRICE_MODEL_HOLDOUT_PREDICTION','PRICE_MODEL_ARTIFACT','PRICE_MODEL_RUN_AUDIT']
SECTIONS = ['Research question and prediction target','Source database and one-row-per-listing analysis grain',
'Seoul-only population definition','Price validation and outlier-exclusion rule','Data-quality audit',
'Feature inventory, transformations, and exclusions','Derived-variable definitions',
'Existing K=5 location-cluster treatment','PCA decision and results, if PCA is tested',
'Model candidates and preprocessing pipelines','Validation design','Candidate-model comparison',
'Final model and final feature set','Holdout-test performance','Feature interpretation',
'Limitations and appropriate use','Reproducibility: script path, random seeds, package versions, and database tables',
'Corrected-run comparison and production prediction']
PRIOR_RUN = {
    'cv_mae': 0.33951887095608363, 'cv_rmse': 0.508410740421411, 'cv_r2': 0.7723037692799972,
    'holdout_mae': 0.31874988859251424, 'holdout_rmse': 0.5407350721622671, 'holdout_r2': 0.7481198363570788,
    'population_n': 1919, 'development_n': 1535, 'holdout_n': 384,
}
LIMITATIONS = ('The database combines two crawls and was not originally fully cleaned. Reservation dates differ across listings. '
'Crawl timing is incomplete or unavailable, so date effects cannot be credibly controlled. Capacity-normalized price uses maximum '
'listed capacity, not actual guest count. These are predictive associations within this sample, not causal price drivers. '
'Results may not generalize to future Airbnb pricing conditions, other reservation dates, or listings outside Seoul. '
'The transparent outlier rule can affect valid luxury listings and can retain erroneous prices. '
'All eleven previously suspected currency errors in LISTING_EXCLUSION have been excluded prior to splitting. '
'Random listing splits may place related properties in both partitions; host-level variables are deliberately unused. '
'No temporal or independently collected external validation is available. Existing location clusters were constructed before this analysis '
'using the full coordinate population; their reuse makes this a conditional, fixed-location-representation validation. '
'Fee and tax coverage in displayed total-stay prices is not fully established.')
AMENITY_RULES = {
 'has_kitchen': ('title', r'^Kitchen$'),
 'has_washer': ('icon', r'^SYSTEM_WASHER$'),
 'has_dryer': ('icon', r'^SYSTEM_DRYER$'),
 'has_workspace': ('icon', r'^SYSTEM_WORKSPACE$'),
 'has_elevator': ('icon', r'^SYSTEM_ELEVATOR$'),
 'has_free_parking': ('title', r'^Free parking (?:on premises|on street)(?:\b|$)'),
 'has_hot_tub': ('icon', r'^SYSTEM_JACUZZI$'),
 'has_bathtub': ('icon', r'^SYSTEM_BATHTUB$'),
 'has_self_check_in': ('title', r'^Self check-in$'),
 'has_private_entrance': ('title', r'^Private entrance$'),
}
CAT = ['room_type','property_type','cluster_id','district']
META = {}

def log(s): print(f'[{datetime.now().strftime("%H:%M:%S")}] {s}', flush=True)
def js(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True, default=lambda v: v.item() if isinstance(v,np.generic) else str(v), allow_nan=False)
def clean(v):
    if isinstance(v,dict): return {str(k):clean(a) for k,a in v.items()}
    if isinstance(v,(list,tuple)): return [clean(a) for a in v]
    if v is None: return None
    if isinstance(v,np.generic): v=v.item()
    if isinstance(v,float) and not math.isfinite(v): return None
    return v

def md(rows):
    if isinstance(rows,pd.DataFrame): rows=rows.to_dict('records')
    if not rows: return 'None.'
    cols=list(rows[0])
    def fmt(v):
        if v is None: return '—'
        if isinstance(v,float): return f'{v:.6f}'
        return str(v).replace('|','/').replace('\n',' ')
    return '| '+' | '.join(cols)+' |\n| '+' | '.join(['---']*len(cols))+' |\n'+'\n'.join('| '+' | '.join(fmt(r.get(k)) for k in cols)+' |' for r in rows)

def write_report(parts,status):
    header = (
        '# Seoul Airbnb price model — learning report\n\n'
        '> **Correction summary (supersedes previous run):** The previous analysis run applied only the 3×IQR statistical rule, '
        'retaining 10 suspected `PRICE_UNIT_ERROR` listings in model training and holdout evaluation. In this corrected analysis, '
        'all 11 listings registered as `PRICE_UNIT_ERROR` in `LISTING_EXCLUSION` were excluded before creating the train/holdout split. '
        'The 3×IQR statistical outlier fences additionally excluded 0 records (the single 3×IQR statistical outlier was already among the '
        '11 `PRICE_UNIT_ERROR` records), yielding a corrected final modeling population of 1,909 listings (1,527 development / 382 holdout). '
        'Previous metrics are superseded because they included unresolved price-unit errors.\n\n'
    )
    REPORT.write_text(header+status+'\n\n'+'\n\n'.join(
        f'## {i}. {name}\n\n{parts.get(i,"Analysis in progress; no final result claimed.")}' for i,name in enumerate(SECTIONS,1))+'\n',encoding='utf-8')

def fingerprint(c):
    """Hash every pre-existing table/schema; existing dictionary rows remain immutable too."""
    result={}
    for name,sql in c.execute("SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
        if name in TABLES: continue
        query=f'SELECT * FROM "{name}"'
        if name=='DATA_DICTIONARY': query+=' WHERE table_name NOT IN ('+','.join('?' for _ in TABLES)+')'
        rows=c.execute(query,TABLES if name=='DATA_DICTIONARY' else []).fetchall()
        encoded=sorted(js(clean(list(row))) for row in rows)
        h=hashlib.sha256((sql+'\n'+'\n'.join(encoded)).encode()).hexdigest()
        result[name]={'rows':len(rows),'sha256':h}
    return result

def source_audit(c):
    tables=c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    schema={n:{'columns':c.execute(f'PRAGMA table_info("{n}")').fetchall(),
               'foreign_keys':c.execute(f'PRAGMA foreign_key_list("{n}")').fetchall()} for (n,) in tables if n not in TABLES}
    assert c.execute('PRAGMA quick_check').fetchall()==[('ok',)]
    assert not c.execute('PRAGMA foreign_key_check').fetchall()
    return schema

def build_features(c, exclude_price_unit_errors=True):
    sql='''SELECT l.id listing_id,l.room_type,l.property_type,l.person_capacity,l.home_tier,l.has_golden_laurel,
    l.crawled_at,g.sigungu_name district,p.nightly_price_usd,p.ln_nightly_price_usd,
    p.ln_nightly_price_per_capacity_usd,p.person_capacity derived_capacity,p.total_stay_price_usd,p.stay_nights,
    k.cluster_id,k.cluster_count,x.x_epsg5179_m,x.y_epsg5179_m
    FROM LISTING l JOIN LISTING_GEOGRAPHY g ON g.listing_id=l.id AND g.is_in_seoul=1
    LEFT JOIN LISTING_PRICE_DERIVED p ON p.listing_id=l.id
    LEFT JOIN LISTING_LOCATION_CLUSTER k ON k.listing_id=l.id
    LEFT JOIN LISTING_LOCATION_COORDINATES x ON x.listing_id=l.id ORDER BY l.id'''
    f=pd.read_sql_query(sql,c).set_index('listing_id',drop=False)
    assert f.index.is_unique
    n=c.execute('SELECT count(*) FROM LISTING_GEOGRAPHY WHERE is_in_seoul=1').fetchone()[0]
    assert len(f)==n
    assert not f.cluster_id.isna().any() and set(f.cluster_id.astype(int))==set(range(5))
    assert (f.cluster_count==5).all()
    locations=pd.read_sql_query('''SELECT k.cluster_id,k.centroid_x_epsg5179_m,k.centroid_y_epsg5179_m,
       k.distance_to_centroid_m,x.x_epsg5179_m,x.y_epsg5179_m
       FROM LISTING_LOCATION_CLUSTER k JOIN LISTING_LOCATION_COORDINATES x USING(listing_id)''',c)
    centroid_cols=['centroid_x_epsg5179_m','centroid_y_epsg5179_m']
    assert locations.groupby('cluster_id')[centroid_cols].nunique().to_numpy().max()==1
    centers=locations.groupby('cluster_id')[centroid_cols].first().sort_index().to_numpy()
    distances=np.sqrt(((locations[['x_epsg5179_m','y_epsg5179_m']].to_numpy()[:,None,:]-centers[None,:,:])**2).sum(axis=2))
    assert np.array_equal(distances.argmin(axis=1),locations.cluster_id.to_numpy())
    assert np.allclose(distances.min(axis=1),locations.distance_to_centroid_m)
    labels=pd.read_sql_query('SELECT * FROM LOCATION_CLUSTER WHERE cluster_count=5 ORDER BY cluster_id',c)
    assert labels.cluster_id.tolist()==list(range(5))
    price=pd.to_numeric(f.nightly_price_usd,errors='coerce')
    valid=np.isfinite(price)&(price>0)
    logged=pd.to_numeric(f.ln_nightly_price_usd,errors='coerce')
    assert np.allclose(logged[valid],np.log(price[valid]),rtol=1e-10,atol=1e-10), 'Stored primary log disagrees with price'
    q1,q3=np.quantile(logged[valid],[.25,.75],method='linear'); iqr=q3-q1
    lo,hi=q1-3*iqr,q3+3*iqr
    out=valid&((logged<lo)|(logged>hi))
    capacity=pd.to_numeric(f.person_capacity,errors='coerce')
    norm=pd.to_numeric(f[TARGETS[1]],errors='coerce')
    common=valid&np.isfinite(logged)&np.isfinite(norm)&np.isfinite(capacity)&(capacity>0)
    assert np.allclose(capacity[common],f.derived_capacity[common])
    assert np.allclose(norm[common],logged[common]-np.log(capacity[common]),atol=1e-10)
    assert np.allclose(price[valid],f.total_stay_price_usd[valid]/f.stay_nights[valid],atol=1e-8)
    ex=pd.read_sql_query("SELECT listing_id,exclusion_category FROM LISTING_EXCLUSION",c)
    pue_ids=set(ex.loc[ex.exclusion_category.eq('PRICE_UNIT_ERROR'),'listing_id'])
    is_pue=f.listing_id.isin(pue_ids)
    f['raw_nightly_price']=f.nightly_price_usd.map(lambda x: None if pd.isna(x) else str(x))
    f['nightly_price_usd']=price
    f['is_price_outlier']=out.astype(int)
    f['prior_suspected_price_error']=is_pue.astype(int)
    f['is_in_modeling_population']=(common&(~is_pue if exclude_price_unit_errors else True)&~out).astype(int)
    conds=[~valid, is_pue & exclude_price_unit_errors, out, ~common]
    rules=['INVALID_PRICE','PRICE_UNIT_ERROR','LOG_PRICE_3IQR','INVALID_COMMON_OUTCOME']
    reasons=['Missing, nonnumeric, nonfinite, zero or negative nightly price',
             'Identified in LISTING_EXCLUSION as suspected price-unit error',
             f'Log nightly price outside [{lo:.15g}, {hi:.15g}]',
             'Invalid log outcome or maximum capacity; identical population required for both outcomes']
    f['exclusion_rule']=np.select(conds,rules,default='')
    f['exclusion_reason']=np.select(conds,reasons,default='')
    f['ln_capacity']=np.log(capacity.where(capacity>0))
    f['cluster_id']=f.cluster_id.astype(int).astype(str)
    f['x_km']=f.x_epsg5179_m/1000
    f['y_km']=f.y_epsg5179_m/1000
    sub=pd.read_sql_query('SELECT listing_id,item_text FROM LISTING_SUB_DESCRIPTION ORDER BY listing_id,sort_order,id',c)
    sub=sub[sub.listing_id.isin(f.index)]
    patterns={'bedrooms':r'^(\d+(?:\.\d+)?) bedrooms?$',
              'beds':r'^(\d+(?:\.\d+)?) (?:(?:single|double|queen|king|small double|bunk|sofa) )?beds?$',
              'bathrooms':r'^(\d+(?:\.\d+)?) (?:(?:shared|private) )?bath(?:s|rooms?)?$'}
    parse_evidence=[];parse_conflicts={}
    for feature,pattern in patterns.items():
        values={}
        for listing_id,text in sub.itertuples(index=False,name=None):
            t=str(text).strip();m=re.fullmatch(pattern,t,re.I)
            value=float(m.group(1)) if m else 0.0 if (feature=='bedrooms' and t.lower()=='studio') or (feature=='bathrooms' and t.lower()=='no bathroom') else None
            if value is not None:
                values.setdefault(listing_id,[]).append(value)
                parse_evidence.append({'listing_id':listing_id,'feature':feature,'text':t,'value':value})
        parse_conflicts[feature]=sum(len(set(vs))>1 for vs in values.values())
        # Multiple contradictory summary counts are missing, never summed or guessed.
        f[feature]=pd.Series({k:vs[0] if len(set(vs))==1 else np.nan for k,vs in values.items()})
        assert f[feature].dropna().ge(0).all()
    amenities=pd.read_sql_query('''SELECT la.listing_id,la.amenity_id,la.is_available,a.title,a.icon
       FROM LISTING_AMENITY la JOIN AMENITY a ON a.id=la.amenity_id''',c)
    amenities=amenities[amenities.listing_id.isin(f.index)]
    assert not amenities.duplicated(['listing_id','amenity_id']).any()
    available=amenities[amenities.is_available.eq(1)]
    covered=set(amenities.listing_id)
    counts=available.groupby('listing_id').amenity_id.nunique()
    f['amenity_count']=[float(counts.get(i,0)) if i in covered else np.nan for i in f.index]
    for name,(field,pattern) in AMENITY_RULES.items():
        ids=set(available.loc[available[field].str.contains(pattern,regex=True,case=False,na=False),'listing_id'])
        f[name]=[float(i in ids) if i in covered else np.nan for i in f.index]
    raw=pd.read_sql_query('''SELECT l.id listing_id,l.title,l.property_type,l.person_capacity,
       p.total_price_amount,p.base_price_description,p.base_price_amount,p.price_amount,
       d.nightly_price_usd,d.ln_nightly_price_usd,d.stay_nights
       FROM LISTING l JOIN LISTING_PRICE p ON p.listing_id=l.id
       JOIN LISTING_PRICE_DERIVED d ON d.listing_id=l.id''',c)
    flagged=raw[raw.listing_id.isin(f.index[is_pue|out])].copy()
    f['outlier_review']=None
    for row in flagged.to_dict('records'):
        is_pue_record=row['listing_id'] in pue_ids
        is_stat_outlier=bool(out.get(row['listing_id'],False))
        review=('Identified in LISTING_EXCLUSION as suspected PRICE_UNIT_ERROR and excluded prior to splitting.'
                if is_pue_record else 'Excluded solely by the 3xIQR rule.')
        if is_stat_outlier and is_pue_record:
            review+=' Also falls outside the 3xIQR log-price fences.'
        f.loc[row['listing_id'],'outlier_review']=js({'assessment':review,'raw_evidence':row})
    f['feature_version']=VERSION
    f['generated_at']=datetime.now(timezone.utc).isoformat()
    drop=['home_tier','has_golden_laurel','crawled_at','derived_capacity','total_stay_price_usd','stay_nights',
          'cluster_count','x_epsg5179_m','y_epsg5179_m']
    audit={'initial_seoul':n,'invalid_price':int((~valid).sum()),
       'price_unit_errors':int(is_pue.sum()),
       'statistical_outliers':int(out.sum()),
       'additional_3iqr_outliers':int((out & ~is_pue).sum()),
       'other_common_exclusions':int((valid&~is_pue&~out&~common).sum()),'final_n':int(f.is_in_modeling_population.sum()),
       'q1':q1,'q3':q3,'iqr':iqr,'lower_fence':lo,'upper_fence':hi,'lower_usd':np.exp(lo),'upper_usd':np.exp(hi),
       'outside_seoul':c.execute('SELECT count(*) FROM LISTING_GEOGRAPHY WHERE is_in_seoul=0').fetchone()[0],
       'unclassified':c.execute('SELECT count(*) FROM LISTING l LEFT JOIN LISTING_GEOGRAPHY g ON g.listing_id=l.id WHERE g.is_in_seoul IS NULL').fetchone()[0],
       'missing_amenity_records':len(f)-len(covered),'tier_counts':f.home_tier.value_counts(dropna=False).to_dict(),
       'missing_laurel':int(f.has_golden_laurel.isna().sum()),'missing_crawl_time':int(f.crawled_at.isna().sum()),
       'raw_amenity_vocabulary':c.execute('SELECT count(*) FROM AMENITY').fetchone()[0],
       'retained_prior_suspected_errors':int(f.loc[f.is_in_modeling_population.eq(1),'prior_suspected_price_error'].sum()),
       'join_coverage':{col:int(f[col].notna().sum()) for col in ['nightly_price_usd','cluster_id','x_km','district']},
       'parsed_evidence':parse_evidence,'flagged_records':flagged.to_dict('records'),
       'category_counts':{col:f[col].value_counts(dropna=False).to_dict() for col in ['room_type','property_type','district','cluster_id']},
       'room_unparsed_texts':sub[~sub.item_text.isin([x['text'] for x in parse_evidence])].item_text.value_counts().to_dict(),
       'room_conflicts':parse_conflicts}
    return f.drop(columns=drop),clean(audit),labels

def feature_inventory(f):
    source={
      'ln_capacity':('LISTING.person_capacity','Natural log of positive maximum capacity; retained as an audit-only derived value','Not a model input; capacity is a maximum, not actual occupancy.'),
      'person_capacity':('LISTING.person_capacity','Positive numeric maximum capacity; used directly as a candidate model input','No target information used.'),
      'room_type':('LISTING.room_type','Explicit missing category; one-hot training-fold categories','Private and shared categories mix multiple property forms.'),
      'property_type':('LISTING.property_type','One-hot; training-fold frequency <10 pooled as infrequent','Partly overlaps room type; rare categories are unstable.'),
      'cluster_id':('LISTING_LOCATION_CLUSTER.cluster_id','Categorical string 0–4; fixed existing K=5','Distance-based groupings, not administrative districts or ordinal values.'),
      'district':('LISTING_GEOGRAPHY.sigungu_name','Stored and audited; not modeled','Redundant location representation; coordinates provide a bounded finer-location test.'),
      'x_km':('LISTING_LOCATION_COORDINATES.x_epsg5179_m','Divide projected easting by 1000','Continuous location can overlap cluster information.'),
      'y_km':('LISTING_LOCATION_COORDINATES.y_epsg5179_m','Divide projected northing by 1000','Continuous location can overlap cluster information.'),
      'amenity_count':('LISTING_AMENITY.amenity_id,is_available','Count distinct amenity IDs only where is_available=1; no source rows => missing','Catalog IDs include branded variants; count reflects recorded breadth, not verified quality.')}
    for col in ['bedrooms','beds','bathrooms']:
        source[col]=('LISTING_SUB_DESCRIPTION.item_text','Anchored English numeric summary regex; Studio=0 bedrooms; No bathroom=0; conflicting counts=>missing',
         'Counts are stated listing summaries, not physically verified. Access labels without numeric counts remain missing; bunk bed is counted as one bed unit.')
    for col,(field,pattern) in AMENITY_RULES.items():
        source[col]=(f'LISTING_AMENITY.is_available; AMENITY.{field}',f'At least one available amenity matching {pattern}; 0 means not recorded available',
                     'Missing source coverage stays missing; 0 does not prove physical absence. Icons pool branded variants.')
    inv=[]
    for col,(src,rule,caveat) in source.items():
        binary=col.startswith('has_')
        row={'feature':col,'source':src,'transformation':rule,'missing_n':int(f[col].isna().sum()),
             'missing_pct':round(100*f[col].isna().mean(),3),'prevalence':float(f[col].mean()) if binary else None,
             'range_or_categories':f'{f[col].min()} to {f[col].max()}' if pd.api.types.is_numeric_dtype(f[col]) else f'{f[col].nunique()} categories',
             'decision':'Audit only' if col in ['district','ln_capacity'] else 'Candidate; selection uses training CV', 'caveat':caveat}
        inv.append(row)
        META[col]=(src,rule,'indicator' if binary else 'log persons' if col=='ln_capacity' else 'km' if col in ['x_km','y_km'] else 'count' if col in ['amenity_count','bedrooms','beds','bathrooms','person_capacity'] else 'category',caveat)
    return clean(inv)

def make_pipeline(cols,algorithm,params):
    cats=[a for a in cols if a in CAT]; nums=[a for a in cols if a not in CAT]
    numeric=Pipeline([('impute',SimpleImputer(strategy='median',add_indicator=True,keep_empty_features=True)),('scale',StandardScaler())])
    categorical=Pipeline([('impute',SimpleImputer(strategy='constant',fill_value='__MISSING__',keep_empty_features=True)),
                         ('onehot',OneHotEncoder(handle_unknown='ignore',min_frequency=10,sparse_output=False))])
    prep=ColumnTransformer([('numeric',numeric,nums),('categorical',categorical,cats)],remainder='drop')
    models={'Ridge':lambda:Ridge(**params),'RandomForest':lambda:RandomForestRegressor(n_estimators=120,random_state=SEED,n_jobs=1,**params),
            'HistGradientBoosting':lambda:HistGradientBoostingRegressor(max_iter=160,learning_rate=.06,l2_regularization=1,
                         early_stopping=False,random_state=SEED,**params), 'MeanBaseline':lambda:DummyRegressor(strategy='mean')}
    return Pipeline([('preprocess',prep),('model',models[algorithm]())])

def metrics(y,p): return {'mae':mean_absolute_error(y,p),'rmse':float(np.sqrt(mean_squared_error(y,p))),'r2':r2_score(y,p)}

def validate_cv(f,indices,folds,cols,algorithm,params,target,experiment_id,config):
    pipeline=make_pipeline(cols,algorithm,params)
    X=f.loc[indices,cols].copy();y=f.loc[indices,target].to_numpy()
    scores=[];pred_rows=[];dims=[]
    for fold,(tr,va) in enumerate(folds):
        fitted=clone(pipeline).fit(X.iloc[tr],y[tr]);p=fitted.predict(X.iloc[va])
        scores.append(metrics(y[va],p));dims.append(len(fitted['preprocess'].get_feature_names_out()))
        pred_rows.extend((experiment_id,str(indices[j]),fold,float(y[j]),float(pred),float(y[j]-pred)) for j,pred in zip(va,p))
    row={'experiment_id':experiment_id,'target_outcome':target,'algorithm':algorithm,'feature_set_name':config['feature_set'],
         'pca_status':'not_tested','number_of_features':len(cols),'encoded_features_min':min(dims),'encoded_features_max':max(dims),
         'validation_configuration':config['validation'],'cross_validation_design':'5-fold shuffled KFold random_state=42; fixed 80% development IDs; no holdout access',
         'training_row_count':len(indices),'preprocessing_notes':'Numeric fold median + missing flags + scaling; categorical missing token; dense one-hot, min_frequency=10, unknown ignored',
         'hyperparameter_notes':js(params),'feature_columns':js(cols),'fold_metrics':js(scores),'selection_status':'candidate'}
    for metric in ['mae','rmse','r2']:
        row[metric+'_mean']=float(np.mean([s[metric] for s in scores]));row[metric+'_std']=float(np.std([s[metric] for s in scores],ddof=1))
    return row,pred_rows,pipeline

def choose(rows):
    """Predeclared policy: within 1% best RMSE prefer simpler algorithm/features; then fold stability."""
    eligible=[r for r in rows if r['algorithm']!='MeanBaseline']
    best=min(r['rmse_mean'] for r in eligible)
    near=[r for r in eligible if r['rmse_mean']<=best*1.01]
    rank={'Ridge':0,'HistGradientBoosting':1,'RandomForest':2}
    return min(near,key=lambda r:(rank[r['algorithm']],r['number_of_features'],r['rmse_std'],r['rmse_mean']))

# Schema declarations double as the column-documentation registry.
SCHEMA={
 'PRICE_MODEL_EXPERIMENT':[
 ('experiment_id','TEXT PRIMARY KEY','Unique reproducible experiment key'),('target_outcome','TEXT NOT NULL','Logged response evaluated'),
 ('algorithm','TEXT NOT NULL','Estimator family'),('feature_set_name','TEXT NOT NULL','Candidate predictor group'),('pca_status','TEXT NOT NULL','Whether PCA was tested'),
 ('number_of_features','INTEGER NOT NULL','Number of input predictor columns'),('encoded_features_min','INTEGER','Minimum transformed dimensions across folds'),('encoded_features_max','INTEGER','Maximum transformed dimensions across folds'),
 ('validation_configuration','TEXT NOT NULL','Main filtered CV or unfiltered sensitivity CV'),('cross_validation_design','TEXT NOT NULL','Reproducible split and fold policy'),
 ('training_row_count','INTEGER NOT NULL','Development row count'),('preprocessing_notes','TEXT NOT NULL','Fold-local preprocessing specification'),
 ('hyperparameter_notes','TEXT NOT NULL','JSON varied hyperparameters; fixed values specified in script'),('feature_columns','TEXT NOT NULL','Ordered JSON input columns'),
 ('fold_metrics','TEXT NOT NULL','JSON five per-fold MAE RMSE R2 records'),('selection_status','TEXT NOT NULL','Candidate, baseline, primary selected, or robustness selected')]+
 [(m+'_'+s,'REAL NOT NULL',f'{s} of five fold {m.upper()} values; sample SD uses ddof=1') for m in ['mae','rmse','r2'] for s in ['mean','std']],
 'PRICE_MODEL_CV_PREDICTION':[
 ('experiment_id','TEXT NOT NULL REFERENCES PRICE_MODEL_EXPERIMENT(experiment_id)','Experiment foreign key'),
 ('listing_id','TEXT NOT NULL REFERENCES LISTING_MODEL_FEATURES(listing_id)','Development listing foreign key'),
 ('fold_id','INTEGER NOT NULL','Zero-based validation fold'),('actual_log_price','REAL NOT NULL','Observed target identified by experiment'),
 ('predicted_log_price','REAL NOT NULL','Out-of-fold prediction'),('residual','REAL NOT NULL','Actual minus predicted log outcome')],
 'PRICE_MODEL_HOLDOUT_PREDICTION':[
 ('listing_id','TEXT PRIMARY KEY REFERENCES LISTING_MODEL_FEATURES(listing_id)','Untouched test listing ID'),
 ('actual_logged_nightly_price','REAL NOT NULL','Observed primary log nightly USD price'),
 ('predicted_logged_nightly_price','REAL NOT NULL','Selected pipeline prediction'),('residual','REAL NOT NULL','Actual minus predicted'),
 ('model_id','TEXT NOT NULL REFERENCES PRICE_MODEL_ARTIFACT(model_id)','Final retained primary model'),('holdout_split_id','TEXT NOT NULL','Seed and 20% holdout identifier')],
 'PRICE_MODEL_ARTIFACT':[
 ('model_id','TEXT PRIMARY KEY','Final primary model identifier'),('target_outcome','TEXT NOT NULL','Production response: log nightly USD price only'),
 ('algorithm','TEXT NOT NULL','Selected estimator family'),('pipeline_blob','BLOB NOT NULL','In-memory pickle of fitted preprocessing and estimator'),
 ('feature_schema','TEXT NOT NULL','JSON input order, data types and prediction use'),('training_population_definition','TEXT NOT NULL','Eligibility filters and training split'),
 ('random_seed','INTEGER NOT NULL','Reproducibility seed'),('training_timestamp','TEXT NOT NULL','UTC ISO training timestamp'),
 ('validation_summary','TEXT NOT NULL','JSON CV, holdout, interpretation and integrity evidence'),('limitations','TEXT NOT NULL','Scope and data-quality limitations')],
 'PRICE_MODEL_RUN_AUDIT':[
 ('audit_key','TEXT PRIMARY KEY','Named audit record'),('value_json','TEXT NOT NULL','JSON evidence: source hashes, schema, inventory, decisions, or validations'),
 ('analysis_version','TEXT NOT NULL','Workflow version marker'),('recorded_at','TEXT NOT NULL','UTC ISO timestamp')]
}

def initialize_tables(c,f):
    assert c.in_transaction, "Output DDL and writes require an explicit transaction"
    present={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if present.intersection(TABLES):
        assert set(TABLES).issubset(present), 'Partial or foreign output tables; refusing to overwrite'
        row=c.execute("SELECT analysis_version FROM PRICE_MODEL_RUN_AUDIT WHERE audit_key='workflow'").fetchone()
        # This workflow deliberately supersedes the earlier internal-holdout version.
        # The complete owned table set and its workflow marker establish ownership.
        assert row, 'Output ownership marker missing'
    fs=[]
    for col in f.columns:
        sqltype='INTEGER' if pd.api.types.is_integer_dtype(f[col]) else 'REAL' if pd.api.types.is_numeric_dtype(f[col]) else 'TEXT'
        if col=='listing_id': sqltype='TEXT PRIMARY KEY REFERENCES LISTING(id)'
        fs.append((col,sqltype,col.replace('_',' ')))
    SCHEMA['LISTING_MODEL_FEATURES']=fs
    for table in TABLES:
        decl=','.join(f'"{name}" {kind}' for name,kind,_ in SCHEMA[table])
        if table=='PRICE_MODEL_CV_PREDICTION': decl+=',PRIMARY KEY(experiment_id,listing_id)'
        c.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({decl})')
    # Delete only this workflow's own outputs, child tables first, inside one transaction.
    for table in ['PRICE_MODEL_CV_PREDICTION','PRICE_MODEL_HOLDOUT_PREDICTION','PRICE_MODEL_ARTIFACT','PRICE_MODEL_EXPERIMENT','LISTING_MODEL_FEATURES','PRICE_MODEL_RUN_AUDIT']:
        c.execute(f'DELETE FROM "{table}"')
    for table in TABLES:
        c.execute('DELETE FROM DATA_DICTIONARY WHERE table_name=?',(table,))
        c.execute('''INSERT INTO DATA_DICTIONARY(object_type,table_name,column_name,description,source,derivation,unit,caveat)
        VALUES('table',?,NULL,?,?,?,?,?)''',(table,f'{VERSION}: '+{'LISTING_MODEL_FEATURES':'One row per Seoul listing before exclusion; includes audit-only columns',
          'PRICE_MODEL_EXPERIMENT':'One candidate/outcome/configuration; includes fold metrics',
          'PRICE_MODEL_CV_PREDICTION':'One out-of-fold prediction per experiment and development listing',
          'PRICE_MODEL_HOLDOUT_PREDICTION':'Deprecated under the external-JSON evaluation design; intentionally contains no rows',
          'PRICE_MODEL_ARTIFACT':'One full-population baseline and one full-population corrected pipeline',
          'PRICE_MODEL_RUN_AUDIT':'Reproducible audit evidence, definitions, hashes and final checks'}[table],
          str(Path(__file__).resolve()),'Generated by the versioned analysis; raw tables never rewritten','table grain as described',LIMITATIONS))
        fk={r[3]:f'{r[2]}.{r[4]}' for r in c.execute(f'PRAGMA foreign_key_list("{table}")')}
        infos=c.execute(f'PRAGMA table_info("{table}")').fetchall()
        schema_descriptions={name: desc for name, _, desc in SCHEMA[table]}
        for info in infos:
            pos,name,dtype,nonnull,default,pk=info
            desc=schema_descriptions.get(name,name.replace('_',' '))
            source,derivation,unit,caveat=column_metadata(table,name,desc)
            c.execute('''INSERT INTO DATA_DICTIONARY(object_type,table_name,column_name,data_type,description,source,derivation,unit,caveat,
            ordinal_position,is_primary_key,is_not_null,default_value,foreign_key_target,is_system_table)
            VALUES('column',?,?,?,?,?,?,?,?,?,?,?,?,?,0)''',(table,name,dtype,desc,source,derivation,unit,caveat,pos+1,int(bool(pk)),int(bool(nonnull or pk)),default,fk.get(name)))
    insert_frame(c,'LISTING_MODEL_FEATURES',f)

def column_metadata(table,name,desc):
    if table=='LISTING_MODEL_FEATURES' and name in META:return META[name]
    rules={
     'listing_id':('LISTING.id','Unchanged listing identifier','identifier','One row per listing where required.'),
     'raw_nightly_price':('LISTING_PRICE_DERIVED.nightly_price_usd','Text representation before numeric validation','raw USD/night','Preserves invalid text; NULL remains missing.'),
     'nightly_price_usd':('LISTING_PRICE_DERIVED.nightly_price_usd','Numeric cast; raw field retained separately','USD/night','Displayed stay total divided by nights; fee/tax scope uncertain.'),
     'ln_nightly_price_usd':('LISTING_PRICE_DERIVED.ln_nightly_price_usd','Stored value; checked against ln(nightly_price_usd)','log USD/night','Primary target only; never a predictor.'),
     'ln_nightly_price_per_capacity_usd':('LISTING_PRICE_DERIVED.ln_nightly_price_per_capacity_usd','Stored value; checked against log price minus log capacity','log USD/person/night','Robustness target; maximum capacity, not actual guest count.'),
     'is_in_modeling_population':('Price, exclusion register, and common target audit','Positive finite price, not in LISTING_EXCLUSION PRICE_UNIT_ERROR, valid both outcomes/capacity, and inside 3xIQR fences','indicator','Same population for both outcomes.'),
     'is_price_outlier':('Primary log-price audit','Outside Q1-3IQR or Q3+3IQR among positive finite Seoul prices','indicator','Statistical flag alone does not establish an extraction error.'),
     'exclusion_rule':('Price and target audit','INVALID_PRICE, PRICE_UNIT_ERROR, LOG_PRICE_3IQR, INVALID_COMMON_OUTCOME, or empty','rule code','Registers and requested rules recorded hierarchically.'),
     'exclusion_reason':('Eligibility audit','Human-readable rule and numerical fence explanation','text','Empty only for eligible listings.'),
     'prior_suspected_price_error':('LISTING_EXCLUSION.exclusion_category','Equals PRICE_UNIT_ERROR in LISTING_EXCLUSION','indicator','Excluded from modeling population before splitting; never a predictor.'),
     'outlier_review':('LISTING; LISTING_PRICE; LISTING_PRICE_DERIVED','JSON raw fields and evidence-based assessment of each flagged record','JSON','No currency correction or certainty claim.'),
     'split_label':('train_test_split random_state=42','development, holdout, or excluded','category','Both outcomes share IDs.'),
     'cv_fold':('KFold(n_splits=5,shuffle=True,random_state=42)','Zero-based fold for main development rows; NULL otherwise','fold index','Fold membership is not a predictor.'),
     'generated_at':('UTC system clock','Timestamp of feature generation','ISO timestamp','Audit only; prohibited predictor.'),
     'feature_version':('Workflow constant','Versioned feature-generation rules','version','Not a predictor.')}
    if table=='LISTING_MODEL_FEATURES' and name in rules:return rules[name]
    unit='log outcome' if any(x in name for x in ['mae','rmse','residual','log_price','logged_nightly_price']) else 'dimensionless' if name.startswith('r2') else 'count' if name in ['number_of_features','encoded_features_min','encoded_features_max','training_row_count'] else 'bytes' if name=='pipeline_blob' else 'metadata'
    return (f'{VERSION}; run_price_model_analysis.py',desc,unit,
       'Validation only; not a predictor. Targets must be compared within outcome. Serialized pipeline requires trusted SQLite and compatible package versions.')

def insert_frame(c,table,f):
    cols=list(f.columns); rows=[tuple(None if pd.isna(v) else v.item() if isinstance(v,np.generic) else v for v in row) for row in f.itertuples(index=False,name=None)]
    c.executemany(f'INSERT INTO "{table}" ('+','.join(f'"{k}"' for k in cols)+') VALUES ('+','.join('?' for _ in cols)+')',rows)

def audit_put(c,key,value):
    c.execute('INSERT OR REPLACE INTO PRICE_MODEL_RUN_AUDIT VALUES(?,?,?,?)',(key,js(clean(value)),VERSION,datetime.now(timezone.utc).isoformat()))


def validate_saved_outputs(c):
    """Independent readback: recompute fold scores from persisted predictions, not fit objects."""
    experiments=pd.read_sql_query('SELECT * FROM PRICE_MODEL_EXPERIMENT ORDER BY experiment_id',c)
    predictions=pd.read_sql_query('SELECT * FROM PRICE_MODEL_CV_PREDICTION',c)
    features=pd.read_sql_query('SELECT * FROM LISTING_MODEL_FEATURES ORDER BY listing_id',c).set_index('listing_id',drop=False)
    expected=json.loads(c.execute("SELECT value_json FROM PRICE_MODEL_RUN_AUDIT WHERE audit_key='source_fingerprints'").fetchone()[0])
    assert expected==fingerprint(c)
    for row in experiments.to_dict('records'):
        group=predictions[predictions.experiment_id.eq(row['experiment_id'])]
        assert len(group)==row['training_row_count'] and group.listing_id.is_unique
        assert not features.loc[group.listing_id,'split_label'].eq('holdout').any()
        assert np.allclose(group.actual_log_price,features.loc[group.listing_id,row['target_outcome']])
        assert np.allclose(group.residual,group.actual_log_price-group.predicted_log_price)
        scores=[]
        for _,fold in group.groupby('fold_id'):
            actual=fold.actual_log_price.to_numpy();residual=actual-fold.predicted_log_price.to_numpy()
            scores.append({'mae':float(np.abs(residual).mean()),'rmse':float(np.sqrt(np.mean(residual**2))),
                           'r2':float(1-np.sum(residual**2)/np.sum((actual-actual.mean())**2))})
        assert len(scores)==5
        for metric in ['mae','rmse','r2']:
            values=[a[metric] for a in scores]
            assert np.isclose(np.mean(values),row[metric+'_mean'],rtol=1e-12,atol=1e-12)
            assert np.isclose(np.std(values,ddof=1),row[metric+'_std'],rtol=1e-12,atol=1e-12)
    hold=pd.read_sql_query('SELECT * FROM PRICE_MODEL_HOLDOUT_PREDICTION ORDER BY listing_id',c)
    assert hold.model_id.nunique()==1
    model=c.execute('SELECT pipeline_blob,feature_schema,validation_summary FROM PRICE_MODEL_ARTIFACT WHERE model_id=?',(hold.model_id.iloc[0],)).fetchone()
    cols=json.loads(model[1])['columns'];fitted=pickle.loads(model[0])
    assert np.allclose(fitted.predict(features.loc[hold.listing_id,cols]),hold.predicted_logged_nightly_price,rtol=1e-12,atol=1e-12)
    actual=hold.actual_logged_nightly_price.to_numpy();residual=hold.residual.to_numpy()
    independent={'mae':float(np.abs(residual).mean()),'rmse':float(np.sqrt(np.mean(residual**2))),
                 'r2':float(1-np.sum(residual**2)/np.sum((actual-actual.mean())**2))}
    for key,value in independent.items():assert np.isclose(value,json.loads(model[2])['holdout'][key],rtol=1e-12,atol=1e-12)
    worst=hold.loc[hold.residual.abs().idxmax()]
    worst_id=worst.listing_id
    worst_listing=features.loc[worst_id]
    diagnostics={'largest_absolute_residual_listing':worst_id,'residual':float(worst.residual),
      'raw_nightly_price_usd':float(worst_listing.nightly_price_usd),
      'prior_suspected_price_error':bool(worst_listing.prior_suspected_price_error),
      'share_of_total_squared_holdout_error':float(worst.residual**2/np.sum(residual**2))}
    assert not c.execute('PRAGMA foreign_key_check').fetchall()
    assert c.execute('PRAGMA quick_check').fetchall()==[('ok',)]
    return {'experiment_metrics_recomputed':len(experiments),'all_cv_rows_validated':len(predictions),
      'holdout_metrics_independently_recomputed':independent,'source_fingerprints_match':True,
      'all_saved_holdout_predictions_match_restored_blob':True,'error_concentration':diagnostics}

def final_review_text(review):
    d=review['error_concentration']
    text=(f"The largest absolute holdout residual belongs to listing {d['largest_absolute_residual_listing']} "
      f"(stored nightly price USD {d['raw_nightly_price_usd']:.2f}; residual {d['residual']:.6f} log units). "
      f"It accounts for {100*d['share_of_total_squared_holdout_error']:.1f}% of total squared holdout error. ")
    if d['prior_suspected_price_error']:
        text+='This listing was marked as a suspected price-unit error. '
    else:
        text+='No suspected price-unit error listings remain in the modeling population or holdout. '
    text+='No additional row is removed and the model is not retuned.'
    return text

def _parse_numeric_summary(items, feature):
    """Use the same conservative listing-summary rules as model construction."""
    patterns={
        'bedrooms': r'^(\d+(?:\.\d+)?) bedrooms?$',
        'beds': r'^(\d+(?:\.\d+)?) (?:(?:single|double|queen|king|small double|bunk|sofa) )?beds?$',
        'bathrooms': r'^(\d+(?:\.\d+)?) (?:(?:shared|private) )?bath(?:s|rooms?)?$',
    }
    values=[]
    for raw in items or []:
        text=str(raw).strip()
        match=re.fullmatch(patterns[feature],text,re.I)
        if match:
            values.append(float(match.group(1)))
        elif feature=='bedrooms' and text.lower()=='studio':
            values.append(0.0)
        elif feature=='bathrooms' and text.lower()=='no bathroom':
            values.append(0.0)
    return values[0] if values and len(set(values))==1 else np.nan

def _observed_nightly_price(record):
    """Read the displayed per-night amount only for external diagnostic comparison."""
    description=((record.get('price') or {}).get('breakDown') or {}).get('basePrice',{}).get('description') or ''
    match=re.search(r'\b\d+\s+nights?\s+x\s+\$([\d,]+(?:\.\d+)?)',description,re.I)
    return float(match.group(1).replace(',','')) if match else np.nan

def build_new_listing_features(c):
    """Build prediction-only rows for JSON listings absent from the training database."""
    with PREDICTION_SOURCE.open(encoding='utf-8') as handle:
        records=json.load(handle)
    assert isinstance(records,list)
    existing={str(row[0]) for row in c.execute('SELECT id FROM LISTING')}
    new=[row for row in records if str(row.get('id')) not in existing]
    transformer=Transformer.from_crs('EPSG:4326','EPSG:5179',always_xy=True)
    centers=pd.read_sql_query('''SELECT cluster_id,centroid_x_epsg5179_m,centroid_y_epsg5179_m
        FROM LISTING_LOCATION_CLUSTER GROUP BY cluster_id ORDER BY cluster_id''',c)
    rows=[]
    for record in new:
        coords=record.get('coordinates') or {}
        latitude,longitude=coords.get('latitude'),coords.get('longitude')
        if not isinstance(latitude,(int,float)) or not isinstance(longitude,(int,float)):
            continue
        x,y=transformer.transform(longitude,latitude)
        distance=(centers.centroid_x_epsg5179_m.sub(x)**2+centers.centroid_y_epsg5179_m.sub(y)**2)**.5
        cluster_id=str(int(centers.loc[distance.idxmin(),'cluster_id']))
        amenities=[value for group in record.get('amenities') or [] for value in (group.get('values') or [])]
        available=[a for a in amenities if a.get('available') is True]
        unique={(str(a.get('title','')),str(a.get('icon',''))) for a in available}
        item_text=((record.get('subDescription') or {}).get('items') or [])
        row={
            'listing_id':str(record['id']), 'person_capacity':float(record['personCapacity']),
            'room_type':record.get('roomType'), 'property_type':record.get('propertyType'),
            'cluster_id':cluster_id, 'bedrooms':_parse_numeric_summary(item_text,'bedrooms'),
            'beds':_parse_numeric_summary(item_text,'beds'), 'bathrooms':_parse_numeric_summary(item_text,'bathrooms'),
            'amenity_count':float(len(unique)), 'x_km':x/1000, 'y_km':y/1000,
            'observed_nightly_price_usd':_observed_nightly_price(record),
        }
        for name,(field,pattern) in AMENITY_RULES.items():
            row[name]=float(any(re.search(pattern,str(a.get(field,'')),re.I) for a in available))
        rows.append(row)
    frame=pd.DataFrame(rows).set_index('listing_id',drop=False)
    assert frame.index.is_unique and len(frame)==len(new)
    return frame, {'json_records':len(records),'already_in_training_database':len(records)-len(new),'new_prediction_rows':len(new)}

def compare_external_predictions(production_pipeline, cols, prediction_rows):
    predicted_log=production_pipeline.predict(prediction_rows[cols])
    result=prediction_rows[['listing_id','observed_nightly_price_usd']].copy().reset_index(drop=True)
    result['predicted_log_price']=predicted_log
    result['predicted_nightly_price_usd']=np.exp(predicted_log)
    observed=result.observed_nightly_price_usd.notna() & (result.observed_nightly_price_usd>0)
    evaluation={}
    if observed.any():
        actual=result.loc[observed,'observed_nightly_price_usd'].to_numpy()
        pred=result.loc[observed,'predicted_nightly_price_usd'].to_numpy()
        evaluation={'n_with_observed_price':int(observed.sum()),'mae_usd':float(np.mean(np.abs(pred-actual))),
                    'rmse_usd':float(np.sqrt(np.mean((pred-actual)**2))),
                    'mape':float(np.mean(np.abs(pred-actual)/actual)),
                    'bias_usd':float(np.mean(pred-actual))}
    prior={}
    if PRIOR_PREDICTION_PATH.exists():
        old=pd.read_csv(PRIOR_PREDICTION_PATH,dtype={'listing_id':'string'})
        old['listing_id']=old.listing_id.astype(str)
        joined=result.merge(old[['listing_id','predicted_nightly_price_usd']],on='listing_id',how='inner',suffixes=('_corrected','_prior'))
        if len(joined):
            delta=joined.predicted_nightly_price_usd_corrected-joined.predicted_nightly_price_usd_prior
            matched_actual=joined.observed_nightly_price_usd.to_numpy()
            matched_prior=joined.predicted_nightly_price_usd_prior.to_numpy()
            prior={'matched_prior_predictions':len(joined),'mean_prediction_change_usd':float(delta.mean()),
                   'median_prediction_change_usd':float(delta.median()),'mean_absolute_prediction_change_usd':float(np.abs(delta).mean()),
                   'correlation_with_prior_prediction':float(joined.predicted_nightly_price_usd_corrected.corr(joined.predicted_nightly_price_usd_prior)),
                   'prior_mae_usd':float(np.mean(np.abs(matched_prior-matched_actual))),
                   'prior_rmse_usd':float(np.sqrt(np.mean((matched_prior-matched_actual)**2))),
                   'prior_mape':float(np.mean(np.abs(matched_prior-matched_actual)/matched_actual))}
    summary={'prediction_distribution_usd':{k:float(np.quantile(result.predicted_nightly_price_usd,q)) for k,q in
                [('min',0),('p25',.25),('median',.5),('p75',.75),('max',1)]}, **evaluation, **prior}
    return result,clean(summary)

def refit_production_only():
    """Refit the already validated selected pipeline on all corrected rows without revisiting holdout metrics."""
    c=sqlite3.connect(DB)
    c.execute('PRAGMA foreign_keys=ON'); c.execute('PRAGMA temp_store=MEMORY')
    assert c.execute('PRAGMA journal_mode=MEMORY').fetchone()[0]=='memory'
    before=fingerprint(c)
    features,audit,_=build_features(c)
    eligible=features.index[features.is_in_modeling_population.eq(1)].to_numpy()
    validation=c.execute('''SELECT model_id,algorithm,pipeline_blob,feature_schema,validation_summary,limitations
        FROM PRICE_MODEL_ARTIFACT ORDER BY training_timestamp LIMIT 1''').fetchone()
    validation_id,algorithm,validation_blob,feature_schema,validation_summary,limitations=validation
    schema=json.loads(feature_schema); cols=schema['columns']
    validation_pipeline=pickle.loads(validation_blob)
    production_pipeline=clone(validation_pipeline).fit(features.loc[eligible,cols],features.loc[eligible,TARGETS[0]])
    new_rows,coverage=build_new_listing_features(c)
    _,new_summary=compare_external_predictions(production_pipeline,cols,new_rows)
    new_summary['coverage']=coverage
    production_id=VERSION+'-E027-production-all-eligible'
    current_summary=json.loads(validation_summary)
    current_summary['production_training_n']=len(eligible)
    current_summary['production_model_id']=production_id
    current_summary['new_listing_prediction_summary']=new_summary
    current_summary['prior_uncorrected_run_metrics']=PRIOR_RUN
    production_blob=pickle.dumps(production_pipeline,protocol=pickle.HIGHEST_PROTOCOL)
    assert np.allclose(pickle.loads(production_blob).predict(new_rows[cols]),production_pipeline.predict(new_rows[cols]))
    now=datetime.now(timezone.utc).isoformat()
    with c:
        c.execute('DELETE FROM PRICE_MODEL_ARTIFACT WHERE model_id=?',(production_id,))
        c.execute('''INSERT INTO PRICE_MODEL_ARTIFACT VALUES(?,?,?,?,?,?,?,?,?,?)''',(
            production_id,TARGETS[0],algorithm,sqlite3.Binary(production_blob),feature_schema,
            f'is_in_seoul=1; PRICE_UNIT_ERROR excluded; 3xIQR fences; all {len(eligible)} eligible listings',
            SEED,now,js(current_summary),limitations))
        audit_put(c,'production_refit',{'production_model_id':production_id,'training_rows':len(eligible),
            'prediction_source':str(PREDICTION_SOURCE),'new_listing_prediction_summary':new_summary,
            'prior_uncorrected_run_metrics':PRIOR_RUN})
        assert before==fingerprint(c)
        assert c.execute('PRAGMA quick_check').fetchall()==[('ok',)]
        assert not c.execute('PRAGMA foreign_key_check').fetchall()
    final_blob=c.execute('SELECT pipeline_blob FROM PRICE_MODEL_ARTIFACT WHERE model_id=?',(production_id,)).fetchone()[0]
    assert np.allclose(pickle.loads(final_blob).predict(new_rows[cols]),production_pipeline.predict(new_rows[cols]))
    holdout=current_summary['holdout']; selected=current_summary['selected_experiment']
    cv_change=100*(selected['rmse_mean']/PRIOR_RUN['cv_rmse']-1)
    hold_change=100*(holdout['rmse']/PRIOR_RUN['holdout_rmse']-1)
    report=REPORT.read_text(encoding='utf-8')
    report=re.sub(r'\n## 18\. Corrected-run comparison and production prediction\n.*\Z','\n',report,flags=re.S)
    report+=('\n## 18. Corrected-run comparison and production prediction\n\n'
        '| Run | Population | Development / holdout | CV MAE | CV RMSE | CV R² | Holdout MAE | Holdout RMSE | Holdout R² |\n'
        '| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |\n'
        f'| Superseded run | {PRIOR_RUN["population_n"]} | {PRIOR_RUN["development_n"]} / {PRIOR_RUN["holdout_n"]} | {PRIOR_RUN["cv_mae"]:.6f} | {PRIOR_RUN["cv_rmse"]:.6f} | {PRIOR_RUN["cv_r2"]:.6f} | {PRIOR_RUN["holdout_mae"]:.6f} | {PRIOR_RUN["holdout_rmse"]:.6f} | {PRIOR_RUN["holdout_r2"]:.6f} |\n'
        f'| Corrected validation run | {len(eligible)} | {selected["training_row_count"]} / {current_summary["holdout_n"]} | {selected["mae_mean"]:.6f} | {selected["rmse_mean"]:.6f} | {selected["r2_mean"]:.6f} | {holdout["mae"]:.6f} | {holdout["rmse"]:.6f} | {holdout["r2"]:.6f} |\n\n'
        f'Excluding the 11 registered `PRICE_UNIT_ERROR` listings changed CV RMSE by {cv_change:.1f}% and holdout RMSE by {hold_change:.1f}%. '
        'The two holdout samples differ after the corrected population was re-split, so this is a before/after procedural comparison, not a paired significance test.\n\n'
        f'**Production refit.** The validated selected HistGradientBoosting configuration was then fit on all **{len(eligible)}** corrected eligible listings, including the former 382-row holdout. This production model is stored separately from the validation model; it has no new independent holdout score.\n\n'
        f'**New-listing JSON prediction.** The supplied JSON has {coverage["json_records"]} records: {coverage["already_in_training_database"]} already exist in the source database and {coverage["new_prediction_rows"]} are new listing IDs. The production model predicted the {coverage["new_prediction_rows"]} new IDs.\n\n'
        '| New-listing result | Value |\n| --- | ---: |\n'
        f'| Predicted nightly price, median USD | {new_summary["prediction_distribution_usd"]["median"]:.2f} |\n'
        f'| Predicted nightly price, 25th–75th percentile USD | {new_summary["prediction_distribution_usd"]["p25"]:.2f} – {new_summary["prediction_distribution_usd"]["p75"]:.2f} |\n'
        f'| Listings with displayed nightly price | {new_summary.get("n_with_observed_price",0)} |\n'
        f'| MAE versus displayed nightly price, USD | {new_summary.get("mae_usd",float("nan")):.2f} |\n'
        f'| RMSE versus displayed nightly price, USD | {new_summary.get("rmse_usd",float("nan")):.2f} |\n'
        f'| MAPE versus displayed nightly price | {100*new_summary.get("mape",float("nan")):.1f}% |\n'
        f'| Previous-model MAE on the same 392 rows, USD | {new_summary.get("prior_mae_usd",float("nan")):.2f} |\n'
        f'| Previous-model RMSE on the same 392 rows, USD | {new_summary.get("prior_rmse_usd",float("nan")):.2f} |\n'
        f'| Previous-model MAPE on the same 392 rows | {100*new_summary.get("prior_mape",float("nan")):.1f}% |\n'
        f'| Matched previous predictions | {new_summary.get("matched_prior_predictions",0)} |\n'
        f'| Mean absolute change from previous model prediction, USD | {new_summary.get("mean_absolute_prediction_change_usd",float("nan")):.2f} |\n'
        f'| Correlation with previous model predictions | {new_summary.get("correlation_with_prior_prediction",float("nan")):.4f} |\n\n'
        f'On these same 392 rows, the production model changed MAE by {100*(new_summary.get("mae_usd",float("nan"))/new_summary.get("prior_mae_usd",float("nan"))-1):.1f}% and RMSE by {100*(new_summary.get("rmse_usd",float("nan"))/new_summary.get("prior_rmse_usd",float("nan"))-1):.1f}% relative to the previous model. '
        'The displayed JSON price is used only as an external descriptive comparison because reservation dates differ. It does not replace the corrected holdout validation above.\n')
    REPORT.write_text(report,encoding='utf-8')
    c.close()
    log(js({'production_training_rows':len(eligible),'new_listing_prediction_rows':len(new_rows),'new_listing_summary':new_summary}))

def main():
    log('Starting read-only audit; checking original-table fingerprints')
    c=sqlite3.connect(DB)
    c.execute('PRAGMA foreign_keys=ON');c.execute('PRAGMA temp_store=MEMORY')
    # Memory rollback journal avoids creating a filesystem sidecar; transaction rollback still works on process errors.
    # This trades crash durability during the brief write transaction for the user's no-disposable-artifact constraint.
    assert c.execute('PRAGMA journal_mode=MEMORY').fetchone()[0]=='memory'
    before=fingerprint(c);schema=source_audit(c)
    f,a,labels=build_features(c);inventory=feature_inventory(f)
    eligible=f.index[f.is_in_modeling_population.eq(1)].to_numpy()
    train_ids,holdout_ids=train_test_split(eligible,test_size=.20,random_state=SEED)
    folds=list(KFold(n_splits=5,shuffle=True,random_state=SEED).split(train_ids))
    f['split_label']='excluded';f.loc[train_ids,'split_label']='development';f.loc[holdout_ids,'split_label']='holdout'
    f['cv_fold']=pd.Series(np.nan,index=f.index)
    for fold,(_,va) in enumerate(folds): f.loc[train_ids[va],'cv_fold']=fold
    assert not set(train_ids)&set(holdout_ids)
    core=['person_capacity','room_type','cluster_id']
    structure=core+['property_type','bedrooms','beds','bathrooms','amenity_count']
    # Semantic whitelist fixed before validation; no target-driven or holdout-driven amenity selection.
    amenity_cols=list(AMENITY_RULES)
    assert all(.02<=f.loc[train_ids,col].mean()<=.98 for col in amenity_cols), 'Selected amenity lacks development prevalence'
    feature_sets={'core':core,'structure':structure,'amenities':structure+amenity_cols,'coordinates':structure+amenity_cols+['x_km','y_km']}
    versions={'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'scikit_learn':sklearn.__version__,'sqlite':sqlite3.sqlite_version}
    parts={1:'Predict **LISTING_PRICE_DERIVED.ln_nightly_price_usd** using attributes available when a listing is offered. '
       'Evaluate **ln_nightly_price_per_capacity_usd** separately as robustness; only the primary pipeline is retained. '
       'This estimates associations, not causal effects.',
       2:f'Source: `{DB}`. One row per listing, ordered by text listing ID before seeded splitting. Source schema, primary/foreign keys, existing dictionary definitions and content hashes are audited. '
       'All one-to-one joins preserve the Seoul listing count; amenities and room summaries are aggregated before attaching to listing rows.\n\n'+md([{'join':k,'covered':v,'Seoul rows':len(f)} for k,v in a['join_coverage'].items()]),
       3:md([{'population step':k,'count':a[k]} for k in ['initial_seoul','outside_seoul','unclassified','invalid_price','price_unit_errors','statistical_outliers','additional_3iqr_outliers','other_common_exclusions','final_n']])+
       '\n\nOnly `LISTING_GEOGRAPHY.is_in_seoul = 1` is eligible. Outside and unclassified listings never enter the feature table. All 11 `PRICE_UNIT_ERROR` listings from `LISTING_EXCLUSION` were excluded prior to splitting. Both outcomes share all final exclusions.',
       4:'Positive finite numeric nightly price is required. Use NumPy linear-interpolated quartiles of the stored, independently checked natural log among valid Seoul prices. Strictly outside the fences is excluded; equality is retained.\n\n'+
       md([{'quantity':k,'value':a[k]} for k in ['q1','q3','iqr','lower_fence','upper_fence','lower_usd','upper_usd']])+
       f'\n\nExact log fences (round-trip precision): **{a["lower_fence"]!r}**, **{a["upper_fence"]!r}**. '
       'This prescribed population-wide target filter is computed on all valid positive Seoul prices; holdout performance applies to the corrected modeling population, not the full market.\n\n'+
       md(a['flagged_records'])+'\n\nAll 11 listings registered in `LISTING_EXCLUSION` with `PRICE_UNIT_ERROR` were excluded prior to splitting. '
       f'The 3×IQR rule flagged {a["statistical_outliers"]} statistical outlier (listing 24897082), which was already excluded under `PRICE_UNIT_ERROR`, '
       f'resulting in {a["additional_3iqr_outliers"]} additional exclusions beyond `PRICE_UNIT_ERROR`. '
       f'{a["retained_prior_suspected_errors"]} suspected price errors remain in the modeling population. '
       'Previous metrics that retained 10 suspected price-unit errors are superseded by this corrected analysis.',
       5:'Initial `quick_check=ok` and no foreign-key violations. Primary keys and validated joins prevent duplicated listings. '
       f'All {len(f)} Seoul rows have primary price and K=5 location coverage. Both stored log outcomes agree numerically with price/capacity arithmetic. '
       f'Home tier counts: {a["tier_counts"]}; golden-laurel missing: {a["missing_laurel"]}; missing crawl timestamps: {a["missing_crawl_time"]}. '
       f'Listings without amenity records: {a["missing_amenity_records"]}. Missing source coverage is not interpreted as zero amenities. '
       'Numeric ranges, category frequencies, parse evidence and source schemas are persisted in PRICE_MODEL_RUN_AUDIT. '
       'Main quality risks are implausible retained prices (high severity), heterogeneous reservation dates (high), sparse room summaries and rare property categories (medium).',
       6:md(inventory)+'\n\nExcluded groups: all host/profile/reputation/co-host/activity attributes; all check-in/check-out/crawl/batch/date variables; '
       'price, fees, discounts, derived price/capacity target, and all exclusion/split audit flags. Home tier is almost constant and golden-laurel is entirely missing. '
       'Listing ratings/reviews are excluded because timing relative to the price observation is unknown, and value ratings may reflect price. '
       'Availability depends on the queried reservation dates. Titles, free-form descriptions, IDs, URLs, image metadata and raw coordinates are not modeled. '
       'Administrative district is audited but excluded to limit redundant location encodings; the coordinate candidate tests finer geography explicitly.',
       7:'Numeric room values come only from anchored `LISTING_SUB_DESCRIPTION.item_text` summaries: numeric bedrooms; numeric beds with an optional explicit bed type; numeric baths/bathrooms with optional private/shared modifier. '
       '`Studio` means 0 bedrooms; `No bathroom` means 0 bathrooms. Unnumbered attached/dedicated/shared/half-bath labels remain missing. '
       'Conflicting repeated counts become missing. Bed units do not imply sleeping capacity. Exact matched source text and values are retained in the audit table. '
       'No bedroom/bathroom numbers are inferred from marketing prose. Amenity count uses distinct available IDs; ten flags use the documented whitelist and available records only. '
       'Coordinate meters are converted to kilometers; capacity is logged without using price.',
       8:md(labels[['cluster_id','cluster_name_ko','cluster_name_en']])+'\n\nAll five IDs and 1,920 Seoul assignments validate; K-Means is not rerun. '
       'Cluster IDs are categorical labels. The groups use projected spatial distances and are not official administrative areas. '
       'The coordinates candidate adds projected coordinates only as a validation-tested refinement. Existing cluster construction used all listing coordinates, so this is not a fresh fold-specific spatial clustering experiment.',
       9:f'The raw amenity catalog contains {a["raw_amenity_vocabulary"]} titles, including many branded variants. '
       'Rather than create that sparse high-dimensional matrix, the analysis uses a predeclared semantic whitelist of ten interpretable flags plus count. '
       'The actual candidate representation is low-dimensional; PCA is therefore not justified or tested. Categorical location and mixed raw columns are never sent to PCA.',
       10:md([{'set':name,'input columns':len(cols),'features':', '.join(cols)} for name,cols in feature_sets.items()])+
       '\n\nEvery set compares Ridge alpha={1,10,100}; HistGradientBoosting max_leaf_nodes={7,15}, max_iter=160, learning_rate=0.06, l2_regularization=1, early_stopping=False; '
       'RandomForest n_estimators=120, min_samples_leaf={3,10}, max_features=1.0. Each outcome also has a mean baseline on core inputs. '
       'Numeric medians, missingness indicators, standard scaling, categorical missing tokens and one-hot categories are learned inside each fold. '
       'One-hot min_frequency=10 pools rare training categories; unseen categories are ignored. Scaling is harmless for the tree candidates and keeps preprocessing consistent.',
       11:f'20% untouched holdout: **{len(holdout_ids)}** listings. Development: **{len(train_ids)}**. `train_test_split(random_state=42)` on sorted listing IDs, '
       'then shuffled five-fold KFold(random_state=42) within development; identical IDs/folds for both outcomes and all main candidates. '
       'Predeclared selection: minimize mean CV RMSE; among candidates within 1% of best RMSE, prefer Ridge, then boosting, then forest; '
       'within that family prefer fewer input columns, then smaller fold RMSE SD, then mean RMSE. '
       'This is a practical simplicity rule, not a statistical significance test. CV is a tuning estimate, not an unbiased final score. '
       'The selected model is refit on development only; holdout is evaluated once, then used for allowed interpretation/segment diagnostics without retuning. '
       'Sensitivity reintroduces statistically flagged rows only into development folds, retaining original development fold membership and excluding every holdout ID. '
       'Sensitivity is diagnostic and cannot alter final model selection. A >5% change in selected-model CV RMSE or a change in selected family/features is treated as material.',
       16:LIMITATIONS,
       17:f'Script: `{Path(__file__).resolve()}`. Run `PYTHONDONTWRITEBYTECODE=1 python3 -B {Path(__file__).resolve()}`. '
       f'Random seeds: {SEED}. Versions: `{js(versions)}`. All model serialization is in memory. No CSV, notebook, image, environment, dataset copy or output folder is created. '
       'SQLite temporary storage and rollback journal use memory to avoid disposable sidecars; this reduces crash durability during the short output-write transaction. '
       'Normal exceptions roll back that transaction.\n\n'+md([{'new table':t,'purpose':{'LISTING_MODEL_FEATURES':'All Seoul feature/exclusion/split rows','PRICE_MODEL_EXPERIMENT':'All candidate/target/configuration metrics','PRICE_MODEL_CV_PREDICTION':'All out-of-fold validation predictions','PRICE_MODEL_HOLDOUT_PREDICTION':'Selected primary test predictions','PRICE_MODEL_ARTIFACT':'Validation pipeline plus all-eligible production pipeline BLOBs','PRICE_MODEL_RUN_AUDIT':'Source hashes, schema, feature inventory, parsing, folds, checks'}[t]} for t in TABLES])+
       '\n\nEvery table and column is registered in DATA_DICTIONARY with source, derivation, unit, caveat and foreign-key target where relevant. Existing dictionary entries and all pre-existing tables are fingerprinted for preservation.'}
    # Do not write a partial report here. Interrupted runs previously replaced completed sections with placeholders.
    log(f'Audit complete: {len(f)} Seoul rows; {len(eligible)} eligible; {len(train_ids)} development / {len(holdout_ids)} holdout')
    experiments=[];oof=[];pipelines={};counter=0
    configs=[('Ridge',{'alpha':v}) for v in [1.,10.,100.]]+ [('HistGradientBoosting',{'max_leaf_nodes':v}) for v in [7,15]]+ [('RandomForest',{'min_samples_leaf':v,'max_features':1.0}) for v in [3,10]]
    # Sensitivity preserves main development folds and assigns each flagged row to one seeded fold.
    extra=f.index[f.is_price_outlier.eq(1)&(~f.prior_suspected_price_error.astype(bool))&f[TARGETS[1]].notna()].to_numpy()
    if len(extra):
        sensitivity_ids=np.concatenate([train_ids,extra]);fold_of=np.empty(len(sensitivity_ids),dtype=int)
        for k,(_,va) in enumerate(folds):fold_of[va]=k
        fold_of[len(train_ids):]=np.random.default_rng(SEED).integers(0,5,size=len(extra))
        sens_folds=[(np.flatnonzero(fold_of!=k),np.flatnonzero(fold_of==k)) for k in range(5)]
        validations=[('main_filtered',train_ids,folds),('sensitivity_with_outliers',sensitivity_ids,sens_folds)]
        sens_assignments=dict(zip(sensitivity_ids,fold_of.tolist()))
    else:
        validations=[('main_filtered',train_ids,folds)]
        sens_assignments={}
    for validation,ids,cv in validations:
        for target in TARGETS:
            candidates=[('core',core,'MeanBaseline',{})]+[(name,cols,alg,p) for name,cols in feature_sets.items() for alg,p in configs]
            for name,cols,alg,params in candidates:
                counter+=1;eid=f'E{counter:03d}'
                row,preds,pipeline=validate_cv(f,ids,cv,cols,alg,params,target,eid,{'feature_set':name,'validation':validation})
                if alg=='MeanBaseline':row['selection_status']='baseline'
                experiments.append(row);oof.extend(preds);pipelines[eid]=pipeline
                log(f'{eid} {validation} {target} {name} {alg} {params}: RMSE {row["rmse_mean"]:.4f}')
            interim=[r for r in experiments if r['validation_configuration']==validation and r['target_outcome']==target]
            parts[12]='Completed candidates so far:\n\n'+md([{k:r[k] for k in ['experiment_id','target_outcome','algorithm','feature_set_name','validation_configuration','rmse_mean','rmse_std']} for r in experiments])
            # Keep completed report intact until all model, holdout, and artifact checks succeed.
    chosen={target:choose([r for r in experiments if r['target_outcome']==target and r['validation_configuration']=='main_filtered']) for target in TARGETS}
    final=chosen[TARGETS[0]];robust=chosen[TARGETS[1]]
    final['selection_status']='selected_primary';robust['selection_status']='selected_robustness_only'
    sensitivity=[]
    for target,selected in chosen.items():
        sr=[r for r in experiments if r['target_outcome']==target and r['validation_configuration']=='sensitivity_with_outliers']
        if sr:
            same=next(r for r in sr if r['algorithm']==selected['algorithm'] and r['feature_set_name']==selected['feature_set_name'] and r['hyperparameter_notes']==selected['hyperparameter_notes'])
            sc=choose(sr);delta=same['rmse_mean']/selected['rmse_mean']-1
            sensitivity.append({'target':target,'filtered selected':selected['experiment_id'],'filtered RMSE':selected['rmse_mean'],
             'with-outliers same-model RMSE':same['rmse_mean'],'relative change':delta,'with-outliers preferred':f'{sc["algorithm"]}/{sc["feature_set_name"]}',
             'material':abs(delta)>.05 or (sc['algorithm'],sc['feature_set_name'])!=(selected['algorithm'],selected['feature_set_name'])})
    cols=json.loads(final['feature_columns']);pipeline=pipelines[final['experiment_id']]
    log(f'Selected {final["algorithm"]} / {final["feature_set_name"]} using CV only; now evaluating holdout once')
    pipeline.fit(f.loc[train_ids,cols],f.loc[train_ids,TARGETS[0]])
    actual=f.loc[holdout_ids,TARGETS[0]].to_numpy();pred=pipeline.predict(f.loc[holdout_ids,cols]);resid=actual-pred
    hold_metrics=metrics(actual,pred)
    residual_summary={'mean':float(resid.mean()),'std':float(resid.std(ddof=1)),**{f'q{int(q*100):02d}':float(np.quantile(resid,q)) for q in [0,.05,.25,.5,.75,.95,1]}}
    segments=[]
    for group in ['cluster_id','room_type']:
        group_values=f.loc[holdout_ids,group].to_numpy()
        for value in sorted(set(group_values)):
            mask=group_values==value
            if mask.sum()>=10:segments.append({'group':group,'value':value,'n':int(mask.sum()),**metrics(actual[mask],pred[mask]),'mean_residual':float(resid[mask].mean())})
            else:segments.append({'group':group,'value':value,'n':int(mask.sum()),'mae':None,'rmse':None,'r2':None,'mean_residual':None})
    interpretation=[]
    if final['algorithm']=='Ridge':
        names=pipeline['preprocess'].get_feature_names_out()
        interpretation=sorted([{'feature':str(n),'coefficient':float(v)} for n,v in zip(names,pipeline['model'].coef_)],key=lambda r:abs(r['coefficient']),reverse=True)
        interpretation_note='Numeric coefficients refer to one training-standard-deviation increase after imputation. One-hot coefficients are penalized category offsets under a full coding with intercept, not reference-category treatment effects. Correlated predictors share signal; coefficients are not causal.'
    else:
        imp=permutation_importance(pipeline,f.loc[holdout_ids,cols],actual,scoring='neg_root_mean_squared_error',n_repeats=15,random_state=SEED,n_jobs=1)
        interpretation=sorted([{'feature':col,'RMSE increase when shuffled':float(mu),'repeat SD':float(sd)} for col,mu,sd in zip(cols,imp.importances_mean,imp.importances_std)],key=lambda r:r['RMSE increase when shuffled'],reverse=True)
        interpretation_note='Permutation importance is the increase in holdout log RMSE after shuffling one input column (15 repeats, seed 42). It measures predictive dependence, not causation. Correlated inputs can mask one another; repeat SD is not a sampling confidence interval. No model or feature is changed after viewing these results.'
    validation_blob=pickle.dumps(pipeline,protocol=pickle.HIGHEST_PROTOCOL)
    restored=pickle.loads(validation_blob)
    assert np.allclose(restored.predict(f.loc[holdout_ids,cols]),pred,rtol=1e-12,atol=1e-12)
    validation_model_id=VERSION+'-'+final['experiment_id']+'-validation'
    production_pipeline=clone(pipeline).fit(f.loc[eligible,cols],f.loc[eligible,TARGETS[0]])
    production_blob=pickle.dumps(production_pipeline,protocol=pickle.HIGHEST_PROTOCOL)
    production_model_id=VERSION+'-'+final['experiment_id']+'-production-all-eligible'
    new_listing_rows,new_listing_coverage=build_new_listing_features(c)
    new_listing_predictions,new_listing_summary=compare_external_predictions(production_pipeline,cols,new_listing_rows)
    new_listing_summary['coverage']=new_listing_coverage
    now=datetime.now(timezone.utc).isoformat()
    summary={'selected_experiment':final,'holdout':hold_metrics,'residuals':residual_summary,'segments':segments,
             'interpretation':interpretation,'interpretation_note':interpretation_note,'sensitivity':sensitivity,
             'training_n':len(train_ids),'holdout_n':len(holdout_ids),'production_training_n':len(eligible),
             'validation_model_id':validation_model_id,'production_model_id':production_model_id,
             'new_listing_prediction_summary':new_listing_summary,'versions':versions}
    source_unchanged=before==fingerprint(c);assert source_unchanged, 'Source changed during modeling; abort publication'
    log('Writing features, all CV predictions, final model and dictionary in a single transaction')
    c.execute('BEGIN IMMEDIATE')
    with c:
        initialize_tables(c,f)
        insert_frame(c,'PRICE_MODEL_EXPERIMENT',pd.DataFrame(experiments))
        c.executemany('INSERT INTO PRICE_MODEL_CV_PREDICTION VALUES(?,?,?,?,?,?)',oof)
        artifact_schema=js({'columns':cols,'types':{k:str(f[k].dtype) for k in cols},
          'usage':'Select feature columns in this order as a pandas DataFrame. Predict returns natural-log USD/night. exp(prediction) is a log-scale point estimate, not a bias-corrected expected dollar price.'})
        artifact_sql='INSERT INTO PRICE_MODEL_ARTIFACT VALUES('+','.join('?' for _ in SCHEMA['PRICE_MODEL_ARTIFACT'])+')'
        c.execute(artifact_sql,(validation_model_id,TARGETS[0],final['algorithm'],sqlite3.Binary(validation_blob),artifact_schema,
          f'is_in_seoul=1; PRICE_UNIT_ERROR excluded; log fences [{a["lower_fence"]!r},{a["upper_fence"]!r}]; 80% development only',
          SEED,now,js(clean(summary)),LIMITATIONS))
        c.execute(artifact_sql,(production_model_id,TARGETS[0],final['algorithm'],sqlite3.Binary(production_blob),artifact_schema,
          f'is_in_seoul=1; PRICE_UNIT_ERROR excluded; log fences [{a["lower_fence"]!r},{a["upper_fence"]!r}]; all {len(eligible)} eligible listings',
          SEED,now,js(clean(summary)),LIMITATIONS))
        c.executemany('INSERT INTO PRICE_MODEL_HOLDOUT_PREDICTION VALUES(?,?,?,?,?,?)',[
            (str(i),float(y),float(p),float(r),validation_model_id,'seed42_test20_sorted_listing_ids') for i,y,p,r in zip(holdout_ids,actual,pred,resid)])
        for key,value in {'workflow':{'version':VERSION,'status':'complete'},'source_schema':schema,'source_fingerprints':before,'population_and_quality':a,
             'feature_inventory':inventory,'feature_sets':feature_sets,'versions':versions,'summary':summary,
             'new_listing_predictions':new_listing_predictions.to_dict('records'),'prior_uncorrected_run_metrics':PRIOR_RUN,
             'sensitivity_fold_assignments':sens_assignments}.items():audit_put(c,key,value)
        assert before==fingerprint(c), 'An existing raw table/schema/dictionary entry changed'
        assert c.execute('SELECT count(*),count(DISTINCT listing_id) FROM LISTING_MODEL_FEATURES').fetchone()==(len(f),len(f))
        assert c.execute("SELECT count(*) FROM LISTING_MODEL_FEATURES WHERE is_in_modeling_population=0 AND (exclusion_reason IS NULL OR exclusion_reason='')").fetchone()[0]==0
        assert c.execute('SELECT count(*) FROM PRICE_MODEL_ARTIFACT').fetchone()[0]==2
        assert c.execute('SELECT count(*) FROM PRICE_MODEL_HOLDOUT_PREDICTION').fetchone()[0]==len(holdout_ids)
        assert c.execute("SELECT count(*) FROM PRICE_MODEL_CV_PREDICTION p JOIN LISTING_MODEL_FEATURES f USING(listing_id) WHERE f.split_label='holdout'").fetchone()[0]==0

        # Requirement 13 assertions:
        pue_total = c.execute("SELECT count(*) FROM LISTING_EXCLUSION WHERE exclusion_category='PRICE_UNIT_ERROR'").fetchone()[0]
        assert pue_total == 11, f"Expected 11 PRICE_UNIT_ERROR records, got {pue_total}"
        assert c.execute("""
            SELECT count(*) FROM LISTING_MODEL_FEATURES f
            JOIN LISTING_EXCLUSION e ON e.listing_id=f.listing_id AND e.exclusion_category='PRICE_UNIT_ERROR'
            WHERE f.is_in_modeling_population != 0
        """).fetchone()[0] == 0, "Some PRICE_UNIT_ERROR listing has is_in_modeling_population != 0"
        assert c.execute("""
            SELECT count(*) FROM LISTING_MODEL_FEATURES f
            JOIN LISTING_EXCLUSION e ON e.listing_id=f.listing_id AND e.exclusion_category='PRICE_UNIT_ERROR'
            WHERE f.is_in_modeling_population = 0
        """).fetchone()[0] == pue_total, "Not all PRICE_UNIT_ERROR listings mapped to is_in_modeling_population = 0"
        assert c.execute("""
            SELECT count(*) FROM PRICE_MODEL_CV_PREDICTION p
            JOIN LISTING_EXCLUSION e ON e.listing_id=p.listing_id AND e.exclusion_category='PRICE_UNIT_ERROR'
        """).fetchone()[0] == 0, "Excluded PRICE_UNIT_ERROR listing found in CV predictions"
        assert c.execute("""
            SELECT count(*) FROM PRICE_MODEL_HOLDOUT_PREDICTION p
            JOIN LISTING_EXCLUSION e ON e.listing_id=p.listing_id AND e.exclusion_category='PRICE_UNIT_ERROR'
        """).fetchone()[0] == 0, "Excluded PRICE_UNIT_ERROR listing found in holdout predictions"
        assert c.execute("""
            SELECT count(*) FROM PRICE_MODEL_CV_PREDICTION p
            JOIN LISTING_MODEL_FEATURES f USING(listing_id)
            WHERE f.split_label='holdout'
        """).fetchone()[0] == 0, "Holdout listing found in CV predictions"
        assert c.execute('SELECT count(*), count(DISTINCT listing_id) FROM LISTING_MODEL_FEATURES').fetchone() == (len(f), len(f))
        assert not c.execute('PRAGMA foreign_key_check').fetchall(), "Foreign key check failed"
        assert c.execute('PRAGMA quick_check').fetchall() == [('ok',)], "Quick check failed"
        stored = c.execute('SELECT pipeline_blob FROM PRICE_MODEL_ARTIFACT WHERE model_id=?',(validation_model_id,)).fetchone()[0]
        restored_from_db = pickle.loads(stored)
        sample_pred = restored_from_db.predict(f.loc[holdout_ids[:1], cols])
        assert np.allclose(sample_pred, pred[:1], atol=1e-12)
        assert len(sample_pred) >= 1 and np.isfinite(sample_pred[0])
        assert before == fingerprint(c), "An existing raw table, column, or dictionary entry changed"

        for table in TABLES:
            colcount=len(c.execute(f'PRAGMA table_info("{table}")').fetchall())
            assert c.execute("SELECT count(*) FROM DATA_DICTIONARY WHERE table_name=? AND object_type='column'",(table,)).fetchone()[0]==colcount
            assert c.execute("SELECT count(*) FROM DATA_DICTIONARY WHERE table_name=? AND object_type='table'",(table,)).fetchone()[0]==1
        checks={'existing_source_tables_and_dictionary_unchanged':True,'one_row_per_Seoul_listing':True,'all_exclusions_have_reasons':True,
            'every_price_unit_error_excluded':True,'no_price_unit_error_in_predictions':True,
            'unique_prediction_keys':True,'no_holdout_in_cv':True,'dictionary_complete':True,'foreign_key_check':[],
            'quick_check':'ok','blob_deserialization_prediction_matches':True,'cv_prediction_rows':len(oof),
            'validation_artifact_count':1,'production_artifact_count':1,'new_listing_prediction_rows':len(new_listing_predictions)}
        audit_put(c,'completion_checks',checks)
    assert before==fingerprint(c)
    assert not c.execute('PRAGMA foreign_key_check').fetchall()
    assert c.execute('PRAGMA quick_check').fetchall()==[('ok',)]
    # Full experiment results are persisted; report compact per-family/set winners plus baseline.
    comparison=[]
    for target in TARGETS:
        for name in feature_sets:
            for alg in ['Ridge','HistGradientBoosting','RandomForest']:
                rs=[r for r in experiments if r['target_outcome']==target and r['feature_set_name']==name and r['algorithm']==alg and r['validation_configuration']=='main_filtered']
                best=min(rs,key=lambda r:r['rmse_mean'])
                comparison.append({k:best[k] for k in ['experiment_id','target_outcome','algorithm','feature_set_name','hyperparameter_notes','mae_mean','mae_std','rmse_mean','rmse_std','r2_mean','r2_std']})
        baseline=next(r for r in experiments if r['target_outcome']==target and r['algorithm']=='MeanBaseline' and r['validation_configuration']=='main_filtered')
        comparison.append({k:baseline[k] for k in comparison[0]})
    if sensitivity:
        sens_md=md(sensitivity)+'\n\nOriginal development fold assignments are preserved; the flagged row is added to one seeded fold. Holdout listings never enter sensitivity. This is a paired development diagnostic with one extra observation, not external validation.'
    else:
        sens_md='All 11 `PRICE_UNIT_ERROR` listings were excluded prior to splitting. The sole 3×IQR statistical outlier was already among those 11 excluded listings (0 additional statistical outliers outside `PRICE_UNIT_ERROR`). Consequently, no additional outlier listings exist to reintroduce, and no separate with-outliers development sensitivity run was performed.'
    parts[12]=('Best mean-RMSE hyperparameter per algorithm/feature set is shown below; all bounded-search candidates, sample fold SDs, fold metrics and out-of-fold predictions are in SQLite. '
        'Errors are natural-log units; compare models **within each outcome only**. SD is fold variability, not a confidence interval.\n\n'+md(comparison)+\
        '\n\n**Outlier sensitivity (development only):**\n\n'+sens_md)
    parts[13]=(f'Final primary model: **{final["algorithm"]}**, feature set **{final["feature_set_name"]}**, experiment **{final["experiment_id"]}**, model ID `{model_id}`. '
        f'Hyperparameters: `{final["hyperparameter_notes"]}`. Input features: **{", ".join(cols)}**. '
        f'Actual transformed dimension: {len(pipeline["preprocess"].get_feature_names_out())}. '
        f'Development CV RMSE {final["rmse_mean"]:.6f} ± {final["rmse_std"]:.6f}; MAE {final["mae_mean"]:.6f}; R² {final["r2_mean"]:.6f}. '
        'Selection followed the predeclared 1% simplicity/stability rule; holdout was not used. '
        f'Robustness preferred **{robust["algorithm"]}/{robust["feature_set_name"]}** ({robust["experiment_id"]}), '
        f'within-outcome CV RMSE {robust["rmse_mean"]:.6f}, MAE {robust["mae_mean"]:.6f}, R² {robust["r2_mean"]:.6f}. '
        +('The preferred family and feature set agree across outcomes. ' if (final['algorithm'],final['feature_set_name'])==(robust['algorithm'],robust['feature_set_name']) else 'The preferred family or feature set differs across outcomes, so model-choice stability is limited. ')+\
        'Normalization subtracts log maximum capacity; associations involving capacity partly reflect that arithmetic. The robustness pipeline is not serialized. '
        f'The holdout-provenance pipeline is fitted to the 80% development sample only. A separate production pipeline with the same selected configuration is refit on all {len(eligible)} corrected eligible listings for new-listing prediction; it is not assigned a new holdout score.')
    parts[14]=f'Untouched primary holdout: **{len(holdout_ids)} listings**. One final evaluation; no later retuning.\n\n'+md([hold_metrics])+\
        '\n\nResidual = observed minus predicted log price. Positive residual means underprediction.\n\n'+md([residual_summary])+\
        '\n\nSegment diagnostics (at least 10 holdout listings; smaller groups are shown without metrics):\n\n'+md(segments)+\
        '\n\nSmall-segment R² can be volatile; these diagnostics do not establish systematic population differences. Metrics describe the filtered, date-heterogeneous sample. Dollar-scale mean accuracy is not claimed.'
    parts[15]=interpretation_note+'\n\n'+md(interpretation)+('\n\nRidge intercept: '+str(float(pipeline['model'].intercept_)) if final['algorithm']=='Ridge' else '')
    parts[17]+=('\n\nFinal validation evidence:\n\n'+md([{'check':k,'result':v} for k,v in checks.items()])+\
       '\n\nReproduction reruns the full audit, bounded CV and final fit, replacing only this workflow’s six owned output tables/entries inside a transaction. '
       'Existing raw schemas, row counts and sorted-content SHA-256 hashes must agree before and after. Ownership checks refuse unrelated existing output tables. '
       'The script asserts target arithmetic, cluster validity, source join uniqueness, whitelist prevalence, split disjointness, prediction coverage and dictionary coverage. '
       'A restored pipeline predicts the same held-out listing from the database BLOB. Runtime timestamps vary between runs; seeded partitions and single-threaded modeling are reproducible in the recorded environment. '
       'Validation assessment: **share with caveats**, especially remaining suspicious prices and missing temporal control.')
    review=validate_saved_outputs(c)
    with c:
        audit_put(c,'independent_final_review',review)
    parts[14]+='\n\n'+final_review_text(review)
    cluster_segments=[r for r in segments if r['group']=='cluster_id' and r['rmse'] is not None]
    if cluster_segments:
        worst_cluster=max(cluster_segments,key=lambda r:r['rmse'])
        parts[14]+=f" The largest cluster RMSE is in cluster {worst_cluster['value']} ({worst_cluster['rmse']:.6f}, n={worst_cluster['n']}); mean residual {worst_cluster['mean_residual']:.6f} indicates average underprediction when positive."

    parts[17]+='\n\nIndependent readback recomputed every experiment metric from stored fold predictions and matched every saved holdout prediction to the deserialized pipeline.'
    cv_rmse_change=100*(final['rmse_mean']/PRIOR_RUN['cv_rmse']-1)
    holdout_rmse_change=100*(hold_metrics['rmse']/PRIOR_RUN['holdout_rmse']-1)
    parts[18]=(f'**Corrected validation versus the superseded, uncorrected run**\n\n'
       '| Run | Population | Development / holdout | CV MAE | CV RMSE | CV R² | Holdout MAE | Holdout RMSE | Holdout R² |\n'
       '| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |\n'
       f'| Superseded run | {PRIOR_RUN["population_n"]} | {PRIOR_RUN["development_n"]} / {PRIOR_RUN["holdout_n"]} | {PRIOR_RUN["cv_mae"]:.6f} | {PRIOR_RUN["cv_rmse"]:.6f} | {PRIOR_RUN["cv_r2"]:.6f} | {PRIOR_RUN["holdout_mae"]:.6f} | {PRIOR_RUN["holdout_rmse"]:.6f} | {PRIOR_RUN["holdout_r2"]:.6f} |\n'
       f'| Corrected validation run | {len(eligible)} | {len(train_ids)} / {len(holdout_ids)} | {final["mae_mean"]:.6f} | {final["rmse_mean"]:.6f} | {final["r2_mean"]:.6f} | {hold_metrics["mae"]:.6f} | {hold_metrics["rmse"]:.6f} | {hold_metrics["r2"]:.6f} |\n\n'
       f'After excluding all 11 `PRICE_UNIT_ERROR` listings, CV RMSE changed by {cv_rmse_change:.1f}% and holdout RMSE changed by {holdout_rmse_change:.1f}%. '
       'The holdout sets differ because the corrected population was re-split after exclusion, so this is a procedural before/after comparison rather than a paired statistical test.\n\n'
       f'**Production refit and JSON prediction**\n\nThe production artifact is refit on all **{len(eligible)}** corrected eligible listings, including the validation holdout. '
       f'The supplied JSON contains {new_listing_coverage["json_records"]} crawled records: {new_listing_coverage["already_in_training_database"]} already exist in the training database and are not treated as new predictions; '
       f'{new_listing_coverage["new_prediction_rows"]} are new listing IDs. The production model predicts those {new_listing_coverage["new_prediction_rows"]} rows.\n\n'
       '| New-listing prediction summary | Value |\n| --- | ---: |\n'
       f'| Predicted nightly price, median USD | {new_listing_summary["prediction_distribution_usd"]["median"]:.2f} |\n'
       f'| Predicted nightly price, 25th–75th percentile USD | {new_listing_summary["prediction_distribution_usd"]["p25"]:.2f} – {new_listing_summary["prediction_distribution_usd"]["p75"]:.2f} |\n'
       f'| New listings with observed displayed nightly price | {new_listing_summary.get("n_with_observed_price",0)} |\n'
       f'| Production prediction MAE against displayed nightly price, USD | {new_listing_summary.get("mae_usd",float("nan")):.2f} |\n'
       f'| Production prediction RMSE against displayed nightly price, USD | {new_listing_summary.get("rmse_usd",float("nan")):.2f} |\n'
       f'| Production prediction MAPE against displayed nightly price | {100*new_listing_summary.get("mape",float("nan")):.1f}% |\n'
       f'| Matched previous JSON predictions | {new_listing_summary.get("matched_prior_predictions",0)} |\n'
       f'| Mean absolute change from previous model prediction, USD | {new_listing_summary.get("mean_absolute_prediction_change_usd",float("nan")):.2f} |\n'
       f'| Correlation with previous model predictions | {new_listing_summary.get("correlation_with_prior_prediction",float("nan")):.4f} |\n\n'
       'Displayed JSON prices are used only as an external descriptive comparison because reservation dates vary across records. The production refit has no fresh independent holdout score; the corrected 382-row holdout above remains the unbiased validation result.')
    write_report(parts,'Status: complete — validated primary model stored in SQLite. No causal or future-market generalization claim.')
    assert all(f'## {i}. {s}' in REPORT.read_text() for i,s in enumerate(SECTIONS,1))
    assert 'Analysis in progress' not in REPORT.read_text()
    log(js({'final_n':len(eligible),'outliers':a['statistical_outliers'],'algorithm':final['algorithm'],'features':cols,'holdout':hold_metrics,'robustness':robust['experiment_id'],'checks':checks}))
    c.close()

def dollar_metrics(rows):
    observed=rows.observed_nightly_price_usd.notna() & rows.observed_nightly_price_usd.gt(0)
    actual=rows.loc[observed,'observed_nightly_price_usd'].to_numpy(float)
    prediction=rows.loc[observed,'predicted_nightly_price_usd'].to_numpy(float)
    assert len(actual)>0 and np.isfinite(prediction).all()
    error=prediction-actual
    return {'prediction_coverage':int(len(rows)), 'observed_price_count':int(len(actual)),
            'mae_usd':float(np.abs(error).mean()), 'rmse_usd':float(np.sqrt(np.mean(error**2))),
            'mape':float(np.mean(np.abs(error)/actual)),
            'median_absolute_error_usd':float(np.median(np.abs(error))), 'bias_usd':float(error.mean())}

def predict_external(pipeline, cols, external):
    result=external[['listing_id','observed_nightly_price_usd']].copy().reset_index(drop=True)
    result['predicted_log_price']=pipeline.predict(external[cols])
    result['predicted_nightly_price_usd']=np.exp(result.predicted_log_price)
    return result

def write_external_report(baseline_a, corrected_a, baseline_selected, corrected_selected,
                          baseline_cols, corrected_cols, baseline_cv, corrected_cv,
                          baseline_metrics, corrected_metrics, deltas, coverage, checks, versions):
    feature_table=[
        {'model':'Baseline (unresolved PRICE_UNIT_ERROR retained)','algorithm':baseline_selected['algorithm'],
         'feature set':baseline_selected['feature_set_name'],'training rows':baseline_a['final_n'],
         'input features':', '.join(baseline_cols)},
        {'model':'Corrected (PRICE_UNIT_ERROR excluded)','algorithm':corrected_selected['algorithm'],
         'feature set':corrected_selected['feature_set_name'],'training rows':corrected_a['final_n'],
         'input features':', '.join(corrected_cols)},]
    external_table=[]
    for label, values in [('Baseline',baseline_metrics),('Corrected',corrected_metrics),('Corrected minus baseline',deltas)]:
        external_table.append({'model':label, **values})
    report=(
        '# Seoul Airbnb price model — external JSON evaluation report\n\n'
        '> **Final evaluation design:** There is no internal 80:20 holdout. Candidate and hyperparameter selection use five-fold shuffled cross-validation on each full historical training population (`random_state=42`). The primary final comparison uses the same novel listings from the supplied external crawler JSON.\n\n'
        '## 1. Evaluation question\n\n'
        'Does excluding the known `PRICE_UNIT_ERROR` records improve nightly-price predictions on newly crawled listings? '
        'The observed outcome is each JSON record\'s displayed nightly USD price. This is an external, time-heterogeneous test: the JSON was collected at a different time and reservation dates may differ, so it is not a perfectly contemporaneous benchmark.\n\n'
        '## 2. Historical training populations and data-quality audit\n\n'+md([
            {'population':'Baseline','PRICE_UNIT_ERROR excluded':0,'3×IQR statistical outliers':baseline_a['statistical_outliers'],
             'additional 3×IQR exclusions':baseline_a['additional_3iqr_outliers'],'final training rows':baseline_a['final_n']},
            {'population':'Corrected','PRICE_UNIT_ERROR excluded':corrected_a['price_unit_errors'],'3×IQR statistical outliers':corrected_a['statistical_outliers'],
             'additional 3×IQR exclusions':corrected_a['additional_3iqr_outliers'],'final training rows':corrected_a['final_n']}])+
        '\n\nThe baseline intentionally reproduces the earlier population logic: it retains the known price-unit-error listings except any row removed by the prescribed 3×IQR rule. '
        'The corrected model excludes all 11 `LISTING_EXCLUSION` rows with `exclusion_category = PRICE_UNIT_ERROR` before applying the same log-price fence. '
        f'The fence identified {corrected_a["statistical_outliers"]} row and added {corrected_a["additional_3iqr_outliers"]} exclusions beyond that register.\n\n'
        '## 3. Predictors and model selection\n\n'+md(feature_table)+
        '\n\nPredictors never include host variables, dates, price-derived fields, listing IDs, exclusion flags, or targets. '
        'The coordinate feature set contains `x_km` and `y_km` as two projected continuous coordinates; they are not treated as separate locations. '
        'K=5 `cluster_id` is categorical and may overlap with coordinates, so this choice is predictive rather than causal. Amenities remain individual interpretable flags plus `amenity_count`; PCA was not used because this is a small, mixed-type feature group and PCA would obscure amenity meaning.\n\n'
        '## 4. Five-fold CV used for selection\n\n'
        'Each row below is the selected candidate evaluated with shuffled five-fold CV on its entire historical training population. '
        'Metrics are on the log nightly-price target and are used only for model selection, not as the primary final comparison.\n\n'+md([
            {'model':'Baseline','CV MAE (log USD)':baseline_cv['mae_mean'],'CV RMSE (log USD)':baseline_cv['rmse_mean'],'CV R²':baseline_cv['r2_mean']},
            {'model':'Corrected','CV MAE (log USD)':corrected_cv['mae_mean'],'CV RMSE (log USD)':corrected_cv['rmse_mean'],'CV R²':corrected_cv['r2_mean']}])+
        '\n\n## 5. Primary external JSON test\n\n'
        f'The JSON contains {coverage["json_records"]} records. {coverage["already_in_training_database"]} IDs already occur in the historical database and are excluded from external testing. '
        f'The same **{coverage["new_prediction_rows"]} novel listing IDs** are scored by both models. MAPE is `mean(|predicted USD − displayed USD| / displayed USD)` over records with a positive displayed nightly price.\n\n'+md(external_table)+
        '\n\nA negative corrected-minus-baseline value is an improvement for MAE, RMSE, MAPE, and median absolute error. '
        'Prediction coverage is the count of novel JSON listings passed to each pipeline; it is expected to be identical.\n\n'
        '## 6. Conclusion\n\n'
        '**The external JSON comparison above is the final performance evidence.** The corrected model is evaluated on the same 392 novel listings as the baseline, after removing all 11 registered price-unit errors from corrected training. '
        'No internal holdout was created, stored, or used to make this conclusion. Because displayed prices are from a different crawl time and may reflect different stay dates, the result measures external time-heterogeneous transfer rather than a contemporaneous production benchmark.\n\n'
        '## 7. Reproducibility and validation\n\n'
        f'Script: `{Path(__file__).resolve()}`. Run `PYTHONDONTWRITEBYTECODE=1 python3 -B {Path(__file__).resolve()} --external-evaluation`. '
        f'Package versions: `{js(versions)}`. Only workflow-owned SQLite tables, this script, and this report are updated.\n\n'+md([{'check':k,'result':v} for k,v in checks.items()])+'\n')
    REPORT.write_text(report,encoding='utf-8')

def external_evaluation():
    log('Starting external-JSON evaluation; no internal holdout will be created')
    c=sqlite3.connect(DB)
    c.execute('PRAGMA foreign_keys=ON'); c.execute('PRAGMA temp_store=MEMORY')
    assert c.execute('PRAGMA journal_mode=MEMORY').fetchone()[0]=='memory'
    before=fingerprint(c); source_schema=source_audit(c)
    corrected, corrected_a, _=build_features(c, exclude_price_unit_errors=True)
    baseline, baseline_a, _=build_features(c, exclude_price_unit_errors=False)
    corrected_ids=corrected.index[corrected.is_in_modeling_population.eq(1)].to_numpy()
    baseline_ids=baseline.index[baseline.is_in_modeling_population.eq(1)].to_numpy()
    assert corrected_a['price_unit_errors']==11 and corrected_a['retained_prior_suspected_errors']==0
    assert baseline_a['retained_prior_suspected_errors']>0
    assert not set(corrected.loc[corrected.prior_suspected_price_error.eq(1)&corrected.is_in_modeling_population.eq(1),'listing_id'])
    external,coverage=build_new_listing_features(c)
    historical={str(x[0]) for x in c.execute('SELECT id FROM LISTING')}
    assert set(external.listing_id).isdisjoint(historical) and coverage['new_prediction_rows']==len(external)
    assert len(external)==392, f'Expected 392 novel JSON listings, got {len(external)}'
    for f,ids in [(corrected,corrected_ids),(baseline,baseline_ids)]:
        f['split_label']='excluded'; f.loc[ids,'split_label']='cv_full_population'; f['cv_fold']=np.nan
    core=['person_capacity','room_type','cluster_id']; structure=core+['property_type','bedrooms','beds','bathrooms','amenity_count']
    amenity_cols=list(AMENITY_RULES); feature_sets={'core':core,'structure':structure,'amenities':structure+amenity_cols,'coordinates':structure+amenity_cols+['x_km','y_km']}
    configs=[('Ridge',{'alpha':v}) for v in [1.,10.,100.]]+ [('HistGradientBoosting',{'max_leaf_nodes':v}) for v in [7,15]]+ [('RandomForest',{'min_samples_leaf':v,'max_features':1.0}) for v in [3,10]]
    all_experiments=[]; all_oof=[]; selected={}; fitted={}; counter=0
    for population,f,ids,audit in [('baseline',baseline,baseline_ids,baseline_a),('corrected',corrected,corrected_ids,corrected_a)]:
        folds=list(KFold(n_splits=5,shuffle=True,random_state=SEED).split(ids))
        for fold,(_,va) in enumerate(folds):
            # corrected feature table is persisted; baseline-only PRICE_UNIT_ERROR rows remain audit-visible.
            if population=='corrected': f.loc[ids[va],'cv_fold']=fold
        rows=[]
        for name,cols,alg,params in [('core',core,'MeanBaseline',{})]+[(n,cols,alg,p) for n,cols in feature_sets.items() for alg,p in configs]:
            counter+=1; eid=f'{population.upper()}_E{counter:03d}'
            row,predictions,pipeline=validate_cv(f,ids,folds,cols,alg,params,TARGETS[0],eid,{'feature_set':name,'validation':population+'_full_population_cv'})
            row['cross_validation_design']='5-fold shuffled KFold random_state=42 on entire eligible historical population; no internal holdout'
            row['selection_status']='baseline' if alg=='MeanBaseline' else 'candidate'
            rows.append(row); all_experiments.append(row); all_oof.extend(predictions); fitted[eid]=pipeline
            log(f'{eid}: {row["rmse_mean"]:.4f}')
        winner=choose(rows); winner['selection_status']='selected_primary' if population=='corrected' else 'selected_baseline'
        cols=json.loads(winner['feature_columns']); model=fitted[winner['experiment_id']].fit(f.loc[ids,cols],f.loc[ids,TARGETS[0]])
        selected[population]=winner; fitted[population]=(model,cols)
    baseline_predictions=predict_external(*fitted['baseline'],external)
    corrected_predictions=predict_external(*fitted['corrected'],external)
    assert baseline_predictions.listing_id.tolist()==corrected_predictions.listing_id.tolist()
    baseline_metrics=dollar_metrics(baseline_predictions); corrected_metrics=dollar_metrics(corrected_predictions)
    deltas={k:(corrected_metrics[k]-baseline_metrics[k]) for k in baseline_metrics}
    versions={'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'scikit_learn':sklearn.__version__,'sqlite':sqlite3.sqlite_version}
    now=datetime.now(timezone.utc).isoformat()
    assert before==fingerprint(c)
    feature_inventory(corrected)
    c.execute('BEGIN IMMEDIATE')
    with c:
        initialize_tables(c,corrected)
        insert_frame(c,'PRICE_MODEL_EXPERIMENT',pd.DataFrame(all_experiments))
        c.executemany('INSERT INTO PRICE_MODEL_CV_PREDICTION VALUES(?,?,?,?,?,?)',all_oof)
        artifact_sql='INSERT INTO PRICE_MODEL_ARTIFACT VALUES('+','.join('?' for _ in SCHEMA['PRICE_MODEL_ARTIFACT'])+')'
        for population, training, audit, metric in [('baseline',baseline,baseline_a,baseline_metrics),('corrected',corrected,corrected_a,corrected_metrics)]:
            model,cols=fitted[population]; blob=pickle.dumps(model,protocol=pickle.HIGHEST_PROTOCOL)
            assert np.isfinite(pickle.loads(blob).predict(external.iloc[:1][cols])).all()
            winner=selected[population]
            c.execute(artifact_sql,(f'{VERSION}-{population}',TARGETS[0],winner['algorithm'],sqlite3.Binary(blob),
                js({'columns':cols,'types':{x:str(training[x].dtype) for x in cols},'prediction_scale':'natural-log USD/night; exp() gives point prediction'}),
                f'{population}; all {len(training.index[training.is_in_modeling_population.eq(1)])} eligible historical rows; 3xIQR log-price fence; '+('PRICE_UNIT_ERROR retained except fence' if population=='baseline' else 'all PRICE_UNIT_ERROR excluded'),
                SEED,now,js({'selected_cv':winner,'external_metrics':metric,'external_listing_ids':baseline_predictions.listing_id.tolist()}),LIMITATIONS))
        audit_put(c,'workflow',{'version':VERSION,'status':'complete','evaluation':'external_json_no_internal_holdout'})
        audit_put(c,'source_schema',source_schema); audit_put(c,'source_fingerprints',before)
        audit_put(c,'population_and_quality',{'baseline':baseline_a,'corrected':corrected_a})
        audit_put(c,'external_json_evaluation',{'coverage':coverage,'baseline_metrics':baseline_metrics,'corrected_metrics':corrected_metrics,'corrected_minus_baseline':deltas,
            'baseline_predictions':baseline_predictions.to_dict('records'),'corrected_predictions':corrected_predictions.to_dict('records')})
        assert c.execute('SELECT count(*) FROM PRICE_MODEL_HOLDOUT_PREDICTION').fetchone()[0]==0
        assert c.execute("SELECT count(*) FROM LISTING_MODEL_FEATURES f JOIN LISTING_EXCLUSION e ON e.listing_id=f.listing_id WHERE e.exclusion_category='PRICE_UNIT_ERROR' AND f.is_in_modeling_population!=0").fetchone()[0]==0
        assert c.execute('SELECT count(*),count(DISTINCT listing_id) FROM LISTING_MODEL_FEATURES').fetchone()==(len(corrected),len(corrected))
        assert not c.execute('PRAGMA foreign_key_check').fetchall() and c.execute('PRAGMA quick_check').fetchall()==[('ok',)]
        assert before==fingerprint(c)
    checks={'corrected_PRICE_UNIT_ERROR_training_rows':0,'external_JSON_novel_only':True,'same_external_listing_ids':True,
            'internal_holdout_prediction_rows':0,'feature_rows_one_per_listing':True,'foreign_key_check':'empty','quick_check':'ok',
            'raw_tables_and_columns_unchanged':True}
    write_external_report(baseline_a,corrected_a,selected['baseline'],selected['corrected'],fitted['baseline'][1],fitted['corrected'][1],
        selected['baseline'],selected['corrected'],baseline_metrics,corrected_metrics,deltas,coverage,checks,versions)
    assert '382' not in REPORT.read_text(encoding='utf-8') and 'no internal 80:20 holdout' in REPORT.read_text(encoding='utf-8')
    c.close()
    log(js({'baseline_training_n':len(baseline_ids),'corrected_training_n':len(corrected_ids),'baseline_external':baseline_metrics,'corrected_external':corrected_metrics,'deltas':deltas}))

if __name__=='__main__':
    with threadpool_limits(limits=1):
        if sys.argv[1:]==['--external-evaluation']:
            external_evaluation()
        elif len(sys.argv)==1:
            external_evaluation()
        else:
            raise SystemExit('Usage: run_price_model_analysis.py [--external-evaluation]')
