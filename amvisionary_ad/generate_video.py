#!/usr/bin/env python3
"""
AMVISIONARY – Luxury Streetwear Cinematic Ad Generator  v3.0
=============================================================
Genera un video publicitario cinematográfico de ~20 s.
Formato: Vertical 9:16  |  1080×1920  |  30 fps

Contenido real de cada imagen (tras EXIF correction):
  img1.jpg  →  Jeans moto acid wash con paneles de costura
  img2.jpg  →  Jacket velvet negro (outfit completo)
  img3.jpg  →  Bomber camo abstracto
  img4.jpg  →  Jeans grises stacked (close-up impactante)
  img5.jpg  →  Hoodie crema con bordado azteca (espalda)

USO:
    python3 generate_video.py
    → output/AMVISIONARY_AD.mp4
"""

import os, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageOps

# ─────────────────────────────────────────────────────────────
#  CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────
W, H   = 1080, 1920
FPS    = 30
OUTPUT = "output/AMVISIONARY_AD.mp4"
IMGDIR = "images"

WHITE  = (255, 255, 255)
BLACK  = (0,   0,   0  )
GOLD   = (212, 175,  55)
SILVER = (210, 210, 210)

# ─────────────────────────────────────────────────────────────
#  FUENTES
# ─────────────────────────────────────────────────────────────
def fnt(size, bold=True):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    if not bold:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ] + candidates
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

# ─────────────────────────────────────────────────────────────
#  CARGA DE IMÁGENES
# ─────────────────────────────────────────────────────────────
def load_image(path: str) -> Image.Image:
    """
    Carga la imagen aplicando EXIF rotation, recorte inteligente a 9:16
    y un 14% de margen extra para el efecto Ken Burns.
    """
    img = Image.open(path).convert("RGB")
    img = ImageOps.exif_transpose(img)   # ← crítico: corrige rotación EXIF

    iw, ih = img.size
    target = W / H   # 0.5625

    # Recortar al ratio 9:16 centrando en el sujeto
    if iw / ih > target:
        # Más ancho que 9:16 → recortar lados
        new_w = int(ih * target)
        x = (iw - new_w) // 2
        img = img.crop((x, 0, x + new_w, ih))
    elif iw / ih < target * 0.9:
        # Mucho más alto que 9:16 → recortar arriba/abajo (queda centrado)
        new_h = int(iw / target)
        y = (ih - new_h) // 2
        img = img.crop((0, y, iw, y + new_h))

    # Resize al frame final y ampliar 14% para margen de movimiento
    pad = 0.14
    nw  = int(W * (1 + pad))
    nh  = int(H * (1 + pad))
    return img.resize((nw, nh), Image.LANCZOS)


# ─────────────────────────────────────────────────────────────
#  COLOR GRADING  (luxury suave – ropa visible y atractiva)
# ─────────────────────────────────────────────────────────────
def grade(img: Image.Image) -> Image.Image:
    arr = np.array(img, dtype=np.float32)

    # Lift suave de sombras (nunca crushed)
    arr = np.clip(arr * 0.96 + 5, 0, 255)

    # Tinte cine frío discreto (look fashion editado)
    arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.01,  0, 255)   # R  +1 %
    arr[:, :, 1] = np.clip(arr[:, :, 1] * 0.985, 0, 255)   # G  −1.5 %
    arr[:, :, 2] = np.clip(arr[:, :, 2] * 1.03,  0, 255)   # B  +3 %

    img = Image.fromarray(arr.astype(np.uint8))
    img = ImageEnhance.Color(img).enhance(0.90)       # desaturación suave
    img = ImageEnhance.Contrast(img).enhance(1.08)    # contraste mínimo
    img = ImageEnhance.Sharpness(img).enhance(1.15)   # nitidez
    return img


# ─────────────────────────────────────────────────────────────
#  VIÑETA  (solo sutil, no destruye la imagen)
# ─────────────────────────────────────────────────────────────
def vignette(img: Image.Image, strength: float = 0.22) -> Image.Image:
    nw, nh = img.size
    cx, cy = nw / 2, nh / 2
    Y, X   = np.ogrid[:nh, :nw]
    dist   = np.sqrt(((X - cx) / cx) ** 2 + ((Y - cy) / cy) ** 2)
    mask   = np.clip(dist ** 2.2 * strength, 0, 1)
    arr    = np.array(img, dtype=np.float32)
    result = arr * (1 - mask[:, :, np.newaxis])
    return Image.fromarray(np.clip(result, 0, 255).astype(np.uint8))


