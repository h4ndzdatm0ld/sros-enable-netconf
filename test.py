import ncclient
from ncclient import manager

def netconfconn(ncusername, ncpassword, node):
    conn = manager.connect(host=node,
                           port='830',
                           username=ncusername,
                           password=ncpassword,
                           hostkey_verify=False,
                           device_params={'name': 'alu'})
    return conn

def main():
    # Define the NETCONF USERNAME / PASSWORD:
    NETCONF_USER = 'netconf'
    NETCONF_PASS = 'NCadmin123'

    rtr = netconfconn(NETCONF_USER,NETCONF_PASS, '192.168.0.200')

    for x in rtr.server_capabilities:
        if 'card' in x: 
            print(x)

    logfilter = """
        <filter>
            <configure xmlns="urn:nokia.com:sros:ns:yang:sr:conf">    
                <card>
                    <slot-number>1</slot-number>
                </card>
            </configure>
        </filter>
    """
    result = rtr.get_config('running', logfilter)
    print(result)

# # 

#     schema = rtr.get_schema('nokia-conf-card')
#     print(schema)

    


if __name__ == "__main__":
    main()
