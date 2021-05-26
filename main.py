#!/usr/bin/env python3
import logging
import configparser
from backends.doctolib import Doctolib
from transports.telegram import Telegram


class VaccinoBot:
    def __init__(self, transport, lab_file, check_interval, confirm_slots=False):
        self.transport = transport
        self.setup_backends(lab_file, check_interval, confirm_slots)

    def setup_backends(self, lab_file, check_interval, confirm_slots):
        self.backends = [
            Doctolib(self.transport, lab_file, check_interval, confirm_slots)
        ]

    def stop(self):
        pass


def main():
    # Create a bot for each profile
    bots = []

    config = configparser.ConfigParser()
    config.read("profiles.ini")

    for profile in config.sections():
        enabled = config[profile].getboolean("enabled", True)

        if not enabled:
            logging.info("Skipping profile %s because enabled is set to no", profile)
            continue

        lab_file = config[profile]["lab_file"]
        check_interval = config[profile].getint("check_interval", 300)
        confirm_slots = config[profile].getboolean("confirm_slot_availability", False)

        # Create a transport to send messages when a slot is found
        transport = Telegram(config[profile])

        logging.info("Creating bot for profile %s", profile)
        bot = VaccinoBot(transport, lab_file, check_interval, confirm_slots)
        bots.append(bot)

    # Wait for all bots and make sure to stop them all once we're done
    logging.info("Started %d bot(s)", len(bots))
    try:
        while True:
            input("Use Ctrl+C to stop\n")
    except KeyboardInterrupt:
        pass
    finally:
        logging.info("Stopping all bots...")
        for bot in bots:
            bot.stop()


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)
    main()
