from random import randrange
import urllib
import flask
import gevent
from disco.voice import VoiceException, BufferedOpusEncoderPlayable, Player
from flask import request
import soco

from disco.bot import Plugin, Config
from disco.bot.command import CommandError

from disco.voice.playable import FFmpegInput

from lib import aws

class QueueObject():
    channel_id = None
    text = None

    def __init__(self, channel_id, text):
        self.channel_id = channel_id
        self.text = text

    def play(self, bot):
        client = bot.client.state.channels[self.channel_id].connect()
        player = Player(client)
        msg_id = str(randrange(1000))
        if msg_id not in bot.plugins['VoicePlugin'].files:
            res = bot.plugins['VoicePlugin'].polly.synthesize_speech(
                OutputFormat='mp3',
                Text=self.text,
                VoiceId='Brian'
            )
            bot.plugins['VoicePlugin'].files[msg_id] = res['AudioStream'].read()

        ffmpeg = FFmpegInput(source='http://10.0.32.1:8082/plugins/voice/serve_polly/{}'.format(msg_id))
        item = ffmpeg.pipe(BufferedOpusEncoderPlayable)
        player.play(item)
        player.disconnect()

class VoiceConfig(Config):
    aws_access_key_id = None
    aws_secret_access_key = None

@Plugin.with_config(VoiceConfig)
class VoicePlugin(Plugin):
    def load(self, ctx):
        self.polly = aws.client('polly', self.config)
        self.channels = {}
        self.files = {}
        self.queue = gevent.queue.Queue()
        self.spawn(self.worker)

    def worker(self):
        while True:
            for item in self.queue:
                item.play(self.bot)

    @Plugin.listen('VoiceStateUpdate')
    def on_voice_state_update(self, event):
        state = event.state
        if state.user_id == self.bot.client.state.me.id:
            return

	chan = None
        action = 'Joined'

        chan_left = None
        if state.user_id in self.channels:
            chan_left = self.channels[state.user_id]

        joined = True
        if state.channel_id:
            # joined
            self.channels[state.user_id] = state.channel_id
            chan = state.channel_id
        else:
            del self.channels[state.user_id]
            joined = False

        g = self.bot.client.state.channels[chan].guild

        c = self.bot.client.state.channels[chan]
        print c.recipients

        m = g.members[state.user_id]
        name = state.user.username
        if m.nick:
            name = m.nick

        if joined:
            o = QueueObject(chan, '{} has {} the channel!'.format(name, action))
            self.queue.put(o)

        if not chan_left:
            return

        o = QueueObject(chan_left, '{} has left the channel!'.format(name))
        self.queue.put(o)

    @Plugin.route('/plugins/voice/serve_polly/<msg>')
    def on_serve_the_polly(self, msg):
        print msg
        if msg in self.files:
            content = self.files[msg]
            return flask.Response(content, mimetype='audio/mp3')
        return flask.Response(status=404)
