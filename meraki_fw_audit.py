#!/usr/bin/env python3
"""Meraki Audit Tool.

Reuse of code from http://www.ifm.net.nz/cookbooks/meraki-backup.html
Author of the original code: Philip D'Ath  - https://www.linkedin.com/in/philip-d-ath/
Philip's code was created to pull a backup of the Meraki configs.
I simply modified it to pull the config and make it auditable for security purposes.
"""
from meraki import meraki
import argparse
import json
import time


def get_org_id(apikey, orgName, suppressprint):
    """Get ORG Id."""
    result = meraki.myorgaccess(apikey, suppressprint)
    for row in result:
        if row['name'] == orgName:
            return row['id']
        raise ValueError('The organization name does not exist')


def write_admins(file, apikey, orgid, suppressprint):
    """Output Dashboard Users."""
    myOrgAdmins = meraki.getorgadmins(apikey, orgid, suppressprint)
    for row in myOrgAdmins:
        file.write("\t" + "{}\n".format(json.dumps(row)))
    file.write("\n")


def write_mx_l3_fw_rules(file, apikey, networkid, suppressprint):
    """Output Network Rules. The real ones, not just NAT."""
    myRules = meraki.getmxl3fwrules(apikey, networkid, suppressprint)[0:-1]
    for row in myRules:
        file.write("\t" + str(row) + "\n")
    file.write("\n")


def write_mx_cellular_fw_rules(file, apikey, networkid, suppressprint):
    """Output Cellular Backup Rules."""
    myRules = meraki.getmxcellularfwrules(apikey, networkid, suppressprint)[0:-1]
    for row in myRules:
        file.write("\t" + str(row) + "\n")
    file.write("\n")


def write_mx_vpn_fw_rules(file, apikey, orgid, suppressprint):
    """Output VPN Rules."""
    myRules = meraki.getmxvpnfwrules(apikey, orgid, suppressprint)[0:-1]
    for row in myRules:
        file.write("\t" + str(row) + "\n")
    file.write("\n")


def write_vpn_settings(file, apikey, networkid, suppressprint):
    """Output VPN Settings."""
    myVPN = meraki.getvpnsettings(apikey, networkid, suppressprint)
    for row in myVPN:
        file.write("\t" + row + ": " + str(json.dumps(myVPN[row])) + "\n")
    file.write("\n")


def write_snmp_settings(file, apikey, orgid, suppressprint):
    """Output SNMP Settings."""
    mySNMP = meraki.getsnmpsettings(apikey, orgid, suppressprint)
    for row in mySNMP:
        file.write("\t" + row + ": " + str(json.dumps(mySNMP[row])) + "\n")
    file.write("\n")


def write_non_meraki_vpn_peers(file, apikey, orgid, suppressprint):
    """Output VPN Peer List."""
    myPeers = meraki.getnonmerakivpnpeers(apikey, orgid, suppressprint)
    file.write("VPN Peers:\n")
    for row in myPeers:
        file.write("\t" + str(row) + "\n")
    file.write("\n")


def write_ssid_settings(file, apikey, networkid, suppressprint):
    """Output SSID Settings."""
    mySSIDs = meraki.getssids(apikey, networkid, suppressprint)
    if mySSIDs is None:
        return
    for row in mySSIDs:
        file.write("\tSSIDs: {} ".format(str(row['number'])))
        file.write(str(row) + "\n")
        file.write("\tRules:\n")
        myRules = meraki.getssidl3fwrules(apikey, networkid, row['number'], suppressprint)[0:-2]
        for row2 in myRules:
            file.write("\t\t" + str(row2) + "\n")
        file.write("\n")
    file.write("\n")


def get_wan_info(file, apikey, networkid, suppressprint):
    """Get the WAN information for all devices, so we know the external IP."""
    myDev = meraki.getnetworkdevices(apikey, networkid, suppressprint=False)
    for row in myDev:
        uplink = meraki.getdeviceuplink(apikey, networkid, row["serial"], suppressprint=False)
        for row in uplink:
            file.write("\t" + str(uplink) + "\n")
        file.write("\n")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Pull Meraki Config for offline Audit * WARNING: INCLUDES PASSWORDS! * ')
    parser.add_argument('-v', help='Enable verbose mode', action='store_true')
    parser.add_argument('-o', help='Output filename.', default="Meraki-Config.txt")
    parser.add_argument('apiKey', help='The API Key')
    parser.add_argument('orgName', help='The name of a Meraki organization')
    args = parser.parse_args()

    suppressprint = True

    if args.v:
        suppressprint = False

    apikey = args.apiKey
    orgid = get_org_id(apikey, args.orgName, suppressprint)

    with open(args.o, 'w') as file:
        file.write("Meraki Firewall Audit tool - {} @ {}\n\n".format(args.orgName, time.strftime("%Y-%m-%d %H:%M")))
        file.flush()
        myNetworks = meraki.getnetworklist(apikey, orgid, None, suppressprint)
        file.write("Dashboard Users:\n")
        try:
            write_admins(file, apikey, orgid, suppressprint)
            file.flush()
        except:
            file.write("\tERROR - Unable to Access or Parse Data")
            pass

        for row in myNetworks:
            tags = row['tags']
            if not tags:
                tags = ""
            networkType = row['type']
            if networkType == 'combined':
                networkType = 'wireless switch appliance phone'

            if networkType == 'systems manager':
                continue

            file.write("Processing network " + row['name'] + "...\n")
            file.write("WAN Info:\n")
            try:
                get_wan_info(file, apikey, row['id'], suppressprint)
                file.flush()
            except:
                file.write("\tERROR - Unable to Access or Parse Data")
                pass

            file.write("MX Cellular Rules: {}\n".format(str(row['id'])))
            try:
                write_mx_cellular_fw_rules(file, apikey, row['id'], suppressprint)
                file.flush()
            except:
                file.write("\tERROR - Unable to Access or Parse Data")
                pass

            file.write("VPN Rules:\n")
            try:
                write_mx_vpn_fw_rules(file, apikey, orgid, suppressprint)
                file.flush()
            except:
                file.write("\tERROR - Unable to Access or Parse Data")
                pass

            file.write("Layer 3 Network Rules: {}\n".format(str(row['id'])))
            try:
                write_mx_l3_fw_rules(file, apikey, row['id'], suppressprint)
                file.flush()
            except:
                file.write("\tERROR - Unable to Access or Parse Data")
                pass

            file.write("VPN Settings: {}\n".format(str(row['id'])))
            try:
                write_vpn_settings(file, apikey, row['id'], suppressprint)
                file.flush()
            except:
                file.write("\tERROR - Unable to Access or Parse Data")
                pass

            file.write("SNMP Settings:\n")
            try:
                write_snmp_settings(file, apikey, orgid, suppressprint)
                file.flush()
            except:
                file.write("\tERROR - Unable to Access or Parse Data")
                pass

            file.write("Wifi/SSID Information:\n")
            try:
                write_ssid_settings(file, apikey, row['id'], suppressprint)
                file.write("\n")
            except:
                file.write("\tERROR - Unable to Access or Parse Data")
                pass

            file.flush()
