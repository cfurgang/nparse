import re

DEFAULT_PUSH_REGEXES = (
    ("Melee Damage On You",
        r'^(?P<source>[\w\s]+?) (?P<attack>\w+?)e?s? YOU for (?P<damage>\d+) points of damage\.$'),
    ("Melee Miss On You",
        r'^(?P<source>[\w\s]+?) tries to (?P<attack>\w+?) YOU, but (?P<miss>\w+?)e?s?!$'),
    ("Slain",
        r'^(?P<target>[\w\s]+?) (?:have|has) been slain by (?P<source>.*)\.'),
    ("You died",
        r'^You died\.'),
    ("Knocked unconscious",
        r'You have been knocked unconscious!'),
    ("Charm Break!",
        r'Your charm spell has worn off\.'),
    ("/tell",
        r'^(?P<source>[\w]+) -> (?P<target>[\w]+): (?P<message>.*)$'),
    ("/say",
        r'^(?P<source>[\w]+) says?, \'(?P<message>.*)\'$'),
    ("/ooc",
        r'^(?P<source>[\w]+) says? out of character, \'(?P<message>.*)\'$'),
    ("/auction",
        r'^(?P<source>[\w]+) auctions?, \'(?P<message>.*)\'$'),
    ("/gsay",
        r'^(?P<source>[\w]+) tells? (?:your party|the group), \'(?P<message>.*)\'$'),
    ("/shout",
        r'^(?P<source>[\w]+) shouts?, \'(?P<message>.*)\'$'),
    ("/guildsay",
        r'^(?P<source>[\w]+) (?:say to your|tells the) guild, \'(?P<message>.*)\'$'),
)

AFK_ON_REGEX = re.compile(r'^You are now A\.F\.K. \(Away From Keyboard\)\.$')
AFK_OFF_REGEX = re.compile(r'^You are no longer A\.F\.K. \(Away From Keyboard\)\.$')
