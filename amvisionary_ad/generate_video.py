#!/usr/bin/env python3
"""
AMVISIONARY – Luxury Streetwear Cinematic Ad Generator
========================================================
Genera un video publicitario cinematográfico de 20 segundos
optimizado para TikTok Ads, Instagram Reels y Meta Ads.

Formato: Vertical 9:16  |  Resolución: 1080x1920  |  30 fps

USO:
    1. Coloca las 5 fotos en la carpeta  images/
       - img1.jpg  →  Jeans grises stacked (close-up frontal)
       - img2.jpg  →  Jacket velvet negro (outfit completo)
       - img3.jpg  →  Jeans moto acid wash (frontal)
       - img4.jpg  →  Hoodie crema con bordado (espalda)
       - img5.jpg  →  Bomber camo abstracto (outfit)
    2. Ejecuta:  python3 generate_video.py
    3. El video se guarda en:  output/AMVISIONARY_AD.mp4
"""

import os
import sys
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
import imageio
import imageio_ffmpeg

# ──────────────────────────────────────────────
#  CONFIGURACIÓN GLOBAL
# ──────────────────────────────────────────────
WIDTH, HEIGHT = 1080, 1920          # 9:16 vertical
FPS = 30
OUTPUT_PATH = "output/AMVISIONARY_AD.mp4"
IMAGES_DIR = "images"

# Paleta de colores luxury
BLACK        = (0, 0, 0)
WHITE        = (255, 255, 255)
GOLD         = (212, 175, 55)
CREAM        = (245, 240, 230)
DARK_GRAY    = (18, 18, 18)
MID_GRAY     = (35, 35, 35)
SILVER       = (192, 192, 192)

