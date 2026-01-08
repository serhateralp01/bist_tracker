from tefas import Crawler
from datetime import datetime, timedelta

def test_tefas():
    crawler = Crawler()
    # Fetch data for a specific fund (e.g., MAC - Marmara Capital) for the last few days
    start = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
    end = datetime.now().strftime("%Y-%m-%d")

    try:
        result = crawler.fetch(start=start, end=end, columns=["date", "code", "price"], name="MAC")
        print("Result columns:", result.columns)
        print("Result head:", result.head())
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_tefas()
