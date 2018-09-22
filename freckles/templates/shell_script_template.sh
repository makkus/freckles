#!/usr/bin/env bash
{% for task in tasklist %}
# {{ task.msg }}
{{ task.command }} {{ task.args | join(' ') }}

{% endfor %}
