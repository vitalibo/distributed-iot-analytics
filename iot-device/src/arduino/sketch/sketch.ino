#include <SPI.h>
#include <Ethernet.h>
#include <Arduino_FreeRTOS.h>
#include <queue.h>
#include <dht.h>

int const DHT11_PIN = 2;

byte const MAC[] = { 0x90, 0xA2, 0xDA, 0x0F, 0x5A, 0x22 };
byte const IP[] = { 192, 168, 0, 111 };
IPAddress const DNS(192, 168, 0, 1);

byte const GATEWAY[] = { 192, 168, 0, 100 };
int const PORT = 10000;

struct Telemetry {
    float temperature;
    float humidity;
};

dht DHT;
EthernetClient client;
QueueHandle_t queue;

void setup() {
    Serial.begin(9600);
    while (!Serial) {
        continue;
    }

    setupEthernet();

    queue = xQueueCreate(10, sizeof(Telemetry));
    xTaskCreate(TaskTelemetryRead, "Read",  128,  NULL, 1, NULL);
    xTaskCreate(TaskTelemetryPublish, "Publish",  128,  NULL, 2, NULL);
}

void loop() {
}

void TaskTelemetryRead(void *pvParameters) {
    (void) pvParameters;

    Telemetry previous;
    for (;;) {
        DHT.read11(DHT11_PIN);

        if (previous.temperature == DHT.temperature && previous.humidity == DHT.humidity) {
            vTaskDelay(10);
            continue;
        }

        Telemetry record;
        record.temperature = DHT.temperature;
        record.humidity = DHT.humidity;

        xQueueSend(queue, &record, portMAX_DELAY);
        previous = record;

        vTaskDelay(10);
    }
}

void TaskTelemetryPublish(void * pvParameters) {
    (void) pvParameters;

    Serial.println("connecting...");
    if (client.connect(GATEWAY, PORT)) {
        Serial.println("connected");
        client.println();
    } else {
        Serial.println("connection failed");
    }

    Telemetry record;
    for (;;) {
        if (xQueueReceive(queue, &record, portMAX_DELAY) == pdPASS) {
            String line = String(record.temperature) + " " + String(record.humidity);
            Serial.println(line);
            if (client.connected()) {
                client.println(line);
            }
        }
    }
}

void setupEthernet() {
    Serial.println("Initialize Ethernet with DHCP:");
    if (Ethernet.begin(MAC) == 0) {
        if (Ethernet.hardwareStatus() == EthernetNoHardware) {
            Serial.println("Ethernet shield was not found.");
            while (true) {
                delay(1);
            }
        }

        if (Ethernet.linkStatus() == LinkOFF) {
            Serial.println("Ethernet cable is not connected.");
        }

        Serial.print("Assigned static IP");
        Ethernet.begin(MAC, IP, DNS);
    } else {
        Serial.print("DHCP assigned IP ");
        Serial.println(Ethernet.localIP());
    }
}