# ─────────────────────────────────────────────────────────────
#  GRADIENTE INFERIOR  (solo debajo del texto, no toca la prenda)
# ─────────────────────────────────────────────────────────────
def bottom_grad(img: Image.Image,
                strength: float = 0.80,
                start_pct: float = 0.58) -> Image.Image:
    """
    Oscurece SOLO la franja inferior (start_pct % desde arriba hacia abajo).
    La prenda queda completamente visible en el 58% superior.
    """
    nw, nh = img.size
    arr    = np.array(img, dtype=np.float32)
    start  = int(nh * start_pct)

    rows = np.arange(start, nh)
    t    = (rows - start) / max(nh - start, 1)
    alpha = np.clip(t ** 0.75 * strength, 0, strength)   # curva suave

    arr[start:] = arr[start:] * (1 - alpha[:, np.newaxis, np.newaxis])
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


# ─────────────────────────────────────────────────────────────
#  KEN BURNS
# ─────────────────────────────────────────────────────────────
def ease(t: float) -> float:
    return t * t * (3 - 2 * t)


def ken_burns(base: Image.Image, t: float, mode: str) -> Image.Image:
    nw, nh = base.size
    ex = nw - W   # margen disponible en X
    ey = nh - H   # margen disponible en Y

    if   mode == "zoom_in":
        # Comienza más alejado (usando el margen X/Y) y acerca al centro
        ox = ease(1 - t) * ex * 0.6 + ex * 0.2
        oy = ease(1 - t) * ey * 0.6 + ey * 0.2
    elif mode == "zoom_out":
        ox = ease(t) * ex * 0.6 + ex * 0.2
        oy = ease(t) * ey * 0.6 + ey * 0.2
    elif mode == "pan_left":
        ox = ease(t) * ex
        oy = ey * 0.35
    elif mode == "pan_right":
        ox = (1 - ease(t)) * ex
        oy = ey * 0.35
    elif mode == "pan_up":
        ox = ex * 0.5
        oy = ease(t) * ey
    elif mode == "pan_down":
        ox = ex * 0.5
        oy = (1 - ease(t)) * ey
    elif mode == "drift_tl":   # drift diagonal sutil
        ox = (1 - ease(t)) * ex * 0.8
        oy = (1 - ease(t)) * ey * 0.8
    else:
        ox, oy = ex * 0.5, ey * 0.5

    ox = int(max(0, min(ox, ex)))
    oy = int(max(0, min(oy, ey)))
    cropped = base.crop((ox, oy, ox + W, oy + H))
    return cropped if cropped.size == (W, H) else cropped.resize((W, H), Image.LANCZOS)


# ─────────────────────────────────────────────────────────────
#  TEXTO CENTRADO CON PILL DE FONDO
# ─────────────────────────────────────────────────────────────
def text_w(text: str, f) -> int:
    dummy = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    bb = dummy.textbbox((0, 0), text, font=f)
    return bb[2] - bb[0]


def text_h(f) -> int:
    dummy = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    bb = dummy.textbbox((0, 0), "Ag", font=f)
    return bb[3] - bb[1]


def draw_txt(canvas: Image.Image, text: str, y: int,
             f, color=WHITE, bg_alpha=0,
             spacing=6, a: float = 1.0) -> Image.Image:
    """Texto centrado con letter-spacing simulado. bg_alpha > 0 = pill oscuro."""
    canvas = canvas.convert("RGBA")

    chars  = list(text)
    widths = []
    dummy  = ImageDraw.Draw(canvas)
    for c in chars:
        bb = dummy.textbbox((0, 0), c, font=f)
        widths.append(bb[2] - bb[0] + spacing)
    total_w = sum(widths)
    ch      = text_h(f)
    sx      = (W - total_w) // 2

    if bg_alpha > 0 and total_w > 0:
        pill = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        pd   = ImageDraw.Draw(pill)
        pad  = 16
        pd.rounded_rectangle(
            [sx - pad, y - 8, sx + total_w + pad, y + ch + 8],
            radius=10,
            fill=(0, 0, 0, int(bg_alpha * a)),
        )
        canvas = Image.alpha_composite(canvas, pill)

    draw = ImageDraw.Draw(canvas)
    cx = sx
    for c, cw in zip(chars, widths):
        # Sombra
        draw.text((cx + 3, y + 3), c, font=f, fill=(0, 0, 0, int(160 * a)))
        draw.text((cx,     y    ), c, font=f, fill=(*color, int(255 * a)))
        cx += cw

    return canvas


