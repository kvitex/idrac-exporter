# Dell servers IDRAC metrics exporter for prometheus
Prometheus exporter of Dell servers IDRAC metrics.
Dell Redfish API is used to gather metrics.

### Runnig exporter as a Flask application:

```
export FLASK_APP=idrac-exporter.py
export IDRAC_USER=username
export IDRAC_PASSWORD=password
/usr/bin/env python3 -m flask run --host=0.0.0.0 --port=8080
```

Username and password should be defined in environment variables or in .env file:

### Running exporter in docker:
```
docker run -d -e DEVICE_USER=username -e DEVICE_PASSWORD=password\
  -p 8080:8080 --name idrac-exporter kvitex/idrac-exporter
```

or

```
docker run --env-file .env -p 8080:8080 --name idrac-exporter kvitex/idrac-exporter
```

### Prometheus job example

Static configuration:

```
scrape_configs:
  - job_name: route_stat
    scrape_interval: 5m
    scrape_timeout: 3m
    metrics_path: /metrics
    static_configs:
      - targets:
        - "10.10.10.1"
        - "10.10.10.2:8443"
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_hostname
      - source_labels: [__param_hostname]
        target_label: instance
      - target_label: __address__
        replacement: my_host_address:8080
```

Or you can use file service discovery:

```
scrape_configs:
  - job_name: route_stat
    scrape_interval: 5m
    scrape_timeout: 3m
    metrics_path: /metrics
    file_sd_configs:
      - files:
        - idrac_*.yml
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_hostname
      - source_labels: [__param_hostname]
        target_label: instance
      - target_label: __address__
        replacement: my_host_address:8080
```

idrac_static.yml

```
- labels:
    device: "server-1"
  targets:
    - "10.10.10.1"
- labels:
    device: "server-2"
  targets:
    - "10.10.10.2:8443"
```


