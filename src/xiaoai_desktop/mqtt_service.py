from __future__ import annotations

from typing import Callable, Iterable, Optional

import paho.mqtt.client as mqtt

from .models import MqttSettings


class MqttService:
    def __init__(
        self,
        settings: MqttSettings,
        on_message: Callable[[str, str], None],
        on_status: Callable[[str], None],
    ) -> None:
        self.settings = settings
        self.on_message_callback = on_message
        self.on_status = on_status
        self._client: Optional[mqtt.Client] = None

    def connect(self, topics: Iterable[str]) -> None:
        if self._client is not None:
            self.disconnect()
        self._client = mqtt.Client(client_id=self.settings.client_id or "")
        if self.settings.username or self.settings.password:
            self._client.username_pw_set(self.settings.username, self.settings.password)
        self._client.on_connect = lambda client, userdata, flags, rc: self._on_connect(client, rc, topics)
        self._client.on_message = self._handle_message
        self._client.on_disconnect = self._handle_disconnect
        self._client.connect(self.settings.host, int(self.settings.port), 60)
        self._client.loop_start()
        self.on_status("正在连接 MQTT")

    def disconnect(self) -> None:
        if self._client is None:
            return
        self._client.loop_stop()
        self._client.disconnect()
        self._client = None
        self.on_status("MQTT 已断开")

    def _on_connect(self, client: mqtt.Client, rc: int, topics: Iterable[str]) -> None:
        self.on_status(f"MQTT 已连接，状态码 {rc}")
        for topic in topics:
            client.subscribe(topic)

    def _handle_message(self, client: mqtt.Client, userdata: object, msg: mqtt.MQTTMessage) -> None:
        topic = str(msg.topic)
        payload = msg.payload.decode("utf-8")
        self.on_message_callback(topic, payload)

    def _handle_disconnect(self, client: mqtt.Client, userdata: object, rc: int) -> None:
        self.on_status(f"MQTT 已断开，状态码 {rc}")
