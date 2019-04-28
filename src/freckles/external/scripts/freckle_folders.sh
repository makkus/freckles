#!/usr/bin/env bash

# ---------------------------------------------------------------------------------------
#
# Copyright 2018 Markus Binsteiner
# licensed under The Parity Public License 3.0.0 (https://licensezero.com/licenses/parity)
#
# ---------------------------------------------------------------------------------------

# -----------------------------------------------------------------------------
#
# Shell script to gather basic facts about a machine.
#
# -----------------------------------------------------------------------------

# from: https://stackoverflow.com/questions/3963716/how-to-manually-expand-a-special-variable-ex-tilde-in-bash/29310477#29310477
function expand_path () {
  local path
  local -a pathElements resultPathElements
  IFS=':' read -r -a pathElements <<<"$1"
  : "${pathElements[@]}"
  for path in "${pathElements[@]}"; do
    : "$path"
    case $path in
      "~+"/*)
        path=$PWD/${path#"~+/"}
        ;;
      "~-"/*)
        path=$OLDPWD/${path#"~-/"}
        ;;
      "~"/*)
        path=$HOME/${path#"~/"}
        ;;
      "~"*)
        username=${path%%/*}
        username=${username#"~"}
        IFS=: read _ _ _ _ _ homedir _ < <(getent passwd "$username")
        if [[ $path = */* ]]; then
          path=${homedir}/${path#*/}
        else
          path=$homedir
        fi
        ;;
    esac
    resultPathElements+=( "$path" )
  done
  local result
  printf -v result '%s:' "${resultPathElements[@]}"
  printf '%s\n' "${result%:}"
  echo
}


function check_directories () {

    OLD_IFS=${IFS}
    IFS=:
    echo "directories:"
    for dir in ${1}
    do
      expanded=$(expand_path ${dir})
      path=$(find ${expanded} -not -path '*/\.git/*' 2> /dev/null)
      if [ -z ${path} ]
      then
         echo "  ${dir}: []"
      else
        echo "  ${dir}:"
        IFS='
        '
        for p in ${path}
        do
           echo "    - \"${p}\""
        done
      fi
    done
    IFS=${OLD_IFS}
    echo
}

function read_freckle_files () {

    OLD_IFS=${IFS}
    IFS=:

    echo "freckle_files:"

    for dir in ${1}
    do
      expanded=$(expand_path ${dir})
      path=$(find ${expanded} -type f -name "*.freckle" -not -path '*/\.git/*'  2> /dev/null)

      if [ -z ${path} ]
      then
         echo "  ${dir}: {}"
      else
        echo "  ${dir}:"
        IFS='
        '
        for p in ${path}
        do
           echo "     \"${p}\": | "
           read_freckle_file ${p}
        done
      fi
    done
    IFS=${OLD_IFS}
    echo

}

function read_freckle_file () {

    cat ${1} | sed 's/^/        /'

}

check_directories "$@"
read_freckle_files "$@"
