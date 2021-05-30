#include <SPI.h>
#include <Ethernet.h>
#include <Arduino_FreeRTOS.h>
#include <queue.h>
#include <dht.h>

int const DHT11_PIN = 2;

byte const MAC[] = { 0x90, 0xA2, 0xDA, 0x0F, 0x5A, 0x22 };
byte const IP[] = { 192, 168, 0, 111 };
IPAddress const DNS(192, 168, 0, 1);

String DEVICE_ID = "arduino";
byte const GATEWAY[] = { 192, 168, 0, 100 };
int const PORT = 10000;

struct Telemetry {
    float temperature;
    float humidity;
};

class DeviceGateway {
    public:
        DeviceGateway(String deviceId) {
            _deviceId = deviceId;
        };

        inline bool connect(const byte *host, uint16_t port) { return _client.connect(host, port); };
        inline bool connected() { return _client.connected(); };
        inline void attach() { return attach(_client); };
        inline void detach() { return detach(_client); };
        inline void publish(Telemetry &record) { return publish(record, _client); };

        void attach(Stream &stream) {
            stream.print("att ");
            stream.println(_deviceId);
        };

        void detach(Stream &stream) {
            stream.print("det ");
            stream.println(_deviceId);
        };

        void publish(Telemetry &record, Stream &stream) {
            stream.print("pub ");
            stream.print(record.temperature);
            stream.print(" ");
            stream.print(record.humidity);
            stream.println();
        };

    private:
        String _deviceId;
        EthernetClient _client;

};

dht DHT;
QueueHandle_t queue;
DeviceGateway gateway = DeviceGateway(DEVICE_ID);

void setup() {
    Serial.begin(9600);
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
    if (gateway.connect(GATEWAY, PORT)) {
        Serial.println("connected");
        gateway.detach();
        gateway.attach();
    } else {
        Serial.println("connection failed");
    }

    Telemetry record;
    for (;;) {
        if (xQueueReceive(queue, &record, portMAX_DELAY) == pdPASS) {
            gateway.publish(record, Serial);
            if (gateway.connected()) {
                gateway.publish(record);
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
