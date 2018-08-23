# Function-app-docker-python-pan

## Introduction and Background

A hub and spokes virtual network (VNET) architectural pattern is often adopted in order meet business requirements for integration with on-premises enterprise data center networks through A set of centrally deployed and managed infrastructure resources.

These resources can comprise DNS services, monitoring services, load balancing, network traffic control, ActiveDirectory domain services. The deployment of on-premises services to a central hub VNET allows for extending current enterprise operations to the Azure Cloud.

While it is often preferable to use Azure platform network traffic controls such as network security groups (NSGs), application security groups (ASGs), customer defined routes, and application load balancing, enterprise network and information security operatons require extending centralized management of network traffic to virtual machine assets in the Azure cloud.

This solution incorporates the following general features:

* A hub VNET that provides a gateway subnet to the on-premises data center networks to a number of peered spoke VNETs.
* A  set of firewall network virtual appliances (NVAS) fronted by by an internal load balancer (ILB)that will expand or contract depending on CPU load on the appliances.
* A set of customer defined routes that force traffic originating from enterprise managed subnets in the peered VNETs to the ILB/NVA for inspection and control via policies ratified by information security.
* Azure Alerts that respond to the creation, modification, or deletion of network interfaces by emitting a webhook payload to a Azure Function App.
* The Function App will then update the IP address objects on the NVAs.

The Azure Marketplace provides  NVAs from third parties fit for use. This implementation uses the NVA furnished by Palo Alto Networks, as it meets the requirements of Yale University's network operations and information security teams.

The elastic characteristics of compute assets in public and provide clouds require that the NVA consistently and reliably apply traffic controls to a changing set of IP addresses. The PAN devices accomplish this by allowing security and network teams the ability to apply policy objects to Dynamic Address Groups. The membership of an IP address object in a Dynamic Access Group is governed by a set of selection criteria obtained by configuring the appliance to read information from the hyper-visor environment.

Currently, PAN supports only Amazon EC2, Google Compute, and VMWare ESX. In order to allow Yale University to use PAN NVAs in Azure, PAN engineers furnished a monitoring solution that polls an Azure subscription or resource group for the running VM assets and their network cards. It then updates the IP Address Objects and their Palo Alto tags with tags from the Azure VM and NIC. One can control membership in a dynamic address group and the associated policy though appropriate tagging. For example, one could create a 'High' security tag and apply it to a VM and its NIC. The associated IP address will be placed in a 'High' security dynamic access group. A 'High' security policy can then be associated to the group.

This solution requires the creation of a Linux virtual machine in the hub VNET to execute the monitoring code.

Yale University's implementation uses Azure Function Apps, Docker and the Azure Function App Runtime 2.0, and Azure alerts to create a microservice to update the address group objects.

The use of a Docker container for the Function App enables the bundling of all the solution dependencies as well as the choice of Python as the execution environment.

Running Python in the Azure Function app runtime is currently alpha. The code in this repository runs. (An automated CI/CD pipeline should be established to catch breaking changes in the upstream MS code base.)

## Pre-Requisites

The solution was developed locally on OSX 10.13.4. The following are the pre-requisites:

