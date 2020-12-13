
import re
from datetime import datetime, timedelta
from helpers.logregex import AFK_ON_REGEX, AFK_OFF_REGEX
from pyprowl import Prowl
from helpers import config
from helpers.win32 import getIdleTime


class LogStreamer:

    def __init__(self):
        self.trigger_cache = None
        self.trigger_cache_hash = None
        self.is_afk = False
        self.camp_time = None
        self.character_name = None

    def shouldPushTriggerNotifications(self):
        push_enabled = config.data['push']['push_enabled']
        afk_only = config.data['push']['afk_only']
        if not push_enabled:
            return False
        if afk_only:
            return self.isUserPlayingEQ() and (self.isAFK() or self.isIdle())
        else:
            return self.isUserPlayingEQ()

    def shouldPushTimerNotifications(self):
        push_enabled = config.data['push']['push_enabled'] and config.data['push']['timer_expiry']
        afk_only = config.data['push']['timer_expiry_afk_only']
        if not push_enabled:
            return False
        if afk_only:
            return self.isUserPlayingEQ() and (self.isAFK() or self.isIdle())
        else:
            return self.isUserPlayingEQ()

    def isAFK(self):
        return self.is_afk

    def isIdle(self):
        idle_time = config.data['push']['idle_time_to_afk']
        if idle_time > 0:
            return getIdleTime() > idle_time
        else:
            return False

    def isUserPlayingEQ(self):
        if self.camp_time:
            return self.camp_time > datetime.now()
        else:
            return True

    def setCharacterName(self, charname):
        self.character_name = charname

    def getRegularExpressionTriggers(self):
        cfg = tuple([tuple(trigger_list) for trigger_list in config.data['push']['triggers']])
        cfghash = hash(cfg)
        if self.trigger_cache_hash != cfghash:
            self.trigger_cache_hash = cfghash
            self._compileTriggers()
        return self.trigger_cache

    def _handleTimerExpiry(self, spell, target):

        if not self.shouldPushTimerNotifications():
            return

        title = spell.name.title()
        if target != '__you__' and target != '__custom__':
            title = "%s | %s" % (spell.name.title(), target)

        description = "Your %s timer has expired." % spell.name.title()
        if spell.id != 0:
            if target == '__you__':
                description = "%s has faded on you." % (spell.name.title())
            else:
                description = "%s has faded on %s." % (spell.name.title(), target)

        prowl = Prowl(config.data['push']['prowl_api_key'])
        prowl.notify(
            event=title,
            description=description,
            priority=0,
            appName='EverQuest'
        )

    def stream(self, timestamp, text):
        # Switch AFK on and off
        if AFK_ON_REGEX.match(text):
            self.is_afk = True
            return
        elif AFK_OFF_REGEX.match(text):
            self.is_afk = False
            return

        # Skip if we are not using push notifications
        if config.data['push']['push_enabled'] is False:
            return

        # Detect when you are camped / in-game
        if text[:20] == "Welcome to EverQuest":
            self.camp_time = None
        elif text[:54] == "It will take about 5 more seconds to prepare your camp":
            self.camp_time = datetime.now() + timedelta(seconds=5)
        elif text[:37] == "You abandon your preparations to camp":
            self.camp_time = None

        # Detect triggers
        for name, trigger in self.getRegularExpressionTriggers():
            match = trigger.match(text)
            if match:
                if len(config.data['push']['prowl_api_key']) == 0:
                    print("LogStreamer ERROR: No API key supplied")
                    continue

                if not self.shouldPushTriggerNotifications():
                    continue

                source = match.groupdict().get('source', None)
                if source and self.character_name and source.strip().lower() in self.character_name:
                    print("DEBUG: Skipping %s because source is player's character")
                    continue

                print("DEBUG: Sent %s notification: %s" % (name, text))
                prowl = Prowl(config.data['push']['prowl_api_key'])
                prowl.notify(
                    event=name,
                    description=text,
                    priority=0,
                    appName='EverQuest'
                )

    def _compileTriggers(self):
        self.trigger_cache = []
        for name, regex in config.data['push']['triggers']:
            self.trigger_cache.append(
                (name, re.compile(regex))
            )

