resource "azurerm_app_service_plan" "test" {
  name                = "${var.application_type}-${var.resource_type}"
  location            = "${var.location}"
  resource_group_name = "${var.resource_group}"
  kind                = "Windows"

  sku {
    tier = "Basic"
    size = "B1"
  }
}

resource "azurerm_app_service" "test" {
  name                = "${var.application_type}-${var.resource_type}-${var.app_suffix}"
  location            = "${var.location}"
  resource_group_name = "${var.resource_group}"
  app_service_plan_id = azurerm_app_service_plan.test.id

  site_config {
    dotnet_framework_version = "v4.0"
  }

  # WEBSITE_RUN_FROM_PACKAGE must be 0 or absent for regular zip deploy.
  # Value of "1" causes Azure to mount from a managed blob that doesn't exist,
  # which leaves a 503-returning Web.config placeholder in wwwroot.
  app_settings = {
    "WEBSITE_RUN_FROM_PACKAGE" = "0"
  }
}
