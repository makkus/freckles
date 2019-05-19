#!/usr/bin/env bash

# -----------------------------------------------------------------------------
#
# Shell script to gather basic facts about a machine.
#
# Copyright 2018 Markus Binsteiner
# licensed under The Parity Public License 6.0.0 (https://licensezero.com/licenses/parity)
#
# -----------------------------------------------------------------------------

# TODO: might need expandPath functionality
export PATH="${FRECKLES_PRE_PATH}:${PATH}:${FRECKLES_POST_PATH}"

if [ -z ${FRECKLES_CHECK_EXECUTABLES} ]
then
  export FRECKLES_CHECK_EXECUTABLES="bzip2:cat:gunzip:wget:curl:python:python2:python2.7:python3:python3.6:vagrant:pip:conda:nix:asdf:brew:rsync:stow:unzip:unrar"
fi
if [ -z ${FRECKLES_CHECK_PYTHON_MODULES} ]
then
  export FRECKLES_CHECK_PYTHON_MODULES="zipfile"
fi

DEFAULT_CHECK_PYTHON_EXES="$HOME/.local/share/freckles/envs/virtualenv/freckles/bin/python3:$HOME/.local/share/freckles/envs/virtualenv/freckles/bin/python3:/usr/bin/python:/usr/bin/python2:/usr/bin/python3"
#DEFAULT_CHECK_PYTHON_EXES="/usr/bin/python:/usr/bin/python2:/usr/bin/python3"

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

function can_passwordless_sudo () {
    sudo -k -n true 2&> /dev/null
    return $?
}


function check_executables () {

    if [ -z ${FRECKLES_CHECK_EXECUTABLES} ]
    then
      echo "executables: {}"
      return
    fi

    OLD_IFS=${IFS}
    IFS=:
    echo "executables:"
    for exe in ${FRECKLES_CHECK_EXECUTABLES}
    do
      path=$(which -a ${exe} 2> /dev/null)
      if [[ -z ${path} ]]
      then
         echo "  ${exe}: []"
      else
        echo "  ${exe}:"
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

function check_directories () {

    if [ -z ${FRECKLES_CHECK_DIRECTORIES} ]
    then
      echo "directories: {}"
      return
    fi

    OLD_IFS=${IFS}
    IFS=:
    echo "directories:"
    for dir in ${FRECKLES_CHECK_DIRECTORIES}
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

    if [ -z ${FRECKLES_CHECK_FRECKLE_FILES} ]
    then
      echo "freckle_files: {}"
      return
    fi
    echo "freckle_files:"

    for dir in ${FRECKLES_CHECK_FRECKLE_FILES}
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

function read_box_basics_file () {

    echo
    echo "box_basics_file: "

    if [ ! -f "$HOME/.local/share/freckles/.box_basics" ]; then
        echo "  exists: false"
    else
        echo "  exists: true"
        cat "$HOME/.local/share/freckles/.box_basics" 2> /dev/null | sed 's/^/  /'
    fi
}

function get_home_directory () {
    echo "home: ${HOME}"
    echo
}

function get_username () {
    echo "user: ${USER}"
    echo
}

function check_git () {
    path=$(which -a git | tr '\n' ':')
    echo "git_exes: \"${path}\""
    echo
}

function check_git_xcode () {

    git --help 2&>1 | grep -q "xcode-select"
    echo "git_xcode: $?"
    echo
}

function check_python_modules_installed () {

    echo

    if [ -z "${FRECKLES_CHECK_PYTHON_MODULES}" ]
    then
      echo "    python_modules: {}"
      return
    fi

    path=$(which -a python 2> /dev/null)
    if [[ -z ${path} ]]
    then
       echo "    python_modules: {}"
       return
    fi

    echo "    python_modules:"
    OLD_IFS=${IFS}
    IFS=:

    for module in ${FRECKLES_CHECK_PYTHON_MODULES}
    do

      eval "$1 -c \"import ${module}\" 2> /dev/null"
      echo "      ${module}: $?"

    done
    IFS=${OLD_IFS}
    echo

}

function check_python_exes () {

    echo
    echo "pythons:"
    OLD_IFS=${IFS}
    IFS=:

    for python_exe in ${DEFAULT_CHECK_PYTHON_EXES}
    do
        echo "  ${python_exe}:"
        path=$(which -a ${python_exe} 2> /dev/null)
        if [[ -z ${path} ]]
        then
          echo "    exists: false"
        else
          echo "    exists: true"
          check_python_modules_installed "${python_exe}"
        fi

    done
    IFS=${OLD_IFS}
}

can_passwordless_sudo
echo "can_passwordless_sudo: $?"
echo "path: \"$PATH\""
check_executables
check_git
check_git_xcode
check_directories
get_home_directory
get_username
read_freckle_files
check_python_exes
read_box_basics_file

exit 0
