
import re
from helpers.logregex import AFK_ON_REGEX, AFK_OFF_REGEX
from pyprowl import Prowl
from helpers import config
from helpers.win32 import getIdleTime


class LogStreamer:

    def __init__(self):
        self.trigger_cache = None
        self.trigger_cache_hash = None
        self.is_afk = False

    def is_idle_or_afk(self):
        if not config.data['push']['push_enabled']:
            return False
        idle_time = config.data['push']['idle_time_to_afk']
        if idle_time > 0:
            return self.is_afk or getIdleTime() > idle_time
        else:
            return self.is_afk

    def get_regex_triggers(self):
        cfg = tuple([tuple(l) for l in config.data['push']['triggers']])
        cfghash = hash(cfg)
        if self.trigger_cache_hash != cfghash:
            self.trigger_cache_hash = cfghash
            self._compile_triggers()
        return self.trigger_cache

    def get_character_names(self):
        return ["you"] + list(map(lambda c: c.strip().lower(), config.data['push']['character_names'].split(',')))

    def handle_timer_expiry(self, spell, target):
        if not config.data['push']['timer_expiry'] or not config.data['push']['push_enabled']:
            return

        if config.data['push']['timer_expiry_afk_only'] and not self.is_idle_or_afk():
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
            print("DEBUG: %s" % text)
            return
        elif AFK_OFF_REGEX.match(text):
            print("DEBUG: %s" % text)
            self.is_afk = False
            return

        # Skip if we are not using push notifications
        if config.data['push']['push_enabled'] is False:
            return

        # Detect triggers
        for name, trigger in self.get_regex_triggers():
            match = trigger.match(text)
            if match:
                if len(config.data['push']['prowl_api_key']) == 0:
                    print("LogStreamer ERROR: No API key supplied")
                    continue
                if not self.is_idle_or_afk() and config.data['push']['afk_only']:
                    print("DEBUG: Skipping %s because you are not AFK." % name)
                    continue

                source = match.groupdict().get('source', None)
                if source and source.strip().lower() in self.get_character_names():
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

    def _compile_triggers(self):
        self.trigger_cache = []
        for name, regex in config.data['push']['triggers']:
            self.trigger_cache.append(
                (name, re.compile(regex))
            )

