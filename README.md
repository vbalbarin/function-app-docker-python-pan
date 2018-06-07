# Function-app-docker-python-pan

## Pre-Requisites

The solution was developed locally on OSX 10.13.4. The following are the pre-requisites:

* [Docker Community Edition](https://www.docker.com/community-edition)
* azure-cli 2.0 (installed via [Homebrew](https://brew.sh/))

## Running Locally

After installing the pre-requesites, run the docker container.  Bring up a terminal and enter the following information.

```bash
# Replace square bracket strings with appropriate values.


# Retrieve API_KEY for PAN device administrative operations.

export FW_IP="[ ip address of PAN virtual appliance ]"
export USERNAME="[ username of PAN administrator user]"
export PASSWORD="[ password of USERNAME ]"
export API_KEY=$(curl -X GET "https://${FW_IP}/api/?type=keygen&user=${USERNAME}&password=${PASSWORD}" | sed -n -e 's/\(.*<key>\)\(.*\)\(<\/key>.*\)/\2/p')

# N.B., add `-k` option to ignore ssl cert validation for self-signed cert on PAN api
# export API_KEY=$(curl -k -X GET "https://${FW_IP}/api/?type=keygen&user=${USERNAME}&password=${PASSWORD}" | sed -n -e 's/\(.*<key>\)\(.*\)\(<\/key>.*\)/\2/p')

echo ${API_KEY}
# N.B., please record API_KEY value; it may be re-used in subsequent runs.


# Generate AUTH_CODE for authenticating to application running in container

export AUTH_CODE=$(python  -c 'import secrets; print(secrets.token_urlsafe(32))') && echo ${AUTH_CODE}
# N.B., please record this AUTH_CODE; it may be re-used in subsequent runs.


# Retrieve repository
git clone https://github.com/vbalbarin/function-app-docker-python-pan.git
cd function-app-docker-python-pan

docker build -t docker build -t [docker_accountame]/azure-functions-docker-python:v0.0.0 .

docker run docker run -p 8080:80 -e AUTH_CODE="${AUTH_CODE}" -e FW_IP="${FW_IP}" -e API_KEY="${API_KEY}" -it [ docker_accountname ]/azure-functions-docker-python:v0.0.0

# To test locally, a scrubbed Azure Alert webhook responsebody has been supplied. Edit `./samples/responseBody.sh`

source ./reponseBody.sh

# Execute curl

curl "http://localhost:8080/api/HttpTrigger?code=${AUTH_CODE}" -X POST -H 'Content-Type: application/json'  -d "${JSON_DATA}"

# If all goes well, a JSON response with the IP Address and tags should be returned:
# TODO: create more meaninful JSON responses

{"ipAddress": "nnn.nnn.nnn.nnn", "tags": ["azure_nic_tags_ForTestingOnly_true", "azure_nic_tags_Name_vmHHMMss", "azure_nic_tags_OwnerId_fl001", "azure_nic_tags_OwnerDepartment_OwnerDepartment", "azure_nic_tags_OwnerDepartmentContact_firstname.lastname@stillness.local", "azure_nic_tags_ChargingAccount_ChargingAccount", "azure_nic_tags_SecurityZone_Zone", "azure_nic_tags_SupportDepartment_SupportDepartment", "azure_nic_tags_SupportDepartmentContact_itsdsqa@stillness.local", "azure_nic_tags_Environment_Prod", "azure_nic_tags_Application_Zone", "azure_nic_tags_CreatedBy_fl001"]}

```

## References

[`pandevice`](https://github.com/PaloAltoNetworks/pandevice)

[`azure-vm-monitoring`](https://github.com/PaloAltoNetworks/azure-vm-monitoring)

[Create a function on Linux using a custom image (preview)](https://docs.microsoft.com/en-us/azure/azure-functions/functions-create-function-linux-custom-image#run-the-build-command)

[`azure-functions-docker-python-sample`](https://github.com/Azure/azure-functions-docker-python-sample)