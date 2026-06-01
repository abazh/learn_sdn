"""SPFBaseController — shared SDN infrastructure for all routing algorithm controllers.

This module provides the SPFBaseController class, which implements all
OpenFlow interaction, topology tracking, host learning, and flow management.
Subclasses need only override compute_path() (and optionally install_path()
for multipath variants) to implement a different routing algorithm.

Class hierarchy:
    SPFBaseController          (this file)
    ├── BFSSwitch              (bfs_osken_controller.py)
    ├── DijkstraSwitch         (dijkstra_osken_controller.py)
    │   └── DijkstraMultipathSwitch
    ├── AStarSwitch            (astar_osken_controller.py)
    │   └── AStarMultipathSwitch
    ├── BellmanFordSwitch      (bellman_ford_osken_controller.py)
    ├── FloydWarshallSwitch    (floyd_warshall_osken_controller.py)
    ├── WidestPathSwitch       (widest_path_osken_controller.py)
    └── KShortestPathsController (kshortest_osken_controller.py)

Subclass contract:
    1. Define FLOW_COOKIE  (unique 64-bit identifier for your flows).
    2. Override compute_path(src, dst, first_port, final_port) → path list.
       Path list format: [(switch_dpid, in_port, out_port), ...]
    3. Optionally override install_path() for multipath (GROUP) forwarding.
    4. Optionally override _on_topology_changed() to pre-compute all-pairs
       data structures (e.g., Floyd-Warshall matrices) after topo updates.
"""

try:
    import warnings
    warnings.simplefilter("ignore", DeprecationWarning)
    import eventlet
    eventlet.monkey_patch()
except ImportError:
    pass

import sys
import signal
import time
from collections import defaultdict, deque

from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from os_ken.controller.handler import set_ev_cls
from os_ken.ofproto import ofproto_v1_3
from os_ken.lib.packet import packet, ethernet, ether_types
from os_ken.topology.api import get_switch, get_link
from os_ken.topology import event


# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

FLOW_COOKIE_MASK = 0xFFFFFFFFFFFFFFFF
FLOW_PRIORITY = 100
TABLE_MISS_PRIORITY = 0
HOST_STALE_SECONDS = 300


def _handle_sigint(signum, frame):
    """Graceful shutdown on Ctrl+C."""
    print("\n[SIGNAL] SIGINT received, initiating graceful shutdown...",
          file=sys.stderr, flush=True)
    app_manager.AppManager.stop()


signal.signal(signal.SIGINT, _handle_sigint)


# ──────────────────────────────────────────────────────────────────────────────
# Base class
# ──────────────────────────────────────────────────────────────────────────────

