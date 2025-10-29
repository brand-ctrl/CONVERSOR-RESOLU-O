import streamlit as st
from PIL import Image
import zipfile, os, io, shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(
    page_title="Conversor de Imagens 1080",
    page_icon="🖼️",
    layout="centered"
)

st.title("🖼️ Conversor de Imagens Automático")
st.write("Converte suas imagens para **1080×1080** ou **1080×1920**, mantendo proporção e fundo colorido centralizado.")

resolucao = st.radio(
    "📏 Escolha a resolução de saída:",
    ("1080x1080", "1080x1920"),
    horizontal=True
)

fundo_hex = st.color_picker(
    "🎨 Escolha a cor de fundo (padrão: #f2f2f2)",
    "#f2f2f2"
)

uploaded_files = st.file_uploader(
    "📂 Envie suas imagens ou um arquivo ZIP com pastas e imagens:",
    type=["zip", "jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True
)

TEMP_DIR = "temp_input"
OUTPUT_DIR = "output_images"
BACKGROUND_COLOR = tuple(int(fundo_hex.strip("#")[i:i+2], 16) for i in (0, 2, 4))
TARGET_SIZE = (1080, 1080) if resolucao == "1080x1080" else (1080, 1920)

def process_image(input_path, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with Image.open(input_path) as img:
        img = img.convert("RGB")
        width, height = img.size
        scale = min(TARGET_SIZE[0] / width, TARGET_SIZE[1] / height)
        new_size = (int(width * scale), int(height * scale))
        img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
        background = Image.new("RGB", TARGET_SIZE, BACKGROUND_COLOR)
        offset = ((TARGET_SIZE[0] - new_size[0]) // 2, (TARGET_SIZE[1] - new_size[1]) // 2)
        background.paste(img_resized, offset)
        background.save(output_path, quality=90, optimize=True)

if uploaded_files:
    st.info("⏳ Processando suas imagens... aguarde.")
    shutil.rmtree(TEMP_DIR, ignore_errors=True)
    shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if len(uploaded_files) == 1 and uploaded_files[0].name.lower().endswith(".zip"):
        with zipfile.ZipFile(uploaded_files[0], 'r') as zip_ref:
            zip_ref.extractall(TEMP_DIR)
        st.write("✅ ZIP extraído com sucesso!")
    else:
        for file in uploaded_files:
            with open(os.path.join(TEMP_DIR, file.name), "wb") as f:
                f.write(file.read())
        st.write("✅ Imagens carregadas diretamente!")

    image_paths = [p for p in Path(TEMP_DIR).rglob("*") if p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]]
    total = len(image_paths)
    if total == 0:
        st.warning("Nenhuma imagem encontrada.")
        st.stop()

    progress = st.progress(0)
    status = st.empty()

    with ThreadPoolExecutor(max_workers=8) as executor:
        for i, path in enumerate(image_paths, 1):
            relative_path = path.relative_to(TEMP_DIR)
            output_path = Path(OUTPUT_DIR) / relative_path
            executor.submit(process_image, path, output_path)
            progress.progress(i / total)
            status.text(f"📸 Processando imagem {i}/{total}...")

    output_zip = io.BytesIO()
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(OUTPUT_DIR):
            for file in files:
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, OUTPUT_DIR)
                zipf.write(filepath, arcname)
    output_zip.seek(0)

    st.success("✅ Todas as imagens foram convertidas com sucesso!")
    st.download_button(
        label="⬇️ Baixar imagens convertidas",
        data=output_zip,
        file_name=f"imagens_{resolucao}.zip",
        mime="application/zip"
    )

    st.balloons()
