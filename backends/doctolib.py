import time
import json
import random
import logging
import datetime
from .generic import LabBackend, Slot


class Doctolib(LabBackend):
    def __init__(self, *args):
        super().__init__(*args, "doctolib")

    def _confirm_slot_availability(self, lab_info, slot_info):
        """
        Even though a slot shows up, it may not be available (clicking on it
        will show that it's unavailable), so double check here
        """
        logging.debug(
            "Making sure that slot %s is available for %s", slot_info, lab_info["url"]
        )

        # There are usually 2 steps (first shot and then second shot), but it's
        # not the case for all vaccines
        # Here, we only want to check that the first shot is available
        steps = slot_info["steps"]
        if not steps:
            return False

        url = "https://www.doctolib.fr/appointments.json"
        data = {
            "practice_ids": lab_info["practice_ids"],
            "agenda_ids": "-".join(map(str, lab_info["agenda_ids"])),
            "appointment": {
                "profile_id": random.randint(100000, 999999),
                "source_action": "profile",
                "start_date": steps[0]["start_date"],
                "visit_motive_ids": str(
                    steps[0]["visit_motive_id"]
                ),  # This is sent as a string for some reason
            },
        }
        try:
            time.sleep(1)
            tmp = self._post(url, data)
            response = json.loads(tmp)
        except json.decoder.JSONDecodeError as e:
            logging.warning("Failed to parse data for slot")
            logging.debug(
                "Sent json %s for lab %s and slot %s", data, lab_info, slot_info
            )
            raise e

        if response.get("error", None) == "unavailable_slot":
            logging.info("Slot is actually unavailable :(")
            return False

        logging.info("Got slot confirmation for %s", data)
        return True

    def _is_slot_valid(self, lab_info, slot_info):
        # Make sure the slot is less than 24 hours from now
        start_time = datetime.datetime.fromisoformat(slot_info["start_date"])
        if start_time.timestamp() - time.time() > 86400:
            return False

        # Make sure the slot is not a ghost slot
        if self.confirm_slots:
            # Try to confirm the slot up to 3 times
            for _ in range(3):
                try:
                    return self._confirm_slot_availability(lab_info, slot_info)
                except json.decoder.JSONDecodeError:
                    # It seems like this is triggering errors sometimes...
                    # I assume it's because we are sending too many requests
                    time.sleep(20)

            # In doubt, assume the slot is unavailable
            # If the bot has too many false negatives, change this
            logging.warning("Failed to confirm slot availability, skipping...")
            return False

        return True

    def _check_lab_slots(self, lab_info):
        logging.info("Checking available slots for %s", lab_info["url"])

        url = "https://www.doctolib.fr/availabilities.json"
        params = {
            "start_date": datetime.date.today().strftime("%Y-%m-%d"),
            "practice_ids": "-".join(map(str, lab_info["practice_ids"])),
            "visit_motive_ids": "-".join(map(str, lab_info["visit_motive_ids"])),
            "agenda_ids": "-".join(map(str, lab_info["agenda_ids"])),
            "insurance_sector": "public",
            "destroy_temporary": True,
            "limit": 4,
        }

        try:
            tmp = self._get(url, params)
            response = json.loads(tmp)
            availabilities = response["availabilities"]
        except (json.decoder.JSONDecodeError, KeyError):
            logging.error("Failed to parse data %s", tmp)
            logging.debug("Sent params %s for lab %s", params, lab_info)
            return []

        out = []
        for day in availabilities:
            for slot_info in day["slots"]:
                # Skip slots which are not usable for our target audience
                if not self._is_slot_valid(lab_info, slot_info):
                    continue

                logging.info("** Found available slot: %s for %s", slot_info, lab_info)
                start_time = datetime.datetime.fromisoformat(slot_info["start_date"])
                data = Slot(
                    start_time,
                    lab_info["vaccine"],
                    lab_info["address"],
                    lab_info["url"],
                )
                out.append(data)

        return out
