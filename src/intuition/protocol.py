"""
intuition/protocol.py - Twisted protocol library for OWL Intuition's multicast UDP energy monitoring protocol.
Copyright 2013 Michael Farrell <micolous+git@gmail.com>

This library is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this library.  If not, see <http://www.gnu.org/licenses/>.

"""

from twisted.internet.protocol import DatagramProtocol
from lxml import objectify
from decimal import Decimal
import time

MCAST_ADDR = '224.192.32.19'
MCAST_PORT = 22600
PREFIX = 'owl'

def OwlMessage(datagram):
	#print "datagram: %r" % (datagram,)
	root = objectify.fromstring(datagram)
		
	# Types of events we know about
	assert (root.tag in ['electricity', 'heating', 'weather'] ), ('Dont know anything about %r).' % root.tag)
	
	# junk we're not going to use
	# 	mac = root.attrib['id']
	# 	rssi = Decimal(root.signal[0].attrib['rssi'])
	# 	lqi = Decimal(root.signal[0].attrib['lqi'])	
	# 	battery = root.battery[0].attrib['level']
	
	# Get time
	timestamp = int(time.time())

	# Electric
	if (root.tag == 'electricity'):
		for channel in root.chan:
			assert channel.curr[0].attrib['units'] == 'w', 'Current units must be watts'
			assert channel.day[0].attrib['units'] == 'wh', 'Daily usage must be watthours'
			
			print "%s %s %s" % (PREFIX + ".electricity." + channel.attrib['id'] + ".current", channel.curr[0].text, timestamp)
			print "%s %s %s" % (PREFIX + ".electricity." + channel.attrib['id'] + ".daily", channel.day[0].text, timestamp)


	# Heating
	if (root.tag == 'heating'):
		for temp in root.temperature:
			print "%s %s %s" % (PREFIX + ".heating." + temp.attrib['zone'] + ".current", temp.current, timestamp)
			print "%s %s %s" % (PREFIX + ".heating." + temp.attrib['zone'] + ".required", temp.required, timestamp)
			
	# Weather
	if (root.tag == 'weather'):
		print "%s %s %s" % (PREFIX + ".weather.temperature", root.temperature, timestamp)


class OwlIntuitionProtocol(DatagramProtocol):
	def __init__(self, iface=''):
		"""
		Protocol for Owl Intution (Network Owl) multicast UDP.
		
		:param iface: Name of the interface to use to communicate with the Network Owl.  If not specified, uses the default network connection on the cost.
		:type iface: str
		"""
		self.iface = iface

	def startProtocol(self):
		self.transport.joinGroup(MCAST_ADDR, self.iface)
	
	def datagramReceived(self, datagram, address):
		OwlMessage(datagram)


if __name__ == '__main__':
	from twisted.internet import reactor
	from argparse import ArgumentParser
	parser = ArgumentParser()
	parser.add_argument('-i', '--iface', dest='iface', default='', help='Network interface to use for getting data.')
	
	options = parser.parse_args()
	
	protocol = OwlIntuitionProtocol(iface=options.iface)
	reactor.listenMulticast(MCAST_PORT, protocol, listenMultiple=True)
	reactor.run()
