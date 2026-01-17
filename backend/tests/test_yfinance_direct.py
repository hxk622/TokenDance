"""Direct test using yfinance library."""

import pytest

yf = pytest.importorskip("yfinance", reason="yfinance not installed (optional finance dependency)")


def test_yfinance():
    """Test yfinance directly."""
    print("\n🔬 Testing yfinance directly\n")

    # Get Apple stock
    ticker = yf.Ticker("AAPL")

    # Get info
    print("1. Getting stock info...")
    info = ticker.info
    print(f"   Name: {info.get('shortName', 'N/A')}")
    print(f"   Price: ${info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))}")
    print(f"   Market Cap: ${info.get('marketCap', 'N/A'):,}")
    print(f"   PE Ratio: {info.get('trailingPE', 'N/A')}")

    # Get historical data
    print("\n2. Getting historical data...")
    hist = ticker.history(period="5d")
    print(f"   Records: {len(hist)}")
    if not hist.empty:
        print(f"   Latest close: ${hist['Close'].iloc[-1]:.2f}")
        print("\n   Recent data:")
        print(hist[['Open', 'High', 'Low', 'Close', 'Volume']].tail())

    print("\n✅ yfinance works correctly!\n")


if __name__ == "__main__":
    test_yfinance()
