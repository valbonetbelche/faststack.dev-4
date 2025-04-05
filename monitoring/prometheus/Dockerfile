# Stage 1: build config with envsubst
FROM alpine:latest as config-builder
RUN apk add --no-cache gettext && mkdir -p /template
COPY prometheus.yml.template /template/prometheus.yml.template
RUN envsubst < /template/prometheus.yml.template > /template/prometheus.yml

# Stage 2: actual Prometheus image
FROM prom/prometheus:latest
COPY --from=config-builder /template/prometheus.yml /etc/prometheus/prometheus.yml

CMD ["--config.file=/etc/prometheus/prometheus.yml"]