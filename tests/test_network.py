from unittest.mock import patch
from src.etl.inflation import get_world_bank_inflation
def test_world_bank_parse():
    payload=[{},[{"date":"2024","value":4.2},{"date":"2023","value":5.0}]]
    with patch("src.etl.inflation.requests.get") as mock:
        mock.return_value.json.return_value=payload;mock.return_value.raise_for_status.return_value=None
        result=get_world_bank_inflation("IND");assert result["value"]==4.2;assert result["year"]==2024
