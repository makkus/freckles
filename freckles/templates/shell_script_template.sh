#!/usr/bin/env bash
{% for task in tasklist %}
{% if task.msg %}# {{ task.msg}}{% endif %}
{{ task.command }} {{ task.args | join(' ') }}

{% endfor %}
