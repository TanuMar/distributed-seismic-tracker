// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title AlertAudit
 * @dev Auditoria inmutable de alertas sismicas
*/
contract AlertAudit {
    
    struct Alerta {
        string idEvento;
        uint256 timestamp;
        uint256 magnitud;    // Representado como entero (ej. 58 para magnitud 5.8)
        string hashContenido; // Hash SHA-256 del JSON original
        address registrador;  // Cuenta Ethereum que firmo la transaccion
        bool existe;          // Bandera para comprobar existencia rapida
    }

    // Almacenamiento en Array y Mapping
    Alerta[] public historialAlertas;
    mapping(string => Alerta) private alertasPorId;

    // Evento emitido para indexacion por Web3.py / Node-RED
    event AlertaRegistrada(
        string indexed idEvento, 
        uint256 timestamp, 
        uint256 magnitud,
        string hashContenido,
        address registrador
    );

    /**
     * @dev Registra una nueva alerta sismica critica on-chain
     */
    function registrarAlerta(
        string memory _id,
        uint256 _timestamp,
        uint256 _magnitud,
        string memory _hash
    ) public {
        require(!alertasPorId[_id].existe, "Error: La alerta con este ID ya esta registrada");
        require(bytes(_id).length > 0, "Error: El ID no puede estar vacio");
        require(bytes(_hash).length > 0, "Error: El hash no puede estar vacio");

        Alerta memory nuevaAlerta = Alerta({
            idEvento: _id,
            timestamp: _timestamp,
            magnitud: _magnitud,
            hashContenido: _hash,
            registrador: msg.sender,
            existe: true
        });

        historialAlertas.push(nuevaAlerta);
        alertasPorId[_id] = nuevaAlerta;

        emit AlertaRegistrada(_id, _timestamp, _magnitud, _hash, msg.sender);
    }

    /**
     * @dev Obtiene los datos de una alerta especifica utilizando su ID de la USGS
     */
    function obtenerAlertaPorId(string memory _id) public view returns (
        string memory idEvento,
        uint256 timestamp,
        uint256 magnitud,
        string memory hashContenido,
        address registrador
    ) {
        require(alertasPorId[_id].existe, "Error: Alerta no encontrada");
        Alerta memory a = alertasPorId[_id];
        return (a.idEvento, a.timestamp, a.magnitud, a.hashContenido, a.registrador);
    }

    /**
     * @dev Comprueba si una alerta existe on-chain
     */
    function existeAlerta(string memory _id) public view returns (bool) {
        return alertasPorId[_id].existe;
    }

    /**
     * @dev Devuelve el numero total de alertas registradas
     */
    function getTotalAlertas() public view returns (uint256) {
        return historialAlertas.length;
    }

    /**
     * @dev Devuelve un lote de alertas recientes para mostrar facilmente en una tabla o dashboard
     */
    function getAlertasPaginadas(uint256 _limite) public view returns (Alerta[] memory) {
        uint256 total = historialAlertas.length;
        if (_limite > total || _limite == 0) {
            _limite = total;
        }

        Alerta[] memory recientes = new Alerta[](_limite);
        for (uint256 i = 0; i < _limite; i++) {
            recientes[i] = historialAlertas[total - 1 - i];
        }

        return recientes;
    }
}