from netmiko import ConnectHandler
import csv
import textfsm
import pprint

#Module 'Global' variables
DEVICE_FILE_PATH = 'devices.csv' # file should contain a list of devices in format: ip,username,password,device_type
DEVICE_ROLES = {'INTERNET':6,'WAN':10,'SERVER-FARM':0,'CORE':4,'DISTRIBUTION':2,'CORE-DISTRIBUTION':3,'ACCESS':0,'UNKNOWN':5}
DEVICE_ICONS = {'CORE':'layer3switch','DISTRIBUTION':'layer3switch','ACCESS':'workgroupswitch',
                'CORE-DISTRIBUTION':'virtuallayerswitch','SERVER-FARM':'serverswitch',
                'INTERNET':'router','WAN':'router','UNKNOWN':'router", iconFill: "grey'}
DIRECTORY = 'C:\\Users\\Nursultan\\PycharmProjects\\DevNetDrawTopology\\venv\\'
TEMPLATE_PATH = 'template.yaml'
TOPOLOGY_PATH = 'devnet.yaml'

def create_topology_info(text):
    try:
        temp_text = ''
        with open(TEMPLATE_PATH,'r') as f1:
            temp_text = f1.read()
        temp_text += text
        with open(TOPOLOGY_PATH, 'w') as file:
            file.write(temp_text)
        print("Save is complete!")
        print('-*-' * 10)
        print()

        # if successfully done
        return True

    except ConnectionError:
        # if there was an error
        print('Error! Unable to backup device ' + hostname)
        return False

def connect_to_device(device):
    # This function opens a connection to the device using Netmiko
    # Requires a device dictionary as an input

    # Since there is a 'hostname' key, this dictionary can't be used as is
    connection = ConnectHandler(
        host = device['ip'],
        username = device['username'],
        password=device['password'],
        device_type=device['device_type'],
        secret=device['secret']
    )

    print ('Opened connection to '+device['ip'])
    print('-*-' * 10)
    print()

    # returns a "connection" object
    return connection

def disconnect_from_device(connection, hostname):
    #This function terminates the connection to the device

    connection.disconnect()
    print ('Connection to device {} terminated'.format(hostname))

def get_devices_from_file(device_file):
    # This function takes a CSV file with inventory and creates a python list of dictionaries out of it
    # Each disctionary contains information about a single device

    # creating empty structures
    device_list = list()

    # reading a CSV file with ',' as a delimeter
    with open(device_file, 'r') as f:
        reader = csv.DictReader(f, delimiter=',')

        # every device represented by single row which is a dictionary object with keys equal to column names.
        for row in reader:
            device_list.append(row)
            #print(row)

    print ("Got the device list from inventory")
    print('-*-' * 10)
    print ()

    # returning a list of dictionaries
    return device_list

def fetch_lldp_neighbors(device):
    connection = connect_to_device(device)

    try:
        # sending a CLI command using Netmiko and printing an output
        connection.enable()

        domain_name = connection.send_command('show run | inc domain-name|domain name')
        if len(domain_name) > 0:
            domain_name = domain_name.split()[-1]
        real_hostname = connection.send_command('show run | inc hostname')
        device['hostname'] = real_hostname.split()[-1]

        output = connection.send_command('show lldp neighbors detail', use_textfsm=True)

        #pprint.pprint(output)
        #print('-*-' * 10)
        #print()

        # if successfully done
        #return True

    except ConnectionError:
        # if there was an error
        print('Error! Unable to backup device ' + device['hostname'])
        return False

    disconnect_from_device(connection, device['hostname'])
    return output,domain_name

def clean_hostname(hostname, domain_names):
    for dn in domain_names:
        hostname = hostname.replace('.' + dn, '')
    return hostname

