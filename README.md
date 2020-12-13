# Nomns' Parser for Project1999


Provides player location and spell tracking support for Project 1999 by reading the player log.

This fork of nparse adds the following features:

* Set custom timers through an in-game command. To do this, use the command `/tell "ntimer <name> <duration>"` (quotes are important). For example, `/tell "ntimer repops 001630"` to set a 16 minute 30 second timer called "Repops"
* Receive push notifications on your iPhone when important things happen. Push notifications can be set to only happen when you are AFK or idle. 
* Automatically pause timers on any spells cast on you while you are camped. Note that quitting nparse will clear all timers.
* Saves the timers of spells cast on you between runs of nparse for each character you log into.