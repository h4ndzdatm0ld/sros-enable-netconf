"""Programmatically Enable NETCONF on SROS Device."""
import argparse
import getpass
import os

import xmltodict
from netmiko import ConnectHandler

from sros_enable_netconf.helpers import (
    create_folder,
    disconnect,
    netconfconn,
    netmiko_logging,
    save_file,
    send_cmmdz,
    send_single,
)

# Define the NETCONF USERNAME / PASSWORD, PICK UP ENV VARS OR USE DEFAULT.
NETCONF_USER = os.getenv("NETCONF_USER", "netconf")
NETCONF_PASS = os.getenv("NETCONF_PASS", "NCadmin123")


def get_arguments():
    parser = argparse.ArgumentParser(
        description="Command Line Driven Utility To Enable NETCONF\
        And MD-CLI on SROS Devices."
    )
    parser.add_argument("-n", "--node", help="Target NODE IP", required=True)
    parser.add_argument("-u", "--user", help="SSH Username", required=False, default="admin")
    parser.add_argument("-p", "--port", help="NETCONF TCP Port", required=False, default="830")
    args = parser.parse_args()
    return args


def main():
    # Extract the Arguements from ARGSPARSE:
    args = get_arguments()

    # start logging
    netmiko_logging()

    # Create a dictionary for our device.
    sros = {
        "device_type": "alcatel_sros",
        "host": args.node,
        "username": args.user,
        "password": getpass.getpass(),
        "response_return": None,
    }
    # Pass in the dict and create the connection.
    sros_conn = ConnectHandler(**sros)

    # Establish a list of pre and post check commands.
    print("Connecting to device and executing script...")

    # TODO: CREATE TTP TEMPLATE
    send_single(sros_conn, "show system information | match Name")
    # TODO: CREATE TTP TEMPLATE
    enabled = send_single(sros_conn, "show system netconf | match State")

    if "Enabled" in enabled:
        print("Netconf already enabled on this device. Disconnecting.")
        disconnect(sros_conn)
    else:
        enable_netconf = [
            '/configure system security profile "netconf" netconf base-op-authorization lock',
            '/configure system security profile "netconf" netconf base-op-authorization kill-session',
            f"/configure system security user netconf access {NETCONF_USER}",
            f"/configure system security user netconf password {NETCONF_PASS}",
            f"/configure system security user netconf console member {NETCONF_USER}",
            "/configure system security user netconf console member 'administrative'",
            "/configure system management-interface yang-modules nokia-modules",
            "/configure system management-interface yang-modules no base-r13-modules",
            "/configure system netconf auto-config-save",
            "/configure system netconf no shutdown",
            "/configure system management-interface cli no cli-engine",
            "/configure system management-interface cli md-cli auto-config-save",
            "/configure system management-interface configuration-mode model-driven",
        ]

        # Execute Script.
        send_cmmdz(sros_conn, enable_netconf)
        # Validate NETCONF is enabled and Operational.

        send_single(sros_conn, "show system netconf")
        # Disconnect from the SSH Connection to our far-end remote device.
        # We need to disconnect to open the pipe for python3 to establish netconf connection.
        disconnect(sros_conn)

    try:
        # Now let's connect to the device via NETCONF and pull the config to validate.
        nc = netconfconn(args, NETCONF_USER, NETCONF_PASS)
        # Retrieve the XML Config
        config = nc.get_config(source="running")
        # Close NETCONF session
        nc.close_session()
        # Convert XML object to string.
        j_config = str(config)
        # TODO: # Can prob skip over saving it and just pass to line 106.
        save_file("temp-config.xml", j_config, mode="w+")

        # Lets open the XML file, read it, and convert to a python dictionary and extract some info.
        with open("temp-config.xml", "r", encoding="utf-8") as temp:
            content = temp.read()
            xml = xmltodict.parse(content)
            sys_name = xml["rpc-reply"]["data"]["configure"]["system"]["name"]
            create_folder(f"backups/{sys_name}")
            save_file(f"backups/{sys_name}/{sys_name}.txt", j_config, mode="w+")
            print(f"Backed up XML Config: backups/{sys_name}/{sys_name}.txt")

    except Exception as e:
        print(f"Issue with NETCONF connection, {e}")


if __name__ == "__main__":
    main()
