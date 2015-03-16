#A Bot Client connection for route.py
######Tested with Python 2.7.6 on MACOSX and Ubuntu

```bash
usage: ddsclient.py [-h] [-v] [--version] [--buffer M] [HOST] [PORT]

Control commands for the bot:
	replyto X: Set default replyto address for broadcast commands
	hostname: Send the client's hostname
	sendfile 'myfile': Send the specified file line-by-line
	exit: Disconnect the client

Any other message will be executed directly with the 
os.system command.

positional arguments:
  HOST              The IP of the router (default: localhost)
  PORT              The port number of the router (default: 23456)

optional arguments:
  -h, --help        show this help message and exit
  -v, --verbose     verbose output and responses (default: False)
  --version         show program's version number and exit
  --buffer M, -b M  The maximum size M of messages to accept (2048 < M <
                    10240) (default: 2048)
```