# 🥤 NovaLat - Infraestructura como Código
# Terraform para Azure - Sistema de trazabilidad alimentaria

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.45"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }
  
  backend "azurerm" {
    resource_group_name  = "novalat-terraform-state"
    storage_account_name = "novalatterraformstate"
    container_name       = "tfstate"
    key                  = "novalat.terraform.tfstate"
  }
}

# Configurar proveedor Azure
provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
    key_vault {
      purge_soft_delete_on_destroy = true
    }
  }
}

# Variables
variable "environment" {
  description = "Ambiente de despliegue"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment debe ser dev, staging o prod."
  }
}

variable "location" {
  description = "Región de Azure"
  type        = string
  default     = "East US"
}

variable "project_name" {
  description = "Nombre del proyecto"
  type        = string
  default     = "novalat"
}

variable "company_name" {
  description = "Nombre de la empresa"
  type        = string
  default     = "NovaLat"
}

# Tags comunes
locals {
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    Company     = var.company_name
    ManagedBy   = "Terraform"
    Purpose     = "Food Traceability System"
  }
  
  name_prefix = "${var.project_name}-${var.environment}"
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "${local.name_prefix}-rg"
  location = var.location
  
  tags = local.common_tags
}

# Virtual Network
resource "azurerm_virtual_network" "main" {
  name                = "${local.name_prefix}-vnet"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  address_space       = ["10.0.0.0/16"]
  
  tags = local.common_tags
}

# Subnets
resource "azurerm_subnet" "aks" {
  name                 = "${local.name_prefix}-aks-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.1.0/24"]
}

resource "azurerm_subnet" "database" {
  name                 = "${local.name_prefix}-db-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.2.0/24"]
  
  service_endpoints = ["Microsoft.Sql"]
}

# Azure Kubernetes Service (AKS)
resource "azurerm_kubernetes_cluster" "main" {
  name                = "${local.name_prefix}-aks"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  dns_prefix          = "${local.name_prefix}-aks"
  
  default_node_pool {
    name                = "default"
    node_count          = var.environment == "prod" ? 3 : 2
    vm_size             = var.environment == "prod" ? "Standard_D4s_v3" : "Standard_D2s_v3"
    os_disk_size_gb     = 128
    vnet_subnet_id      = azurerm_subnet.aks.id
    enable_auto_scaling = true
    min_count           = 1
    max_count           = var.environment == "prod" ? 5 : 3
  }
  
  identity {
    type = "SystemAssigned"
  }
  
  network_profile {
    network_plugin     = "azure"
    network_policy     = "azure"
    load_balancer_sku  = "standard"
    service_cidr       = "10.1.0.0/16"
    dns_service_ip     = "10.1.0.10"
    docker_bridge_cidr = "172.17.0.1/16"
  }
  
  addon_profile {
    oms_agent {
      enabled                    = true
      log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
    }
  }
  
  tags = local.common_tags
}

# Log Analytics Workspace
resource "azurerm_log_analytics_workspace" "main" {
  name                = "${local.name_prefix}-logs"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  
  tags = local.common_tags
}

# Azure Database for PostgreSQL
resource "azurerm_postgresql_server" "main" {
  name                = "${local.name_prefix}-postgres"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  
  sku_name = var.environment == "prod" ? "GP_Gen5_4" : "B_Gen5_2"
  
  storage_mb                   = var.environment == "prod" ? 102400 : 5120
  backup_retention_days        = 7
  geo_redundant_backup_enabled = var.environment == "prod"
  auto_grow_enabled            = true
  
  administrator_login          = "novalat_admin"
  administrator_login_password = random_password.postgres_password.result
  version                     = "11"
  ssl_enforcement_enabled     = true
  
  tags = local.common_tags
}

# PostgreSQL Database
resource "azurerm_postgresql_database" "traceability" {
  name                = "novalat_traceability"
  resource_group_name = azurerm_resource_group.main.name
  server_name         = azurerm_postgresql_server.main.name
  charset             = "UTF8"
  collation           = "en_US.utf8"
}

# Azure Redis Cache
resource "azurerm_redis_cache" "main" {
  name                = "${local.name_prefix}-redis"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  capacity            = var.environment == "prod" ? 2 : 1
  family              = var.environment == "prod" ? "C" : "C"
  sku_name            = var.environment == "prod" ? "Standard" : "Basic"
  enable_non_ssl_port = false
  
  redis_configuration {
    maxmemory_reserved = 2
    maxmemory_delta    = 2
    maxmemory_policy   = "volatile-lru"
  }
  
  tags = local.common_tags
}

# Azure Container Registry
resource "azurerm_container_registry" "main" {
  name                = "${replace(local.name_prefix, "-", "")}acr"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.environment == "prod" ? "Premium" : "Basic"
  admin_enabled       = true
  
  tags = local.common_tags
}

# Key Vault para secretos
resource "azurerm_key_vault" "main" {
  name                        = "${local.name_prefix}-kv"
  location                    = azurerm_resource_group.main.location
  resource_group_name         = azurerm_resource_group.main.name
  enabled_for_disk_encryption = true
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days  = 7
  purge_protection_enabled    = false
  sku_name                    = "standard"
  
  tags = local.common_tags
}

