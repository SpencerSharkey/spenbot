from disco.types.message import MessageEmbed


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
    attribute = 'motion'
    emoji = ':eyes:'
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
