locals {
  name = "${var.environment}-${var.name}"
  tags = {
    environment = var.environment
    name        = var.name
    terraform   = true
  }
}

resource "google_pubsub_topic" "telemetry" {
  name   = "${local.name}-iot-telemetry-topic"
  labels = local.tags
}

resource "google_cloudiot_registry" "registry" {
  name      = "${local.name}-iot-registry"
  region    = var.region
  project   = var.project
  log_level = var.log_level

  event_notification_configs {
    pubsub_topic_name = google_pubsub_topic.telemetry.id
    subfolder_matches = ""
  }

  mqtt_config = {
    mqtt_enabled_state = "MQTT_ENABLED"
  }

  http_config = {
    http_enabled_state = "HTTP_DISABLED"
  }

  dynamic "credentials" {
    for_each = var.credentials

    content {
      public_key_certificate = {
        format      = "X509_CERTIFICATE_PEM"
        certificate = file("certs/${credentials.value}")
      }
    }
  }
}

resource "google_cloudiot_device" "gateway" {
  name      = "${local.name}-rpi4-gateway"
  registry  = google_cloudiot_registry.registry.id
  blocked   = false
  log_level = var.log_level

  credentials {
    public_key {
      format = "RSA_PEM"
      key    = file("certs/${var.gateway_public_key}")
    }
  }

  gateway_config {
    gateway_type        = "GATEWAY"
    gateway_auth_method = "ASSOCIATION_ONLY"
  }
}

resource "google_cloudiot_device" "device" {
  for_each = var.devices

  name      = "${local.name}-${each.value}-device"
  registry  = google_cloudiot_registry.registry.id
  blocked   = false
  log_level = var.log_level

  metadata = {
    region   = var.region
    registry = google_cloudiot_registry.registry.name
    gateway  = google_cloudiot_device.gateway.name
    project  = var.project
  }

  gateway_config {
    gateway_type = "NON_GATEWAY"
  }

  provisioner "local-exec" {
    when    = create
    command = join("", [
      "gcloud iot devices gateways bind",
      "  --device=${self.name}",
      "  --device-region=${self.metadata.region}",
      "  --device-registry=${self.metadata.registry}",
      "  --gateway=${self.metadata.gateway}",
      "  --gateway-region=${self.metadata.region}",
      "  --gateway-registry=${self.metadata.registry}",
      "  --project=${self.metadata.project}"
    ])
  }

  provisioner "local-exec" {
    when    = destroy
    command = join("", [
      "gcloud iot devices gateways unbind",
      "  --device=${self.name}",
      "  --device-region=${self.metadata.region}",
      "  --device-registry=${self.metadata.registry}",
      "  --gateway=${self.metadata.gateway}",
      "  --gateway-region=${self.metadata.region}",
      "  --gateway-registry=${self.metadata.registry}",
      "  --project=${self.metadata.project}"
    ])
  }
}

resource "google_dataflow_job" "word_count_pipeline" {
  region                  = var.region
  project                 = var.project
  name                    = "${local.name}-word-count-pipeline"
  template_gcs_path       = "gs://${var.dataflow_job_bucket}/templates/word_count"
  temp_gcs_location       = "gs://${var.dataflow_job_bucket}/tmp_dir"
  max_workers             = 2
  on_delete               = "cancel"
  machine_type            = var.machine_type
  enable_streaming_engine = false
  additional_experiments  = [
    "use_fastavro"
  ]

  lifecycle {
    ignore_changes = [
      state
    ]
  }
}
