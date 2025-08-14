import webbrowser
import requests

def open_url(url):
    webbrowser.open(url)

def fetch_gbp_exchange_rate():
    """
    Fetches the current ZAR to GBP exchange rate using frankfurter.app.
    Returns the rate as a float, or None if failed.
    """
    try:
        response = requests.get("https://api.frankfurter.app/latest?amount=1&from=ZAR&to=GBP", timeout=5)
        data = response.json()
        # The response is like: {'amount': 1, 'base': 'ZAR', 'date': '2025-08-01', 'rates': {'GBP': 0.0421}}
        return data["rates"]["GBP"]
    except Exception:
        return None