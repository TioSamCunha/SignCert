import requests
from flask import current_app

_LOCAL_IPS = {'127.0.0.1', '::1', 'localhost'}


def get_geolocation(ip_address: str) -> dict:
    if not ip_address or ip_address in _LOCAL_IPS:
        return {}
    try:
        timeout = current_app.config.get('GEO_TIMEOUT_SECONDS', 3)
        resp = requests.get(
            f'http://ip-api.com/json/{ip_address}',
            timeout=timeout,
            params={'fields': 'status,country,countryCode,regionName,city,lat,lon,timezone,isp'},
        )
        data = resp.json()
        if data.get('status') == 'success':
            return {
                'country': data.get('country'),
                'country_code': data.get('countryCode'),
                'region': data.get('regionName'),
                'city': data.get('city'),
                'lat': data.get('lat'),
                'lon': data.get('lon'),
                'timezone': data.get('timezone'),
                'isp': data.get('isp'),
            }
    except Exception:
        pass
    return {}