class SPFBaseController(app_manager.OSKenApp):
    """Shared SDN infrastructure for all SPF routing algorithm controllers.

    Handles: topology discovery, host learning, flow installation/deletion,
    broadcast tree flooding, proactive route refresh, and graceful shutdown.

    Subclasses must set FLOW_COOKIE and override compute_path().
    """

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    TOPOLOGY_EVENTS = [
        event.EventSwitchEnter,
        event.EventSwitchLeave,
        event.EventPortAdd,
        event.EventPortDelete,
        event.EventPortModify,
        event.EventLinkAdd,
        event.EventLinkDelete,
    ]

    # Each subclass sets its own cookie to identify its flow entries.
    FLOW_COOKIE: int = 0x5350460000000000   # "SPF\x00" base — override in subclass

    def __init__(self, *args, **kwargs):
        super(SPFBaseController, self).__init__(*args, **kwargs)
        # Datapath registry: dpid -> datapath object
        self.datapaths: dict = {}
        # Ordered list of active switch DPIDs
        self.switches: list = []
        # Host MAC → (dpid, access_port)
        self.mymacs: dict = {}
        # Host MAC → last-seen timestamp (for stale-entry eviction)
        self.host_last_seen: dict = {}
        # Adjacency: dpid → [(neighbor_dpid, out_port), ...]
        self.adjacency: defaultdict = defaultdict(list)
        # Port map: (src_dpid, dst_dpid) → out_port  (fast lookup)
        self.port_map: dict = {}
        # Topology version hash for change detection
        self.topology_signature = None
        # Installed path cache: (src_mac, dst_mac) → path
        self.installed_paths: dict = {}
        # Broadcast spanning tree: dpid → [neighbor_dpid, ...]
        self.broadcast_tree: dict = {}
        # Access ports: dpid → {port_no, ...}  (ports connected to hosts)
        self.access_ports: defaultdict = defaultdict(set)

    # ──────────────────────────────────────────────────────────────────────────
    # Abstract interface — override in subclasses
    # ──────────────────────────────────────────────────────────────────────────

    def compute_path(self, src, dst, first_port, final_port):
        """Compute the forwarding path from switch src to switch dst.

        Args:
            src:        source switch DPID (host's attachment switch)
            dst:        destination switch DPID
            first_port: port on src where the source host is connected
            final_port: port on dst where the destination host is connected

        Returns:
            List of (switch_dpid, in_port, out_port) tuples in hop order,
            or [] if no path exists.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement compute_path()"
        )

    def _on_topology_changed(self):
        """Hook called immediately after topology updates.

        Override in subclasses that need to pre-compute all-pairs data
        structures (e.g., Floyd-Warshall) before route reinstallation.
        """
        pass

    # ──────────────────────────────────────────────────────────────────────────
    # Path reconstruction helper (shared by single-path algorithm subclasses)
    # ──────────────────────────────────────────────────────────────────────────

    def _reconstruct_path(self, src, dst, first_port, final_port, distance, previous):
        """Build a path tuple-list from algorithm output (distance, previous).

        Args:
            src, dst:          source and destination switch DPIDs
            first_port:        access port on src (host → src direction)
            final_port:        access port on dst (dst → host direction)
            distance, previous: outputs of any single-source algorithm

        Returns:
            [(dpid, in_port, out_port), ...] or []
        """
        if src not in self.switches or dst not in self.switches:
            self.logger.warning("[PATH-QUERY] invalid endpoints: src=s%d dst=s%d", src, dst)
            return []

        if src != dst and distance.get(dst, float("inf")) == float("inf"):
            self.logger.debug("[PATH-UNREACHABLE] s%d→s%d: no path in current topology", src, dst)
            return []

        # Same-switch: host is directly reachable on this switch
        if src == dst:
            return [(src, first_port, final_port)]

        # Walk back through predecessor pointers to rebuild node sequence
        path_nodes = [dst]
        current = previous.get(dst)
        while current is not None:
            path_nodes.append(current)
            if current == src:
                break
            current = previous.get(current)

        if not path_nodes or path_nodes[-1] != src:
            self.logger.error("[PATH-CORRUPT] s%d→s%d: reconstruction failed", src, dst)
            return []

        path_nodes.reverse()               # now ordered src → dst

        # Annotate each hop with port numbers
        result = []
        in_port = first_port
        for s1, s2 in zip(path_nodes[:-1], path_nodes[1:]):
            out_port = self._get_port(s1, s2)
            if out_port is None:
                self.logger.error("[PATH-PORTMAP] s%d→s%d: port mapping lost", s1, s2)
                return []
            result.append((s1, in_port, out_port))
            in_port = self._get_port(s2, s1)
            if in_port is None and s2 != dst:
                self.logger.error("[PATH-PORTMAP] s%d→s%d: reverse port lost", s2, s1)
                return []

        result.append((dst, in_port, final_port))
        self.logger.info("[PATH-COMPUTED] s%d→s%d: %d hop(s) %d flow entries",
                         src, dst, len(result) - 1, len(result) * 2)
        return result

    # ──────────────────────────────────────────────────────────────────────────
    # Helper utilities
    # ──────────────────────────────────────────────────────────────────────────

    def _switch_name(self, dpid):
        return f"s{dpid}"

    def _format_path(self, path_tuples):
        if not path_tuples:
            return "(empty)"
        return " -> ".join(self._switch_name(sw) for sw, _, _ in path_tuples)

    def _is_access_port(self, dpid, port_no):
        return port_no in self.access_ports.get(dpid, set())

    def _get_port(self, src_dpid, dst_dpid):
        return self.port_map.get((src_dpid, dst_dpid))

    # ──────────────────────────────────────────────────────────────────────────
    # Host learning
    # ──────────────────────────────────────────────────────────────────────────

    def _learn_host(self, mac_addr, dpid, port_no):
        self.mymacs[mac_addr] = (dpid, port_no)
        self.host_last_seen[mac_addr] = time.time()

    def _update_host_location(self, mac, dpid, port):
        current = self.mymacs.get(mac)
        new_loc = (dpid, port)
        if current != new_loc:
            is_new = mac not in self.mymacs
            self._learn_host(mac, dpid, port)
            action = "discovered" if is_new else "moved"
            self.logger.info("[HOST-LEARN] MAC %s %s at s%d port %d", mac, action, dpid, port)
        else:
            self.host_last_seen[mac] = time.time()

    def _purge_stale_hosts(self):
        """Evict host entries not seen for HOST_STALE_SECONDS."""
        now = time.time()
        stale = {mac for mac, t in self.host_last_seen.items()
                 if now - t > HOST_STALE_SECONDS}
        if not stale:
            return
        self.mymacs = {m: l for m, l in self.mymacs.items() if m not in stale}
        self.host_last_seen = {m: t for m, t in self.host_last_seen.items()
                               if m not in stale}
        self.installed_paths = {k: v for k, v in self.installed_paths.items()
                                if k[0] not in stale and k[1] not in stale}

    def _purge_hosts_on_departed_switches(self):
        """Remove hosts whose attachment switch left the topology."""
        current = set(self.switches)
        gone = {mac for mac, (dpid, _) in self.mymacs.items() if dpid not in current}
        if not gone:
            return
        self.logger.debug("[HOST-PURGE] removing %d host(s) from departed switches", len(gone))
        self.mymacs = {m: l for m, l in self.mymacs.items() if m not in gone}
        self.host_last_seen = {m: t for m, t in self.host_last_seen.items()
                               if m not in gone}
        self.installed_paths = {k: v for k, v in self.installed_paths.items()
                                if k[0] not in gone and k[1] not in gone}

    def _active_hosts(self):
        self._purge_stale_hosts()
        return sorted(self.mymacs.keys())

    # ──────────────────────────────────────────────────────────────────────────
    # Flow management
    # ──────────────────────────────────────────────────────────────────────────

    def _install_unicast_flow(self, datapath, in_port, out_port, src_mac, dst_mac):
        """Install a unicast forwarding rule: delete-then-add for idempotency."""
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        match = parser.OFPMatch(in_port=in_port, eth_src=src_mac, eth_dst=dst_mac)
        actions = [parser.OFPActionOutput(out_port)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

        # Delete existing match (strict) before re-adding
        datapath.send_msg(parser.OFPFlowMod(
            datapath=datapath,
            cookie=self.FLOW_COOKIE,
            cookie_mask=FLOW_COOKIE_MASK,
            command=ofproto.OFPFC_DELETE_STRICT,
            out_port=ofproto.OFPP_ANY,
            out_group=ofproto.OFPG_ANY,
            priority=FLOW_PRIORITY,
            match=match,
        ))
        datapath.send_msg(parser.OFPFlowMod(
            datapath=datapath,
            cookie=self.FLOW_COOKIE,
            command=ofproto.OFPFC_ADD,
            idle_timeout=0,
            hard_timeout=0,
            priority=FLOW_PRIORITY,
            match=match,
            instructions=inst,
        ))

    def _install_drop_flow(self, datapath, in_port, src_mac, dst_mac, idle_timeout=5):
        """Install a drop rule with idle_timeout to prevent PacketIn storms."""
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        match = parser.OFPMatch(in_port=in_port, eth_src=src_mac, eth_dst=dst_mac)
        # Empty action list means drop
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, [])]

        # Delete existing match (strict) before re-adding
        datapath.send_msg(parser.OFPFlowMod(
            datapath=datapath,
            cookie=self.FLOW_COOKIE,
            cookie_mask=FLOW_COOKIE_MASK,
            command=ofproto.OFPFC_DELETE_STRICT,
            out_port=ofproto.OFPP_ANY,
            out_group=ofproto.OFPG_ANY,
            priority=FLOW_PRIORITY,
            match=match,
        ))
        datapath.send_msg(parser.OFPFlowMod(
            datapath=datapath,
            cookie=self.FLOW_COOKIE,
            command=ofproto.OFPFC_ADD,
            idle_timeout=idle_timeout,
            hard_timeout=0,
            priority=FLOW_PRIORITY,
            match=match,
            instructions=inst,
        ))

    def _delete_all_flows(self, datapath):
        """Send a wildcard DELETE for all flows matching this controller's cookie."""
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        datapath.send_msg(parser.OFPFlowMod(
            datapath=datapath,
            cookie=self.FLOW_COOKIE,
            cookie_mask=FLOW_COOKIE_MASK,
            command=ofproto.OFPFC_DELETE,
            out_port=ofproto.OFPP_ANY,
            out_group=ofproto.OFPG_ANY,
            match=parser.OFPMatch(),
        ))

    def _flush_all_flows(self):
        """Delete all installed flow entries and clear the path cache."""
        for dp in self.datapaths.values():
            self._delete_all_flows(dp)
        self.installed_paths.clear()

    def install_path(self, path, src_mac, dst_mac):
        """Install unicast flows for a single path (forward + reverse).

        Override in multipath subclasses to install SELECT groups instead.
        """
        key = (src_mac, dst_mac)
        if self.installed_paths.get(key) == path:
            return                          # already installed — no-op

        self.installed_paths[key] = path
        self.logger.debug("[FLOW-INSTALL] %s → %s: %s", src_mac, dst_mac,
                          self._format_path(path))

        for sw, in_port, out_port in path:
            dp = self.datapaths.get(int(sw))
            if dp:
                self._install_unicast_flow(dp, in_port, out_port, src_mac, dst_mac)

        for sw, in_port, out_port in reversed(path):
            dp = self.datapaths.get(int(sw))
            if dp:
                self._install_unicast_flow(dp, out_port, in_port, dst_mac, src_mac)

    # ──────────────────────────────────────────────────────────────────────────
    # Broadcast spanning tree (BFS-based — independent of routing algorithm)
    # ──────────────────────────────────────────────────────────────────────────

    def _build_broadcast_tree(self):
        """Build a spanning tree for controlled flooding using BFS."""
        if not self.switches:
            self.broadcast_tree = {}
            return

        root = min(self.switches)
        visited = {root}
        queue = deque([root])
        tree = defaultdict(set)

        while queue:
            u = queue.popleft()
            for v, _ in self.adjacency.get(u, []):
                if v not in visited:
                    visited.add(v)
                    queue.append(v)
                    tree[u].add(v)
                    tree[v].add(u)      # bidirectional for flood direction

        self.broadcast_tree = {node: sorted(neighbors)
                               for node, neighbors in tree.items()}
        self.logger.info("[TREE-DONE] root=s%d tree_edges=%d reachable=%d/%d",
                         root, len(tree), len(visited), len(self.switches))

    def _flood_over_tree(self, datapath, in_port, data, buffer_id):
        """Controlled flood over the spanning tree + access ports."""
        parser = datapath.ofproto_parser
        out_ports = set()

        for neighbor in self.broadcast_tree.get(datapath.id, []):
            port = self._get_port(datapath.id, neighbor)
            if port and port != in_port:
                out_ports.add(port)

        for access_port in self.access_ports.get(datapath.id, set()):
            if access_port != in_port:
                out_ports.add(access_port)

        if not out_ports:
            self.logger.debug("[PKT-DROP] s%d: no flood ports available", datapath.id)
            return

        actions = [parser.OFPActionOutput(p) for p in sorted(out_ports)]
        data_arg = None if buffer_id != datapath.ofproto.OFP_NO_BUFFER else data
        datapath.send_msg(parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=buffer_id,
            in_port=in_port,
            actions=actions,
            data=data_arg,
        ))

    # ──────────────────────────────────────────────────────────────────────────
    # Route reinstallation
    # ──────────────────────────────────────────────────────────────────────────

    def _reinstall_all_known_routes(self):
        """Proactively reinstall routes for all known host pairs after a topology change."""
        hosts = self._active_hosts()
        installed = skipped = unreachable = 0

        for src_mac in hosts:
            for dst_mac in hosts:
                if src_mac == dst_mac:
                    continue
                src_loc = self.mymacs.get(src_mac)
                dst_loc = self.mymacs.get(dst_mac)
                if not src_loc or not dst_loc:
                    skipped += 1
                    continue
                path = self.compute_path(src_loc[0], dst_loc[0], src_loc[1], dst_loc[1])
                if path:
                    self.install_path(path, src_mac, dst_mac)
                    installed += 1
                else:
                    unreachable += 1
                    self.logger.warning("[ROUTE-INSTALL] %s→%s no path (s%d→s%d)",
                                        src_mac, dst_mac, src_loc[0], dst_loc[0])

        self.logger.info("[TOPO] route refresh: installed=%d skipped=%d unreachable=%d hosts=%d",
                         installed, skipped, unreachable, len(hosts))

    # ──────────────────────────────────────────────────────────────────────────
    # OpenFlow event handlers
    # ──────────────────────────────────────────────────────────────────────────

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """On switch connect: install table-miss flow (send all to controller)."""
        dp = ev.msg.datapath
        ofproto = dp.ofproto
        parser = dp.ofproto_parser
        dp.send_msg(parser.OFPFlowMod(
            datapath=dp,
            match=parser.OFPMatch(),
            cookie=0,
            command=ofproto.OFPFC_ADD,
            idle_timeout=0,
            hard_timeout=0,
            priority=TABLE_MISS_PRIORITY,
            instructions=[parser.OFPInstructionActions(
                ofproto.OFPIT_APPLY_ACTIONS,
                [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)],
            )],
        ))

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        """Handle packets not matched by any flow rule.

        Learns source host, looks up destination, computes path if needed,
        installs flows, and sends the triggering packet on its way.
        """
        msg = ev.msg
        dp = msg.datapath
        ofproto = dp.ofproto
        parser = dp.ofproto_parser
        in_port = msg.match["in_port"]
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return          # LLDP is handled by the topology module

        src, dst, dpid = eth.src, eth.dst, dp.id

        # Learn source host only when arriving on an access port
        if self._is_access_port(dpid, in_port):
            self._update_host_location(src, dpid, in_port)

        if src not in self.mymacs:
            self.logger.debug("[PKT-DROP] %s→%s: source not on access port", src, dst)
            return

        if dst in self.mymacs:
            if (src, dst) in self.installed_paths:
                p = self.installed_paths[(src, dst)]
            else:
                src_sw, src_port = self.mymacs[src]
                dst_sw, dst_port = self.mymacs[dst]
                p = self.compute_path(src_sw, dst_sw, src_port, dst_port)
                if p:
                    self.install_path(p, src, dst)
                else:
                    self.logger.debug("[PKT-DROP] %s→%s: no path available, installing temporary drop flow", src, dst)
                    self._install_drop_flow(dp, in_port, src, dst, idle_timeout=5)
                    return

            # Find the output port for the current switch in the path
            out_port = next((port for sw, _, port in p if sw == dpid), None)
            if out_port is None:
                self.logger.warning("[PKT-DROP] %s→%s: s%d not in path", src, dst, dpid)
                return

            data = msg.data if msg.buffer_id == ofproto.OFP_NO_BUFFER else None
            dp.send_msg(parser.OFPPacketOut(
                datapath=dp, buffer_id=msg.buffer_id,
                in_port=in_port,
                actions=[parser.OFPActionOutput(out_port)],
                data=data,
            ))
        else:
            self.logger.debug("[PKT-FLOOD] %s→%s: dst unknown, flooding", src, dst)
            self._flood_over_tree(dp, in_port, msg.data, msg.buffer_id)

    @set_ev_cls(TOPOLOGY_EVENTS)
    def get_topology_data(self, ev):
        """Handle topology change events from OSKen's LLDP-based discovery."""
        switch_list = get_switch(self, None)
        switch_ids = sorted(s.dp.id for s in switch_list)
        links_list = get_link(self, None)
        new_links = sorted(
            (l.src.dpid, l.dst.dpid, l.src.port_no, l.dst.port_no)
            for l in links_list
        )

        # Guard against momentary empty snapshots during startup
        if not new_links:
            if self.topology_signature is not None:
                self.logger.debug("[TOPO] ignoring transient empty snapshot")
            return

        self.switches = switch_ids
        self.datapaths = {s.dp.id: s.dp for s in switch_list}

        # Identify inter-switch ports (not access ports)
        inter_switch = defaultdict(set)
        for s1, s2, p1, p2 in new_links:
            inter_switch[s1].add(p1)
            inter_switch[s2].add(p2)

        self.access_ports = defaultdict(set)
        for sw in switch_list:
            all_ports = {p.port_no for p in getattr(sw, "ports", [])}
            self.access_ports[sw.dp.id] = all_ports - inter_switch[sw.dp.id]

        new_adj = defaultdict(list)
        new_port_map = {}
        for s1, s2, p1, p2 in new_links:
            new_adj[s1].append((s2, p1))
            new_adj[s2].append((s1, p2))
            new_port_map[(s1, s2)] = p1
            new_port_map[(s2, s1)] = p2

        self.adjacency = new_adj
        self.port_map = new_port_map

        old_sig = self.topology_signature
        new_sig = (tuple(sorted(self.switches)), tuple(sorted(new_links)))

        if old_sig != new_sig:
            if old_sig is not None:
                _, old_links = old_sig
                added = sorted(set(new_links) - set(old_links))
                removed = sorted(set(old_links) - set(new_links))
                self.logger.info(
                    "[TOPO-CHANGE] switches=%d links=%d  delta +%d -%d",
                    len(self.switches), len(new_links), len(added), len(removed)
                )
                if added:
                    self.logger.info("[TOPO-UP]   %s", [(s1, s2) for s1, s2, *_ in added])
                if removed:
                    self.logger.warning("[TOPO-DOWN] %s", [(s1, s2) for s1, s2, *_ in removed])

                self._purge_hosts_on_departed_switches()
                self.logger.info("[TOPO-REFRESH] flushing %d flows, rebuilding routes",
                                 len(self.installed_paths))
                self._flush_all_flows()
            else:
                self.logger.info("[TOPO-INITIAL] %d switch(es) %d link(s)",
                                 len(self.switches), len(new_links))

            self.topology_signature = new_sig
            self._build_broadcast_tree()
            self._on_topology_changed()         # subclass hook (e.g., Floyd-Warshall)
            self._reinstall_all_known_routes()

    # ──────────────────────────────────────────────────────────────────────────
    # Lifecycle
    # ──────────────────────────────────────────────────────────────────────────

    def stop(self):
        """Clean shutdown: purge all installed flows and clear state."""
        self.logger.info("[CONTROLLER-STOP] clearing %d hosts, %d paths",
                         len(self.mymacs), len(self.installed_paths))
        self._flush_all_flows()
        self.mymacs.clear()
        self.host_last_seen.clear()
        self.installed_paths.clear()
        self.broadcast_tree.clear()
        self.datapaths.clear()
        super(SPFBaseController, self).stop()
        self.logger.info("[CONTROLLER-EXIT] graceful exit complete")
        sys.exit(0)
