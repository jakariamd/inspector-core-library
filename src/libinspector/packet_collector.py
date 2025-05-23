"""
Captures and analyzes packets from the network.

"""
import scapy.all as sc
import time
import logging

from . import global_state

logger = logging.getLogger(__name__)

sc.load_layer('tls')

print_queue_size_dict = {'last_updated_ts': 0}


def start():

    with global_state.global_state_lock:
        host_active_interface = global_state.host_active_interface
        host_ip_addr = global_state.host_ip_addr

    # Continuously sniff packets for 30 second intervals (as sniff might crash).
    # Also, avoid capturing packets to/from the host itself, except ARP, which
    # we need for discovery.
    sc.sniff(
        prn=add_packet_to_queue,
        iface=host_active_interface,
        stop_filter=lambda _: not inspector_is_running(),
        filter=f'(not arp and host not {host_ip_addr}) or arp',
        timeout=30
    )


def inspector_is_running():
    """
    Returns whether the Inspector is running or not.

    """
    with global_state.global_state_lock:
        return global_state.is_running


def add_packet_to_queue(pkt):
    """
    Adds a packet to the packet queue.

    """
    with global_state.global_state_lock:
        if not global_state.is_inspecting:
            return

    global_state.packet_queue.put(pkt)

    # Print the queue size every 10 seconds
    current_time = time.time()
    if current_time - print_queue_size_dict['last_updated_ts'] > 10:
        logger.info(f'[packet_collector] Packet queue size: {global_state.packet_queue.qsize()}')
        print_queue_size_dict['last_updated_ts'] = current_time