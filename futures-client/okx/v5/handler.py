from okx.v5.utils import log


class Handler:

    def __init__(self, channel: str, inst_id: str):
        self._channel = channel
        self._inst_id = inst_id

    def channel(self) -> str:
        return self._channel

    def inst_id(self) -> str:
        return self._inst_id

    def fire_handle(self, raw):
        if 'arg' not in raw or 'data' not in raw:
            log.warning('unknown recv data')
            return
        arg = raw['arg']
        if self._channel == arg.get('channel') and self._inst_id == arg['instId']:
            self._handle(raw['data'])

    def _handle(self, data):
        pass
