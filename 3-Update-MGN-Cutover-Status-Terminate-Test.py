import csv
import boto3

session = boto3.session.Session()
client_mgn = session.client('mgn')

input_file = csv.DictReader(open("./servers.csv"))

# For loop through CSV file
for each_row in input_file:

    # Declare variables
    server = (each_row["Server"])

    source_servers = client_mgn.describe_source_servers()['items']

    # For loop through all MGN source servers to change cutover status
    for each_item in source_servers:
        if each_item['tags']['Name'] == server:
            print("\nGetting source server ID for {}...".format(server))
            print("\nChanging cutover status for {}...".format(server))

            response = client_mgn.change_server_life_cycle_state(
                lifeCycle={
                    'state': 'READY_FOR_CUTOVER'
                },
                sourceServerID=each_item['sourceServerID']
            )

            print(response)

    # For loop through all MGN source servers to terminate test instances
    for each_item in source_servers:
        if each_item['tags']['Name'] == server:
            print("\nGetting source server ID for {}...".format(server))
            print("\nTerminating test instance for {}...".format(server))

            response = client_mgn.terminate_target_instances(
                sourceServerIDs=[
                    each_item['sourceServerID'],
                ],
            )

            print(response)
