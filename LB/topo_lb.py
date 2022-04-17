from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from functools import partial


class MyTopo( Topo ):
    "Simple topology example."
    def addSwitch( self, name, **opts ):
        kwargs = { 'protocols' : 'OpenFlow13'}
        kwargs.update( opts )
        return super(MyTopo, self).addSwitch( name, **kwargs )

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )

        # Add hosts and switches
        h1 = self.addHost( 'h1' )
        h2 = self.addHost( 'h2' )
        h3 = self.addHost( 'h3' )
        h4 = self.addHost( 'h4' )
        s1 = self.addSwitch( 's1' )

        # Add links
        self.addLink( h1, s1 )
        self.addLink( h2, s1 )
        self.addLink( h3, s1 )
        self.addLink( h4, s1 )

def run():
    "The Topology for Server - Round Robin LoadBalancing"
    topo = MyTopo()
    net = Mininet( topo=topo, controller=RemoteController, autoSetMacs=True, waitConnected=True )
    
    info("\n***Disabling IPv6***\n")
    for host in net.hosts:
        print("disable ipv6 in", host)
        host.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
    
    for sw in net.switches:
        print("disable ipv6 in", sw)
        sw.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")

    info("\n***Running Web Servers***\n")
    for web in ["h2", "h3", "h4"]:
        info("Web Server running in", web, net[web].cmd("python -m http.server 80 &"))


    info("\n\n************************\n")
    net.start()
    net.pingAll()
    info("************************\n")
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    run()
