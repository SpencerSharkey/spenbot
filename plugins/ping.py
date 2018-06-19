import socket

from disco.bot import Plugin

PY_CODE_BLOCK = '```py\n{}\n```'

class PingPlugin(Plugin):
    def load(self, ctx):
        super(PingPlugin, self).load(ctx)

    @Plugin.command('ping')
    def command_ping(self, event):
        event.msg.reply('`{}` - Hey {}! Pong from `{}`'.format(event.msg.id, event.msg.author.mention, socket.gethostname()))

    @Plugin.command('eval')
    def command_eval(self, event):
        if event.msg.author.id != 61189081970774016:
             return event.msg.reply('Not spencer')
        ctx = {
            'bot': self.bot,
            'client': self.bot.client,
            'state': self.bot.client.state,
            'event': event,
            'msg': event.msg,
            'guild': event.msg.guild,
            'channel': event.msg.channel,
            'author': event.msg.author
        }

        # Mulitline eval
        src = event.codeblock
        if src.count('\n'):
            lines = filter(bool, src.split('\n'))
            if lines[-1] and 'return' not in lines[-1]:
                lines[-1] = 'return ' + lines[-1]
            lines = '\n'.join('    ' + i for i in lines)
            code = 'def f():\n{}\nx = f()'.format(lines)
            local = {}

            try:
                exec(compile(code, '<eval>', 'exec'), ctx, local)
            except Exception as e:
                event.msg.reply(PY_CODE_BLOCK.format(type(e).__name__ + ': ' + str(e)))
                return

            event.msg.reply(PY_CODE_BLOCK.format(pprint.pformat(local['x'])))
        else:
            try:
                result = eval(src, ctx)
            except Exception as e:
                event.msg.reply(PY_CODE_BLOCK.format(type(e).__name__ + ': ' + str(e)))
                return

            event.msg.reply(PY_CODE_BLOCK.format(result))
