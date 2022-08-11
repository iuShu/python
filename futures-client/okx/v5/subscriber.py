from okx.v5 import stream
from okx.v5.utils import log


class Subscriber:

    def __init__(self):
        self._channels = dict()
        self._running = False

    def subscribe(self, channel: str, inst_id: str):
        if not channel or not inst_id:
            raise ValueError('must provide channel and instId value')

        key = self._channel_key(channel, inst_id)
        added = stream.add_channel(channel, inst_id)
        if not added:
            raise RuntimeError(f'channel {channel} {inst_id} already in subscribing or subscribe waiting')
        self._channels[key] = added

    def startup(self):
        if not self._channels:
            raise ValueError('subscribe to at least ONE channel')
        stream.register(self)
        stream.startup()
        self._running = True

    def shutdown(self):
        if not self._running:
            log.warning('subscriber is not running')
            return
        self._running = False
        stream.shutdown()

    def on_data(self, resp):
        if 'arg' not in resp or 'data' not in resp:
            log.warning('unknown recv data')
            return
        arg = resp['arg']
        key = self._channel_key(arg['channel'], arg['instId'])
        if key in self._channels:
            self._handle(resp['data'])

    def _handle(self, data):
        pass

    def is_running(self) -> bool:
        return self._running

    @staticmethod
    def _channel_key(channel: str, inst_id: str):
        return hash(channel + inst_id)

