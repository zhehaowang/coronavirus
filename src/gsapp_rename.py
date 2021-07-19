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
    """
    )
    parser.add_argument(
        "--folder", help="folder", default="/Users/zwang/personal/gradapp",
    )
    args = parser.parse_args()
    return args


class GSAppRename:
    def __init__(self, folder):
        self.folder = folder
        return
    
    def rename(self):
        import os
        for subdir, dirs, files in os.walk(self.folder):
            for file in files:
                filepath = subdir + os.sep + file
                print(filepath)
                if file == "&":
                    target_name = os.path.join(os.path.dirname(filepath), "index.html")
                    os.rename(filepath, target_name)
                    print(f"{filepath} -> {target_name}")
                elif "." not in file:
                    with open(filepath, "r") as rfile:
                        for line in rfile:
                            if "<!DOCTYPE html>" in line:
                                target_name = filepath + ".html"
                                os.rename(filepath, target_name)
                                print(f"{filepath} -> {target_name}")
                                break
        return


if __name__ == "__main__":
    args = parse_args()
    getter = GSAppRename(args.folder)
    getter.rename()
