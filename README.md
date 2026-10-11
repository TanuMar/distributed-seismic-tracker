# Description - ENGLISH
This project implements a distributed, event-driven system that collects global seismic data from the USGS API, distributes it via MQTT (Mosquitto), and visualizes it in real time using Node-RED. The solution incorporates a decoupled publisher/subscriber architecture, off-chain distributed storage using region-partitioned databases, and an on-chain auditing system based on Ethereum. To ensure the integrity and traceability of the data, each seismic alert generates a SHA-256 cryptographic hash that is recorded in a smart contract developed in Solidity and deployed on Ganache. In this way, the system combines real-time processing efficiency with an immutable audit mechanism backed by blockchain.

# Descripción - ESPAÑOL
Este proyecto implementa un sistema distribuido basado en eventos que recopila información sísmica global desde la API de USGS, la distribuye mediante MQTT (Mosquitto) y la visualiza en tiempo real a través de Node-RED. La solución incorpora una arquitectura desacoplada de tipo Publicador/Suscriptor, almacenamiento distribuido off-chain mediante bases de datos particionadas por región y un sistema de auditoría on-chain basado en Ethereum. Para garantizar la integridad y trazabilidad de la información, cada alerta sísmica genera una huella criptográfica SHA-256 que se registra en un contrato inteligente desarrollado en Solidity y desplegado sobre Ganache. De esta forma, el sistema combina eficiencia en el procesamiento en tiempo real con un mecanismo de auditoría inmutable respaldado por blockchain.

# System Startup - ENGLISH
Only first time:
    - $python3 -m venv venv
    - $source venv/bin/activate
    - $pip install requests paho-mqtt web3
    - $pip install reverse_geocoder pycountry-convert

## Node Red
- Start Eclipse mosquito
- $node-red
- Open node-red (http://127.0.0.1:1880)
- Menu, palette, install (only first time):
  - node-red
  - node-red-dashboard
  - node-red-contrib-web-worldmap
  - node-red-node-ui-table
- Import the file flow_nodered.json
- Instanciate dashboard

## Blockchain Consumer
- $docker run -d -p 8545:8545 trufflesuite/ganache-cli:latest
- Open https://app.remix.live/
- Import on this IDE the file contracts/AlertAudit.sol
- Compile (advanced configuration, EVM version London)
- Deploy (enviroment custom http provider)
- In deploy/deployed contracts, copy the address generated and paste in CONTACT_ADDRESS in blockchain_consumer.py
- $source venv/bin/activate
- $python blockchain_consumer.py
- On the IDE the functions can be called to read the data stored on-chain

## Data Base
- $source venv/bin/activate
- Start consumer by continent $python sqlite_consumer.py x, where x:
    - africa
    - antarctica
    - asia
    - europe
    - noamerica
    - oceania
    - saamerica
    - Empty if all the data will be collected together


# Arranque de sistema - ESPAÑOL
Solo primera vez:
    - $python3 -m venv venv
    - $source venv/bin/activate
    - $pip install requests paho-mqtt web3
    - $pip install reverse_geocoder pycountry-convert

## Node Red
- Arrancar Eclipse mosquito
- $node-red
- Abrir node-red (http://127.0.0.1:1880)
- Menú, administrar paleta, instalar (solo primera vez):
  - node-red
  - node-red-dashboard
  - node-red-contrib-web-worldmap
  - node-red-node-ui-table
- Importar el archivo flow_nodered.json
- Vista, Dashboard, abrir Dashboard e instanciar

## Blockchain Consumer
- $docker run -d -p 8545:8545 trufflesuite/ganache-cli:latest
- Abrir https://app.remix.live/
- Importar en este IDE el archivo contracts/AlertAudit.sol
- Compilar (advanced configuration, EVM version London)
- Deploy (elegir en enviroment custom http provider)
- En deploy/deployed contracts, copiar el address que genera y pegarlo en CONTACT_ADDRESS de blockchain_consumer.py
- $source venv/bin/activate
- $python blockchain_consumer.py
- En el IDE se puede llamar a las funciones

## Base de datos
- $source venv/bin/activate
- Arrancar consumer por continente $python sqlite_consumer.py x, donde x
    - africa
    - antarctica
    - asia
    - europe
    - noamerica
    - oceania
    - saamerica
    - Vacio si se quieren recoger todos los datos juntos

## Productor
- $source venv/bin/activate
- $python producer.py
