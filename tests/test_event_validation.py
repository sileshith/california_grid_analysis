import numpy as np
import pandas as pd
import pytest
from src.event_validation import evaluate


def sample():
    times=pd.date_range('2024-01-01',periods=24*100,freq='h',tz='UTC')
    d=100+np.sin(np.arange(len(times))/24)*10
    return pd.DataFrame(dict(balancing_authority='CISO',utc_time=times,demand_mw=d,demand_mw_adjusted=d,total_interchange_mw=-5.,total_interchange_mw_adjusted=-5.,demand_forecast_mw=d+1))


def test_equal_workload_and_undefined_no_event_recall():
    r=evaluate(sample(),dict(catalog_start='2024-01-01',catalog_end='2024-12-31',events=[]),'2024-02-01','2024-03-31',6,'_adjusted')
    assert all(len(v['flagged_days'])==6 and v['recall'] is None for v in r['rules'].values())


def test_catalog_and_budget_boundaries():
    catalog=dict(catalog_start='2024-02-01',catalog_end='2024-03-31',events=[])
    with pytest.raises(ValueError,match='catalog coverage'):
        evaluate(sample(),catalog,'2024-01-25','2024-03-31',6,'')
    with pytest.raises(ValueError,match='Review budget'):
        evaluate(sample(),catalog,'2024-02-01','2024-03-31',999,'')
