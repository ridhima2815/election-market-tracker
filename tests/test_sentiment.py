from src.etl.sentiment import classify_sentiment,score_text
def test_labels():assert classify_sentiment(.5)=="positive";assert classify_sentiment(-.5)=="negative";assert classify_sentiment(0)=="neutral"
def test_polarity():assert score_text("A wonderful victory and successful reform")['sentiment']>0;assert score_text("terrible crisis and corruption")['sentiment']<0
