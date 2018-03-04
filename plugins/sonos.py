import urllib

import requests
import soco
from disco.bot import Plugin, Config


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
        msg = event.msg.reply(':loudspeaker: Announcing...')
        self.say(tts_msg)
        msg.edit(':ok: Done announcing: `{}`!'.format(tts_msg))