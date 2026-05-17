from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from functools import partial
import random


class JellyfishTopo( Topo ):
    "Jellyfish topology — random regular graph."

    def addSwitch( self, name, **opts ):
        kwargs = { 'protocols' : 'OpenFlow13'}
        kwargs.update( opts )
        return super(JellyfishTopo, self).addSwitch( name, **kwargs )

    def __init__( self, num_switches=10, num_ports=4, num_sw_ports=3, seed=42 ):
        "Create jellyfish topo. k=num_ports, r=num_sw_ports, 1 host per switch."

        Topo.__init__( self )

        random.seed( seed )

        N = num_switches
        k = num_ports       # total ports per switch
        r = num_sw_ports    # ports used for switch-switch links (must be < k)

        assert r < k, "r must be less than k (need at least 1 port for hosts)"

        # Add switches and hosts
        switches = []
        for i in range( N ):
            sw   = self.addSwitch( f's{i}' )
            host = self.addHost(
                f'h{i}',
                ip=f'10.0.{i}.1/24',
                mac=f'00:00:00:00:{i:02x}:01'
            )
            self.addLink( sw, host )
            switches.append( sw )

        # Build random r-regular graph via incremental algorithm
        # Each switch starts with r free ports; randomly pair free ports
        free = { sw: r for sw in switches }
        connected = { sw: set() for sw in switches }
        added_links = set()

        def get_free_switches():
            return [ sw for sw, f in free.items() if f > 0 ]

        def add_link_between( a, b ):
            pair = tuple( sorted( [a, b] ) )
            if pair not in added_links:
                self.addLink( a, b )
                added_links.add( pair )
                free[a]  -= 1
                free[b]  -= 1
                connected[a].add( b )
                connected[b].add( a )
                return True
            return False

        # Phase 1: randomly connect free ports
        attempts = 0
        while True:
            candidates = get_free_switches()
            if len( candidates ) < 2:
                break

            random.shuffle( candidates )
            a = candidates[0]
            possible = [
                sw for sw in candidates[1:]
                if sw != a and sw not in connected[a]
            ]

            if not possible:
                # Deadlock: try to rewire (swap)
                if attempts > 200:
                    break
                attempts += 1
                all_with_free = get_free_switches()
                if len( all_with_free ) >= 2:
                    x = random.choice( all_with_free )
                    linked = list( connected[x] )
                    if linked:
                        y = random.choice( linked )
                        # find z with free port not connected to x
                        z_candidates = [
                            sw for sw in get_free_switches()
                            if sw != x and sw != y and sw not in connected[x]
                        ]
                        if z_candidates:
                            z = random.choice( z_candidates )
                            # rewire: remove x-y, add x-z and y gets free port
                            # (we just disconnect logically; Mininet links stay)
                            connected[x].discard( y )
                            connected[y].discard( x )
                            free[x] += 1
                            free[y] += 1
                            add_link_between( x, z )
                continue

            b = random.choice( possible )
            add_link_between( a, b )
            attempts = 0


def run():
    "The Topology for Jellyfish Random Regular Graph"
    topo = JellyfishTopo( num_switches=10, num_ports=4, num_sw_ports=3, seed=42 )
    net = Mininet( topo=topo, controller=RemoteController, autoSetMacs=True, waitConnected=True )

    info("\n***Disabling IPv6***\n")
    for host in net.hosts:
        print("disable ipv6 in", host)
        host.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")

    for sw in net.switches:
        print("disable ipv6 in", sw)
        sw.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")

    info("\n\n**********************\n")
    net.start()
    net.pingAll()
    info("**********************\n")
    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel( 'info' )
    run()
