#!/usr/bin/env python3

import argparse
import subprocess
import smtplib
import json
import os
import datetime
import re
from email.mime.text import MIMEText

def parse_args():
    parser = argparse.ArgumentParser(
        """
        NJ MVC (DMV) appointments usually run out. Try to let a bot keep probing.
        If found anything, send an email. (assuming sendmail in local system is set up.)

        example usage:
            ./nj_appt.py --get nondriverid --only pater --email ""
    """
    )
    parser.add_argument(
        "--email", help="Recipient", default="wangzhehao410305@gmail.com",
    )
    parser.add_argument(
        "--get", help="Which type of appointment to get", default="initial",
    )
    parser.add_argument(
        "--only", help="only alert when certain offices have availability", default="",
    )
    parser.add_argument(
        "--latest", help="alert only if the earliest appointment is no later than specified days from now", default=9999, type=int,
    )
    args = parser.parse_args()
    return args


class MVCGetter:
    def __init__(self, args):
        url_map = {
            "initial": "https://telegov.njportal.com/njmvc/AppointmentWizard/15",
            "nondriverid": "https://telegov.njportal.com/njmvc/AppointmentWizard/16",
        }
        self.recipient = [] if not args.email else args.email.split(",")
        self.only = args.only.split(",")
        self.url = url_map[args.get]
        self.requested = args.get
        self.latest = args.latest
        return

    def get(self):
        process = subprocess.Popen(
            ["curl", self.url], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        stdout = stdout.decode("utf-8")
        # this doesn't bother with curl --silent (for easy copy and replacing of curl_file) and status is printed
        stderr = stderr.decode("utf-8")
        print(stderr)

        location_data = {}
        time_data = {}
        location_model = {}

        def load_data(line, character_str):
            if line.find(character_str) >= 0:
                data = line.strip().strip(";").strip(character_str)
                end_idx = data.find(";")
                if end_idx >= 0:
                    data = data[:end_idx]
                return json.loads(data)
            return None

        # NJ MVC appt site populates location-availability data as js in a single line in the source page.
        for line in stdout.split("\n"):
            if location_data and time_data and location_model:
                break
            if not location_data:
                location_data = load_data(line, "var locationData = ")
                continue
            if not time_data:
                time_data = load_data(line, "var timeData = ")
                continue
            if not location_model:
                location_model = load_data(line, "var locationModel = ")
                continue
        
        if not time_data:
            print("time data not loaded!")
        if not location_data:
            print("location data not loaded!")

        # Join time_data with location_data
        for t in time_data:
            for l in location_data:
                # note that LocationId definition is not per-location, but per-location-per-get-type
                if t["LocationId"] == l["Id"]:
                    t.update(l)
                    break

        availability = []
        for t in time_data:
            if t["FirstOpenSlot"] == "No Appointments Available":
                continue
            matched = not self.only or any([o in t["Name"].lower() for o in self.only])
            if matched:
                matched = re.match(r".*<br/> Next Available: ([^ ]+) .*", t["FirstOpenSlot"])
                if not matched:
                    print(f"unexpected FirstOpenSlot format: {t['FirstOpenSlot']}")
                    continue
                earliest_date = datetime.datetime.strptime(matched.group(1), '%m/%d/%Y')
                if (earliest_date - datetime.datetime.now()).days <= self.latest:
                    availability.append({
                        "first": t["FirstOpenSlot"],
                        "name": t["Name"],
                        "id": str(t["LocationId"]),
                    })
        
        return availability

    def notify(self, avails):
        notify_str = ""
        for a in avails:
            url_str = self.url + "/" + a["id"]
            notify_str += f"{a['name']} {a['first'].replace(' <br/> ', ' ')}. Url: {url_str}\n"
        
        if len(self.recipient) > 0:
            msg = MIMEText(f"Hi,\n\nWe found NJ DMV availability for {self.requested}:\n{notify_str}\nCheers,\nBot")
            msg["From"] = "testname.zhehao@gmail.com"
            msg["To"] = ",".join(self.recipient)
            msg["Subject"] = f"DMV availability found {self.requested}"
            p = subprocess.Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=subprocess.PIPE)
            p.communicate(msg.as_bytes())
        else:
            print(notify_str)
        return


if __name__ == "__main__":
    args = parse_args()
    getter = MVCGetter(args)
    avails = getter.get()
    if (avails):
        getter.notify(avails)
        print(f"found availability {avails}, notified")
    else:
        print("availability not found")
