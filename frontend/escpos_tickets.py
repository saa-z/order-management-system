"""Générateurs de tickets ESC/POS pour l'imprimante SAGA SGPR-200II.

Largeur : 42 caractères (Font A, 72mm).
Encodage : WPC1252 (Windows-1252) pour les accents français.
"""

ENCODING = "cp1252"
LINE_W = 42

# ── Commandes ESC/POS ──
INIT = b'\x1B\x40'
CODEPAGE_1252 = b'\x1B\x74\x10'
ALIGN_L = b'\x1B\x61\x00'
ALIGN_C = b'\x1B\x61\x01'
ALIGN_R = b'\x1B\x61\x02'
BOLD_ON = b'\x1B\x45\x01'
BOLD_OFF = b'\x1B\x45\x00'
DOUBLE = b'\x1D\x21\x11'       # double largeur + double hauteur
DOUBLE_H = b'\x1D\x21\x01'     # double hauteur seule
NORMAL = b'\x1D\x21\x00'
DOUBLE_W = b'\x1D\x21\x10'     # double largeur seule
FEED3 = b'\x1B\x64\x03'
FEED6 = b'\x1B\x64\x06'
CUT = b'\x1D\x56\x00'

TYPE_LABELS = {"eat_in": "SUR PLACE", "take_away": "A EMPORTER"}
SEATING_LABELS = {"indoor": "Salle", "outdoor": "Terrasse"}

_BOTTOM_CATEGORIES = {
    "boissons", "alcools", "cocktails", "vins", "bieres",
    "softs", "aperitifs", "digestifs", "desserts",
}


def _enc(text: str) -> bytes:
    return text.encode(ENCODING, errors="replace")


def _line(char="-") -> bytes:
    return _enc(char * LINE_W + "\n")


def _fmt_datetime(dt_str: str) -> str:
    if not dt_str:
        return ""
    return dt_str[:16].replace("T", " ")


def _item_category(it: dict) -> str:
    return (it.get("item") or {}).get("category_name") or ""


def _is_bottom(cat_name: str) -> bool:
    return cat_name.lower().strip() in _BOTTOM_CATEGORIES


def _group_by_category(items: list) -> list[tuple[str, list]]:
    groups: dict[str, list] = {}
    for it in items:
        cat = _item_category(it) or "Autres"
        groups.setdefault(cat, []).append(it)
    top = [(k, v) for k, v in groups.items() if not _is_bottom(k)]
    bottom = [(k, v) for k, v in groups.items() if _is_bottom(k)]
    return top + bottom


def _mods_text(mods: list) -> list[str]:
    if not mods:
        return []
    lines = []
    base = [m for m in mods if m.get("modification_type") == "base_change"]
    add = [m for m in mods if m.get("modification_type") == "add"]
    rem = [m for m in mods if m.get("modification_type") == "remove"]
    for m in base:
        lines.append(f"   BASE {m.get('ingredient_name_snapshot', '')}")
    if add:
        names = ", ".join(m.get("ingredient_name_snapshot", "") for m in add)
        lines.append(f"   SUPP [{names}]")
    if rem:
        names = ", ".join(m.get("ingredient_name_snapshot", "") for m in rem)
        lines.append(f"   SANS [{names}]")
    return lines


def _opts_text(opts: list) -> str:
    if not opts:
        return ""
    return "(" + ", ".join(
        f"{o.get('option_name_snapshot', '')} x{o.get('quantity', 1)}" for o in opts
    ) + ")"


def _price_line(label: str, amount: float) -> bytes:
    """Ligne avec label à gauche et montant à droite."""
    price_str = f"{amount:.2f} EUR"
    spaces = LINE_W - len(label) - len(price_str)
    if spaces < 1:
        spaces = 1
    return _enc(label + " " * spaces + price_str + "\n")


# ══════════════════════════════════════════
# BON DE CUISINE
# ══════════════════════════════════════════

