from aiohttp.web import AppKey

db_key: AppKey = AppKey('db')
config_key: AppKey = AppKey('config')
cache_key: AppKey = AppKey('cache')
client_session_key: AppKey = AppKey('client_session')
oauth_client_id_key: AppKey = AppKey('CLIENT_ID')
oauth_authorize_url_key: AppKey = AppKey('AUTHORIZE_URL')
oauth_scopes_key: AppKey = AppKey('SCOPES')
oauth_auth_extras_key: AppKey = AppKey('AUTH_EXTRAS')
