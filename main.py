from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import Response
from rembg import remove
from PIL import Image
import io

app = FastAPI()

CANVAS_W = 1200
CANVAS_H = 1500
PRODUCT_SCALE = 0.88  # producto ocupa 88% del ancho del lienzo


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/process")
async def process_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")

    data = await file.read()

    # Eliminar fondo
    result = remove(data)
    img = Image.open(io.BytesIO(result)).convert("RGBA")

    # Recortar al bounding box exacto de la prenda
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)

    # Calcular tamaño manteniendo proporción para que ocupe PRODUCT_SCALE del ancho
    target_w = int(CANVAS_W * PRODUCT_SCALE)
    ratio = target_w / img.width
    target_h = int(img.height * ratio)

    # Si el alto supera el lienzo, ajustar por alto
    if target_h > int(CANVAS_H * PRODUCT_SCALE):
        target_h = int(CANVAS_H * PRODUCT_SCALE)
        ratio = target_h / img.height
        target_w = int(img.width * ratio)

    img = img.resize((target_w, target_h), Image.LANCZOS)

    # Crear lienzo blanco y pegar la prenda centrada
    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), (255, 255, 255))
    x = (CANVAS_W - target_w) // 2
    y = (CANVAS_H - target_h) // 2
    canvas.paste(img, (x, y), img)

    # Exportar como JPEG
    output = io.BytesIO()
    canvas.save(output, format="JPEG", quality=95)
    output.seek(0)

    return Response(content=output.read(), media_type="image/jpeg")
