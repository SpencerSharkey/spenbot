# -*- coding: utf-8 -*-
import socket

from disco.bot import Plugin

MSG_WELCOME = """**:shinto_shrine: Welcome {} to the RUST village gate! :shinto_shrine:**
A member of the village will need to approve your request to join. For now, hang out and talk here!"""

MSG_WELCOME_ERROR = """Whoa there, {}! You've already requested to join the RUST village!"""

CHANNEL_VILLAGE_GATE = 412223344495165440
CHANNEL_VILLAGE_CHAT = 412223366674776065

ROLE_ADMIN = 373919597209976832
ROLE_RUST = 412223931013922826
ROLE_RUST_VILLAGE = 412224960317358080

class RustPlugin(Plugin):
    def load(self, ctx):
        super(RustPlugin, self).load(ctx)

    @Plugin.command('rust')
    def command_rust(self, event):

        guild = event.msg.channel.guild
        if not guild:
            return

        member = guild.get_member(event.msg.author)
        if not member:
            return

        if ROLE_RUST in member.roles:
            return event.msg.reply(MSG_WELCOME_ERROR.format(event.msg.author.mention))

        member.add_role(ROLE_RUST)
        channel = guild.channels.get(CHANNEL_VILLAGE_GATE)
        channel.send_message(MSG_WELCOME.format(event.msg.author.mention))

        event.msg.add_reaction('✅')

    @Plugin.command('approve', '<user:int>')
    def command_approve(self, event, user):

        guild = event.msg.channel.guild
        if not guild:
            return

        member = guild.get_member(event.msg.author)
        if not member:
            return

        if ROLE_RUST not in member.roles:
            return event.msg.reply('That user isn\'t even at the gate. Tell them to type `!rust` if they want to play. Then re-approve')

        if ROLE_RUST_VILLAGE in member.roles or ROLE_ADMIN in member.roles:
            target = guild.get_member(user)

            if not target:
                return event.msg.reply('User {} not found! Did you copy the right ID?'.format(user))


            target.add_role(ROLE_RUST_VILLAGE)

            event.msg.add_reaction('✅')

            event.msg.reply(':tada: {} has been added to the RUST village! They are worthy!'.format(target.user.mention))
