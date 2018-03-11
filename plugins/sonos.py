import flask

import gevent
import soco
from disco.bot import Plugin, Config
from disco.bot.command import CommandError

from lib import aws


class SonosConfig(Config):
    aws_access_key_id = None
    aws_secret_access_key = None
    sonos_discovery_interface = None
    sonos_discovery_timeout = 5


@Plugin.with_config(SonosConfig)
class SonosPlugin(Plugin):
    def __init__(self, *args, **kwargs):
        super(SonosPlugin, self).__init__(*args, **kwargs)
        self.speakers = set()
        self.messages = {}
        self.polly = aws.client('polly', self.config)
        self.devices = soco.discovery.discover(
            timeout=self.config.sonos_discovery_timeout,
            interface_addr=self.config.sonos_discovery_interface
        )
        self.sonos = next(iter(self.devices)).group.coordinator

    def load(self, ctx):
        self.spawn(self.discover)

    def play_all(self, media_uri):
        for speaker in self.speakers:
            speaker.play_uri(media_uri)

    def discover(self):
        print 'Discovering Sonos devices...'
        discovered = soco.discover(timeout=self.config.sonos_discovery_timeout, interface_addr=self.config.sonos_discovery_interface)
        if discovered:
            self.speakers = discovered
        else:
            self.speakers = set()

    @Plugin.route('/plugins/sonos/serve_polly/<msg>')
    def on_serve_polly(self, msg):
        print msg
        if msg in self.messages:
            content = self.messages[msg]
            return flask.Response(content, mimetype='audio/mp3')
        return flask.Response(status=404)

    def say(self, msg_id, msg):
        msg_id = str(msg_id)
        res = self.polly.synthesize_speech(
            OutputFormat='mp3',
            Text=msg,
            VoiceId='Brian'
        )
        self.messages[msg_id] = res['AudioStream'].read()
        host = 'x-rincon-mp3radio://{}:{}'.format(self.bot.config.http_host, self.bot.config.http_port)
        print 'Playing to {}'.format(self.sonos.player_name)
        vol = self.sonos.volume
        size = len(self.messages[msg_id])
        self.sonos.volume = 50
        self.sonos.play_uri('{}/plugins/sonos/serve_polly/{}'.format(host, msg_id), title='TTS', force_radio=True)
        gevent.sleep((size * 8)/22050)
        del self.messages[msg_id]
        self.sonos.volume = vol

    @Plugin.listen('MessageCreate')
    def on_messagecreate(self, event):
        msg = event.message
        if 61189081970774016 in msg.mentions:
            announcement = msg.channel.send_message(':loudspeaker: :house: Letting Spencer know that he was mentioned.')
            self.say(msg.id, u'Mentioned on Discord: {}'.format(msg.with_proper_mentions).replace('#0001', ''))
            gevent.sleep(5)
            announcement.delete()

    @Plugin.command('discover', group='sonos')
    def command_discover(self, event):
        self.bot.client.api.channels_typing(event.channel.id)
        self.discover()
        msg = 'Discovered Speakers:'
        for speaker in self.speakers:
            msg += '\n\t{} - `{}`'.format(speaker.player_name, speaker.ip_address)
        event.msg.reply(msg)

    @Plugin.command('say', '<tts_msg:str...>')
    def command_say(self, event, tts_msg):
        if len(tts_msg) > 100:
            raise CommandError(':warning: Your speech is too powerful! Shorten it down a bit.')
        if tts_msg.lower().startswith('alexa'):
            raise CommandError(':rage: Stop trying to activate Alexa!')
        msg = event.msg.reply(':loudspeaker: Announcing...')
        self.say(event.msg.id, tts_msg.encode('utf8'))
        msg.delete()
