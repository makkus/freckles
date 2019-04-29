# -*- coding: utf-8 -*-
import json, subprocess  # noqa: E401

hosts = ["dev.cutecode.co"]
tasks = []

for host in hosts:
    task = {
        "frecklecute": {
            "target": "root@{}".format(host),
            "frecklet": "basic-hardening",
            "vars": {"fail2ban": True, "ufw": True, "ufw_open_tcp": [80, 443]},
        }
    }
    tasks.append(task)

subprocess.run(["freckles", json.dumps(tasks)])
