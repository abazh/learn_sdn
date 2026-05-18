#!/usr/bin/env python3
"""Ring topology with 5 switches for multipath and resilience labs.

Topology design: 5 switches connected in a ring with 2 hosts per switch.
This creates multiple paths between any two nodes, suitable for testing
shortest-path algorithms, ECMP (Equal-Cost Multipath), and failover scenarios.

ASCII art:

        h1   h3   h5   h7   h9
        |    |    |    |    |
       -s1---s2---s3---s4---s5-
        |    |    |    |    |
        h2   h4   h6   h8   h10

Ring topology: s1-s2-s3-s4-s5-s1
All inter-switch links: 100 Mbps, 2ms delay, HFSC enabled.
Each switch connects to 2 hosts (local connections).

Use this topology for:
    - Dijkstra: Tests with multiple equal-cost paths
    - ECMP: Round-robin over 2 alternative paths
    - Resilience: Verify fast failover when a link fails
    - Floyd-Warshall: All-pairs shortest paths with 5 nodes
    - Yen's K-shortest: Multiple diverse paths between nodes
"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel, info
from mininet.cli import CLI


class Ring5Topo(Topo):
    """5-switch ring topology with 10 hosts (2 per switch)."""

    def addSwitch(self, name, **opts):
        kwargs = {"protocols": "OpenFlow13"}
        kwargs.update(opts)
        return super(Ring5Topo, self).addSwitch(name, **kwargs)

    def __init__(self):
        Topo.__init__(self)

        info("*** Adding hosts\n")
        h1 = self.addHost("h1", ip="10.0.0.1/24")
        h2 = self.addHost("h2", ip="10.0.0.2/24")
        h3 = self.addHost("h3", ip="10.0.0.3/24")
        h4 = self.addHost("h4", ip="10.0.0.4/24")
        h5 = self.addHost("h5", ip="10.0.0.5/24")
        h6 = self.addHost("h6", ip="10.0.0.6/24")
        h7 = self.addHost("h7", ip="10.0.0.7/24")
        h8 = self.addHost("h8", ip="10.0.0.8/24")
        h9 = self.addHost("h9", ip="10.0.0.9/24")
        h10 = self.addHost("h10", ip="10.0.0.10/24")

        info("*** Adding switches\n")
        s1 = self.addSwitch("s1")
        s2 = self.addSwitch("s2")
        s3 = self.addSwitch("s3")
        s4 = self.addSwitch("s4")
        s5 = self.addSwitch("s5")

        info("*** Adding host links\n")
        # Each switch connects to 2 hosts
        self.addLink(s1, h1, port1=1, port2=1)
        self.addLink(s1, h2, port1=2, port2=1)

        self.addLink(s2, h3, port1=1, port2=1)
        self.addLink(s2, h4, port1=2, port2=1)

        self.addLink(s3, h5, port1=1, port2=1)
        self.addLink(s3, h6, port1=2, port2=1)

        self.addLink(s4, h7, port1=1, port2=1)
        self.addLink(s4, h8, port1=2, port2=1)

        self.addLink(s5, h9, port1=1, port2=1)
        self.addLink(s5, h10, port1=2, port2=1)

        info("*** Adding ring inter-switch links\n")
        # Ring topology: s1-s2-s3-s4-s5-s1
        # All links: 100 Mbps, 2ms delay, HFSC enabled
        self.addLink(s1, s2, port1=3, port2=3, bw=100, delay="2ms", use_hfsc=True)
        self.addLink(s2, s3, port1=4, port2=3, bw=100, delay="2ms", use_hfsc=True)
        self.addLink(s3, s4, port1=4, port2=3, bw=100, delay="2ms", use_hfsc=True)
        self.addLink(s4, s5, port1=4, port2=3, bw=100, delay="2ms", use_hfsc=True)
        self.addLink(s5, s1, port1=4, port2=4, bw=100, delay="2ms", use_hfsc=True)


def run():
    """Run the 5-switch ring topology with OpenFlow controller."""
    topo = Ring5Topo()
    net = Mininet(
        topo=topo,
        controller=RemoteController,
        link=TCLink,
        autoSetMacs=True,
        autoStaticArp=True,
        waitConnected=True,
    )

    info("\n*** Disabling IPv6\n")
    for host in net.hosts:
        host.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
    for sw in net.switches:
        sw.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")

    info("\n*** Starting network\n")
    net.start()

    info("\n*** Dumping host connections\n")
    dumpNodeConnections(net.hosts)

    info("\n*** Network is running. Use Mininet CLI to test.\n")
    info("    Suggested tests:\n")
    info("      pingall                    # Verify connectivity\n")
    info("      h1 ping h5                 # Single path test\n")
    info("      h1 ping h6                 # Alternative path test\n")
    info("      dpctl dump-flows -O OpenFlow13  # View installed rules\n")
    info("      iperf h1 h6                # Measure throughput\n")
    info("\n    Controllers to use:\n")
    info("      dijkstra_osken_controller.py      # Shortest paths\n")
    info("      dijkstra_multipath_osken_controller.py  # ECMP\n")
    info("      kshortest_osken_controller.py     # K-shortest paths\n")
    info("      floyd_warshall_osken_controller.py # All-pairs paths\n")

    CLI(net)
    net.stop()


if __name__ == "__main__":
    setLogLevel("info")
    run()
