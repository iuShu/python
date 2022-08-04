
GET = "GET"
POST = "POST"
DELETE = "DELETE"

APPLICATION_JSON = 'application/json'
CONTENT_TYPE = 'Content-Type'
OK_ACCESS_KEY = 'OK-ACCESS-KEY'
OK_ACCESS_SIGN = 'OK-ACCESS-SIGN'
OK_ACCESS_TIMESTAMP = 'OK-ACCESS-TIMESTAMP'
OK_ACCESS_PASSPHRASE = 'OK-ACCESS-PASSPHRASE'

API_URL = 'https://www.okx.com'

# instrument type
INST_TYPE_SPOT = 'SPOT'
INST_TYPE_MARGIN = 'MARGIN'
INST_TYPE_SWAP = 'SWAP'           # PERP
INST_TYPE_FUTURES = 'FUTURES'
INST_TYPE_OPTION = 'OPTION'

# category
CATEGORY_TWAP = 'twap'
CATEGORY_ADL = 'adl'
CATEGORY_FULL_LIQUIDATION = 'full_liquidation'
CATEGORY_PARTIAL_LIQUIDATION = 'partial_liquidation'
CATEGORY_DELIVERY = 'delivery'
CATEGORY_DDH = 'ddh'

# order type
ORDER_TYPE_MARKET = 'market'
ORDER_TYPE_LIMIT = 'limit'
ORDER_TYPE_POST_ONLY = 'post_only'
ORDER_TYPE_FOK = 'fok'
ORDER_TYPE_IOC = 'ioc'
ORDER_TYPE_OPTIMAL_LIMIT_IOC = 'optimal_limit_ioc'

# order state
STATE_CANCELED = 'canceled'
STATE_FILLED = 'filled'

# public
SERVER_TIMESTAMP_URL = '/api/v5/public/time'

# account
ACCOUNT_BALANCE = '/api/v5/account/balance'
ASSET_BALANCE = '/api/v5/asset/balances'

# trade
GET_ORDER_HISTORY = '/api/v5/trade/orders-history'
GET_ORDER_HISTORY_ARCHIVE = '/api/v5/trade/orders-history-archive'
GET_ORDER_DETAILS = '/api/v5/trade/fills'
