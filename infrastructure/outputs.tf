output "iot_registry_name" {
  value       = google_cloudiot_registry.registry.name
  description = "Name of the IoT core registry."
}

output "iot_device_gateway_name" {
  value       = google_cloudiot_device.gateway.name
  description = "Name of the IoT core device gateway."
}

output "iot_device_name" {
  value       = [for device in google_cloudiot_device.device : device.name]
  description = "List of names for IoT core devices."
}

output "telemetry_topic_name" {
  value       = google_pubsub_topic.telemetry.name
  description = "Name of the IoT telemetry PubSub topic."
}

output "dataflow_word_count_pipeline_id" {
  value       = google_dataflow_job.word_count_pipeline.job_id
  description = "The unique ID of word count job."
}
