from src.etl.news import clean_title,normalize_url
def test_title():assert clean_title("Election result - Publisher")=="Election result"
def test_url():assert "ved" not in normalize_url("https://example.com/a&ved=abc")
