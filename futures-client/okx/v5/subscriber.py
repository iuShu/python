from logger import log
from okx.v5 import stream


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
        try:
            self._running = True
            stream.register(self)
            stream.startup()
        except Exception:
            log.error('[subscriber] startup error', exc_info=True)
            self._running = False

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
            self._handle(arg['channel'], arg['instId'], resp['data'])

    def _handle(self, channel: str, inst_id: str, data):
        pass

    def is_running(self) -> bool:
        return self._running

    @staticmethod
    def _channel_key(channel: str, inst_id: str):
        return hash(channel + inst_id)

