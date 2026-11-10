"""Demonstrates mixed-feature preprocessing for retrieval candidate analysis.

Numeric features -> train-only StandardScaler; categorical metadata ->
train-only OneHotEncoder(handle_unknown='ignore'). No target leakage.
"""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from .core import RoboGuide
from .evaluation import load_benchmark

NUMERIC=list(RoboGuide.WEIGHTS)
CATEGORICAL=['subsystem','version']

def candidate_table(assistant:RoboGuide,benchmark=None):
    benchmark=benchmark or load_benchmark()
    records=[]
    for example in benchmark:
        for h in assistant.search(example['question'],k=len(assistant.docs),version=example['version']):
            records.append({'query_id':example['id'],'split':example['split'],
                'relevant':int(h.id in example['gold_ids']),
                'subsystem':h.subsystem,'version':h.version,
                **h.features})
    return pd.DataFrame.from_records(records)

def encode_features(assistant=None):
    assistant=assistant or RoboGuide()
    df=candidate_table(assistant)
    development=df['split']=='development'
    # Split before fit; no categorical vocab learned from test candidates.
    transform=ColumnTransformer([
      ('numeric',StandardScaler(),NUMERIC),
      ('categorical',OneHotEncoder(handle_unknown='ignore',sparse_output=False),CATEGORICAL)
    ],remainder='drop',sparse_threshold=0)
    Xdev=transform.fit_transform(df.loc[development,NUMERIC+CATEGORICAL])
    Xtest=transform.transform(df.loc[~development,NUMERIC+CATEGORICAL])
    assert np.isfinite(Xdev).all() and np.isfinite(Xtest).all()
    return df,transform,Xdev,Xtest
