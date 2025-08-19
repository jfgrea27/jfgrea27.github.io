## Infra

```zsh
RESOURCE_GROUP=tfjfgrea27
LOCATION=uksouth
STORAGE_ACCOUNT=tfaccountjfgrea27
STORAGE_CONTAINER=tfstatejfgrea27
# create resource group
az group create --name $RESOURCE_GROUP  --location $LOCATION
# create service account for tf-state
az storage account create \
    --name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku Standard_LRS
# create storage container for tf-state
az storage container create \
    --name $STORAGE_CONTAINER \
    --account-name $STORAGE_ACCOUNT
```
