import yaml
import shutil
import os
import time
from os import path
from loguru import logger
from device import Device
import requests
import json
from paho.mqtt import client as mqtt_client
import struct
import random


MQTT_BROKER_ADDRESS=os.getenv("MQTT_BROKER_ADDRESS")
MQTT_BROKER_PORT=int(os.getenv("MQTT_BROKER_PORT",1883))
MQTT_BROKER_USER=os.getenv("MQTT_BROKER_USER")
MQTT_BROKER_PASSWORD=os.getenv("MQTT_BROKER_PASSWORD")
CLIENT_ID=f'zanzito-exporter-{random.randint(0, 1000)}'
TB_SERVER_ADDRESS= os.getenv("TB_SERVER_ADDRESS")
CONFIG_PATH = 'config/devices.yaml'
FIRST_RECONNECT_DELAY = 1
RECONNECT_RATE = 2
MAX_RECONNECT_COUNT = 12
MAX_RECONNECT_DELAY = 60        
DEVICES = []


def send_telemetry(access_token,payload):
    headers = {"Content-Type": "application/json"}
    report_url = f"{TB_SERVER_ADDRESS}/api/v1/{access_token}/telemetry" 
    
    try:
        response = requests.post(report_url, headers=headers, data=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors (non-2xx responses)
    except requests.exceptions.RequestException as e:
        print(f"Failed to send data: {e}")
    except Exception as e:
        print(f"Failed to send data: {e}")

def load_devices():
    try:
        logger.info("Loading devices list")
        if not path.exists(CONFIG_PATH):
            shutil.copy('devices.yaml', CONFIG_PATH)
        with open("config/devices.yaml",'r',encoding='utf-8') as stream:
            try:
                for _device in yaml.safe_load(stream)["devices"]:
                    DEVICES.append(Device(name=_device["name"],topic=_device["topic"],access_token=_device["access_token"]))
            except yaml.YAMLError as exc:
                logger.error(exc)
    except Exception as e:
        logger.error(str(e))

def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc==0:
            client.connected_flag=True #set flag
            logger.info("connected OK Returned code=" + str(rc))
        else:
            if rc==1:
                logger.error("Connection refused – incorrect protocol version")
            if rc==2:
                logger.error("Connection refused – invalid client identifier")
            if rc==3:
                logger.error("Connection refused – server unavailable")
            if rc==4:
                logger.error("Connection refused – bad username or password")
            if rc==5:
                logger.error("Connection refused – not authorised")

    def on_disconnect(client, userdata, rc):
        logger.info("Disconnected with result code: %s", rc)
        reconnect_count, reconnect_delay = 0, FIRST_RECONNECT_DELAY
        while reconnect_count < MAX_RECONNECT_COUNT:
            logger.info("Reconnecting in %d seconds...", reconnect_delay)
            time.sleep(reconnect_delay)

            try:
                client.reconnect()
                logger.info("Reconnected successfully!")
                return
            except Exception as err:
                logger.error("%s. Reconnect failed. Retrying...", err)

            reconnect_delay *= RECONNECT_RATE
            reconnect_delay = min(reconnect_delay, MAX_RECONNECT_DELAY)
            reconnect_count += 1
        logger.info("Reconnect failed after %s attempts. Exiting...", reconnect_count)



    client = mqtt_client.Client(callback_api_version=mqtt_client.CallbackAPIVersion.VERSION1,client_id=CLIENT_ID)
    client.username_pw_set(MQTT_BROKER_USER, MQTT_BROKER_PASSWORD)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.connect(host=MQTT_BROKER_ADDRESS,port=MQTT_BROKER_PORT,keepalive=60)
    return client

def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        try:
            # print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
            _device = [device for device in DEVICES if device.topic == msg.topic]
            if _device:
                matched_device = _device[0]
                send_telemetry(access_token=matched_device.access_token,payload=msg.payload.decode())
        except Exception as e:
            logger.error(str(e))
        

    for device in DEVICES:
        client.subscribe(device.topic)
    # client.subscribe("zanzito/tomersphone/location")
    client.on_message = on_message



if __name__ == '__main__':
    load_devices()
    client = connect_mqtt()

    subscribe(client)
    client.loop_forever()