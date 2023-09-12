import csv
import boto3
from pprint import pprint

session = boto3.session.Session()
client_mgn = session.client('mgn')
client_ec2 = session.client('ec2')

input_file = csv.DictReader(open("./servers.csv"))

# For loop through CSV file
for each_row in input_file:

    ## Declare variables
    server = (each_row["Server"])
    subnet_id = (each_row["subnet_id"])
    disk_type = (each_row["disk_type"])
    iops = (each_row["iops"])
    subnet_id = (each_row["subnet_id"])
    securitygroup_id = (each_row["securitygroup_id"])
    instanceType = (each_row["instanceType"])
    ip_address = (each_row["ip_address"])
    instance_role_arn = (each_row["instance_role_arn"])
    tag_environment = (each_row["tag_environment"])
    tag_application = (each_row["tag_application"])


    my_list_of_dicts = []

    source_servers = client_mgn.describe_source_servers()['items']

    # For loop through all MGN source servers
    for each_item in source_servers:
        if each_item['tags']['Name'] == server:
            print("\nGetting source server ID for {}...".format(server))
            print(each_item['sourceServerID'])

            # Update MGN Launch Configuration
            update_launch_config = client_mgn.update_launch_configuration(
                launchDisposition='STOPPED',
                licensing={
                    'osByol': True
                },
                sourceServerID=each_item['sourceServerID'],
                targetInstanceTypeRightSizingMethod='NONE'
            )
            print("/n")
            pprint(update_launch_config)

            print("\nGetting launch template ID for {}...".format(server))
            get_launch_config = client_mgn.get_launch_configuration(
                sourceServerID=each_item['sourceServerID'],
            )
            print(get_launch_config['ec2LaunchTemplateID'])

            print("\nGetting latest template version for {}...".format(server))

            launch_template_version = client_ec2.describe_launch_template_versions(
                LaunchTemplateId=get_launch_config['ec2LaunchTemplateID'],
                Versions=['$Latest']
            )

            for each_version in launch_template_version['LaunchTemplateVersions']:
                print("Latest version is {}...".format(each_version['VersionNumber']))

                for each_block_device in each_version['LaunchTemplateData']['BlockDeviceMappings']:
                    print("dev name is {}".format(each_block_device['DeviceName']))
                    print("size is {}".format(each_block_device['Ebs']['VolumeSize']))
                    print("type is {}".format(disk_type))

                    my_list_of_dicts.append({'DeviceName': each_block_device['DeviceName'],'Ebs': {'VolumeSize': each_block_device['Ebs']['VolumeSize'], 'Iops': int(iops), 'VolumeType': disk_type}})
                
            create_launch_template = client_ec2.create_launch_template_version(
                LaunchTemplateId=get_launch_config['ec2LaunchTemplateID'],
                SourceVersion=str(each_version['VersionNumber']),
                # SourceVersion="1",
                LaunchTemplateData={
                    'BlockDeviceMappings': my_list_of_dicts
                }
            )

            ## Get latest launch template version
            launch_template_version = client_ec2.describe_launch_template_versions(
                LaunchTemplateId=get_launch_config['ec2LaunchTemplateID'],
                Versions=['$Latest']
            )
            for each_version in launch_template_version['LaunchTemplateVersions']:
                print("Latest version is {}...".format(each_version['VersionNumber']))

                create_launch_template = client_ec2.create_launch_template_version(
                    LaunchTemplateId=get_launch_config['ec2LaunchTemplateID'],
                    SourceVersion=str(each_version['VersionNumber']),
                    LaunchTemplateData={
                        'IamInstanceProfile': {
                            'Arn': instance_role_arn
                        },
                        'NetworkInterfaces': [
                            {
                                'DeviceIndex': 0,
                                'Groups': [
                                    securitygroup_id
                                ],
                                'PrivateIpAddresses': [
                                    {
                                        'Primary': True,
                                        'PrivateIpAddress': ip_address
                                    },
                                ],
                                'SubnetId': subnet_id
                            },
                        ],
                        'TagSpecifications': [
                            {
                                'ResourceType': 'instance',
                                'Tags': [
                                    {
                                        'Key': 'Name',
                                        'Value': server
                                    },
                                    {
                                        'Key': 'tag_environment',
                                        'Value': tag_environment
                                    },
                                    {
                                        'Key': 'tag_application',
                                        'Value': tag_application
                                    },
                                ]
                            },
                        ],
                        'InstanceType': instanceType
                    }
                )

            ## Get latest launch template version
            launch_template_version = client_ec2.describe_launch_template_versions(
                LaunchTemplateId=get_launch_config['ec2LaunchTemplateID'],
                Versions=['$Latest']
            )
            for each_version in launch_template_version['LaunchTemplateVersions']:
                print("Latest version is {}...".format(each_version['VersionNumber']))
            
            ## Setting new default version of launch template
            set_default_version = client_ec2.modify_launch_template(
                LaunchTemplateId=get_launch_config['ec2LaunchTemplateID'],
                DefaultVersion=str(each_version['VersionNumber'])
            )