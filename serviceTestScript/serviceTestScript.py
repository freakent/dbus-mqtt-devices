import json
import time
import math
import sys
import yaml
import argparse
import paho.mqtt.client as mqtt
from typing import Dict, Any, List

def load_services(file_path: str) -> Dict[str, Any]:
    """
    Reads and parses the Victron service definitions from a YAML file.

    This function is used to identify which paths (like Ac/Power or Temperature)
    are available for the selected service type.

    Args:
        file_path (str): The relative or absolute path to 'services.yml'.

    Returns:
        Dict[str, Any]: A dictionary where keys are service names and values 
                        are their respective path definitions.
    """
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)

class VictronTester:
    """
    A minimalistic MQTT client implementation of the Victron registration protocol.
    
    This class handles the asynchronous 'handshake' required by the 
    dbus-mqtt-devices driver:
    1. It connects to the VenusOS MQTT broker.
    2. It waits for a system message to learn the local 'Portal ID' (VRM ID).
    3. It publishes a 'Status' message to register the virtual device.
    4. It listens for the 'DBus' response to get an assigned 'Device Instance'.
    """
    
    def __init__(self, broker_ip: str, service_type: str):
        """
        Initializes the tester with connection parameters.
        
        Args:
            broker_ip (str): The IP address or hostname of the VenusOS device.
            service_type (str): The Victron service type to emulate (e.g. 'heatpump').
        """
        self.broker_ip = broker_ip
        self.service_type = service_type
        # We use a test-specific client ID to avoid conflicts with real devices.
        self.client_id = f"{service_type}_test"
        self.portal_id = None
        self.device_instance = None
        
        # Initialize the Paho MQTT Client
        self.client = mqtt.Client(client_id=f"tester_{self.client_id}")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        # Setting a 'Last Will and Testament' (LWT) ensures that if the script
        # crashes, the driver is notified that the device is now 'connected: 0'.
        lw_topic = f"device/{self.client_id}/Status"
        lw_payload = json.dumps({
            "clientId": self.client_id, 
            "connected": 0, 
            "services": {"s1": self.service_type}
        })
        self.client.will_set(lw_topic, lw_payload, qos=1)

    def on_connect(self, client: mqtt.Client, userdata: Any, flags: Dict, rc: int):
        """
        Callback triggered when the MQTT connection is established.
        
        According to the Victron protocol, we must:
        - Subscribe to 'N/+/system/0/Serial' to discover the unique Portal ID.
        - Subscribe to 'device/<clientId>/DBus' to receive our Device Instance.
        """
        if rc == 0:
            print(f"[*] Connected to {self.broker_ip}. Waiting for Portal ID discovery...")
            # We use the 'N/#' namespace (Notification) to find the Portal ID
            self.client.subscribe("N/+/system/0/Serial")
            # This is where the driver sends the assigned Instance ID
            self.client.subscribe(f"device/{self.client_id}/DBus")
        else:
            print(f"[!] MQTT Connection failed with result code: {rc}")
            sys.exit(1)

    def on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage):
        """
        Callback triggered when any subscribed MQTT message arrives.
        
        Logic Flow:
        1. If we see a serial number message, we extract the Portal ID (the 2nd part of the topic).
        2. Once we have the Portal ID, we immediately trigger the 'Status' registration.
        3. Finally, we wait for the driver to send us our assigned 'deviceInstance'.
        """
        try:
            # Topic format for serial: N/<portal_id>/system/0/Serial
            if "/system/0/Serial" in msg.topic:
                self.portal_id = msg.topic.split("/")[1]
                print(f"[*] Portal ID detected: {self.portal_id}")
                # Now that we know who to talk to, we register our device
                self.register()
                
            # Topic format for driver response: device/<clientId>/DBus
            elif msg.topic == f"device/{self.client_id}/DBus":
                data = json.loads(msg.payload)
                # The driver returns a map of labels to instances. We used 's1' as our label.
                self.device_instance = data.get("deviceInstance", {}).get("s1")
                print(f"[*] Assigned Device Instance: {self.device_instance}")
        except Exception as e:
            print(f"[E] Error in message handler: {e}")

    def register(self):
        """
        Publishes the 'Status' message to initiate the device registration.
        
        The payload tells the driver:
        - Our unique clientId
        - That we are currently 'connected' (1)
        - Which 'services' we provide (mapping a local label 's1' to a service type).
        """
        payload = {
            "clientId": self.client_id, 
            "connected": 1, 
            "version": "test-1.0", 
            "services": {"s1": self.service_type}
        }
        topic = f"device/{self.client_id}/Status"
        self.client.publish(topic, json.dumps(payload), qos=1, retain=True)

    def start(self):
        """Starts the MQTT connection and the background network loop."""
        self.client.connect(self.broker_ip, 1883, 60)
        self.client.loop_start()

    def stop(self):
        """Cleanly deregisters the device and disconnects from the broker."""
        # Notifying the driver that the device is now disconnected (connected: 0)
        # removes the device from the VenusOS DBus.
        self.client.publish(f"device/{self.client_id}/Status", 
                            json.dumps({"clientId": self.client_id, "connected": 0, "services": {}}), 
                            qos=1, retain=True)
        self.client.loop_stop()
        self.client.disconnect()

