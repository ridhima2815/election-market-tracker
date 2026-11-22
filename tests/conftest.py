import pandas as pd
import pytest
@pytest.fixture
def sample_prices():
    return pd.DataFrame({"Close":range(100,200)},index=pd.date_range("2024-01-01",periods=100,freq="B"))
@pytest.fixture
def sample_market():
    return pd.DataFrame({"Close":range(200,300)},index=pd.date_range("2024-01-01",periods=100,freq="B"))
