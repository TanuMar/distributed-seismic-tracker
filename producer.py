import json
import time
import requests
import paho.mqtt.client as mqtt
import reverse_geocoder as rg
import pycountry_convert as pc
from collections import OrderedDict

# Configuración del Broker MQTT
BROKER = "localhost"
PORT = 1883
CLIENT_ID = "usgs_ingestor"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, CLIENT_ID, clean_session=True)

# Configurar Last Will and Testament (LWT)
client.will_set("estado/ingestor", payload="offline", qos=1, retain=True)

client.connect(BROKER, PORT, 60)
client.loop_start()

# Informar que el ingestor está online
client.publish("estado/ingestor", payload="online", qos=1, retain=True)

# Endpoint USGS (Seismos de la última hora)
USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"

def clasificar_magnitud(mag):
    if mag is None: return "magdesconocida"
    if mag >= 5.0: return "fuerte"
    if mag >= 3.0: return "moderado"
    return "leve"

CONTINENTS_TO_TOPIC = {
    "AF": "africa",
    "AN": "antarctica",
    "AS": "asia",
    "EU": "europe",
    "NA": "noamerica",
    "OC": "oceania",
    "SA": "saamerica"
}

# Event list cache
MAX_EVENTS = 1000
seen_events = OrderedDict()
def is_new_event(eq_id, timestamp):
    key = (eq_id, timestamp)
    if key in seen_events:
        return False
    seen_events[key] = True
    if len(seen_events) > MAX_EVENTS:
        seen_events.popitem(last=False)
    return True

print("[PRODUCTOR] Iniciado. Consultando USGS...")

try:
    while True:
        response = requests.get(USGS_URL)
        if response.status_code == 200:
            data = response.json()
            features = data.get("features", [])

            for eq in features:
                props = eq["properties"]
                geom = eq["geometry"]
                coord = geom["coordinates"]
                lon=coord[0]
                lat=coord[1]
                id = eq["id"]
                timestamp = props.get("updated", 0)

                # Ver si el evento ya se ha leido
                if is_new_event(id,timestamp):
                    # Mirar magnitud
                    mag = props.get("mag", 0.0)
                    lugar = props.get("place", "Desconocido").lower()
                    cat_mag = clasificar_magnitud(mag)

                    # Determinar región para el topic
                    region_search = rg.search([(lat, lon)], mode=1)[0]
                    country_code = region_search["cc"]
                    try:
                        region = CONTINENTS_TO_TOPIC[pc.country_alpha2_to_continent_code(country_code)]
                    except:
                        region = "regiondesconocida"

                    # Definición de la jerarquía de Topics
                    topic = f"terremotos/{region}/{cat_mag}"

                    payload = json.dumps({
                        "id": id,
                        "lugar": props["place"],
                        "magnitud": mag,
                        "tiempo": props["time"],
                        "coordenadas": coord
                    })

                    # Publicar con QoS 2 para asegurar la entrega de eventos importantes
                    qos = 2 if cat_mag == "fuerte" else 1
                    client.publish(topic, payload, qos=qos, retain=True)
                    print(f"[PRODUCTOR] Publicado en '{topic}': {props['place']} (Mag: {mag})")

        time.sleep(30) # Polling cada 30 segundos
except KeyboardInterrupt:
    client.publish("estado/ingestor", payload="offline", qos=1, retain=True)
    client.loop_stop()
    client.disconnect()
