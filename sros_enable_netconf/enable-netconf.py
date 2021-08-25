import argparse
import getpass
from xml.etree import ElementTree
from netmiko import ConnectHandler

import xmltodict

from sros_enable_netconf.helpers import (
    create_folder,
    save_file,
    netmiko_logging,
    send_single,
    disconnect,
    netconfconn,
    send_cmmdz,
)


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

    # Define the NETCONF USERNAME / PASSWORD:
    NETCONF_USER = "netconf"
    NETCONF_PASS = "NCadmin123"

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
    sros_conn = net_connect = ConnectHandler(**sros)

    # Establish a list of pre and post check commands.
    print("Connecting to device and executing script...")

    send_single(sros_conn, "show system information | match Name")

    enabled = sros_conn.send_command("show system netconf | match State")

    if "Enabled" in enabled:
        disconnect(sros_conn)
        print("Netconf already enabled on this device.")
    else:
        enableNetconf = [
            '/configure system security profile "netconf" netconf base-op-authorization lock',
            '/configure system security profile "netconf" netconf base-op-authorization kill-session',
            f"/configure system security user netconf access netconf",
            f"/configure system security user netconf password NCadmin123",
            f"/configure system security user netconf console member netconf",
            f'/configure system security user netconf console member "administrative"',
            "/configure system management-interface yang-modules nokia-modules",
            "/configure system management-interface yang-modules no base-r13-modules",
            "/configure system netconf auto-config-save",
            "/configure system netconf no shutdown",
            "/configure system management-interface cli no cli-engine",
            "/configure system management-interface cli md-cli auto-config-save",
            "/configure system management-interface configuration-mode model-driven",
        ]

        # Execute Script.
        send_cmmdz(sros_conn, enableNetconf)
        # Validate NETCONF is enabled and Operational.

        send_single(sros_conn, "show system netconf")
        # Disconnect from the SSH Connection to our far-end remote device.
        # We need to disconnect to open the pipe for python3 to establish netconf connection.
        disconnect(sros_conn)

    try:
        # Now let's connect to the device via NETCONF and pull the config to validate.
        nc = netconfconn(args, NETCONF_USER, NETCONF_PASS)
        # Grab the running configuration on our device, as an NCElement.
        rfilter = """
            <filter>
                <configure xmlns="urn:nokia.com:sros:ns:yang:sr:conf">
                </configure>
            </filter>
        """
        # Retrieve the XML Config
        config = nc.get_config(source="running")
        # Close NETCONF session
        nc.close_session()
        # Convert XML object to string.
        j_config = str(config)
        print(j_config)
        save_file("temp-config.xml", j_config)
        # Lets open the XML file, read it, and convert to a python dictionary and extract some info.

        with open("temp-config.xml", "r") as temp:
            content = temp.read()
            xml = xmltodict.parse(content)
            sys_name = xml["rpc-reply"]["data"]["configure"]["system"]["name"]
            create_folder(f"backups/{sys_name}")
            save_file(f"backups/{sys_name}/{sys_name}.txt", j_config)
            print(f"Backed up XML Config: backups/{sys_name}/{sys_name}.txt")

    except Exception as e:
        print(f"Issue with NETCONF connection, {e}")


if __name__ == "__main__":
    main()
