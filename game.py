#!/usr/bin/python
###############################################################################
# Copyright (C) 2013-2015 Joe Rawson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
#
# Algorithm:
#
# Need to load the scores, if they exist, and connect to irc, displaying
# a welcome message, then waiting.
#
# Scores should be kept in a class which will hold a nick -> score dict
# object, and at the end of every question will dump the dict to json
# where it can be loaded from.
#
# irc connection should be a class, and we should use twisted. We don't
# really care if people come and go, since everyone in the channel is
# playing. Should handle this like karma. Watch all traffic, and if
# someone blurts out a string that matches the answer, they get the points.
# If they haven't scored before, add them to the scoreboard and give them
# their points, else, add their points to their total. Then dump the json.
#
# This bot requires there to be a ./questions/ directory with text files
# in it full of questions.  While the bot is running, it will randomly choose a
# file from this directory, open it, randomly choose a line, which is
# a question`answer pair, then load that into a structure to be asked.
#
# Once the question is started, the bot will ask the IRC channel the
# question, wait a period of time, show a character, then ask the question
# again. After 3 clues revealed, it will quit the question and reveal the
# answer, and the bot will start again.
#
# The bots libraries are kept in ./lib and imported from there.
#
# The bot should respond to /msgs, so that users can check their scores,
# and admins can give admin commands, like die, show all scores, edit
# player scores, etc. Commands should be easy to implement.
#
###############################################################################
# TODO:
# Make more modular: should have a trivia class that only knows the game, a
# parser that acts as the interface between the irc client and the
# game, since the game should only worry about the game, and then the irc
# client class and factory needed for twisted.
# Make tests: modularity can bring unit-tests into being so that we can test
# refactoring before breaking the world.
#
###############################################################################

import re

from twisted.words.protocols.irc import IRCClient
from twisted.internet import reactor, ssl
from twisted.internet.protocol import ClientFactory
from twisted.internet.task import LoopingCall

from lib.trivia import trivia

import config


class gamebot(IRCClient):
    '''
    This is the irc bot portion of the trivia bot.

    It should really not implement the whole program.

    It should manage the connection to the irc server
    and manage the traffic to-and-from.

    We should figure out where the program should go.
    (Probaby in its own class.)
    '''
    def __init__(self):
        # Know who our masters are.
        self._admins = list(config.ADMINS)
        # Know where we're connecting to.
        self._game_channel = config.GAME_CHANNEL
        # Get a handle on the game being saved in the factory.
        self._game = self.factory._game
        # LoopingCall is the twisted method that implements the state-machine.
        # The game class is responsible for maintaining its state and sending
        # game messages.
        self._lc = LoopingCall(self._game.play_game, self._gmsg)

    def _get_nickname(self):
        return self.factory.nickname

    nickname = property(_get_nickname)

    def _get_lineRate(self):
        return self.factory.lineRate

    lineRate = property(_get_lineRate)

    def _cmsg(self, dest, msg):
        """
        Write a colorized message.
        """
        self.msg(dest, "%s%s" % (config.COLOR_CODE, msg))

    def _gmsg(self, msg):
        """
        Write a message to the channel(s) playing the trivia game.
        """
        self._cmsg(self._game_channel, msg)

    def signedOn(self):
        '''
        Actions to perform on signon to the server.
        '''
        self.join(self._game_channel)
        self.msg('NickServ', 'identify %s' % config.IDENT_STRING)
        print("Signed on as %s." % (self.nickname,))
        if self.factory.running:
            self._start(None, None, None)
        else:
            self._game.start_msg(self._gmsg, self._game_channel, self.nickname)

    def joined(self, channel):
        '''
        Callback runs when the bot joins a channel
        '''
        print("Joined %s." % (channel,))

    def privmsg(self, user, channel, msg):
        '''
        Parse incoming message and pass it to the game's message handler.
        '''
        self._game.parse_msg(user, channel, msg)

    def ctcpQuery(self, user, channel, msg):
        '''
        Responds to ctcp requests.
        Currently just reports them.
        '''
        print("CTCP recieved: "+user+":"+channel+": "+msg[0][0]+" "+msg[0][1])

    def _die(self, *args):
        '''
        Terminates execution of the bot.
        Need to dig into twisted to figure out how this happens.
        '''
        global reactor
        self.quit(message='This is triviabot, signing off.')
        reactor.stop()
        # TODO: figure out how to kill the bot


class ircbotFactory(ClientFactory):
    ''' Factory used to generate a bot instance on the server. '''
    protocol = gamebot

    def __init__(self, nickname=config.NICK):
        self.nickname = nickname
        self.running = False
        self.lineRate = config.LINE_RATE
        # Instantiate a game.
        self._game = trivia(config)

    def clientConnectionLost(self, connector, reason):
        print("Lost connection (%s)" % (reason,))
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print("Could not connect: %s" % (reason,))
        connector.connect()


if __name__ == "__main__":
    # these two lines do the irc connection over ssl.
    reactor.connectSSL(config.SERVER, config.SERVER_PORT,
                       ircbotFactory(), ssl.ClientContextFactory())
    # reactor.connectTCP(config.SERVER, config.SERVER_PORT, ircbotFactory())
    reactor.run()
