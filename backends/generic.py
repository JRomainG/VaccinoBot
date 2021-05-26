import abc
import time
import json
import random
import requests
import threading


USER_AGENT_STRING = (
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) Gecko/20100101 Firefox/81.0"
)


class Slot:
    def __init__(self, date, vaccine, address, url):
        self.date = date
        self.vaccine = vaccine
        self.address = address
        self.url = url


class LabBackend(abc.ABC):
    """
    Abstract class for lab backends
    """

    def __init__(self, transport, lab_file, check_interval, confirm_slots, backend_id):
        self.transport = transport
        self.check_interval = check_interval
        self.confirm_slots = confirm_slots
        self.labs = self._load_labs(lab_file, backend_id)
        self.threads = []

        for i in range(len(self.labs)):
            thread = threading.Thread(target=self.check_slot_thread, args=(i,))
            thread.start()
            self.threads.append(thread)

    def lab_list(self):
        out = []
        for lab in self.labs:
            out.append(
                "{address} ({vaccine}): {url}".format(
                    address=lab["address"], vaccine=lab["vaccine"], url=lab["url"]
                )
            )
        return out

    def stop(self):
        pass

    def _get(self, url, params):
        res = requests.get(
            url=url, params=params, headers={"User-Agent": USER_AGENT_STRING}
        )
        return res.text

    def _post(self, url, data):
        res = requests.post(
            url=url, json=data, headers={"User-Agent": USER_AGENT_STRING}
        )
        return res.text

    def _load_labs(self, lab_file, backend_key):
        with open(lab_file) as f:
            labs_json = f.read()
            labs = json.loads(labs_json)
            return labs[backend_key]

    def check_slot_thread(self, lab_id):
        def recurse(self, lab):
            # Get available slots and send a message if there are any
            slots = self._check_lab_slots(lab)
            if len(slots) > 0:
                txt = "Found {vaccine} shot(s) at {address}".format(
                    vaccine=lab["vaccine"], address=lab["address"]
                )
                for slot in slots:
                    txt += "• {}\n".format(slot.date.strftime("%d %b at %Hh%M"))

                txt += "URL: {}".format(lab["url"])
                self.transport.send_message(txt)

            # Wait self.check_interval seconds, with some random offset
            # to avoid being banned
            time.sleep(self.check_interval + random.randint(-30, 30))

            recurse(self, lab)

        # Wait a random amount of time before starting so not all
        # requests are sent at the same time
        time.sleep(random.randint(5, self.check_interval))

        lab = self.labs[lab_id]
        recurse(self, lab)

    @abc.abstractmethod
    def _check_lab_slots(self, lab_id):
        pass

    def check_all_lab_slots(self):
        out = []

        for lab in self.labs:
            out += self._check_lab_slots(lab)

        return out
