from src.config import load_countries,load_elections
def test_countries():
    c=load_countries();assert len(c)==8;assert c["IN"]["ticker"]=="^NSEI"
def test_elections():
    e=load_elections();assert not e.empty;assert "verified" in e;assert e.event_date.notna().all()
