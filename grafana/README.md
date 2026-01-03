# Grafana Dashboard for Edge Detection Metrics

This directory contains a pre-configured Grafana dashboard for monitoring edge detection performance metrics.

## Dashboard: detection-dashboard.json

### Panels

1. **Detection Latency** - Shows average, p50, p95, and p99 latency percentiles
2. **Current FPS** - Real-time FPS gauge with threshold indicators
3. **FPS Over Time** - FPS trend graph
4. **Memory Usage** - Application memory consumption over time
5. **Error Rate** - Detection error rate per second
6. **GPU Utilization (%)** - GPU utilization percentage (if GPU available)
7. **GPU Memory Usage** - GPU memory consumption (if GPU available)
8. **Detection Rate** - Detections per second
9. **Total Detections** - Cumulative detection counter
10. **Total Errors** - Cumulative error counter

### Configuration

- **Refresh Interval**: 10 seconds
- **Time Range**: Last 1 hour (default)
- **Datasource**: Prometheus (must be configured in Grafana)

### Importing the Dashboard

1. Open Grafana web interface
2. Navigate to Dashboards -> Import
3. Upload `detection-dashboard.json` or paste its contents
4. Select your Prometheus datasource
5. Click Import

### Prometheus Configuration

Add this to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'edge-detection'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 10s
```

### Metrics

The dashboard expects the following metrics to be exposed by the edge detection application:

- `detection_latency_ms` (Histogram) - Detection inference latency
- `detection_fps` (Gauge) - Current frames per second
- `detection_memory_mb` (Gauge) - Memory usage in MB
- `detection_total` (Counter) - Total detections
- `detection_errors_total` (Counter) - Total errors
- `detection_gpu_utilization_percent` (Gauge) - GPU utilization (optional)
- `detection_gpu_memory_used_mb` (Gauge) - GPU memory used (optional)
