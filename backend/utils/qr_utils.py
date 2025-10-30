import qrcode
from fastapi.responses import FileResponse

def generate_qr_code(patient_id: str):
    qr = qrcode.make(f"https://secure-medical-records.com/{patient_id}")
    qr_path = f"qr_codes/{patient_id}.png"
    qr.save(qr_path)
    return FileResponse(qr_path)
