# Search and replace following values in file and then `source responseBody.sh` 
# IP Address:                           nnn.nnn.nnn.nnn
# VM Name:                              vmHHMMss
# Security Zone [High|Medium|Low|None]: Zone

export JSON_DATA='{"authorization":{"action":"Microsoft.Network/networkInterfaces/write","scope":"/subscriptions/ae2298e8-test-11e8-94ab-acbc32a6d8a1/resourcegroups/vmHHMMss-rg/providers/Microsoft.Network/networkInterfaces/vmHHMMss-nic"},"caller":"firstname.lastname@stillness.local","channels":"Operation","claims":{"aud":"https://management.core.windows.net/","iss":"https://sts.windows.net/8d8eae5a-test-11e8-8c77-acbc32a6d8a1/","iat":"000000test","nbf":"000000test","exp":"000000test","_claim_names":"{\"groups\":\"src1\"}","_claim_sources":"{\"src1\":{\"endpoint\":\"https://graph.windows.net/8d8eae5a-test-11e8-8c77-acbc32a6d8a1/users/7b458ade-test-11e8-b8d8-acbc32a6d8a1/getMemberObjects\"}}","http://schemas.microsoft.com/claims/authnclassreference":"1","aio":"test-26EPwTmzuiLttfNzMInyWgqobsJrG8ttBiGZm4kKNQx-svIPTGitJ301_MuGZWBhpTp2DD4syRcg9zY4g1A6Hz26EPwTmzuiLttfNzMInyWgqobsJr=","http://schemas.microsoft.com/claims/authnmethodsreferences":"pwd,mfa","appid":"9be2f346-test-11e8-9360-acbc32a6d8a1","appidacr":"0","e_exp":"262800","http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname":"lastname","http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname":"firstname","ipaddr":"169.254.0.1","name":"lastname, firstname","http://schemas.microsoft.com/identity/claims/objectidentifier":"7b458ade-test-11e8-b8d8-acbc32a6d8a1","onprem_sid":"S-1-5-21-000000000-00000000-0000000000-00000","puid":"10033FFF8524C971","http://schemas.microsoft.com/identity/claims/scope":"user_impersonation","http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier":"test-vum8s30tK2rBvhsm-TSiHXVxzvKmq3FhZD0Pd8","http://schemas.microsoft.com/identity/claims/tenantid":"8d8eae5a-test-11e8-8c77-acbc32a6d8a1","http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name":"firstname.lastname@stillness.local","http://schemas.xmlsoap.org/ws/2005/05/identity/claims/upn":"firstname.lastname@stillness.local","uti":"wvOuLIG6LUOpPnIsU0cKAA","ver":"1.0"},"correlationId":"b11ab983-test-4c85-bc67-e6f9fac9be66","description":"","eventDataId":"8f7ca8ba-test-11e8-a63f-acbc32a6d8a1","eventName":{"value":"EndRequest","localizedValue":"End request"},"category":{"value":"Administrative","localizedValue":"Administrative"},"eventTimestamp":"2018-04-30T14:53:36.4755868Z","id":"/subscriptions/ae2298e8-test-11e8-94ab-acbc32a6d8a1/resourcegroups/vmHHMMss-rg/providers/Microsoft.Network/networkInterfaces/vmHHMMss-nic/events/8f7ca8ba-test-11e8-a63f-acbc32a6d8a1/ticks/636606968164755868","level":"Informational","operationId":"3a651772-test-4c81-8471-70e6de95c2c7","operationName":{"value":"Microsoft.Network/networkInterfaces/write","localizedValue":"Microsoft.Network/networkInterfaces/write"},"resourceGroupName":"vmHHMMss-rg","resourceProviderName":{"value":"Microsoft.Network","localizedValue":"Microsoft.Network"},"resourceType":{"value":"Microsoft.Network/networkInterfaces","localizedValue":"Microsoft.Network/networkInterfaces"},"resourceId":"/subscriptions/ae2298e8-test-11e8-94ab-acbc32a6d8a1/resourcegroups/vmHHMMss-rg/providers/Microsoft.Network/networkInterfaces/vmHHMMss-nic","status":{"value":"Succeeded","localizedValue":"Succeeded"},"subStatus":{"value":"Created","localizedValue":"Created (HTTP Status Code: 201)"},"submissionTimestamp":"2018-04-30T14:53:50.1104276Z","subscriptionId":"ae2298e8-test-11e8-94ab-acbc32a6d8a1","properties":{"statusCode":"Created","serviceRequestId":"1a694686-test-11e8-b94d-acbc32a6d8a1","responseBody":"{\"name\":\"vmHHMMss-nic\",\"id\":\"/subscriptions/ae2298e8-test-11e8-94ab-acbc32a6d8a1/resourceGroups/vmHHMMss-rg/providers/Microsoft.Network/networkInterfaces/vmHHMMss-nic\",\"etag\":\"W/\\\"10c6a2b4-test-11e8-8faf-acbc32a6d8a1\\\"\",\"location\":\"eastus2\",\"tags\":{\"ForTestingOnly\":\"true\",\"Name\":\"vmHHMMss\",\"OwnerId\":\"fl001\",\"OwnerDepartment\":\"OwnerDepartment\",\"OwnerDepartmentContact\":\"firstname.lastname@stillness.local\",\"ChargingAccount\":\"ChargingAccount\",\"SecurityZone\":\"Zone\",\"SupportDepartment\":\"SupportDepartment\",\"SupportDepartmentContact\":\"itsdsqa@stillness.local\",\"Environment\":\"Prod\",\"Application\":\"Zone\",\"CreatedBy\":\"fl001\"},\"properties\":{\"provisioningState\":\"Succeeded\",\"resourceGuid\":\"e2bfa12d-abc3-4b4e-9a24-26c003860ce4\",\"ipConfigurations\":[{\"name\":\"ipconfig1\",\"id\":\"/subscriptions/ae2298e8-test-11e8-94ab-acbc32a6d8a1/resourceGroups/vmHHMMss-rg/providers/Microsoft.Network/networkInterfaces/vmHHMMss-nic/ipConfigurations/ipconfig1\",\"etag\":\"W/\\\"10c6a2b4-test-11e8-8faf-acbc32a6d8a1\\\"\",\"properties\":{\"provisioningState\":\"Succeeded\",\"privateIPAddress\":\"nnn.nnn.nnn.nnn\",\"privateIPAllocationMethod\":\"Dynamic\",\"subnet\":{\"id\":\"/subscriptions/ae2298e8-test-11e8-94ab-acbc32a6d8a1/resourceGroups/sandbox-vnet-rg/providers/Microsoft.Network/virtualNetworks/sandbox-vnet/subnets/sandbox-1-subnet\"},\"primary\":true,\"privateIPAddressVersion\":\"IPv4\",\"isInUseWithService\":false}}],\"dnsSettings\":{\"dnsServers\":[],\"appliedDnsServers\":[],\"internalDomainNameSuffix\":\"nhttefyh0h0e3mi0qmi5ompvmb.cx.internal.cloudapp.net\"},\"enableAcceleratedNetworking\":false,\"enableIPForwarding\":false,\"networkSecurityGroup\":{\"id\":\"/subscriptions/ae2298e8-test-11e8-94ab-acbc32a6d8a1/resourceGroups/vmHHMMss-rg/providers/Microsoft.Network/networkSecurityGroups/vmHHMMss-nsg\"}},\"type\":\"Microsoft.Network/networkInterfaces\"}","requestbody":"{\"location\":\"eastus2\",\"tags\":{\"ForTestingOnly\":\"true\",\"Name\":\"vmHHMMss\",\"OwnerId\":\"fl001\",\"OwnerDepartment\":\"OwnerDepartment\",\"OwnerDepartmentContact\":\"firstname.lastname@stillness.local\",\"ChargingAccount\":\"ChargingAccount\",\"SecurityZone\":\"Zone\",\"SupportDepartment\":\"SupportDepartment\",\"SupportDepartmentContact\":\"itsdsqa@stillness.local\",\"Environment\":\"Dev\",\"Application\":\"Zone\",\"CreatedBy\":\"fl001\"},\"properties\":{\"ipConfigurations\":[{\"name\":\"ipconfig1\",\"properties\":{\"subnet\":{\"id\":\"/subscriptions/ae2298e8-test-11e8-94ab-acbc32a6d8a1/resourceGroups/sandbox-vnet-rg/providers/Microsoft.Network/virtualNetworks/sandbox-vnet/subnets/sandbox-1-subnet\"},\"privateIPAllocationMethod\":\"Dynamic\"}}],\"networkSecurityGroup\":{\"id\":\"/subscriptions/ae2298e8-test-11e8-94ab-acbc32a6d8a1/resourceGroups/vmHHMMss-rg/providers/Microsoft.Network/networkSecurityGroups/vmHHMMss-nsg\"}}}"},"relatedEvents":[]}'