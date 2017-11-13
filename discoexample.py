import socket

from disco.bot import Plugin

class DiscoExample(Plugin):
    @Plugin.command('ping')
    def command_ping(self, event):
        event.msg.reply('Pong, from `' + socket.gethostname() + '`!')