# ──────────────────────────────────────────────
#  FUENTES  (usa fallback si no hay TTF externo)
# ──────────────────────────────────────────────
def get_font(size, bold=False):
    """Carga una fuente del sistema o usa la fuente PIL por defecto."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ]
    if not bold:
        candidates = [p.replace("Bold", "").replace("-Bold", "") for p in candidates] + candidates
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

# ──────────────────────────────────────────────
#  UTILIDADES DE IMAGEN
# ──────────────────────────────────────────────
def load_and_fit(path, target_w=WIDTH, target_h=HEIGHT):
    """Carga imagen y la redimensiona para cubrir el frame (cover crop)."""
    img = Image.open(path).convert("RGB")
    iw, ih = img.size
    scale = max(target_w / iw, target_h / ih) * 1.15   # 15 % extra para zoom
    nw = int(iw * scale)
    nh = int(ih * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    # Centro crop
    x = (nw - target_w) // 2
    y = (nh - target_h) // 2
    return img.crop((x, y, x + target_w, y + target_h))


def color_grade_luxury(img: Image.Image) -> Image.Image:
    """Aplica color grading dark luxury premium."""
    arr = np.array(img, dtype=np.float32)

    # Crush shadows ligeramente
    arr = arr * 0.88 + 8

    # Lift rojos/magentas en highlights (tono cine)
    arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.04, 0, 255)   # R  ↑
    arr[:, :, 1] = np.clip(arr[:, :, 1] * 0.97, 0, 255)   # G  ↓
    arr[:, :, 2] = np.clip(arr[:, :, 2] * 1.08, 0, 255)   # B  ↑ (tono frío premium)

    img = Image.fromarray(arr.astype(np.uint8))

    # Reducir saturación para look de moda
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(0.82)

    # Contraste premium
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.18)

    # Nitidez suave
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.25)

    return img


def vignette(img: Image.Image, strength=0.55) -> Image.Image:
    """Agrega viñeta cinematográfica."""
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    # Gradiente radial desde el centro
    cx, cy = w // 2, h // 2
    max_r = math.sqrt(cx**2 + cy**2)
    for r in range(int(max_r), 0, -2):
        alpha = int(255 * strength * (r / max_r) ** 2.2)
        draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            fill=min(alpha, 220),
            outline=None,
        )
    black = Image.new("RGB", (w, h), (0, 0, 0))
    img = img.copy()
    img.paste(black, mask=ImageOps.invert(mask))
    return img


def overlay_dark(img: Image.Image, alpha=0.32) -> Image.Image:
    """Oscurece con overlay negro semitransparente."""
    dark = Image.new("RGB", img.size, (0, 0, 0))
    return Image.blend(img, dark, alpha)


def draw_centered_text(
    draw, y, text, font, color=WHITE, letter_spacing=6, shadow=True
):
    """Dibuja texto centrado con sombra y letter-spacing simulado."""
    # Separar caracteres para letter-spacing manual
    chars = list(text)
    widths = []
    for c in chars:
        bbox = font.getbbox(c)
        widths.append(bbox[2] - bbox[0] + letter_spacing)
    total_w = sum(widths)
    x = (WIDTH - total_w) // 2

    for i, c in enumerate(chars):
        cx = x + sum(widths[:i])
        if shadow:
            draw.text((cx + 3, y + 3), c, font=font, fill=(0, 0, 0, 160))
        draw.text((cx, y), c, font=font, fill=color)


def draw_line(draw, y, color=GOLD, width=2, margin=80):
    draw.line([(margin, y), (WIDTH - margin, y)], fill=color, width=width)


# ──────────────────────────────────────────────
#  EFECTOS DE MOVIMIENTO  (Ken Burns)
# ──────────────────────────────────────────────
def ken_burns_frame(base_img: Image.Image, progress: float, mode="zoom_in") -> Image.Image:
    """
    Genera un frame con efecto Ken Burns.
    progress: 0.0 → 1.0
    modes: zoom_in | zoom_out | pan_left | pan_right | pan_up
    """
    w, h = base_img.size
    # La base ya tiene 15% extra para el movimiento
    extra = 0.12   # cuánto se puede mover

    if mode == "zoom_in":
        scale = 1.0 - extra * progress      # comienza grande, termina 1:1
        off_x, off_y = 0, 0
    elif mode == "zoom_out":
        scale = 1.0 - extra * (1 - progress)
        off_x, off_y = 0, 0
    elif mode == "pan_left":
        scale = 1.0 - extra * 0.5
        off_x = extra * progress
        off_y = 0
    elif mode == "pan_right":
        scale = 1.0 - extra * 0.5
        off_x = -extra * progress
        off_y = 0
    elif mode == "pan_up":
        scale = 1.0 - extra * 0.5
        off_x = 0
        off_y = extra * progress
    else:
        scale, off_x, off_y = 1.0, 0, 0

    # Recortar region visible
    view_w = int(WIDTH * scale)
    view_h = int(HEIGHT * scale)
    start_x = int((w - view_w) * (0.5 + off_x))
    start_y = int((h - view_h) * (0.5 + off_y))
    start_x = max(0, min(start_x, w - view_w))
    start_y = max(0, min(start_y, h - view_h))

    cropped = base_img.crop((start_x, start_y, start_x + view_w, start_y + view_h))
    return cropped.resize((WIDTH, HEIGHT), Image.LANCZOS)


def ease_in_out(t):
    """Curva de ease-in-out suave (sigmoid-like)."""
    return t * t * (3 - 2 * t)


# ──────────────────────────────────────────────
#  COMPOSITOR DE TEXTOS POR ESCENA
# ──────────────────────────────────────────────
def add_scene_text(img: Image.Image, scene: int, alpha: float) -> Image.Image:
    """
    Agrega textos y branding según la escena.
    alpha: 0.0→1.0 para fade in/out del texto.
    """
    img = img.copy().convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    a = int(255 * min(alpha, 1.0))

    if scene == 0:   # HOOK
        # Logo AMVISIONARY arriba
        font_logo = get_font(44, bold=True)
        font_tag  = get_font(26, bold=False)
        font_hook = get_font(88, bold=True)
        font_sub  = get_font(34, bold=False)

        # Línea dorada superior
        draw.line([(60, 120), (WIDTH - 60, 120)], fill=(*GOLD, a), width=1)

        # AMVISIONARY
        draw_centered_text(draw, 132, "AMVISIONARY", font_logo,
                           color=(*WHITE, a), letter_spacing=10)

        # Tag line
        draw_centered_text(draw, 185, "LUXURY STREETWEAR", font_tag,
                           color=(*GOLD, a), letter_spacing=8)

        draw.line([(60, 218), (WIDTH - 60, 218)], fill=(*GOLD, a), width=1)

        # Hook principal – parte baja
        draw_centered_text(draw, HEIGHT - 420, "NO ES", font_hook,
                           color=(*WHITE, a), letter_spacing=4)
        draw_centered_text(draw, HEIGHT - 320, "ROPA", font_hook,
                           color=(*WHITE, a), letter_spacing=4)
        draw_centered_text(draw, HEIGHT - 220, "COMÚN.", font_hook,
                           color=(*GOLD, a), letter_spacing=4)

    elif scene == 1:   # DETALLES PREMIUM
        font_main = get_font(72, bold=True)
        font_sub  = get_font(32, bold=False)
        font_tag  = get_font(24, bold=False)

        draw.line([(60, HEIGHT - 440), (WIDTH - 60, HEIGHT - 440)],
                  fill=(*GOLD, a), width=1)

        draw_centered_text(draw, HEIGHT - 420, "PREMIUM", font_main,
                           color=(*WHITE, a), letter_spacing=8)
        draw_centered_text(draw, HEIGHT - 335, "STREETWEAR", font_main,
                           color=(*GOLD, a), letter_spacing=6)

        draw.line([(60, HEIGHT - 290), (WIDTH - 60, HEIGHT - 290)],
                  fill=(*SILVER, a // 2), width=1)

        draw_centered_text(draw, HEIGHT - 268, "IMPORTADO  ·  EXCLUSIVO  ·  LIMITED", font_tag,
                           color=(*SILVER, a), letter_spacing=4)

        # Mini logo abajo
        font_logo = get_font(30, bold=True)
        draw_centered_text(draw, HEIGHT - 180, "AMVISIONARY", font_logo,
                           color=(*GOLD, a), letter_spacing=10)

    elif scene == 2:   # STOCK LIMITADO
        font_main  = get_font(78, bold=True)
        font_sub   = get_font(36, bold=False)
        font_small = get_font(26, bold=False)

        # Badge "STOCK LIMITADO" arriba centrado
        badge_w, badge_h = 520, 66
        bx = (WIDTH - badge_w) // 2
        draw.rectangle([bx, 110, bx + badge_w, 110 + badge_h],
                       fill=(0, 0, 0, int(a * 0.85)))
        draw.rectangle([bx, 110, bx + badge_w, 110 + badge_h],
                       outline=(*GOLD, a), width=1)
        draw_centered_text(draw, 124, "⬥  STOCK LIMITADO  ⬥", font_sub,
                           color=(*GOLD, a), letter_spacing=4)

        # Texto central-bajo
        draw_centered_text(draw, HEIGHT - 480, "AGENDANDO", font_main,
                           color=(*WHITE, a), letter_spacing=5)
        draw_centered_text(draw, HEIGHT - 388, "PEDIDOS.", font_main,
                           color=(*GOLD, a), letter_spacing=5)

        draw.line([(60, HEIGHT - 330), (WIDTH - 60, HEIGHT - 330)],
                  fill=(*SILVER, a // 2), width=1)

        draw_centered_text(draw, HEIGHT - 308, "PIDE ANTES DE QUE SE AGOTE", font_small,
                           color=(*SILVER, a), letter_spacing=3)

    elif scene == 3:   # NO SIGAS TENDENCIAS
        font_main = get_font(84, bold=True)
        font_sub  = get_font(42, bold=True)
        font_tag  = get_font(28, bold=False)

        draw_centered_text(draw, HEIGHT - 530, "NO SIGAS", font_main,
                           color=(*WHITE, a), letter_spacing=4)
        draw_centered_text(draw, HEIGHT - 430, "TENDENCIAS.", font_sub,
                           color=(*SILVER, a), letter_spacing=6)

        # Línea diagonal decorativa
        draw.line([(WIDTH // 2 - 220, HEIGHT - 370),
                   (WIDTH // 2 + 220, HEIGHT - 370)],
                  fill=(*GOLD, a), width=2)

        draw_centered_text(draw, HEIGHT - 345, "IMPÓNLAS.", font_main,
                           color=(*GOLD, a), letter_spacing=4)

        draw.line([(60, HEIGHT - 270), (WIDTH - 60, HEIGHT - 270)],
                  fill=(*GOLD, a // 2), width=1)
        draw_centered_text(draw, HEIGHT - 245, "AMVISIONARY", get_font(32, bold=True),
                           color=(*WHITE, a), letter_spacing=10)

    elif scene == 4:   # FINAL ÉPICO
        font_brand = get_font(96, bold=True)
        font_cta   = get_font(46, bold=True)
        font_sub   = get_font(28, bold=False)
        font_small = get_font(22, bold=False)

        # Overlay oscuro adicional para el final
        dark_rect = Image.new("RGBA", img.size, (0, 0, 0, int(a * 0.5)))
        img = Image.alpha_composite(img, dark_rect)
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Líneas decorativas
        for offset in [-3, 0, 3]:
            draw.line([(60, HEIGHT // 2 - 160 + offset),
                       (WIDTH - 60, HEIGHT // 2 - 160 + offset)],
                      fill=(*GOLD, a // 3), width=1)

        # Nombre de marca gigante
        draw_centered_text(draw, HEIGHT // 2 - 140, "AMV", font_brand,
                           color=(*WHITE, a), letter_spacing=12)
        draw_centered_text(draw, HEIGHT // 2 - 30,  "ISIONARY", font_brand,
                           color=(*GOLD, a), letter_spacing=6)

        for offset in [-3, 0, 3]:
            draw.line([(60, HEIGHT // 2 + 100 + offset),
                       (WIDTH - 60, HEIGHT // 2 + 100 + offset)],
                      fill=(*GOLD, a // 3), width=1)

        # CTA
        draw_centered_text(draw, HEIGHT // 2 + 130, "DM PARA ORDENAR", font_cta,
                           color=(*WHITE, a), letter_spacing=5)

        draw.line([(200, HEIGHT // 2 + 192), (WIDTH - 200, HEIGHT // 2 + 192)],
                  fill=(*GOLD, a), width=1)

        draw_centered_text(draw, HEIGHT // 2 + 210, "LIMITED DROP  ·  PIDE HOY", font_sub,
                           color=(*GOLD, a), letter_spacing=4)

        # Tagline final
        draw_centered_text(draw, HEIGHT - 160, "@AMVISIONARY", font_small,
                           color=(*SILVER, a // 2), letter_spacing=6)

    img = Image.alpha_composite(img, overlay)
    return img.convert("RGB")


# ──────────────────────────────────────────────
#  FLASH DE TRANSICIÓN
# ──────────────────────────────────────────────
def flash_frame(progress: float, style="white") -> np.ndarray:
    """Frame de flash para transiciones. progress 0→1→0."""
    intensity = math.sin(progress * math.pi)   # pico en 0.5
    v = int(255 * intensity * 0.85)
    if style == "white":
        arr = np.full((HEIGHT, WIDTH, 3), v, dtype=np.uint8)
    else:  # black flash
        arr = np.full((HEIGHT, WIDTH, 3), 255 - v, dtype=np.uint8)
    return arr


# ──────────────────────────────────────────────
#  GENERADOR PRINCIPAL
# ──────────────────────────────────────────────
def generate_ad(image_paths: list):
    """
    Genera el video completo y lo guarda en OUTPUT_PATH.
    image_paths: lista de 5 rutas de imagen.
    """
    print("═" * 60)
    print("  AMVISIONARY — Generando Video Publicitario")
    print("  Formato: 1080×1920  |  30 fps  |  ~20 seg")
    print("═" * 60)

    # ── Cargar y pre-procesar imágenes ──
    print("\n[1/4] Cargando y optimizando imágenes...")
    bases = []
    for i, path in enumerate(image_paths):
        print(f"      ↳ Imagen {i+1}: {path}")
        img = load_and_fit(path)
        img = color_grade_luxury(img)
        img = vignette(img)
        bases.append(img)

    # ── Definir escenas ──────────────────────────────────────────
    # Cada escena: (imagen_idx, duración_seg, modo_ken_burns, texto_escena)
    SCENES = [
        # idx  dur   ken_burns      text_scene  dark_overlay
        (0,    2.5,  "zoom_in",     0,          0.25),  # Hook – jeans grises stacked
        (4,    0.4,  "pan_right",   -1,         0.15),  # Flash jacket camo
        (1,    2.8,  "zoom_out",    1,          0.25),  # Detalles – jacket velvet
        (2,    0.4,  "pan_left",    -1,         0.15),  # Flash moto jeans
        (2,    2.5,  "pan_up",      2,          0.28),  # Stock limitado – moto jeans
        (3,    0.4,  "zoom_in",     -1,         0.15),  # Flash hoodie
        (3,    2.8,  "pan_left",    3,          0.30),  # No sigas tendencias – hoodie
        (4,    0.4,  "zoom_out",    -1,         0.15),  # Flash bomber
        (4,    2.5,  "zoom_in",     3,          0.30),  # Tendencias – bomber
        (0,    0.8,  "pan_right",   -1,         0.20),  # Montaje rápido 1
        (1,    0.6,  "zoom_out",    -1,         0.20),  # Montaje rápido 2
        (2,    0.6,  "pan_up",      -1,         0.20),  # Montaje rápido 3
        (0,    4.0,  "zoom_in",     4,          0.55),  # FINAL ÉPICO – dark overlay fuerte
    ]
    total_dur = sum(s[1] for s in SCENES)
    total_frames = int(total_dur * FPS)
    print(f"\n[2/4] Planificando {len(SCENES)} escenas → {total_dur:.1f}s  ({total_frames} frames)")

    # ── Renderizar frames ────────────────────────────────────────
    print("\n[3/4] Renderizando frames cinematográficos...")
    os.makedirs("output", exist_ok=True)
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    writer = imageio.get_writer(
        OUTPUT_PATH,
        fps=FPS,
        codec="libx264",
        quality=9,
        ffmpeg_log_level="quiet",
        macro_block_size=None,
        output_params=["-crf", "18", "-preset", "slow",
                       "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
    )

    frame_count = 0
    FADE_FRAMES = int(0.18 * FPS)   # 5–6 frames de fade entre escenas

    for scene_idx, (img_i, dur, kb_mode, text_scene, dark_ov) in enumerate(SCENES):
        n_frames = int(dur * FPS)
        base = bases[img_i]

        # Overlay más oscuro para ciertos textos
        working = overlay_dark(base, dark_ov) if dark_ov > 0.01 else base

        for f in range(n_frames):
            progress = ease_in_out(f / max(n_frames - 1, 1))

            # Ken Burns
            frame_img = ken_burns_frame(working, progress, kb_mode)

            # Texto (fade in primeros frames, fade out últimos)
            if text_scene >= 0:
                fade_in_frames  = min(FADE_FRAMES * 2, n_frames // 4)
                fade_out_frames = min(FADE_FRAMES * 2, n_frames // 4)
                if f < fade_in_frames:
                    txt_alpha = f / fade_in_frames
                elif f > n_frames - fade_out_frames:
                    txt_alpha = (n_frames - f) / fade_out_frames
                else:
                    txt_alpha = 1.0
                frame_img = add_scene_text(frame_img, text_scene, txt_alpha)

            # Flash de transición saliente (últimos FADE_FRAMES)
            if f >= n_frames - FADE_FRAMES and scene_idx < len(SCENES) - 1:
                ft = (f - (n_frames - FADE_FRAMES)) / FADE_FRAMES
                flash_arr = flash_frame(ft * 0.5, style="white")
                frame_arr = np.array(frame_img, dtype=np.float32)
                frame_arr = frame_arr * (1 - ft * 0.6) + flash_arr * (ft * 0.6)
                frame_img = Image.fromarray(frame_arr.astype(np.uint8))

            writer.append_data(np.array(frame_img))
            frame_count += 1

            if frame_count % 60 == 0:
                pct = frame_count / total_frames * 100
                bar = "█" * int(pct / 4) + "░" * (25 - int(pct / 4))
                print(f"      [{bar}] {pct:.0f}%  ({frame_count}/{total_frames} frames)",
                      end="\r", flush=True)

    writer.close()
    print(f"\n\n[4/4] ✓ Video exportado → {OUTPUT_PATH}")
    print(f"      Frames totales : {frame_count}")
    print(f"      Duración       : {frame_count / FPS:.1f}s")
    print(f"      Resolución     : {WIDTH}×{HEIGHT} px  (9:16)")
    print("═" * 60)
    print("  Listo para subir a TikTok Ads, Instagram Reels y Meta Ads")
    print("═" * 60)


# ──────────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────────
if __name__ == "__main__":
    # Buscar imágenes en la carpeta images/
    supported = (".jpg", ".jpeg", ".png", ".webp")
    found = sorted([
        os.path.join(IMAGES_DIR, f)
        for f in os.listdir(IMAGES_DIR)
        if f.lower().endswith(supported)
    ])

    if len(found) < 2:
        print("ERROR: Coloca al menos 2 imágenes en la carpeta images/")
        print("       Nombre sugerido: img1.jpg, img2.jpg, img3.jpg, img4.jpg, img5.jpg")
        sys.exit(1)

    # Si hay menos de 5, repetir cíclicamente
    while len(found) < 5:
        found += found
    image_paths = found[:5]

    print(f"\nImágenes detectadas: {len(image_paths)}")
    for p in image_paths:
        print(f"  · {p}")
    print()

    generate_ad(image_paths)
