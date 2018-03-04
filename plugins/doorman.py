# -*- coding: utf-8 -*-
import socket

from disco.bot import Plugin

DOORMAN_CHANNEL = 412363722791714827

MSG_JOIN = ':inbox_tray: {} has joined our wholesome server!'
MSG_LEAVE = ':outbox_tray: {} has left the server!'

class DoormanPlugin(Plugin):
    def load(self, ctx):
        super(DoormanPlugin, self).load(ctx)

    @Plugin.listen('GuildMemberAdd')
    def on_GuildMemberAdd(self, event):
        user = event.member.user
        channel = self.state.channels[DOORMAN_CHANNEL]
        channel.send_message(MSG_JOIN.format(user.mention))

    @Plugin.listen('GuildMemberRemove')
    def on_GuildMemberRemove(self, event):
        user = event.user
        channel = self.state.channels[DOORMAN_CHANNEL]
        channel.send_message(MSG_LEAVE.format(user.mention))
