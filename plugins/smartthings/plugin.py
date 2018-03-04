import json
import requests
from fuzzywuzzy import fuzz

from disco.bot import Plugin, Config
from disco.bot.command import CommandError
from disco.types.user import Status, Game, GameType
from disco.types.message import Emoji, MessageEmbed

from pubnub.callbacks import SubscribeCallback
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub, PNReconnectionPolicy

EVENT_CALLBACK_MSG = '`{}` - {}: {}'


class SwitchEmbed(MessageEmbed):
    def set_device(self, device):
        self.title = device['name']
        self.description = 'Toggle the switch on and off'
        val = device['attributes']['switch']
        self.add_field(name='Current State', value=val)
        color = 0x000000
        if val == 'on':
            color = 0xFFFFFF
        self.color = color


class EventEmbed(MessageEmbed):
    attribute = None
    emoji = ':spenbot_on:'
    user = '<@61189081970774016>'
    colors = {}
    include = None
    messages = {}

    def set_device(self, device):
        name = device['name']
        self.title = name
        attr = device['attributes'][self.attribute]
        self.description = '{} - __{}__ is **{}**!'.format(self.user, name, attr)
        if self.include and attr not in self.include:
            return False
        if attr in self.messages:
            self.description = '{} - __{}__ {}'.format(self.user, name, self.messages[attr])
        if attr in self.colors:
            self.color = self.colors[attr]
        self.footer = {
            'text': 'Attribute: {}'.format(self.attribute.title())
        }
        return True


class DoorEmbed(EventEmbed):
    attribute = 'contact'
    emoji = ':door:'
    colors = {
        'open': 0x00FF00,
        'closed': 0xFF0000
    }


class PresenceEmbed(EventEmbed):
    attribute = 'presence'
    emoji = ':iphone:'
    colors = {
        'present': 0x44CCFF,
        'not present': 0xFFB01E
    }


class MotionEmbed(EventEmbed):
    attribute = 'presence'
    emoji = ':iphone:'
    include = {
        'active'
    }
    messages = {
        'active': 'has been triggered!'
    }
    colors = {
        'active': 0x44CCFF,
        'inactive': 0xFFB01E
    }


class EventCallback(SubscribeCallback):
    def __init__(self, plugin):
        self.plugin = plugin
        super(EventCallback, self).__init__()

    def presence(self, pubnub, presence):
        pass

    def status(self, pubnub, status):
        pass

    def message(self, pubnub, message):
        if self.plugin.config.pubnub_channel_id:
            chan = self.plugin.state.channels[self.plugin.config.pubnub_channel_id]
            msg = message.message
            device = self.plugin.devices[msg['device']]
            name = 'Unknown Device'
            if device:
                name = device['name']
            chan.send_message(EVENT_CALLBACK_MSG.format(name, msg['attribute'], msg['value']))
            if device:
                device['attributes'][msg['attribute']] = msg['value']
                event_chan = self.plugin.state.channels[self.plugin.config.events_channel_id]
                # Switch
                if msg['attribute'] == 'switch':
                    if msg['device'] in self.plugin.switch_messages:
                        status = SwitchEmbed()
                        status.set_device(device)
                        self.plugin.switch_messages[msg['device']].edit(embed=status)

                # Contact
                if msg['attribute'] == 'contact':
                    status = DoorEmbed()
                    if status.set_device(device) != False:
                        event_chan.send_message(embed=status)

                # Motion
                if msg['attribute'] == 'motion':
                    status = MotionEmbed()
                    if status.set_device(device) != False:
                        event_chan.send_message(embed=status)

                # Motion
                if msg['attribute'] == 'presence':
                    status = PresenceEmbed()
                    if status.set_device(device) != False:
                        event_chan.send_message(embed=status)


class SmartthingsConfig(Config):
    graph_endpoint = 'http://localhost'
    graph_access_token = 'foobar'

    pubnub_enabled = False
    pubnub_sub_key = None
    pubnub_pub_key = None
    pubnub_channel = None

    pubnub_channel_id = None

    events_channel_id = None

    emoji_off = 'spenbot_off:407468391365083167'
    emoji_on = 'spenbot_on:407468402098307072'


