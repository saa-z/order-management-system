"""Ouverture du tiroir-caisse via l'imprimante thermique SAGA SGPR-200II.

Le tiroir-caisse est branché à l'imprimante via le port RJ11.
On envoie la commande ESC/POS "kick drawer" en raw via l'API Windows
winspool (ctypes — aucune dépendance externe).
"""
import ctypes
from ctypes import wintypes

PRINTER_NAME = "Saga"

KICK_PIN0 = bytes([0x1B, 0x70, 0x00, 0x19, 0xFA])
KICK_PIN1 = bytes([0x1B, 0x70, 0x01, 0x19, 0xFA])


class _DOCINFO(ctypes.Structure):
    _fields_ = [
        ("pDocName", ctypes.c_char_p),
        ("pOutputFile", ctypes.c_char_p),
        ("pDataType", ctypes.c_char_p),
    ]


_winspool = ctypes.WinDLL("winspool.drv", use_last_error=True)


def send_raw(data: bytes, printer_name: str = PRINTER_NAME) -> tuple[bool, str]:
    """Envoie des bytes raw à l'imprimante Windows via winspool."""
    handle = wintypes.HANDLE()
    name_buf = ctypes.c_char_p(printer_name.encode("utf-8"))

    if not _winspool.OpenPrinterA(name_buf, ctypes.byref(handle), None):
        return False, f"Imprimante « {printer_name} » introuvable."

    try:
        doc = _DOCINFO()
        doc.pDocName = b"RawESCPOS"
        doc.pOutputFile = None
        doc.pDataType = b"RAW"

        if not _winspool.StartDocPrinterA(handle, 1, ctypes.byref(doc)):
            return False, "Impossible de démarrer le document d'impression."

        try:
            _winspool.StartPagePrinter(handle)
            written = wintypes.DWORD()
            buf = ctypes.create_string_buffer(data)
            _winspool.WritePrinter(handle, buf, len(data), ctypes.byref(written))
            _winspool.EndPagePrinter(handle)
        finally:
            _winspool.EndDocPrinter(handle)

        return True, ""

    finally:
        _winspool.ClosePrinter(handle)


def open_cash_drawer(printer_name: str = PRINTER_NAME) -> tuple[bool, str]:
    """Envoie la commande kick à l'imprimante pour ouvrir le tiroir."""
    return send_raw(KICK_PIN0 + KICK_PIN1, printer_name)
