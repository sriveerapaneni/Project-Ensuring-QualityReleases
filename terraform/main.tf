provider "azurerm" {
  tenant_id       = "${var.tenant_id}"
  subscription_id = "${var.subscription_id}"
  client_id       = "${var.client_id}"
  client_secret   = "${var.client_secret}"
  features {}
}
terraform {
  backend "azurerm" {
    storage_account_name = "svuniquetfstorage"
    container_name       = "tfstate"
    key                  = "terraform.tfstate"
    access_key           = "ENbVB4GPp0SP+fFOwVud71E0x9dAAL8CSXt4c0A3ptpHzTZUq0xaD2Fyok8q0W38mD9IF2Il9kQZ+AStqGFI1Q=="
  }
}
module "resource_group" {
  source               = "./modules/resource_group"
  resource_group       = "${var.resource_group}"
  location             = "${var.location}"
}
module "network" {
  source               = "./modules/network"
  address_space        = "${var.address_space}"
  location             = "${var.location}"
  virtual_network_name = "${var.virtual_network_name}"
  application_type     = "${var.application_type}"
  resource_type        = "NET"
  resource_group       = "${module.resource_group.resource_group_name}"
  address_prefix_test  = "${var.address_prefix_test}"
}

module "nsg-test" {
  source           = "./modules/networksecuritygroup"
  location         = "${var.location}"
  application_type = "${var.application_type}"
  resource_type    = "NSG"
  resource_group   = "${module.resource_group.resource_group_name}"
  subnet_id        = "${module.network.subnet_id_test}"
  address_prefix_test = "${var.address_prefix_test}"
}
module "appservice" {
  source           = "./modules/appservice"
  location         = "${var.location}"
  application_type = "${var.application_type}"
  resource_type    = "AppService"
  resource_group   = "${module.resource_group.resource_group_name}"
}
module "publicip" {
  source           = "./modules/publicip"
  location         = "${var.location}"
  application_type = "${var.application_type}"
  resource_type    = "publicip"
  resource_group   = "${module.resource_group.resource_group_name}"
}
module "vm" {
  source               = "./modules/vm"
  location             = "${var.location}"
  application_type     = "${var.application_type}"
  resource_type        = "VM"
  resource_group       = "${module.resource_group.resource_group_name}"
  admin_username       = "${var.admin_username}"
  public_ip_address_id = "${module.publicip.public_ip_address_id}"
  subnet_id            = "${module.network.subnet_id_test}"
}
module "loganalytics" {
  source           = "./modules/loganalytics"
  location         = "${var.location}"
  application_type = "${var.application_type}"
  resource_type    = "LogAnalytics"
  resource_group   = "${module.resource_group.resource_group_name}"
  workspace_name   = "${var.workspace_name}"
}
