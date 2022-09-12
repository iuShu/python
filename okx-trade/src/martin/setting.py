from src.okx.consts import INST_TYPE_SWAP, INST_BTC_USDT_SWAP, BAR_1M, TD_MODE_ISOLATE
from src.okx.side import LongSide, ShortSide

EXCHANGE = 'okx'
TEST = True
INST_ID = INST_BTC_USDT_SWAP
INST_TYPE = INST_TYPE_SWAP
CANDLE_BAR_TYPE = BAR_1M

STRATEGY_MA_DURATION = 10
STRATEGY_MAX_REPO_SIZE = STRATEGY_MA_DURATION * 5

ORDER_POS_SIDE = ShortSide()
ORDER_START_POS = 10
ORDER_FOLLOW_RATE = .004
ORDER_PROFIT_STEP_RATE = .0002
ORDER_MAX_COUNT = 5
ORDER_POS_TYPE = TD_MODE_ISOLATE

FAILURE_THRESHOLD_CONFIRM = 10
FAILURE_THRESHOLD_PLACE_ALGO = 10
FAILURE_THRESHOLD_EXTRA_MARGIN = 10

NOTIFY_NAME = 'aliyun'
KEY_NOTIFY_MSG = 'notify-msg'
NOTIFY_SERVICE_SECRET = '..'
NOTIFY_OP_LOGIN = 'login'
NOTIFY_OP_PING = 'ping'
NOTIFY_OP_NOTIFY = 'notify'
NOTIFY_OP_SUBSCRIBE = 'subscribe'
NOTIFY_OP_OPERATE = 'operate'
NOTIFY_CLOSE_SIGNAL = 'ws-close'

key_strategy_repo = 'strategy-repo'
key_monitor_repo = 'monitor-repo'
