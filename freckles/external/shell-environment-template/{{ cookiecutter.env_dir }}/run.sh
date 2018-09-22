#!/usr/bin/env bash


THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ -e "$HOME/.nix-profile/etc/profile.d/nix.sh" ]; then source "$HOME/.nix-profile/etc/profile.d/nix.sh"; fi

if [ -d "$HOME/.local/share/inaugurate/conda/envs/inaugurate/bin" ]; then
    export PATH="$PATH:$HOME/.local/share/inaugurate/conda/envs/inaugurate/bin"
fi
if [ -d "$HOME/.local/share/inaugurate/conda/bin" ]; then
    export PATH="$PATH:$HOME/.local/share/inaugurate/conda/bin"
fi
if [ -d "$HOME/.local/share/inaugurate/bin" ]; then
    export PATH="$PATH:$HOME/.local/share/inaugurate/bin"
fi
if [ -d "$HOME/.local/bin" ]; then
    export PATH="$PATH:$HOME/.local/bin"
fi

export PATH="$THIS_DIR/executables:$PATH"

cd "${THIS_DIR}/working_dir"

{% for task in tasklist %}
# {{ task.msg }}
{{ task.command }} {{ task.args | join(' ') }}

{% endfor %}
