# Use official Prometheus image
FROM prom/prometheus:v2.47.0

# Copy config files
COPY prometheus_render.yml /etc/prometheus/
COPY alerts.yml /etc/prometheus/

# Enable environment variable expansion features
CMD ["--config.file=/etc/prometheus/prometheus_render.yml", \
     "--enable-feature=expand-external-labels", \
     "--enable-feature=expand-external-vars"]