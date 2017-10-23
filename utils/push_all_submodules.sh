#! /usr/bin/env bash

git submodule foreach git push origin master 
git pull origin master