def draw_line(canvas: Image.Image, y: int,
              color=GOLD, margin=80, width=1, a=1.0) -> Image.Image:
    canvas = canvas.convert("RGBA")
    layer  = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.line([(margin, y), (W - margin, y)],
           fill=(*color, int(210 * a)), width=width)
    return Image.alpha_composite(canvas, layer)


def draw_badge(canvas: Image.Image, text: str, cy: int,
               f, a=1.0) -> Image.Image:
    """Badge con borde dorado (ej: STOCK LIMITADO)."""
    canvas  = canvas.convert("RGBA")
    dummy   = ImageDraw.Draw(canvas)
    tw      = text_w(text, f)
    th      = text_h(f)
    pad_x, pad_y = 24, 10
    bw = tw + pad_x * 2
    bh = th + pad_y * 2
    bx = (W - bw) // 2

    pill = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd   = ImageDraw.Draw(pill)
    pd.rounded_rectangle(
        [bx, cy, bx + bw, cy + bh],
        radius=6,
        fill=(0, 0, 0, int(200 * a)),
        outline=(*GOLD, int(230 * a)),
        width=2,
    )
    canvas = Image.alpha_composite(canvas, pill)

    draw   = ImageDraw.Draw(canvas)
    tx     = (W - tw) // 2
    ty     = cy + pad_y
    draw.text((tx + 2, ty + 2), text, font=f, fill=(0, 0, 0, int(150 * a)))
    draw.text((tx,     ty    ), text, font=f, fill=(*GOLD,  int(255 * a)))
    return canvas


# ─────────────────────────────────────────────────────────────
#  TEXTOS POR ESCENA
# ─────────────────────────────────────────────────────────────
def add_text(img: Image.Image, scene: int, a: float) -> Image.Image:
    if a <= 0:
        return img
    a = min(a, 1.0)
    out = img.convert("RGBA")

    # ─── helpers locales ───
    def line(y, color=GOLD, margin=80, w=1):
        nonlocal out
        out = draw_line(out, y, color, margin, w, a)

    def txt(text, y, f, color=WHITE, bg=0, sp=6):
        nonlocal out
        out = draw_txt(out, text, y, f, color, bg, sp, a)

    def badge(text, cy, f):
        nonlocal out
        out = draw_badge(out, text, cy, f, a)

    # ═══════════════════════════════════════════════════════════════
    if scene == 0:
        # ── HOOK: NO ES ROPA COMÚN ──────────────────────────────────
        # Logo top
        f_logo = fnt(44)
        f_sub  = fnt(23, bold=False)
        f_hook = fnt(88)

        line(106, GOLD, 66)
        txt("AMVISIONARY",       114,  f_logo, WHITE,  bg=0, sp=9)
        txt("LUXURY  STREETWEAR", 166, f_sub,  GOLD,   bg=0, sp=7)
        line(200, GOLD, 66)

        # Hook inferior (texto sobre gradiente oscuro)
        by = H - 430
        txt("NO ES",   by,       f_hook, WHITE,  bg=170, sp=4)
        txt("ROPA",    by + 100, f_hook, WHITE,  bg=170, sp=4)
        txt("COMÚN.",  by + 200, f_hook, GOLD,   bg=170, sp=4)

    elif scene == 1:
        # ── PREMIUM STREETWEAR ──────────────────────────────────────
        f_main = fnt(76)
        f_sub  = fnt(28, bold=False)
        f_logo = fnt(30)

        by = H - 400
        line(by - 14, GOLD)
        txt("PREMIUM",    by,       f_main, WHITE,  bg=160, sp=6)
        txt("STREETWEAR", by + 88,  f_main, GOLD,   bg=160, sp=5)
        line(by + 182, SILVER, 120)
        txt("IMPORTADO  ·  EXCLUSIVO  ·  LIMITED", by + 198, f_sub, SILVER, bg=0, sp=4)
        txt("AMVISIONARY",                         by + 244, f_logo, GOLD,  bg=0, sp=9)

    elif scene == 2:
        # ── STOCK LIMITADO ──────────────────────────────────────────
        f_main = fnt(80)
        f_sub  = fnt(27, bold=False)

        badge("⬥  STOCK LIMITADO  ⬥", 106, fnt(32))

        by = H - 430
        line(by - 12, GOLD)
        txt("AGENDANDO", by,      f_main, WHITE, bg=165, sp=5)
        txt("PEDIDOS.",  by + 92, f_main, GOLD,  bg=165, sp=5)
        line(by + 190, SILVER, 120)
        txt("PIDE ANTES DE QUE SE AGOTE", by + 205, f_sub, SILVER, bg=0, sp=3)

    elif scene == 3:
        # ── NO SIGAS TENDENCIAS – IMPÓNLAS ──────────────────────────
        f_main = fnt(82)
        f_sub  = fnt(44)
        f_logo = fnt(32)

        by = H - 500
        txt("NO SIGAS",    by,       f_main, WHITE,  bg=165, sp=4)
        txt("TENDENCIAS.", by + 94,  f_sub,  SILVER, bg=145, sp=5)
        line(by + 152, GOLD, 100)
        txt("IMPÓNLAS.",   by + 165, f_main, GOLD,   bg=165, sp=4)
        line(by + 262, GOLD, 100)
        txt("AMVISIONARY", by + 278, f_logo, WHITE,  bg=0,   sp=9)

    elif scene == 4:
        # ── FINAL ÉPICO ─────────────────────────────────────────────
        f_brand = fnt(100)
        f_cta   = fnt(48)
        f_sub   = fnt(28, bold=False)
        f_tag   = fnt(21, bold=False)

        # El branding va en el TERCIO INFERIOR para que la prenda domine
        by = int(H * 0.60)      # comienza al 60 % de la pantalla

        line(by - 10, GOLD, 50, w=1)
        txt("AMVISIONARY", by + 4,  f_brand, WHITE, bg=0, sp=7)
        line(by + 114, GOLD, 50, w=1)

        txt("DM PARA ORDENAR",       by + 136, f_cta, WHITE, bg=160, sp=5)
        line(by + 202, SILVER, 180)
        txt("LIMITED DROP  ·  PIDE HOY", by + 218, f_sub, GOLD, bg=0, sp=4)
        txt("@AMVISIONARY",           H - 120,  f_tag, SILVER, bg=0, sp=6)

    return out.convert("RGB")


