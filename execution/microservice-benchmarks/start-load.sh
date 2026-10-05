#!/usr/bin/env bash

port_forward=$(kubectl port-forward -n "load-generators-${microservice_benchmark}" svc/locust 8089:8089 >/dev/null 2>&1)