def main():
    """
    Main entry point. Orchestrates CLI arguments, service selection, 
    and the simulation loop.
    """
    desc = """
Victron dbus-mqtt-devices: Service Test Script
==============================================
A transparent tool to verify the correctness of 'services.yml' definitions.

Protocol Workflow:
1. DISCOVERY:  Subscribes to 'N/#' to find the local VRM Portal ID.
2. HANDSHAKE:  Publishes 'device/<clientId>/Status' to register.
3. ASSIGNMENT: Receives 'deviceInstance' from 'device/<clientId>/DBus'.
4. SIMULATION: Publishes values (W/<portalId>/<service>/<instance>/<path>).

Simulation Logic:
- A 0.05 Hz sine wave (20-second period) is used for ALL paths.
- Values oscillate between 0.000 and 1.000.
- This creates a visible, predictable curve in the Victron Remote Console.
    """
    
    parser = argparse.ArgumentParser(
        description=desc,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--ip", required=True, help="IP address of the VenusOS device")
    parser.add_argument("--duration", type=int, default=300, help="Test duration in seconds (default: 300)")
    args = parser.parse_args()
    
    # 1. Load available services from the YAML file
    try:
        services = load_services('services.yml')
    except Exception as e:
        print(f"[E] CRITICAL: services.yml not found or invalid: {e}")
        return

    # Exclude 'vebus' as it requires complex multi-phase handling
    available = sorted([s for s in services.keys() if s != 'vebus'])
    
    # 2. Service Selection Logic
    if len(available) == 1:
        # If there is only one service (e.g. the new 'heatpump'), auto-select it.
        selected = available[0]
        print(f"[*] Auto-selecting single available service: {selected}")
    else:
        # Otherwise, let the user choose from a list.
        print("
--- Available Victron Services ---")
        for i, s in enumerate(available): print(f"[{i:2}] {s}")
        try:
            choice = int(input(f"
Select service index (0-{len(available)-1}): "))
            selected = available[choice]
        except (ValueError, IndexError, KeyboardInterrupt):
            print("
[!] Selection cancelled.")
            return

    # 3. Initialize and start the Handshake
    tester = VictronTester(args.ip, selected)
    tester.start()
    
    # 4. Prepare Paths for Simulation
    # We ignore static configuration keys (metadata) defined in services.yml
    meta_keys = ['ProductId', 'CustomName', 'AllowedRoles', 'Role', 'DeviceType', 'Position', 'Model']
    paths = [p for p in services[selected].keys() if p not in meta_keys]
    
    print(f"[*] Simulating {selected} for {args.duration}s. Update rate: 1s.")
    print(f"[*] Target: {len(paths)} DBus paths.")
    
    # 5. Simulation Loop
    start_time = time.time()
    try:
        while (elapsed := time.time() - start_time) < args.duration:
            # We can only send data once the Portal ID and Device Instance are known
            if tester.portal_id and tester.device_instance is not None:
                # Calculate a smooth sine wave: 0.5 center + 0.5 amplitude = 0 to 1 range
                # Frequency: 0.05 Hz = 1 cycle every 20 seconds.
                val = round(0.5 + 0.5 * math.sin(2 * math.pi * 0.05 * elapsed), 3)
                
                for path in paths:
                    # Construct the Victron 'Write' topic
                    topic = f"W/{tester.portal_id}/{selected}/{tester.device_instance}/{path}"
                    tester.client.publish(topic, json.dumps({"value": val}))
                
                # Visual feedback in the terminal
                print(f"[{int(elapsed):3}s / {args.duration}s] Sending value: {val:0.3f}", end="")
            
            time.sleep(1) # Send data every 1 second
            
    except KeyboardInterrupt:
        print("
[!] Simulation interrupted by user.")
    finally:
        # Ensure the virtual device is removed from the DBus before exiting
        tester.stop()
        print("
[*] Clean shutdown complete. Test finished.")

if __name__ == "__main__":
    main()
