import httpx

def test_api():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 52.52,
        "longitude": 13.41,
        "daily": "temperature_2m_max,apparent_temperature_max",
        "hourly": "soil_moisture_0_to_1cm",
        "timezone": "auto"
    }
    response = httpx.get(url, params=params)
    print(response.json())

if __name__ == "__main__":
    test_api()
