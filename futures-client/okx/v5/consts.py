
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
WSS_PUBLIC_URL = 'wss://wspap.okx.com:8443/ws/v5/public?brokerId=9999'
WSS_PRIVATE_URL = 'wss://wspap.okx.com:8443/ws/v5/private?brokerId=9999'

# instrument
INST_BTC_USDT_SWAP = 'BTC-USDT-SWAP'

# instrument type
INST_TYPE_SPOT = 'SPOT'
INST_TYPE_MARGIN = 'MARGIN'
INST_TYPE_SWAP = 'SWAP'           # PERP
INST_TYPE_FUTURES = 'FUTURES'
INST_TYPE_OPTION = 'OPTION'

# price type
PRICE_TYPE_LAST = 'last'
PRICE_TYPE_MARKET = 'market'
PRICE_TYPE_MARK = 'mark'

# side
SIDE_BUY = 'buy'
SIDE_SELL = 'sell'

# position side
POS_SIDE_LONG = 'long'
POS_SIDE_SHORT = 'short'

# td mode
TD_MODE_CROSS = 'cross'
TD_MODE_ISOLATE = 'isolated'

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

# algo order type
ALGO_TYPE_CONDITIONAL = 'conditional'   # single side
ALGO_TYPE_OCO = 'oco'                   # dual side
ALGO_TYPE_TRIGGER = 'trigger'
ALGO_TYPE_MOVE_ORDER_STOP = 'move_order_stop'
ALGO_TYPE_ICEBERG = 'iceberg'
ALGO_TYPE_TWAP = 'twap'

# algo order state
ALGO_STATE_EFFECTIVE = 'effective'
ALGO_STATE_CANCELED = 'canceled'
ALGO_STATE_ORDER_FAILED = 'order_failed'

# order state
STATE_CANCELED = 'canceled'
STATE_FILLED = 'filled'
STATE_PARTIALLY_FILLED = 'partially_filled'
STATE_LIVE = 'live'

# public
SERVER_TIMESTAMP_URL = '/api/v5/public/time'
MARKET_CANDLE = '/api/v5/market/candles'
MARKET_TICKER = '/api/v5/market/ticker'

# account
ACCOUNT_CONFIG = '/api/v5/account/config'
ACCOUNT_BALANCE = '/api/v5/account/balance'
ASSET_BALANCE = '/api/v5/asset/balances'
ACCOUNT_LEVERAGE = '/api/v5/account/leverage-info'
ACCOUNT_SET_LEVERAGE = '/api/v5/account/set-leverage'

# trade
PLACE_ORDER = '/api/v5/trade/order'
PLACE_BATCH_ORDERS = '/api/v5/trade/batch-orders'
CANCEL_ORDER = '/api/v5/trade/cancel-order'
CANCEL_BATCH_ORDERS = '/api/v5/trade/cancel-batch-order'
GET_ORDER_INFO = '/api/v5/trade/order'
GET_PENDING_ORDER = '/api/v5/trade/orders-pending'
GET_ORDER_HISTORY = '/api/v5/trade/orders-history'                  # 7 days
GET_ORDER_HISTORY_ARCHIVE = '/api/v5/trade/orders-history-archive'  # 3 months
GET_ORDER_DETAILS = '/api/v5/trade/fills'                           # 3 days
GET_ORDER_DETAILS_ARCHIVE = '/api/v5/trade/fills-history'           # 3 months
CLOSE_POSITION = '/api/v5/trade/close-position'
PLACE_ALGO_ORDER = '/api/v5/trade/order-algo'
CANCEL_ALGO_ORDER = '/api/v5/trade/cancel-algos'
ALGO_ORDER_PENDING = '/api/v5/trade/orders-algo-pending'
ALGO_ORDER_HISTORY = '/api/v5/trade/orders-algo-history'

# channels
TICKERS_BTC_USDT_SWAP = [{'channel': 'tickers', 'instId': INST_BTC_USDT_SWAP}]

# bar
BAR_1M = '1m'
BAR_3M = '3m'
BAR_5M = '5m'
BAR_15M = '15m'
BAR_30M = '30m'
BAR_1H = '1H'
BAR_2H = '2H'
BAR_4H = '4H'
