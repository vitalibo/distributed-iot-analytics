provider "google" {
  project = var.project
  region  = var.region
}

terraform {
  required_version = ">= 0.14.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 3.72.0"
    }
  }

  backend "gcs" {
  }
}
