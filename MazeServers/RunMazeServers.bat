@echo off
start "server1" /MIN mongod --config c:\MazeServers\Server1\Server1.conf
start "server2" /MIN mongod --config c:\MazeServers\Server2\Server2.conf
start "server3" /MIN mongod --config c:\MazeServers\Server3\Server3.conf