# ─────────────────────────────────────────────────────────────
#  FLASH DE TRANSICIÓN
# ─────────────────────────────────────────────────────────────
def flash_frame(t: float, intensity=0.65) -> np.ndarray:
    v = int(255 * math.sin(t * math.pi) * intensity)
    return np.full((H, W, 3), v, dtype=np.uint8)


# ─────────────────────────────────────────────────────────────
#  GENERADOR PRINCIPAL
# ─────────────────────────────────────────────────────────────
def generate(paths: list):
    print("═" * 62)
    print("  AMVISIONARY — Video Ad Generator  v3.0")
    print("  1080×1920 · 9:16 · 30 fps")
    print("═" * 62)

    # ── Cargar y pre-procesar ──
    print("\n[1/4] Cargando imágenes (EXIF correction ON)...")
    bases = []
    for i, p in enumerate(paths):
        print(f"      [{i+1}] {p}")
        b = load_image(p)
        b = grade(b)
        b = vignette(b, strength=0.22)
        bases.append(b)

    # ─────────────────────────────────────────────────────────
    #  SECUENCIA DE ESCENAS  (con mapeo correcto de imágenes)
    #
    #  Índices tras corrección EXIF:
    #    0 → img1 = Jeans moto acid wash (paneles)
    #    1 → img2 = Jacket velvet negro
    #    2 → img3 = Bomber camo abstracto
    #    3 → img4 = Jeans stacked grises close-up   ← HERO / HOOK / FINAL
    #    4 → img5 = Hoodie crema con bordado        ← pieza estrella
    # ─────────────────────────────────────────────────────────
    #  (img_idx, dur_s, kb_mode, text_scene, usar_gradiente)
    SCENES = [
        # HOOK – jeans stacked grises (close-up súper impactante, llena pantalla)
        (3,  2.6,  "zoom_in",    0,  True ),
        # Flash cut: jacket velvet
        (1,  0.35, "pan_right",  -1, False),
        # Jacket velvet – PREMIUM STREETWEAR (material premium visible)
        (1,  2.9,  "zoom_out",   1,  True ),
        # Flash cut: moto jeans
        (0,  0.35, "pan_left",   -1, False),
        # Moto jeans – STOCK LIMITADO (paneles y costuras premium)
        (0,  2.5,  "pan_up",     2,  True ),
        # Flash cut: hoodie
        (4,  0.35, "zoom_in",    -1, False),
        # Hoodie crema – NO SIGAS TENDENCIAS (bordado impresionante)
        (4,  2.9,  "zoom_out",   3,  True ),
        # Flash cut: bomber
        (2,  0.35, "pan_left",   -1, False),
        # Bomber camo – IMPÓNLAS (look actitud máxima)
        (2,  2.0,  "zoom_in",    3,  True ),
        # Montaje rápido: 4 cortes sin texto (ritmo de música)
        (3,  0.45, "drift_tl",   -1, False),
        (1,  0.45, "zoom_out",   -1, False),
        (4,  0.45, "pan_right",  -1, False),
        (0,  0.45, "pan_up",     -1, False),
        # FINAL ÉPICO – jeans stacked (el más fotogénico / hero image)
        # branding en tercio inferior, prenda domina la pantalla
        (3,  4.0,  "zoom_in",    4,  True ),
    ]

    total_dur    = sum(s[1] for s in SCENES)
    total_frames = int(total_dur * FPS)
    print(f"\n[2/4] {len(SCENES)} escenas · {total_dur:.1f}s · {total_frames} frames")

    # ── Renderizar ──
    print("\n[3/4] Renderizando frames...")
    os.makedirs("output", exist_ok=True)

    import imageio
    writer = imageio.get_writer(
        OUTPUT,
        fps=FPS,
        codec="libx264",
        quality=9,
        ffmpeg_log_level="quiet",
        macro_block_size=None,
        output_params=["-crf", "16", "-preset", "slow",
                       "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
    )

    fc     = 0
    FADE_F = int(0.14 * FPS)

    for si, (img_i, dur, kb, txt_sc, use_grad) in enumerate(SCENES):
        nf   = max(int(dur * FPS), 1)
        base = bases[img_i]

        for f in range(nf):
            t = ease(f / max(nf - 1, 1))

            # Ken Burns
            frame = ken_burns(base, t, kb)

            # Gradiente inferior solo donde hay texto
            if use_grad and txt_sc >= 0:
                frame = bottom_grad(frame, strength=0.82, start_pct=0.56)

            # Texto con fade in/out
            if txt_sc >= 0:
                if f < FADE_F:
                    ta = f / FADE_F
                elif f > nf - FADE_F:
                    ta = (nf - f) / FADE_F
                else:
                    ta = 1.0
                frame = add_text(frame, txt_sc, ta)

            # Flash de salida
            if f >= nf - FADE_F and si < len(SCENES) - 1:
                ft    = (f - (nf - FADE_F)) / FADE_F
                fl    = flash_frame(ft * 0.5, intensity=0.60)
                fa    = np.array(frame, dtype=np.float32)
                blend = fa * (1 - ft * 0.55) + fl * (ft * 0.55)
                frame = Image.fromarray(blend.astype(np.uint8))

            writer.append_data(np.array(frame))
            fc += 1

            if fc % 60 == 0:
                pct = fc / total_frames * 100
                bar = "█" * int(pct / 4) + "░" * (25 - int(pct / 4))
                print(f"      [{bar}] {pct:.0f}%  ({fc}/{total_frames})",
                      end="\r", flush=True)

    writer.close()
    mb = os.path.getsize(OUTPUT) / 1_048_576
    print(f"\n\n[4/4] ✓ Exportado → {OUTPUT}")
    print(f"      Frames   : {fc}")
    print(f"      Duración : {fc / FPS:.1f} s")
    print(f"      Tamaño   : {mb:.1f} MB")
    print(f"      Resolución: {W}×{H} (9:16)")
    print("═" * 62)
    print("  Listo → TikTok Ads · Instagram Reels · Meta Ads")
    print("═" * 62)


# ─────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    exts  = (".jpg", ".jpeg", ".png", ".webp")
    found = sorted([
        os.path.join(IMGDIR, f)
        for f in os.listdir(IMGDIR)
        if f.lower().endswith(exts)
    ])

    if not found:
        print(f"ERROR: No hay imágenes en {IMGDIR}/")
        sys.exit(1)

    while len(found) < 5:
        found += found
    paths = found[:5]

    print(f"\nImágenes ({len(paths)}):")
    for p in paths:
        print(f"  · {p}")
    print()

    generate(paths)
