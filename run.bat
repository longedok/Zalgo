@echo off
start "server" cmd /k main.py
start "client" cmd /k main.py --client