# Access Policy para AKS
resource "azurerm_key_vault_access_policy" "aks" {
  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_kubernetes_cluster.main.kubelet_identity[0].object_id
  
  key_permissions = [
    "Get",
    "List"
  ]
  
  secret_permissions = [
    "Get",
    "List"
  ]
  
  certificate_permissions = [
    "Get",
    "List"
  ]
}

# Application Gateway
resource "azurerm_public_ip" "agw" {
  name                = "${local.name_prefix}-agw-pip"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  allocation_method   = "Static"
  sku                 = "Standard"
  
  tags = local.common_tags
}

resource "azurerm_application_gateway" "main" {
  name                = "${local.name_prefix}-agw"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  
  sku {
    name     = var.environment == "prod" ? "WAF_v2" : "Standard_v2"
    tier     = var.environment == "prod" ? "WAF_v2" : "Standard_v2"
    capacity = var.environment == "prod" ? 2 : 1
  }
  
  gateway_ip_configuration {
    name      = "gateway-ip-configuration"
    subnet_id = azurerm_subnet.aks.id
  }
  
  frontend_port {
    name = "http-port"
    port = 80
  }
  
  frontend_ip_configuration {
    name                 = "frontend-ip-configuration"
    public_ip_address_id = azurerm_public_ip.agw.id
  }
  
  backend_address_pool {
    name = "backend-pool"
  }
  
  backend_http_settings {
    name                  = "http-settings"
    cookie_based_affinity = "Disabled"
    port                  = 80
    protocol              = "Http"
    request_timeout       = 60
  }
  
  http_listener {
    name                           = "http-listener"
    frontend_ip_configuration_name = "frontend-ip-configuration"
    frontend_port_name             = "http-port"
    protocol                       = "Http"
  }
  
  request_routing_rule {
    name                       = "routing-rule"
    rule_type                  = "Basic"
    http_listener_name         = "http-listener"
    backend_address_pool_name  = "backend-pool"
    backend_http_settings_name = "http-settings"
    priority                   = 100
  }
  
  tags = local.common_tags
}

# Monitor de Azure
resource "azurerm_monitor_action_group" "main" {
  name                = "${local.name_prefix}-action-group"
  resource_group_name = azurerm_resource_group.main.name
  short_name          = "novalat"
  
  email_receiver {
    name                    = "admin"
    email_address          = "admin@novalat.com"
    use_common_alert_schema = true
  }
}

# Alertas
resource "azurerm_monitor_metric_alert" "cpu" {
  name                = "${local.name_prefix}-cpu-alert"
  resource_group_name = azurerm_resource_group.main.name
  scopes               = [azurerm_kubernetes_cluster.main.id]
  description          = "Alerta de CPU alta en AKS"
  
  criteria {
    metric_namespace = "Microsoft.ContainerService/managedClusters"
    metric_name      = "cpuUsageNanoCores"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 80
  }
  
  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }
}

# Variables de entorno
resource "azurerm_key_vault_secret" "database_url" {
  name         = "database-url"
  value        = "postgresql://${azurerm_postgresql_server.main.administrator_login}:${random_password.postgres_password.result}@${azurerm_postgresql_server.main.fqdn}:5432/${azurerm_postgresql_database.traceability.name}"
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_key_vault_secret" "redis_url" {
  name         = "redis-url"
  value        = "redis://:${azurerm_redis_cache.main.primary_access_key}@${azurerm_redis_cache.main.hostname}:6380/0"
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_key_vault_secret" "jwt_secret" {
  name         = "jwt-secret"
  value        = random_password.jwt_secret.result
  key_vault_id = azurerm_key_vault.main.id
}

# Passwords aleatorios
resource "random_password" "postgres_password" {
  length  = 16
  special = true
}

resource "random_password" "jwt_secret" {
  length  = 32
  special = true
}

# Data sources
data "azurerm_client_config" "current" {}

# Outputs
output "resource_group_name" {
  description = "Nombre del Resource Group"
  value       = azurerm_resource_group.main.name
}

output "aks_cluster_name" {
  description = "Nombre del cluster AKS"
  value       = azurerm_kubernetes_cluster.main.name
}

output "aks_kube_config" {
  description = "Configuración de kubectl"
  value       = azurerm_kubernetes_cluster.main.kube_config_raw
  sensitive   = true
}

output "postgresql_server_name" {
  description = "Nombre del servidor PostgreSQL"
  value       = azurerm_postgresql_server.main.name
}

output "redis_cache_name" {
  description = "Nombre del Redis Cache"
  value       = azurerm_redis_cache.main.name
}

output "container_registry_name" {
  description = "Nombre del Container Registry"
  value       = azurerm_container_registry.main.name
}

output "key_vault_name" {
  description = "Nombre del Key Vault"
  value       = azurerm_key_vault.main.name
}

output "application_gateway_public_ip" {
  description = "IP pública del Application Gateway"
  value       = azurerm_public_ip.agw.ip_address
} 