def build_kitchen_ticket(order: dict, batch: int) -> bytes:
    items = [it for it in order.get("items", []) if (it.get("batch") or 1) == (batch or 1)]
    dt = _fmt_datetime(order.get("created_at"))
    oid = order.get("id", "")
    typ = TYPE_LABELS.get(order.get("order_type", ""), "")

    out = INIT + CODEPAGE_1252

    # 3 lignes vides en haut
    out += FEED3

    # En-tête
    out += ALIGN_C + DOUBLE + BOLD_ON
    out += _enc("BON DE CUISINE\n")
    if batch and batch > 1:
        out += _enc(f"Bon {batch}\n")
    out += NORMAL + BOLD_OFF
    out += _line("=")

    # Infos commande (double hauteur)
    out += ALIGN_L + DOUBLE_H + BOLD_ON
    out += _enc(f"#{oid} {typ}\n")
    out += NORMAL + BOLD_OFF
    out += _enc(f"{dt}\n")

    if order.get("order_type") == "eat_in":
        parts = []
        if order.get("table_number"):
            parts.append(f"Table {order['table_number']}")
        if order.get("covers"):
            parts.append(f"{order['covers']} couverts")
        if order.get("seating_location"):
            parts.append(SEATING_LABELS.get(order["seating_location"], ""))
        if parts:
            out += DOUBLE_H + BOLD_ON
            out += _enc(" | ".join(parts) + "\n")
            out += NORMAL + BOLD_OFF
    elif order.get("order_type") == "take_away":
        if order.get("customer_name"):
            out += DOUBLE_H + _enc(f"{order['customer_name']}\n") + NORMAL
        if order.get("pickup_time"):
            out += DOUBLE_H + BOLD_ON + _enc(f"Retrait : {order['pickup_time']}\n") + NORMAL + BOLD_OFF

    if order.get("created_by"):
        out += _enc(f"Serveur : {order['created_by'].get('username', '')}\n")

    out += _line("-")

    # Articles par catégorie (texte agrandi)
    grouped = _group_by_category(items)
    for cat_name, cat_items in grouped:
        total_qty = sum(it.get("quantity", 1) for it in cat_items)
        out += DOUBLE_H + BOLD_ON + _enc(f"{cat_name.upper()} ({total_qty})\n") + NORMAL + BOLD_OFF

        for it in cat_items:
            qty = it.get("quantity", 1)
            name = it.get("item_name_snapshot", "")
            opts = _opts_text(it.get("selected_options") or [])
            line = f" {qty}x {name}"
            if opts:
                line += f" {opts}"
            out += DOUBLE_H + _enc(line + "\n") + NORMAL

            for mod_line in _mods_text(it.get("modifications")):
                out += BOLD_ON + _enc(mod_line + "\n") + BOLD_OFF

            if it.get("comment"):
                out += BOLD_ON + _enc(f"   > {it['comment']}\n") + BOLD_OFF

        out += _enc("\n")

    out += _line("=")
    # 3 lignes vides en bas + coupe
    out += FEED6 + CUT
    return out


# ══════════════════════════════════════════
# TICKET CLIENT (REÇU / FACTURATION)
# ══════════════════════════════════════════

TVA_RATE = 0.055

def _fmt_price(amount: float) -> str:
    """Format prix avec virgule (style français)."""
    return f"{amount:,.2f}".replace(",", " ").replace(".", ",")


