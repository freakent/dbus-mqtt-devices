def device_instances(services):
    return dict( map( lambda s : (s, services[s].device_instance), services ))

def build_dbus_payload(portal_id, services):
    # { "portalId": self.portalId, "topicPath": device.topic_paths(self.portalId), "deviceInstance": device.device_instances() } ) )
    
    topic_path = {
        "N": "N/{}/{}/{}",
        "R": "R/{}/{}/{}",
        "W": "W/{}/{}/{}",
    }
    return {
        "portalId": portal_id,
        "deviceInstance": device_instances(services),
        "topicPath": dict( map( lambda s : (s, { 
            "N": topic_path["N"].format(portal_id, services[s].serviceType, services[s].device_instance),
            "R": topic_path["R"].format(portal_id, services[s].serviceType, services[s].device_instance),
            "W": topic_path["W"].format(portal_id, services[s].serviceType, services[s].device_instance)
        }), services ))
    }

