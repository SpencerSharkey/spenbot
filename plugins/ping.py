import socket

from disco.bot import Plugin

class PingPlugin(Plugin):
    def load(self, ctx):
        super(PingPlugin, self).load(ctx)

    @Plugin.command('ping')
    def command_ping(self, event):
        event.msg.reply('`{}` - Hey {}! Pong from `{}`'.format(event.msg.id, event.msg.author.mention, socket.gethostname()))