def build_receipt_ticket(order: dict) -> bytes:
    dt_raw = order.get("created_at") or ""
    date_str = dt_raw[:10].replace("-", "/") if len(dt_raw) >= 10 else ""
    time_str = dt_raw[11:16] if len(dt_raw) >= 16 else ""
    items = order.get("items", [])
    covers = order.get("covers")
    table = order.get("table_number")
    server = (order.get("created_by") or {}).get("username", "")

    out = INIT + CODEPAGE_1252

    # ── En-tête restaurant ──
    out += ALIGN_C + DOUBLE + BOLD_ON
    out += _enc("SAN GIORGIO\n")
    out += NORMAL + BOLD_OFF
    out += _enc("10 Avenue de la Liberation\n")
    out += _enc("63780 Saint Georges de Mons\n")
    out += _enc("SIRET : 95213378300029\n")
    out += _line("=")

    # ── Date / Table / Serveur ──
    out += ALIGN_L
    left1 = f"Date : {date_str}"
    right1 = f"Heure : {time_str}"
    out += _enc(left1 + " " * (LINE_W - len(left1) - len(right1)) + right1 + "\n")

    left2 = f"Table : {table:02d}" if table else ""
    right2 = f"Serveur : {server}" if server else ""
    if left2 or right2:
        pad = LINE_W - len(left2) - len(right2)
        if pad < 1:
            pad = 1
        out += _enc(left2 + " " * pad + right2 + "\n")

    out += _line("-")

    # ── En-tête colonnes ──
    header = "Qte  Designation"
    header_r = "P.U.  Total"
    out += BOLD_ON
    out += _enc(header + " " * (LINE_W - len(header) - len(header_r)) + header_r + "\n")
    out += BOLD_OFF
    out += _line("-")

    # ── Articles ──
    total_ttc = 0.0
    for it in items:
        name = it.get("item_name_snapshot", "")
        opts = it.get("selected_options") or []
        if opts:
            opts_str = ", ".join(
                f"{o.get('option_name_snapshot', '')} x{o.get('quantity', 1)}" for o in opts
            )
            name += f" ({opts_str})"
        qty = it.get("quantity", 1)
        up = float(it.get("unit_price") or 0)
        supp = sum(1 for m in (it.get("modifications") or [])
                   if m.get("modification_type") == "add")
        line_up = up + supp
        line_total = qty * line_up
        total_ttc += line_total

        qty_str = f"{qty}"
        pu_str = _fmt_price(line_up)
        tot_str = _fmt_price(line_total)
        right_part = f"{pu_str}  {tot_str}"
        # 5 chars for "Qte  " prefix
        max_name = LINE_W - 5 - len(right_part) - 1
        if len(name) > max_name:
            name = name[:max_name - 1] + "."
        left_part = f"{qty_str:<4} {name}"
        pad = LINE_W - len(left_part) - len(right_part)
        if pad < 1:
            pad = 1
        out += _enc(left_part + " " * pad + right_part + "\n")

    out += _line("-")

    # ── Totaux ──
    ht = total_ttc / (1 + TVA_RATE)
    tva = total_ttc - ht

    out += _price_line("Total HT", ht)
    out += _price_line(f"TVA {TVA_RATE*100:.1f}%".replace(".", ","), tva)
    out += BOLD_ON + DOUBLE_H
    total_label = "TOTAL TTC"
    total_val = f"{_fmt_price(total_ttc)} EUR"
    out += _enc(total_label + " " * (LINE_W - len(total_label) - len(total_val)) + total_val + "\n")
    out += NORMAL + BOLD_OFF

    # ── Total par personne ──
    if covers and covers > 0:
        pp = total_ttc / covers
        pp_label = "Total par personne"
        pp_val = f"{_fmt_price(pp)} EUR"
        out += _enc(pp_label + " " * (LINE_W - len(pp_label) - len(pp_val)) + pp_val + "\n")

    out += _line("=")

    # ── Détail TVA ──
    out += BOLD_ON
    tva_hdr = "DETAIL TVA"
    tva_cols = "HT      TVA      TTC"
    out += _enc(tva_hdr + " " * (LINE_W - len(tva_hdr) - len(tva_cols)) + tva_cols + "\n")
    out += BOLD_OFF

    tva_label = f"TVA {TVA_RATE*100:.2f}".replace(".", ",") + " %"
    ht_s = _fmt_price(ht)
    tva_s = _fmt_price(tva)
    ttc_s = _fmt_price(total_ttc)
    tva_vals = f"{ht_s}    {tva_s}   {ttc_s}"
    out += _enc(tva_label + " " * (LINE_W - len(tva_label) - len(tva_vals)) + tva_vals + "\n")

    out += _line("=")

    # ── Message ──
    out += ALIGN_C
    out += _enc("\nMerci et a bientot !\n\n")

    out += FEED3 + CUT
    return out


# ══════════════════════════════════════════
# BON D'ANNULATION
# ══════════════════════════════════════════

def build_cancel_ticket(order: dict) -> bytes:
    oid = order.get("id", "")
    dt = _fmt_datetime(order.get("created_at"))

    out = INIT + CODEPAGE_1252
    out += ALIGN_C + DOUBLE + BOLD_ON
    out += _enc("COMMANDE ANNULEE\n")
    out += NORMAL + BOLD_OFF
    out += _line("=")
    out += _enc(f"#{oid} | {dt}\n\n")
    out += BOLD_ON
    out += _enc("Ne pas preparer /\narreter la preparation.\n")
    out += BOLD_OFF
    out += _line("=")
    out += FEED3 + CUT
    return out
