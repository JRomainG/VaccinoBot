#!/usr/bin/env python3
import json
import time
import requests
import urllib.parse


USER_AGENT_STRING = (
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) Gecko/20100101 Firefox/81.0"
)

# Enter doctlib URLs, e.g. "https://www.doctolib.fr/vaccination-covid-19/paris/centre-de-vaccination-covid-19-ville-de-paris?pid=practice-176642"
LAB_URLS = []


def get_lab_options(lab_url, lab_id):
    url = "https://www.doctolib.fr/booking/{}.json".format(lab_id)
    res = requests.get(url=url, headers={"User-Agent": USER_AGENT_STRING})
    lab_info = json.loads(res.text)["data"]

    # Parse information about the lab itself
    lab_addr = "{name}, {address}".format(
        name=lab_info["places"][0]["name"],
        address=lab_info["places"][0]["full_address"],
    )

    # Build a list of agendas available for each motive
    motive_to_agenda_mapping = {}
    for agenda in lab_info["agendas"]:
        if (
            agenda["booking_disabled"] is True
            or agenda["booking_temporary_disabled"] is True
        ):
            continue

        for motive_ids in agenda["visit_motive_ids"]:
            if motive_ids not in motive_to_agenda_mapping:
                motive_to_agenda_mapping[motive_ids] = []

            motive_to_agenda_mapping[motive_ids].append(agenda)

    practice_ids = []
    for place in lab_info["places"]:
        practice_ids += place["practice_ids"]

    out = []

    for motive in lab_info["visit_motives"]:
        # Make sure this is a first injection
        if not motive["vaccination_motive"] or not motive["first_shot_motive"]:
            continue

        # New patients need to be allowed
        if not motive["allow_new_patients"]:
            continue

        # Only Moderna and Pfizer-BioNTech are allowed for everyone
        vaccine_type = None
        if "Moderna" in motive["name"]:
            vaccine_type = "Moderna"
        elif "Pfizer-BioNTech" in motive["name"]:
            vaccine_type = "Pfizer-BioNTech"
        else:
            continue

        # Make sure there are available agendas (and thus booking slots) for
        # this motive
        agendas = motive_to_agenda_mapping.get(motive["id"], None)
        if not agendas:
            continue

        # Group agendas by practice
        practice_to_agenda_mapping = {}
        for agenda in agendas:
            if agenda["practice_id"] not in practice_to_agenda_mapping:
                practice_to_agenda_mapping[agenda["practice_id"]] = []

            practice_to_agenda_mapping[agenda["practice_id"]].append(agenda["id"])

        for practice_id in practice_to_agenda_mapping.keys():
            info = {
                "vaccine": vaccine_type,
                "address": lab_addr,
                "url": lab_url,
                "practice_ids": [practice_id],
                "visit_motive_ids": [motive["id"]],
                "agenda_ids": practice_to_agenda_mapping[practice_id],
            }

            print("Adding motive", motive["name"], "with info", info)
            out.append(info)

    return out


if __name__ == "__main__":
    labs = []

    for lab_url in LAB_URLS:
        parsed_url = urllib.parse.urlparse(lab_url)
        lab_id = parsed_url.path.split("/")[-1]
        labs += get_lab_options(lab_url, lab_id)
        time.sleep(0.1)

    with open("generated_labs.json", "w") as f:
        f.write(json.dumps({"doctolib": labs}, indent=4))
