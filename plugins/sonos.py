import urllib

import requests
import soco
from disco.bot import Plugin, Config
from disco.bot.command import CommandError


class SonosConfig(Config):
    http_bridge_uri = 'http://localhost:5005'
    discovery_interface = None
    discovery_timeout = 5


@Plugin.with_config(SonosConfig)
class SonosPlugin(Plugin):
    def __init__(self, *args, **kwargs):
        super(SonosPlugin, self).__init__(*args, **kwargs)
        self.speakers = set()

    def load(self, ctx):
        self.spawn(self.discover)

    def play_all(self, media_uri):
        for speaker in self.speakers:
            speaker.play_uri(media_uri)

    def discover(self):
        print 'Discovering Sonos devices...'
        discovered = soco.discover(timeout=self.config.discovery_timeout, interface_addr=self.config.discovery_interface)
        if discovered:
            self.speakers = discovered
        else:
            self.speakers = set()

    def say(self, msg):
        requests.get(self.config.http_bridge_uri + '/sayall/' + urllib.quote(msg))

    @Plugin.listen('MessageCreate')
    def on_messagecreate(self, event):
        msg = event.message
        if 61189081970774016 in msg.mentions:
            announcement = msg.channel.send_message(':loudspeaker: :house: Letting Master Spencer know that he was mentioned.')
            self.say(u'Mentioned on Discord: {}'.format(msg.with_proper_mentions).replace('#0001', ''))
            announcement.edit(':loudspeaker: :house: :ok: Announced to home speakers that Master Spencer was mentioned!')

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
        self.say(tts_msg.encode('utf8'))
        msg.edit(u':ok: Done announcing: `{}`'.format(tts_msg))
