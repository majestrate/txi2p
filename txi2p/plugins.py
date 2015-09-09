# Copyright (c) str4d <str4d@mail.i2p>
# See COPYING for details.

from twisted.internet.endpoints import clientFromString
from twisted.internet.interfaces import IStreamClientEndpointStringParserWithReactor
from twisted.internet.interfaces import IStreamServerEndpointStringParser
from twisted.python.compat import _PY3
from zope.interface import implementer

#from txi2p.bob.endpoints import BOBI2PClientEndpoint, BOBI2PServerEndpoint
from txi2p.sam.endpoints import (
    SAMI2PStreamClientEndpoint,
    SAMI2PStreamServerEndpoint,
)

DEFAULT_ENDPOINT = {
    'BOB': 'tcp:127.0.0.1:2827',
    'SAM': 'tcp:127.0.0.1:7656',
    }

DEFAULT_API = 'SAM'

if not _PY3:
    from twisted.plugin import IPlugin
else:
    from zope.interface import Interface
    class IPlugin(Interface):
        pass


@implementer(IPlugin, IStreamClientEndpointStringParserWithReactor)
class I2PClientParser(object):
    prefix = 'i2p'

    def _parseBOBClient(self, reactor, host, port, bobEndpoint,
                     tunnelNick=None,
                     inhost='localhost',
                     inport=None,
                     options=None):
        return BOBI2PClientEndpoint(reactor, clientFromString(reactor, bobEndpoint),
                                    host, port, tunnelNick, inhost,
                                    inport and int(inport) or None, options)

    def _parseSAMClient(self, reactor, host, port, samEndpoint,
                     nickname=None,
                     options=None):
        return SAMI2PStreamClientEndpoint(
            clientFromString(reactor, samEndpoint),
            host, port, nickname, options)

    _apiParsers = {
        'BOB': _parseBOBClient,
        'SAM': _parseSAMClient,
        }

    def _parseClient(self, reactor, host, port=None,
                     api=None, apiEndpoint=None, **kwargs):
        if not api:
            if apiEndpoint:
                raise ValueError('api must be specified if apiEndpoint is given')
            else:
                api = DEFAULT_API

        if api not in self._apiParsers:
            raise ValueError('Specified I2P API is invalid or unsupported')

        if not apiEndpoint:
            apiEndpoint = DEFAULT_ENDPOINT[api]

        return self._apiParsers[api](self, reactor, host,
                                     port and int(port) or None,
                                     apiEndpoint, **kwargs)

    def parseStreamClient(self, reactor, *args, **kwargs):
        # Delegate to another function with a sane signature.  This function has
        # an insane signature to trick zope.interface into believing the
        # interface is correctly implemented.
        return self._parseClient(reactor, *args, **kwargs)


@implementer(IPlugin, IStreamServerEndpointStringParser)
class I2PServerParser(object):
    prefix = 'i2p'

    def _parseBOBServer(self, reactor, keypairPath, port, bobEndpoint,
                     tunnelNick=None,
                     outhost='localhost',
                     outport=None,
                     options=None):
        return BOBI2PServerEndpoint(reactor, clientFromString(reactor, bobEndpoint),
                                    keypairPath, port, tunnelNick, outhost,
                                    outport and int(outport) or None, options)

    def _parseSAMServer(self, reactor, keypairPath, port, samEndpoint,
                     nickname=None,
                     options=None):
        return SAMI2PStreamServerEndpoint(reactor,
            clientFromString(reactor, samEndpoint),
            keypairPath, port, nickname, options)

    _apiParsers = {
        'BOB': _parseBOBServer,
        'SAM': _parseSAMServer,
        }

    def _parseServer(self, reactor, keypairPath, port=None,
                     api=None, apiEndpoint=None, **kwargs):
        if not api:
            if apiEndpoint:
                raise ValueError('api must be specified if apiEndpoint is given')
            else:
                api = DEFAULT_API

        if api not in self._apiParsers:
            raise ValueError('Specified I2P API is invalid or unsupported')

        if not apiEndpoint:
            apiEndpoint = DEFAULT_ENDPOINT[api]

        return self._apiParsers[api](self, reactor, keypairPath,
                                     port and int(port) or None,
                                     apiEndpoint, **kwargs)

    def parseStreamServer(self, reactor, *args, **kwargs):
        # Delegate to another function with a sane signature.  This function has
        # an insane signature to trick zope.interface into believing the
        # interface is correctly implemented.
        return self._parseServer(reactor, *args, **kwargs)
