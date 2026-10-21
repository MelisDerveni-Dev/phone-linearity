"""Build the optional offline phyphox import QR. Build dependency: qrcode>=8,<9.

The viewer has no QR runtime dependency. Payload follows the official offline
format: https://phyphox.org/docs/transferring-experiments/#offline-qr-codes
"""

from io import BytesIO
from pathlib import Path
import struct
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo
import zlib

import qrcode
from qrcode.image.svg import SvgPathFillImage


ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "experiments/observatory-motion.phyphox"
archive = BytesIO()
with ZipFile(archive, "w", compression=ZIP_DEFLATED, compresslevel=9) as bundle:
    entry = ZipInfo(source.name, date_time=(2026, 10, 21, 0, 0, 0))
    entry.compress_type = ZIP_DEFLATED
    bundle.writestr(entry, source.read_bytes())
contents = archive.getvalue()
payload = b"phyphox" + struct.pack(">I", zlib.crc32(contents)) + bytes([0, 1]) + contents
assert payload[:7] == b"phyphox" and len(payload[:13]) == 13
with ZipFile(BytesIO(payload[13:])) as check:
    assert check.read(source.name) == source.read_bytes()
code = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=8, border=4)
code.add_data(payload, optimize=0)
code.make(fit=True)
target = ROOT / "web/motion-setup-qr.svg"
code.make_image(image_factory=SvgPathFillImage).save(target)
print(f"{target}: {len(payload)} bytes; QR version {code.version}; {code.modules_count} modules")
