import flask
import gevent
from disco.voice import VoiceException, BufferedOpusEncoderPlayable, Player
from flask import request
import soco

from disco.bot import Plugin, Config
from disco.bot.command import CommandError

from disco.voice.playable import FFmpegInput

from lib import aws

class VoiceConfig(Config):
    aws_access_key_id = None
    aws_secret_access_key = None

@Plugin.with_config(VoiceConfig)
class VoicePlugin(Plugin):
    def load(self, ctx):
        self.polly = aws.client('polly', self.config)
        self.channels = {}
        self.files = {}


    @Plugin.listen('VoiceStateUpdate')
    def on_voice_state_update(self, event):
        state = event.state
        if state.user_id == self.bot.client.state.me.id:
            return

        if state.channel_id:
            # joined
            self.channels[state.user_id] = state.channel_id
            try:
                client = state.channel.connect()
            except VoiceException as e:
                print 'woo'

            player = Player(client)

            msg_id = str(state.user_id)
            res = self.polly.synthesize_speech(
                OutputFormat='mp3',
                Text=state.user.username + ' has joined the channel!',
                VoiceId='Brian'
            )

            self.files[msg_id] = res['AudioStream'].read()

            ffmpeg = FFmpegInput(source='http://192.168.1.69/plugins/voice/serve_polly/{}'.format(state.user_id))
            item = ffmpeg.pipe(BufferedOpusEncoderPlayable)

            player.queue.append(item)

            player.complete.wait()

            player.disconnect()

        else:
            #left
            if state.user_id in self.channels:
                #channel =
                del self.channels[state.user_id]


    @Plugin.route('/plugins/voice/serve_polly/<msg>')
    def on_serve_the_polly(self, msg):
        print msg
        if msg in self.files:
            content = self.files[msg]
            return flask.Response(content, mimetype='audio/mp3')
        return flask.Response(status=404)