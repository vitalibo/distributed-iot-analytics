variable "project" {
  type        = string
  description = "(Required) The default project to manage resources in."
}

variable "region" {
  type        = string
  description = "(Required) The Google Cloud region to use."
}

variable "environment" {
  type        = string
  description = "(Required) Environment name"
}

variable "name" {
  type        = string
  description = "(Required) Service name that will be part of resource names."
}

variable "credentials" {
  type        = list(string)
  description = "(Optional) List of public key certificates to authenticate devices."
  default     = []
}

variable "gateway_public_key" {
  type        = string
  description = "(Required) The gateway public key name."
}

variable "devices" {
  type        = set(string)
  description = "(Required) Set of devices."
}

variable "log_level" {
  type        = string
  description = "(Optional) The logging verbosity for device activity."
  default     = "DEBUG"
}

variable "backend_bucket" {
  type        = string
  description = "(Required) The name of the GCS bucket where state snapshots are stored."
  default     = null
}