def main():
    device_list = get_devices_from_file(DEVICE_FILE_PATH)
    print (device_list)

    row_counter = dict()
    col_counter = dict()
    # 'INTERNET': 0, 'WAN': 0, 'SERVER-FARM': 0,
    #                'CORE': 0, 'DISTRIBUTION': 0, 'CORE-DISTRIBUTION': 0,
    #                'ACCESS': 0, 'UNKNOWN': 0}
    conn_dict = dict()
    domain_names = set()
    all_neighbors = list()

    for device in device_list:
        role = device['device_role']
        if role in ('SERVER-FARM','WAN'):
            row_counter.setdefault(role,0)
            row_counter[role] += 1
        elif role not in list(DEVICE_ROLES.keys()):
            col_counter.setdefault('UNKNOWN', 0)
            col_counter['UNKNOWN'] += 1
        else:
            col_counter.setdefault(role,0)
            col_counter[role] += 1

        neighbors,domain_name = fetch_lldp_neighbors(device)
        #print('!!!!!!!!!!!! - ---- '+str(device['hostname']))
        all_neighbors.append(neighbors)
        domain_names.add(domain_name)

    hostnames = set()
    for device in device_list:
        device['hostname'] = clean_hostname(device['hostname'], domain_names)
        hostnames.add(device['hostname'])

    did = 0
    for neighbors in all_neighbors:
        hostname = device_list[did]['hostname']
        did = did + 1
        #print(str(did)+'----------hostname--------'+hostname)

        for dneighbor in neighbors:
            neighbor_hostname = clean_hostname(dneighbor['neighbor'],domain_names)
            if neighbor_hostname not in hostnames:
                hostnames.add(neighbor_hostname)
                device_list.append({'hostname':neighbor_hostname,'ip':dneighbor['management_ip'],'device_role':'UNKNOWN'})
                col_counter.setdefault('UNKNOWN',0)
                col_counter['UNKNOWN'] += 1

            #print(str(did) + '--------neigh_hostname--------' + neighbor_hostname)
            neighbor_port = dneighbor['neighbor_port_id'].split('.')[0]
            st = tuple(sorted([hostname,neighbor_hostname]))
            ld = {hostname:{dneighbor['local_interface']},neighbor_hostname:{neighbor_port}}

            #pprint.pprint(st)
            #pprint.pprint(ld)
            if st not in conn_dict:
                conn_dict.update({st:ld})
            else:
                conn_dict[st][hostname].add(dneighbor['local_interface'])
                conn_dict[st][neighbor_hostname].add(neighbor_port)

    pprint.pprint(conn_dict)
    print('-*-' * 10)
    print()

    rows = 0
    cols = 0
    if len(row_counter.values()) > 0:
        rows = max(row_counter.values()) + 2
    if rows < 7:
        rows = 7
    if len(col_counter.values()) > 0:
        cols = max(col_counter.values()) + 2

    init_point = dict()
    for key in list(row_counter.keys()):
        init_point[key] = int((rows-row_counter.get(key))/2)
    for key in list(col_counter.keys()):
        if key != 'UNKNOWN':
            init_point[key] = int((cols - col_counter.get(key)) / 2)
        else:
            init_point[key] = 1

    pprint.pprint(row_counter)
    print('-+-' * 10)
    pprint.pprint(col_counter)
    print('-+-' * 10)
    pprint.pprint(init_point)
    print('-+-' * 10)

    x = 0
    y = 0
    z = 0
    output = '  columns: '+str(cols)+'\n  rows: '+str(rows)+'\nicons:\n'
    print(output)

    for device in device_list:
        role = device['device_role']
        z = init_point.get(role,1)
        #print("-----------------------"+str(role)+"--------"+str(init_point[role]))
        if role == 'SERVER-FARM':
            x = 0
            y = z
        elif role == 'WAN':
            x = cols
            y = z
        elif role in ('CORE','DISTRIBUTION','CORE-DISTRUBUTION'):
            y = DEVICE_ROLES.get(role)
            x = z
            z += 1
        else:
            y = DEVICE_ROLES.get(role)
            x = z

        init_point[role] = z+1

        line = '  ' + device['hostname'] + ': {<<: *cisco, x: ' + str(x) + ', y: '+ str(y) + ', icon: "'+DEVICE_ICONS[role]+'", url: "ssh://'+device['ip']+'"}\n'
        print(line)
        output += line;

    # print('-+-' * 10)
    # print()

    cdv = list(conn_dict.values())
    # pprint.pprint(cdv)
    # print('-*-' * 10)
    # print()
    output += 'connections:\n'
    for cl in cdv:
        h1 = list(cl.keys())[0]
        h2 = list(cl.keys())[1]
        p1 = ','.join(list(cl.values())[0])
        p2 = ','.join(list(cl.values())[1])
        line = '  - { <<: *connection, endpoints: ["'+h1+':'+p1+'", "'+h2+':'+p2+'"] }\n';
        print(line)
        output += line;

    create_topology_info(output)

if __name__ == '__main__':
    main()
