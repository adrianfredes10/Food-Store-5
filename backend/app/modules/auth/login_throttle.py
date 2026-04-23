"""Cuenta solo logins fallidos por IP (ventana 15 min). Memoria local; no multi-worker."""

from __future__ import annotations

import time
from collections import defaultdict

_VENTANA_SEGUNDOS = 15 * 60
_MAX_FALLOS = 5

_fallos_por_ip: dict[str, list[float]] = defaultdict(list)


def _limpiar(ip: str) -> None:
    ahora = time.monotonic()
    corte = ahora - _VENTANA_SEGUNDOS
    _fallos_por_ip[ip] = [t for t in _fallos_por_ip[ip] if t > corte]


def assert_ip_puede_intentar_login(ip: str) -> None:
    from app.modules.auth.exceptions import DemasiadosIntentosLoginError

    _limpiar(ip)
    if len(_fallos_por_ip[ip]) >= _MAX_FALLOS:
        raise DemasiadosIntentosLoginError()


def registrar_login_fallido(ip: str) -> None:
    _limpiar(ip)
    _fallos_por_ip[ip].append(time.monotonic())


def limpiar_fallos_ip(ip: str) -> None:
    _fallos_por_ip.pop(ip, None)
