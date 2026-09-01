"""QR code generation for consumer verification.

Each QR encodes a deep link to the Streamlit consumer-verify page (port 8501),
so scanning with a phone opens the human-friendly product history — not the
raw JSON API.
"""
from __future__ import annotations

from pathlib import Path

import qrcode

from config import QR_DIR, consumer_verify_url


def generate_qr(batch_id: str, out_dir: Path | str | None = None) -> str:
    out_dir = Path(out_dir) if out_dir else QR_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    url = consumer_verify_url(batch_id)
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1b5e20", back_color="white")
    path = out_dir / f"{batch_id}.png"
    img.save(path)
    return str(path)


if __name__ == "__main__":  # pragma: no cover
    print(generate_qr("RICE-KONASE-2026-0001"))
