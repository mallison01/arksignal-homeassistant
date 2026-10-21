FROM python:3.12-slim
LABEL org.opencontainers.image.source="https://github.com/ArkSignal/arksignal-homeassistant" org.opencontainers.image.licenses="MIT" org.opencontainers.image.title="ArkSignal Tempest bridge" org.opencontainers.image.description="Sends a Tempest hub's local readings to your ArkSignal upload address"
WORKDIR /app
COPY arksignal_tempest_bridge.py .
USER nobody
CMD ["python3", "-u", "arksignal_tempest_bridge.py"]