* [Docker Community Edition](https://www.docker.com/community-edition)
* azure-cli 2.0 (installed via [Homebrew](https://brew.sh/))

One should be able to reproduce this work on a similarly configured Unix system.

## Running Locally

After installing the pre-requesites, run the docker container.  Bring up a terminal session and enter the following information.

```bash
# Replace square bracket strings with appropriate values.

# Docker and application info
export APP_NAME="function-app-docker-python-pan"
export DOCKER_ID="<docker_id>"
export DOCKER_IMAGE_NAME="${APP_NAME}"
export DOCKER_IMAGE_TAG="${DOCKER_ID}/${DOCKER_IMAGE_NAME}:v0.0.0"


# Retrieve API_KEY for PAN device administrative operations.
export FW_IP="<pan_fw_ip_addres>"
export USERNAME="<pan_fw_administrator_username>"
export PASSWORD="<pan_fw_administrator_password>"
export API_KEY=$(curl -k \
  -X GET "https://${FW_IP}/api/?type=keygen&user=${USERNAME}&password=${PASSWORD}" | \
  sed -n -e 's/\(.*<key>\)\(.*\)\(<\/key>.*\)/\2/p')

# N.B., add `-k` option to ignore ssl cert validation for self-signed cert on PAN api
# export API_KEY=$(curl -k -X GET "https://${FW_IP}/api/?type=keygen&user=${USERNAME}&password=${PASSWORD}" | sed -n -e 's/\(.*<key>\)\(.*\)\(<\/key>.*\)/\2/p')

echo ${API_KEY}

# N.B., please record API_KEY value; it may be re-used in subsequent runs.

# Generate AUTH_CODE for authenticating to application running in container. N.B., please record this AUTH_CODE; it may be re-used in subsequent runs.

export AUTH_CODE=$(python  -c 'import secrets; print(secrets.token_urlsafe(32))') && echo ${AUTH_CODE}

# Retrieve repository
export REPO=https://github.com/vbalbarin/function-app-docker-python-pan.git

### Clone repository
mkdir ${APP_NAME}
git clone ${REPO} ${APP_NAME} --config core.autocrlf=input
cd ${APP_NAME}

docker build -t ${DOCKER_IMAGE_TAG} .

docker run -p 8080:80 \
  -e AUTH_CODE="${AUTH_CODE}" \
  -e FW_IP="${FW_IP}" \
  -e API_KEY="${API_KEY}" \
  -it ${DOCKER_IMAGE_TAG}

# To test locally, a scrubbed Azure Alert webhook responsebody has been supplied. Edit `./samples/responseBody.sh`
# Generate a Response Body for local testing from sample/responseBody.sh.txt with specific test values
# Remember to escape dots in your_ip_address_value
sed 's/\<ip_address\>/your_ip_address_value/g' sample/responseBody.sh.txt > sample/responseBody.sh
sed -i '' 's/\<vmHHMMss\>/your_vm_name/g' sample/responseBody.sh
sed -i '' 's/\<security_zone\>/your_security_zone/g' sample/responseBody.sh

source ./reponseBody.sh

# Execute curl

curl "http://localhost:8080/api/HttpTrigger?code=${AUTH_CODE}" -X POST \ 
  -H 'Content-Type: application/json' -d "${JSON_DATA}"

# If all goes well, a JSON response with the IP Address and tags should be returned:
# TODO: create more meaninful JSON responses

{"ipAddress": "nnn.nnn.nnn.nnn", "tags": ["azure_nic_tags_ForTestingOnly_true", "azure_nic_tags_Name_vmHHMMss", "azure_nic_tags_OwnerId_fl001", "azure_nic_tags_OwnerDepartment_OwnerDepartment", "azure_nic_tags_OwnerDepartmentContact_firstname.lastname@stillness.local", "azure_nic_tags_ChargingAccount_ChargingAccount", "azure_nic_tags_SecurityZone_Zone", "azure_nic_tags_SupportDepartment_SupportDepartment", "azure_nic_tags_SupportDepartmentContact_itsdsqa@stillness.local", "azure_nic_tags_Environment_Prod", "azure_nic_tags_Application_Zone", "azure_nic_tags_CreatedBy_fl001"]}

```

## Deploying to Azure

These steps were adapted from [Create a function on Linux using a custom image (preview)](https://docs.microsoft.com/en-us/azure/azure-functions/functions-create-function-linux-custom-image#run-the-build-command). 

** This was not successful. Please see troubleshooting steps in Appendix I and the workaround in Azure Kubernetes Service (AKS) detailed in Appendix II. **

```bash
## Testing in Azure Function App Service
### Initialize environment
## Replace <value> with specific values
export APP_NAME="function-app-docker-python-pan"
export DOCKER_ID="<docker_id>"
export DOCKER_IMAGE_NAME="${APP_NAME}"

export APPSERVICE_PLAN="${APP_NAME}-asp"
export RESOURCE_GROUP_NAME="${APP_NAME}-rg"
export STORAGE_ACCOUNT_NAME="<storage_account_name>"
export DOCKER_IMAGE_TAG="${DOCKER_ID}/${DOCKER_IMAGE_NAME}:v0.0.0"

### Push custom docker container to docker hub
docker login --name ${DOCKER_ID}
docker push ${DOCKER_IMAGE_TAG}

### Create a new Azure Resource Group for Testing
az group create --name ${RESOURCE_GROUP_NAME} --location eastus2

### Create storage account
az storage account create --name ${STORAGE_ACCOUNT_NAME} \
  --location eastus2 \
  --resource-group ${RESOURCE_GROUP_NAME} \
  --sku Standard_LRS

### Retrieve storage account connection string for later use
export STORAGE_CONNECTION_STRING=$(az storage account show-connection-string \
  --resource-group ${RESOURCE_GROUP_NAME} --name ${STORAGE_ACCOUNT_NAME} \
  --query connectionString --output tsv)

### Create a new Linux appservice plan to run docker container
az appservice plan create --name ${APPSERVICE_PLAN} \
  --resource-group ${RESOURCE_GROUP_NAME} \
  --sku S1 --is-linux 

### Create new function app using custom docker image
az functionapp create --name ${APP_NAME} \ 
  --storage-account ${STORAGE_ACCOUNT_NAME} \
  --resource-group ${RESOURCE_GROUP_NAME} \
  --plan ${APPSERVICE_PLAN} \
  --deployment-container-image-name ${DOCKER_IMAGE_TAG}

### Configure function app with storage account connection strings
az functionapp config appsettings set --name ${APP_NAME} \
  --resource-group ${RESOURCE_GROUP_NAME} \
  --settings AzureWebJobsDashboard=${STORAGE_CONNECTION_STRING} \
    AzureWebJobsStorage=${STORAGE_CONNECTION_STRING}

### Open browser to 
### http://${APP_NAME}.azurewebsites.net/api/HttpTrigger?name=foo
```

## References

[`pandevice`](https://github.com/PaloAltoNetworks/pandevice)

[`azure-vm-monitoring`](https://github.com/PaloAltoNetworks/azure-vm-monitoring)

[Create a function on Linux using a custom image (preview)](https://docs.microsoft.com/en-us/azure/azure-functions/functions-create-function-linux-custom-image#run-the-build-command)

[`azure-functions-docker-python-sample`](https://github.com/Azure/azure-functions-docker-python-sample)

## Appendix I: Troubleshooting Function  App on Linux: Azure Function App 2.0, Docker, and Python

### Testing Azure Function Apps in Custom Image

Steps to run an Azure Function App in a custom Linux container using the Azure Function App 2.0 runtime--adapted from [Create a function on Linux using a custom image (Preview)](https://docs.microsoft.com/en-us/azure/azure-functions/functions-create-function-linux-custom-image#run-the-build-command)

The following repositories were tested:

1. https://github.com/Azure-Samples/functions-linux-custom-image.git
2. https://github.com/Azure/azure-functions-docker-python-sample.git

```bash
### Initialize environment
## Replace <value> with specific values
export DOCKER_ID=<docker_id>
export DOCKER_IMAGE_NAME=<docker_image_name>

export APPSERVICE_PLAN=<azure_appservice_name>
export APP_NAME=<application_name>
export RESOURCE_GROUP_NAME=<resource_group_name>
export STORAGE_ACCOUNT_NAME=<storage_account_name>

export DOCKER_IMAGE_TAG=${DOCKER_ID}/${DOCKER_IMAGE_NAME}:v0.0.0

### REPOs to test, uncomment one or the other

# export REPO=https://github.com/Azure-Samples/functions-linux-custom-image.git
# or
# export REPO=https://github.com/Azure/azure-functions-docker-python-sample.git

### Clone repository
mkdir ${APP_NAME}
git clone ${REPO} ${APP_NAME} --config core.autocrlf=input

### Build docker container
cd ${APP_NAME}
docker build --tag ${DOCKER_IMAGE_TAG} .

### Run docker container
docker run --publish 8080:80 --tag ${DOCKER_IMAGE_TAG} --interactive

### Test locally
# repo 1
# curl http://localhost:8080/api/HttpTriggerJS1?name=Foo
# or
# repo 2
# curl http://localhost:8080/api/HttpTrigger?name=Foo


## Testing in Azure Function App Service

### Push custom docker container to docker hub
docker login --name ${DOCKER_ID}
docker push ${DOCKER_IMAGE_TAG}

### Create a new Azure Resource Group for Testing
az group create --name ${RESOURCE_GROUP_NAME} --location eastus2

### Create storage account
az storage account create --name ${STORAGE_ACCOUNT_NAME} \
  --location eastus2 \
  --resource-group ${RESOURCE_GROUP_NAME} \
  --sku Standard_LRS

### Retrieve storage account connection string for later use
export STORAGE_CONNECTION_STRING=$(az storage account show-connection-string \
  --resource-group ${RESOURCE_GROUP_NAME} --name ${STORAGE_ACCOUNT_NAME} \
  --query connectionString --output tsv)

### Create a new Linux appservice plan to run docker container
az appservice plan create --name ${APPSERVICE_PLAN} \
  --resource-group ${RESOURCE_GROUP_NAME} \
  --sku S1 --is-linux 

### Create new function app using custom docker image
az functionapp create --name ${APP_NAME} \ 
  --storage-account ${STORAGE_ACCOUNT_NAME} \
  --resource-group ${RESOURCE_GROUP_NAME} \
  --plan ${APPSERVICE_PLAN} \
  --deployment-container-image-name ${DOCKER_IMAGE_TAG}

### Configure function app with storage account connection strings
az functionapp config appsettings set --name ${APP_NAME} \
  --resource-group ${RESOURCE_GROUP_NAME} \
  --settings AzureWebJobsDashboard=${STORAGE_CONNECTION_STRING} \
    AzureWebJobsStorage=${STORAGE_CONNECTION_STRING}

### Open browser to 
### http://${APP_NAME}.azurewebsites.net/api/HttpTriggerJS1?name=foo
### or
### http://${APP_NAME}.azurewebsites.net/api/HttpTrigger?name=foo
```

## Appendix II: Creating AKS cluster in a VNET

Because of a breaking change on the Azure Function App backend, Function Apps could not be hosted on docker. A workaround hosting the Python Docker Image running the Azure Function App v2 runtime in an Azure Kubernetes Service (AKS) cluster attached to an Azure VNET was used.

Replace the `<value>`s strings with suitable values for your environment. In order to perform the following steps, one must have the following permissions:

1. Network Contributor roles in the subscription or resource groups containing the AKS VNET and the "Hub" VNET containing the enterprise gateway.

2. Permission to create Azure Active Directory application registrations/service principals that will be used to pull Docker images from the Azure Container Registry.

3. User Access Administrator role to assign roles to applications/service principals.

```bash
$ # Deleted Credentials of test Service Principal, these are now generated in situ below.
$ # Deleted Service Principal.
$ # delete AZ_ environment variables

$ while IFS= read -r result; do unset ${result%%=*}; done < <(env | grep AZ_)

$ export AZ_AKS_LOCATION=eastus2 && \
  export AZ_AKS_NAME=<azure_kubernetes_service_cluster_name> && \
  export AZ_ACR_NAME=<azure_container_repository_name> && \
  export AZ_AKS_RESOURCE_GROUP=${AZ_AKS_NAME}-rg && \
  export AZ_ACR_RESOURCE_GROUP=${AZ_ACR_NAME}-rg && \
  export AZ_AKS_CLUSTER=${AZ_AKS_NAME}-cluster && \
  export AZ_AKS_VNET=${AZ_AKS_NAME}-${AZ_AKS_LOCATION}-vnet && \
  export AZ_AKS_VNET_CIDR='<azure_vnet_cidr_block_for_azure_kubernetes_service_slash22>' && \
  export AZ_AKS_DNS_SERVICE_IP='<azure_kubernetes_dns_service_ip_in_cidr_block_for_services>' && \
  export AZ_AKS_CLUSTER_SUBNET=${AZ_AKS_NAME}-cluster-subnet && \
  export AZ_AKS_SERVICE_SUBNET=${AZ_AKS_NAME}-service-subnet && \
  export AZ_AKS_CLUSTER_SUBNET_CIDR='<azure_kubernetes_cidr_block_for_cluster_subnet_slash23>' && \
  export AZ_AKS_SERVICE_CIDR='<azure_kubernetes_cidr_block_for_services_slash24>'

$ az login
Note, we have launched a browser for you to login. For old experience with device code, use "az login --use-device-code"
You have logged in. Now let us find all subscriptions you have access to...
[
  {
    "cloudName": "AzureCloud",
    "id": "aaaaaaaa-bbbb-0000-1111-cccccccccccc",
    "isDefault": true,
    "name": "SubscriptionName",
    "state": "Enabled",
    "tenantId": "aaaaaaaa-bbbb-0000-1111-cccccccccccc",
    "user": {
      "name": "first.last@contoso.com",
      "type": "user"
    }
  },
  <truncated>
]

$ export AZ_CURRENT_SUBSCRPTN_ID=$(az account show --query "id" --output tsv)

$ # Search for "id" value that corresponds to subscription in which to place AKS resource group.
$ # $ az account set -s "< id >"

$ az group create --name ${AZ_AKS_RESOURCE_GROUP} --location ${AZ_AKS_LOCATION}

$ # Create VNET with AZ_AKS_CLUSTER_SUBNET
$ az network vnet create --name ${AZ_AKS_VNET} \
                         --location ${AZ_AKS_LOCATION} \
                         --resource-group ${AZ_AKS_RESOURCE_GROUP} \
                         --address-prefix "${AZ_AKS_VNET_CIDR}" \
                         --subnet-name ${AZ_AKS_CLUSTER_SUBNET} \
                         --subnet-prefix "${AZ_AKS_CLUSTER_SUBNET_CIDR}"

$ export AZ_AKS_VNET_ID=$(az network vnet show --name ${AZ_AKS_VNET} \
                                               --resource-group ${AZ_AKS_RESOURCE_GROUP} \
                                               --query "id" --output tsv)

$ # Create service subnet (May not be necessary. TODO: ASK)
$ #$ az network vnet subnet create --name ${AZ_AKS_SERVICE_SUBNET} \
$ #                                --resource-group ${AZ_AKS_RESOURCE_GROUP} \
$ #                                --vnet-name ${AZ_AKS_VNET} \
$ #                                --address-prefix "${AZ_AKS_SERVICE_CIDR}"

$ # Will need to create peering with hub VNET.

$ # Create peering from current subscription to remote vnet in second subscription
$ # Retrieve subscription id of subscription containing the remote vnet, in this case <ITS Shared Services>

$ export AZ_REMOTE_VNET_SUBSCRPTN_NAME="ITS Shared Services" && \
  export AZ_AKS_VNET_PEER="VNET-ITS-SharedServices" && \
  export AZ_REMOTE_VNET_SUBSCRPTN_QUERY="[?name=='${AZ_REMOTE_VNET_SUBSCRPTN_NAME}'].{subscriptionId: id}" && \
  export AZ_REMOTE_VNET_QUERY="[?name=='${AZ_AKS_VNET_PEER}'].{vnetID: id}" && \
  export AZ_REMOTE_VNET_RG_QUERY="[?name=='${AZ_AKS_VNET_PEER}'].{vnetRG: resourceGroup}"


$ export AZ_REMOTE_VNET_SUBSCRPTN_ID=$(az account list --query "${AZ_REMOTE_VNET_SUBSCRPTN_QUERY}" \
                                                           --output tsv)

$ export AZ_REMOTE_VNET_RG=$(az network vnet list --subscription ${AZ_REMOTE_VNET_SUBSCRPTN_ID} \
                                                  --query "${AZ_REMOTE_VNET_RG_QUERY}" \
                                                  --output tsv)

$ # Using subscription id, retrieve resource id of the remote vnet with name <VNET-ITS-SharedServices>
$ export AZ_REMOTE_VNET_ID=$(az network vnet list --subscription ${AZ_REMOTE_VNET_SUBSCRPTN_ID} \
                                                  --query "${AZ_REMOTE_VNET_QUERY}" \
                                                  --output tsv)

$ az network vnet peering create --resource-group ${AZ_AKS_RESOURCE_GROUP} \
                                 --name ${AZ_AKS_VNET}-${AZ_AKS_VNET_PEER}-peering \
                                 --vnet-name ${AZ_AKS_VNET} \
                                 --remote-vnet-id ${AZ_REMOTE_VNET_ID} \
                                 --allow-vnet-access \
                                 --allow-forwarded-traffic \
                                 --use-remote-gateways

$ # Create peering from remote vnet in second subscription to vnet in current subscription
$ # Specifying remote subscription id and reversing values:

$ az network vnet peering create --subscription ${AZ_REMOTE_VNET_SUBSCRPTN_ID} \
                                 --resource-group ${AZ_REMOTE_VNET_RG} \
                                 --name ${AZ_AKS_VNET_PEER}-${AZ_AKS_VNET}-peering \
                                 --vnet-name ${AZ_AKS_VNET_PEER} \
                                 --remote-vnet-id ${AZ_AKS_VNET_ID} \
                                 --allow-vnet-access \
                                 --allow-forwarded-traffic \
                                 --allow-gateway-transit

$ # Create a service principal and get name and password.
$ az ad sp create-for-rbac --skip-assignment --name ${AZ_AKS_NAME}-$(date -j -f "%a %b %d %T %Z %Y" "`date`" "+%s")-app-sp | tee "/tmp/AZ_sp.json"

$ #  `jq` utility istalled via via homebrew
$ export AZ_SERVICE_PRINCIPAL=$(jq -r .appId "/tmp/AZ_sp.json") && \
  export AZ_CLIENT_SECRET=$(jq -r .password "/tmp/AZ_sp.json")

$ # Get subnet resource id
$ export AZ_AKS_CLUSTER_SUBNET_ID="$(az network vnet subnet list --resource-group ${AZ_AKS_RESOURCE_GROUP} --vnet-name ${AZ_AKS_VNET} --query [].id --output tsv | grep ${AZ_AKS_CLUSTER_SUBNET})"

$ # Assign role to service principal
$ az role assignment create --assignee ${AZ_SERVICE_PRINCIPAL} \
                            --role "Network Contributor" \
                            --scope "${AZ_AKS_CLUSTER_SUBNET_ID}"


$ # Create AKS cluster
$ az aks create --resource-group ${AZ_AKS_RESOURCE_GROUP} \
              --name ${AZ_AKS_CLUSTER} \
              --network-plugin azure \
              --vnet-subnet-id "${AZ_AKS_CLUSTER_SUBNET_ID}" \
              --docker-bridge-address 172.17.0.1/16 \
              --service-cidr ${AZ_AKS_SERVICE_CIDR} \
              --dns-service-ip ${AZ_AKS_DNS_SERVICE_IP} \
              --service-principal ${AZ_SERVICE_PRINCIPAL} \
              --client-secret "${AZ_CLIENT_SECRET}" \
              --debug

$ # Get cluster credentials and cache in .kube config
$ az aks get-credentials --resource-group ${AZ_AKS_RESOURCE_GROUP} --name ${AZ_AKS_CLUSTER}

$ kubectl get nodes
NAME                       STATUS    ROLES     AGE       VERSION
aks-nodepool1-56068326-0   Ready     agent     19h       v1.9.9
aks-nodepool1-56068326-1   Ready     agent     19h       v1.9.9
aks-nodepool1-56068326-2   Ready     agent     19h       v1.9.9

$ export AZ_ACR_LOGIN_SERVER=$(az acr list --resource-group ${AZ_ACR_RESOURCE_GROUP} --query "[].{acrLoginServer:loginServer}" --output tsv) && \
 export AZ_ACR_IMAGE=function-app-docker-python-pan:v0.0.0 && \
 export AZ_FUNC_NAME=function-app-docker-python-pan

$ # Allow SP access to ACR registry
$ export AZ_ACR_REGISTRY_ID=$(az acr show --name ${AZ_ACR_NAME} --query id --output tsv)
$ az role assignment create --assignee ${AZ_SERVICE_PRINCIPAL} --scope "${AZ_ACR_REGISTRY_ID}" --role reader

$ cat <<:EOF | tee function-app-docker-python-pan.yaml
---
apiVersion: apps/v1beta1
kind: Deployment
metadata:
  name: ${AZ_FUNC_NAME}
spec:
  replicas: 1
  template:
    metadata:
      labels:
        app: ${AZ_FUNC_NAME}
    spec:
      containers:
      - name: ${AZ_FUNC_NAME}
        image: ${AZ_ACR_LOGIN_SERVER}/${AZ_ACR_IMAGE}
        ports:
        - containerPort: 80
        env:
        - name: AUTH_CODE
          valueFrom:
            secretKeyRef:
              name: authcode
              key: AUTH_CODE
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: apikey
              key: API_KEY
        - name: FW_IP
          valueFrom:
            configMapKeyRef:
              name: fwip
              key: FW_IP
---
apiVersion: v1
kind: Service
metadata:
  name: ${AZ_FUNC_NAME}
  annotations:
    service.beta.kubernetes.io/azure-load-balancer-internal: "true"
spec:
  type: LoadBalancer
  ports:
  - port: 80
  selector:
    app: ${AZ_FUNC_NAME}
:EOF

$ # Create Secrets for Kubernetes
$ kubectl create secret generic authcode --from-literal=AUTH_CODE="${AUTH_CODE}" && \
  kubectl create secret generic apikey --from-literal=API_KEY="${API_KEY}" && \
  kubectl create configmap fwip --from-literal=FW_IP="${FW_IP}"

$ # Deploy application
$ kubectl apply -f function-app-docker-python-pan.yaml

$ # Obtain pod status
$ kubectl get pods
NAME                                              READY     STATUS    RESTARTS   AGE
function-app-docker-python-pan-788f777c49-mf9zp   1/1       Running   0          3m

$ # Obtain service status
$ kubectl get service ${AZ_FUNC_NAME} --watch
NAME                             TYPE           CLUSTER-IP   EXTERNAL-IP       PORT(S)        AGE
function-app-docker-python-pan   LoadBalancer   <cluster-ip> <internal-ip>     80:31865/TCP   5m
$ # The external IP is the IP of the Interanl LoadBalancer taken from the IP address pool of the AKS cluster

$ # Testing.
$ # Generate a Response Body for local testing from sample/responseBody.sh.txt with specific test values
$ # Remember to escape dots in your_ip_address_value
$ sed 's/\<ip_address\>/your_ip_address_value/g' sample/responseBody.sh.txt > sample/responseBody.sh
$ sed -i '' 's/\<vmHHMMss\>/your_vm_name/g' sample/responseBody.sh
$ sed -i '' 's/\<security_zone\>/your_security_zone/g' sample/responseBody.sh
$
$ source ./sample/responseBody.sh
$ curl "http://<internal-ip>/api/HttpTrigger?code=${AUTH_CODE}" -X POST -H 'Content-Type: application/json'  -d "${JSON_DATA}"
{"ipAddress": "<vm_private_ip>", "tags": ["azure_nic_tags_ForTestingOnly_true", "azure_nic_tags_Name_vm123308", "azure_nic_tags_OwnerId_fl001", "azure_nic_tags_OwnerDepartment_OwnerDepartment", "azure_nic_tags_OwnerDepartmentContact_firstname.lastname@stillness.local", "azure_nic_tags_ChargingAccount_ChargingAccount", "azure_nic_tags_SecurityZone_High", "azure_nic_tags_SupportDepartment_SupportDepartment", "azure_nic_tags_SupportDepartmentContact_itsdsqa@stillness.local", "azure_nic_tags_Environment_Prod", "azure_nic_tags_Application_App", "azure_nic_tags_CreatedBy_fl001"]}
$ # verify on the PAN

````

### Results

1. Testing `https://github.com/Azure-Samples/functions-linux-custom-image.git`

```bash
# local
curl http://localhost:8080/api/HttpTriggerJS1?name=foo
# Works
```

Browsing with Chrome to url `http://${APP_NAME}.azurewebsites.net/api/HttpTriggerJS1?name=foo`works correctly.

2. Testing `https://github.com/Azure/azure-functions-docker-python-sample.git`

```bash
curl "http://localhost:8080/api/HttpTrigger?name=foo"
# Returns null
```

Browsing with Chrome to url `http://${APP_NAME}.azurewebsites.net/api/HttpTrigger?name=foo` returns a 500 error.
