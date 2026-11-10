import numpy as np
from roboguide.preprocessing import encode_features

def test_numeric_and_categorical_pipeline():
    df,trans,train,test=encode_features()
    assert train.shape[0]>test.shape[0] and train.shape[1]>8
    assert np.isfinite(train).all() and np.isfinite(test).all()
    assert df['subsystem'].notna().all()
