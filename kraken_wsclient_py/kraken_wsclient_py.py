# coding=utf-8
import threading
import json
import hmac
import hashlib
from autobahn.twisted.websocket import WebSocketClientFactory, \
    WebSocketClientProtocol, \
    connectWS
from twisted.internet import reactor, ssl
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet.error import ReactorAlreadyRunning


class KrakenClientProtocol(WebSocketClientProtocol):

    def __init__(self, factory, payload=None):
        super().__init__()
        self.factory = factory
        self.payload = payload

    def onOpen(self):
        self.factory.protocol_instance = self

    def onConnect(self, response):
        if self.payload:
            self.sendMessage(self.payload, isBinary=False)
        # reset the delay after reconnecting
        self.factory.resetDelay()

    def onMessage(self, payload, isBinary):
        if not isBinary:
            try:
                payload_obj = json.loads(payload.decode('utf8'))
            except ValueError:
                pass
            else:
                self.factory.callback(payload_obj)


class KrakenReconnectingClientFactory(ReconnectingClientFactory):

    # set initial delay to a short time
    initialDelay = 0.1

    maxDelay = 20

    maxRetries = 30


class KrakenClientFactory(WebSocketClientFactory, KrakenReconnectingClientFactory):

    def __init__(self, *args, payload=None, **kwargs):
        WebSocketClientFactory.__init__(self, *args, **kwargs)
        self.protocol_instance = None
        self.base_client = None
        self.payload = payload

    protocol = KrakenClientProtocol
    _reconnect_error_payload = {
        'e': 'error',
        'm': 'Max reconnect retries reached'
    }

    def clientConnectionFailed(self, connector, reason):
        self.retry(connector)
        if self.retries > self.maxRetries:
            self.callback(self._reconnect_error_payload)

    def clientConnectionLost(self, connector, reason):
        self.retry(connector)
        if self.retries > self.maxRetries:
            self.callback(self._reconnect_error_payload)

    def buildProtocol(self, addr):
        return KrakenClientProtocol(self, payload=self.payload)


class KrakenSocketManager(threading.Thread):

    STREAM_URL = 'wss://ws.kraken.com'
    PRIVATE_STREAM_URL = 'wss://ws-auth.kraken.com'

    def __init__(self):  # client
        """Initialise the KrakenSocketManager"""
        threading.Thread.__init__(self)
        self.factories = {}
        self._connected_event = threading.Event()
        self._conns = {}
        self._user_timer = None
        self._user_listen_key = None
        self._user_callback = None

    def _start_socket(self, id_, payload, callback, private=False):
        if id_ in self._conns:
            return False

        if private:
            factory_url = self.PRIVATE_STREAM_URL
        else:
            factory_url = self.STREAM_URL

        factory = KrakenClientFactory(factory_url, payload=payload)
        factory.base_client = self
        factory.protocol = KrakenClientProtocol
        factory.callback = callback
        factory.reconnect = True
        self.factories[id_] = factory
        reactor.callFromThread(self.add_connection, id_, factory_url)

    def add_connection(self, id_, url):
        """
        Convenience function to connect and store the resulting
        connector.
        """
        if not url.startswith("wss://"):
            raise ValueError("expected wss:// URL prefix")

        hostname = url[6:]

        factory = self.factories[id_]
        options = ssl.optionsForClientTLS(hostname=hostname) # for TLS SNI
        self._conns[id_] = connectWS(factory, options)

    def stop_socket(self, conn_key):
        """Stop a websocket given the connection key

        Parameters
        ----------
        conn_key : str
            Socket connection key

        Returns
        -------
        str, bool
            connection key string if successful, False otherwise
        """
        if conn_key not in self._conns:
            return

        # disable reconnecting if we are closing
        self._conns[conn_key].factory = WebSocketClientFactory(self.STREAM_URL)
        self._conns[conn_key].disconnect()
        del self._conns[conn_key]

    def run(self):
        try:
            reactor.run(installSignalHandlers=False)
        except ReactorAlreadyRunning:
            # Ignore error about reactor already running
            pass

    def close(self):
        """Close all connections
        """
        keys = set(self._conns.keys())
        for key in keys:
            self.stop_socket(key)
        self._conns = {}


class WssClient(KrakenSocketManager):
    """ Websocket client for Kraken """

    ###########################################################################
    # Kraken commands
    ###########################################################################

    def __init__(self, key=None, secret=None, nonce_multiplier=1.0):  # client
        super().__init__()
        self.key = key
        self.secret = secret
        self.nonce_multiplier = nonce_multiplier

    def stop(self):
        """Tries to close all connections and finally stops the reactor.
        Properly stops the program."""
        try:
            self.close()
        finally:
            reactor.stop()

    def subscribe_public(self, subscription, callback, **kwargs):
        self._subscribe(subscription, callback, False, **kwargs)

    def subscribe_private(self, subscription, callback, **kwargs):
        self._subscribe(subscription, callback, True, **kwargs)

    def _subscribe(self, subscription, callback, private, **kwargs):
        if 'pair' in kwargs:
            id_ = "_".join([subscription['name'], kwargs['pair'][0]])
        else:
            id_ = "_".join([subscription['name']])

        data = {
            'event': 'subscribe',
            'subscription': subscription,
        }
        data.update(**kwargs)
        payload = json.dumps(data, ensure_ascii=False).encode('utf8')
        return self._start_socket(id_, payload, callback, private=private)

    def request(self, request, callback, **kwargs):
        id_ = "_".join([request['event'], request['type']])
        payload = json.dumps(request, ensure_ascii=False).encode('utf8')
        return self._start_socket(id_, payload, callback, private=True)
