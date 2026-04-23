#!/bin/bash
echo "Generando stubs de gRPC para Python..."
python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. meteo.proto
echo "¡Archivos generados correctamente (meteo_pb2.py y meteo_pb2_grpc.py)!"
