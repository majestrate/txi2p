# Copyright (c) str4d <str4d@mail.i2p>
# See COPYING for details.

import os
from parsley import makeProtocol
from twisted.internet import defer
from twisted.python import log

from txi2p import grammar
from txi2p.sam.base import SAMSender, SAMReceiver, SAMFactory


class SessionCreateSender(SAMSender):
    def sendSessionCreate(self, style, id, privKey=None, options={}):
        msg = 'SESSION CREATE'
        msg += ' STYLE=%s' % style
        msg += ' ID=%s' % id
        msg += ' DESTINATION=%s' % (privKey if privKey else 'TRANSIENT')
        for option in options:
            msg += ' %s=%s' % option
        msg += '\n'
        self.transport.write(msg)


class SessionCreateReceiver(SAMReceiver):
    def command(self):
        if not (hasattr(self.factory, 'nickname') and self.factory.nickname):
            # All tunnels in the same process use the same nickname
            # TODO is using the PID a security risk?
            self.factory.nickname = 'txi2p-%d' % os.getpid()

        self.sender.sendSessionCreate(
            'STREAM',
            self.factory.nickname,
            self.factory.privKey,
            self.factory.options)
        self.currentRule = 'State_create'

    def create(self, result, destination=None, message=None):
        if result != 'OK':
            self.factory.resultNotOK(result, message)
            return

        self.sender.sendNamingLookup('ME')
        self.currentRule = 'State_naming'

    def postLookup(self, dest):
        self.factory.sessionCreated(self, dest)

    def destGenerated(self, pub, priv):
        pass


# A Protocol for making a SAM session
SessionCreateProtocol = makeProtocol(
    grammar.samGrammarSource,
    SessionCreateSender,
    SessionCreateReceiver)


class SessionCreateFactory(SAMFactory):
    protocol = SessionCreateProtocol

    def __init__(self, nickname, keyfile=None, options={}):
        self.nickname = nickname
        self._keyfile = keyfile
        self.options = options
        self.deferred = defer.Deferred(self._cancel)

    def startFactory(self):
        self.privKey = None
        self._writeKeypair = False
        if self._keyfile:
            try:
                f = open(self._keyfile, 'r')
                self.privKey = f.read()
                f.close()
            except IOError:
                log.msg('Could not load private key from %s' % sef._keyfile)
                self._writeKeypair = True

    def sessionCreated(self, proto, pubKey):
        if self._writeKeypair:
            try:
                f = open(self._keyfile, 'w')
                f.write(self.privKey)
                f.close()
            except IOError:
                log.msg('Could not save private key to %s' % self._keyfile)
        # Now continue on with creation of SAMSession
        self.deferred.callback((self.nickname, proto, pubKey))


# Dictionary containing all active SAM sessions
_sessions = {}


class SAMSession(object):
    samEndpoint = None
    nickname = None
    proto = None
    streams = []

    def removeStream(self, stream):
        self.streams.remove(stream)
        if not self.streams:
            # No more streams, close the session
            self.proto.transport.loseConnection()
            del _sessions[self.samEndpoint][self.nickname]


def getSession(samEndpoint, nickname, **kwargs):
    if _sessions.has_key(samEndpoint):
        if _sessions[samEndpoint].has_key(nickname):
            return defer.succeed(sessions[samEndpoint][nickname])
    else:
        _sessions[samEndpoint] = {}

    def createSession((id, proto, pubKey)):
        s = SAMSession()
        s.samEndpoint = samEndpoint
        s.id = id
        s.proto = proto
        s.pubKey = pubKey
        _sessions[samEndpoint][nickname] = s
        return s

    sessionFac = SessionCreateFactory(nickname, **kwargs)
    d = samEndpoint.connect(sessionFac)
    # Force caller to wait until the session is actually created
    d.addCallback(lambda proto: sessionFac.deferred)
    d.addCallback(createSession)
    return d