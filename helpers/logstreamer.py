
import re
from helpers.logregex import AFK_ON_REGEX, AFK_OFF_REGEX
from pyprowl import Prowl
from helpers import config


class LogStreamer:

    def __init__(self):
        self.trigger_cache = None
        self.trigger_cache_hash = None
        self.is_afk = False

    def get_regex_triggers(self):
        cfg = tuple([tuple(l) for l in config.data['spells']['push_notification_triggers']])
        cfghash = hash(cfg)
        if self.trigger_cache_hash != cfghash:
            self.trigger_cache_hash = cfghash
            self._compile_triggers()
        return self.trigger_cache

    def get_character_names(self):
        return list(map(lambda c: c.strip().lower(), config.data['spells']['character_names'].split(',')))

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
        if config.data['spells']['use_push_notifications'] is False:
            return

        # Detect triggers
        for name, trigger in self.get_regex_triggers():
            match = trigger.match(text)
            if match:
                if len(config.data['spells']['prowl_api_key']) == 0:
                    print("LogStreamer ERROR: No API key supplied")
                    continue
                if not self.is_afk and config.data['spells']['use_push_notifications_afk_only']:
                    print("DEBUG: Skipping %s because you are not AFK." % name)
                    continue

                source = match.groupdict().get('source', None)
                if source and source.strip().lower() in self.get_character_names():
                    print("DEBUG: Skipping %s because source is player's character")
                    continue

                print("DEBUG: Sent %s notification: %s" % (name, text))
                prowl = Prowl(config.data['spells']['prowl_api_key'])
                prowl.notify(
                    event=name,
                    description=text,
                    priority=0,
                    appName='EverQuest'
                )

    def _compile_triggers(self):
        self.trigger_cache = []
        for name, regex in config.data['spells']['push_notification_triggers']:
            self.trigger_cache.append(
                (name, re.compile(regex))
            )

