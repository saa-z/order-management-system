"""Ouvrière d'impression du central.

Interroge périodiquement la file `print_jobs` du serveur (jobs créés par les
appareils distants : bons cuisine, reçus, annulations) et imprime via
l'imprimante thermique SAGA en ESC/POS natif.

L'app desktop tourne sur 127.0.0.1 → traitée comme admin (confiance loopback),
donc aucun token requis.
"""
from PySide6.QtCore import QObject, QTimer

from cash_drawer import send_raw
from escpos_tickets import build_kitchen_ticket, build_receipt_ticket, build_cancel_ticket


class PrintWorker(QObject):
    def __init__(self, api_client, interval_ms=4000, parent=None):
        super().__init__(parent)
        self.api = api_client
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.poll)
        self._timer.start(interval_ms)

    def poll(self):
        try:
            jobs = self.api.get_print_jobs()
        except Exception as e:
            print(f"[print] poll échoué : {e}")
            return
        for job in jobs or []:
            try:
                order = self.api.get_order(job["order_id"])
                if order:
                    ticket = self._build(job, order)
                    if ticket:
                        ok, msg = send_raw(ticket)
                        if not ok:
                            print(f"[print] impression échouée (job {job.get('id')}) : {msg}")
            finally:
                self.api.mark_print_done(job["id"])

    def _build(self, job, order):
        t = job.get("job_type")
        if t == "kitchen":
            return build_kitchen_ticket(order, job.get("batch"))
        if t == "receipt":
            return build_receipt_ticket(order)
        if t == "cancel":
            return build_cancel_ticket(order)
        return None
