import pandas as pd
import pytest
from src.etl.prices import normalize_prices
def test_normalize():
    df=pd.DataFrame({"Close":[100,101,102]},index=pd.date_range("2024-01-01",periods=3));out=normalize_prices(df);assert len(out)==3;assert out.index.is_monotonic_increasing
def test_empty():
    with pytest.raises(ValueError):normalize_prices(pd.DataFrame())
def test_nan_removed():
    df=pd.DataFrame({"Close":[100,float("nan"),102]});assert len(normalize_prices(df))==2
