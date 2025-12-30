import time
import paho.mqtt.client as mqtt

MQTT_HOST = "localhost"       # hoặc IP của Pi4
MQTT_PORT = 1883
TOPIC = "fall_detection/status"

client = mqtt.Client("pi4_publisher")

client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)

client.loop_start()

try:
    while True:
        client.publish(TOPIC, "1", qos=1)
        print("Published 1 (ALERT ON)")
        time.sleep(5)

        client.publish(TOPIC, "0", qos=1)
        print("Published 0 (ALERT OFF)")
        time.sleep(5)

except KeyboardInterrupt:
    print("Stopped by user")
    client.loop_stop()
    client.disconnect()