@Plugin.with_config(SmartthingsConfig)
class SmartthingsPlugin(Plugin):
    def load(self, ctx):
        super(SmartthingsPlugin, self).load(ctx)
        self.devices = {}
        self.switch_messages = {}
        self.switch_messages_id = {}

        self.load_devices()
        if self.config.pubnub_enabled:
            self.load_pubnub()

    @Plugin.listen('Ready')
    def on_ready(self, event):
        self.client.update_presence(Status.ONLINE, Game(
            type=GameType.WATCHING,
            name='{} devices'.format(len(self.devices)),
            url='http://spencer.gg'
        ))

    @Plugin.listen('MessageReactionAdd')
    def on_reaction_add(self, event):
        if self.reaction_hook(event):
            event.delete()

    @Plugin.listen('MessageReactionRemove')
    def on_reaction_remove(self, event):
        self.reaction_hook(event)

    def reaction_hook(self, event):
        if event.user_id == self.state.me.id:
            return
        msg_id = event.message_id
        if msg_id in self.switch_messages_id:
            device = self.switch_messages_id[msg_id]
            device_id = device['deviceid']
            emoji = event.emoji.to_string()
            if emoji == self.config.emoji_on:
                device['attributes']['switch'] = 'on'
                self.api_command(device_id, 'on')
            elif emoji == self.config.emoji_off:
                device['attributes']['switch'] = 'off'
                self.api_command(device_id, 'off')
            status = SwitchEmbed()
            status.set_device(device)
            msg = self.state.channels[event.channel_id].get_message(msg_id)
            msg.edit(embed=status)
            return True
        else:
            return False

    def rank_devices(self, search):
        ranks = []
        for device_id, device in self.devices.iteritems():
            ranks.append((self.devices[device_id], fuzz.token_sort_ratio(search, device['name'])))
        ranks.sort(key=lambda d: d[1], reverse=True)
        return ranks

    def search_devices(self, search, device_filter=None):
        ranks = self.rank_devices(search)
        if device_filter:
            ranks = filter(lambda t: device_filter(t[0]), ranks)
        top = ranks[0]
        top2 = ranks[1]
        if top[1] < 30 or top[1] == top2[1]:
            raise CommandError(':warning: Can\'t find that device! Maybe you mean `{}`, or `{}`?'.format(
                top[0]['name'],
                top2[0]['name']
            ))
        return top[0]

    @Plugin.command('devices', '[capability...]')
    def command_devices(self, event, capability=None):
        self.load_devices()
        device_list = 'Device List:\n\t'
        for deviceid, device in self.devices.iteritems():
            if not capability or capability.lower() in map(lambda c: c.lower(), device['capabilities']):
                device_list += '{} - [`{}`]\n\t'.format(
                    device['name'],
                    '`, `'.join(device['capabilities'])
                )
        event.msg.reply(device_list[:-2])

    @Plugin.command('device', '<device_name:str>')
    def command_device(self, event, device_name):
        device = self.search_devices(device_name)
        msg = '```{}```'.format(json.dumps(device, indent=2))
        event.msg.reply(msg)

    @Plugin.command('find', '<search:str...>')
    def command_find(self, event, search):
        ranks = self.rank_devices(search)
        msg = 'Finding device for query: `{}`\n'.format(search)
        for device, rank in ranks:
            msg += '\t`{}` - {}\n'.format(rank, device['name'])
        event.msg.reply(msg)

    @Plugin.command('switch', '<device_name:str>')
    def command_switch(self, event, device_name):
        device = self.search_devices(device_name, lambda d: 'Switch' in d['capabilities'])
        status = SwitchEmbed()
        status.set_device(device)
        msg = event.msg.reply(embed=status)
        msg.chain(False). \
            add_reaction(get_emoji(self.config.emoji_off)). \
            add_reaction(get_emoji(self.config.emoji_on))

        self.switch_messages[device['deviceid']] = msg
        self.switch_messages_id[msg.id] = device

    def api_call(self, endpoint, payload=None, method='GET'):
        if not payload:
            payload = {}
        url = self.config.graph_endpoint + endpoint
        payload['access_token'] = self.config.graph_access_token
        req = requests.request(method, url=url, params=payload)
        return req

    def api_command(self, device_id, command, params=None, value1=None, value2=None):
        if not params:
            params = {}
        url = self.config.graph_endpoint + '/' + device_id + '/command/' + command
        params['access_token'] = self.config.graph_access_token
        payload = {
            'value1': value1,
            'value2': value2
        }
        req = requests.post(url, params=params, data=json.dumps(payload))
        return req

    def load_devices(self):
        res = self.api_call('/devices')
        self.devices = {}
        for device in res.json()['deviceList']:
            self.devices[device['deviceid']] = device

    """PubNub Stuff"""

    def load_pubnub(self):
        config = PNConfiguration()
        config.subscribe_key = self.config.pubnub_sub_key
        config.publish_key = self.config.pubnub_pub_key
        config.reconnect_policy = PNReconnectionPolicy.LINEAR
        self.pubnub = PubNub(config)
        self.pubnub_listener = EventCallback(self)
        self.pubnub.add_listener(self.pubnub_listener)
        self.pubnub.subscribe().channels(self.config.pubnub_channel).execute()


def get_emoji(emoji_str):
    """From the given emoji string returns an Emoji object"""
    parts = emoji_str.split(':')
    return Emoji(name=parts[0], id=parts[1]) if len(parts) > 1 else Emoji(name=parts[0])
