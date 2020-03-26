#!/usr/bin/env python3

import argparse
import subprocess
import smtplib
import json
import os
import datetime


def parse_args():
    parser = argparse.ArgumentParser(
        """
        As of 20200325 Amazon Fresh delivery is often booked out in NY area.
        Reddit posts seem to suggest delivery window gets posted at midnight.
        Is that the case?
        
        Given a curl command file, run it, check the output for 3 "unavailable"s,
        upon not seeing 3, notify the specified recipient. Give this to cron and
        let it do its thing.

        example usage:
            ./amazon_refresh.py --curl ../data/amazon_curl.sh --email wangzhehao410305@gmail.com --cred ../data/email.json
    """
    )
    parser.add_argument(
        "--curl",
        help="""
            The curl command to run.
            Copy this from Amazon Fresh checkout page where it says unavailable for the next 3 days""",
        default="../data/amazon_curl.sh",
    )
    parser.add_argument(
        "--email", help="Recipient", default="wangzhehao410305@gmail.com",
    )
    parser.add_argument(
        "--cred",
        help="Sender email account credential file",
        default="../data/email.json",
    )
    parser.add_argument(
        "--log",
        help="Log file to record status and avoid self spamming",
        default="amazon_refresh.log",
    )
    args = parser.parse_args()
    return args


class AmazonRefresh:
    def __init__(self, args):
        self.curl_file = args.curl
        self.email = args.email

        self.server = None
        with open(args.cred, "r") as infile:
            cred_obj = json.loads(infile.read())
            self.server = smtplib.SMTP("smtp.gmail.com", 587)
            self.server.ehlo()
            self.server.starttls()
            self.server.login(cred_obj["user"], cred_obj["pwd"])
            self.sender = cred_obj["account"]

        self.recipient = args.email.split(",")
        self.log = None
        if args.log:
            self.log = args.log
        return

    def should_act(self):
        if not self.log or not os.path.isfile(self.log):
            return True
        with open(self.log, "r") as logfile:
            lines = logfile.readlines()
            if len(lines) > 0:
                timestr, status = lines[-1].split(",")
                time = datetime.datetime.strptime(timestr, "%Y-%m-%dT%H:%M:%S.%f")
                if status == "found" or status == "sorry":
                    # 2 hours interval
                    return (datetime.datetime.now() - time).total_seconds() < 3600 * 2
        return True

    def record_status(self, status):
        if not self.log:
            return
        with open(self.log, "a") as logfile:
            logfile.write("{},{}\n".format(datetime.datetime.now().isoformat(), status))
        return

    def request_amazon_refresh(self, target="Not available", target_num=3):
        if not self.should_act():
            print("sent a found email lately, skipped")
            return

        process = subprocess.Popen(
            ["bash", self.curl_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        stdout = stdout.decode("utf-8")
        # this doesn't bother with curl --silent (for easy copy and replacing of curl_file) and status is printed
        stderr = stderr.decode("utf-8")
        print(stderr)

        if stdout.count(target) != target_num:
            if "sorry" in stdout.lower():
                self.notify(
                    "Amazon Refresh: adjust item",
                    "Something is no longer available :(\n\nSigh,\nBot",
                )
                self.record_status("sorry")
            else:
                self.notify(
                    "Amazon Refresh: found availability",
                    "Go check out {} \n\nEnjoy,\nBot".format(
                        "https://www.amazon.com/gp/buy/shipoptionselect/handlers/display.html?hasWorkingJavascript=1"
                    ),
                )
                self.record_status("found")
        else:
            print("occurrences {} == {}".format(target, target_num))
            self.record_status("unavailable")
        return

    def notify(self, subject, text):
        if self.server:
            try:
                message = "Subject: {}\n\n{}".format(subject, text)
                self.server.sendmail(self.sender, self.recipient, message)
            except Exception as e:
                print(e + " : failed to send mail")
        else:
            print("smtp client is None")
        return


if __name__ == "__main__":
    args = parse_args()
    refresher = AmazonRefresh(args)
    refresher.request_amazon_refresh()
