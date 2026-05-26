# 🎬 AMVISIONARY — Luxury Ad Video Generator

Generador automático de anuncio publicitario cinematográfico para **TikTok Ads, Instagram Reels y Meta Ads**.

## Características del Video
- ✅ Formato vertical **9:16** (1080×1920 px)
- ✅ **30 FPS** · duración ~20 segundos
- ✅ Codificado en **H.264** optimizado para redes sociales
- ✅ **13 escenas** con efectos Ken Burns y transiciones flash
- ✅ **Color grading dark luxury** aplicado automáticamente
- ✅ **Viñeta cinematográfica** profesional
- ✅ **Tipografía y branding** AMVISIONARY integrados
- ✅ Copy psicológico de conversión y urgencia

## Instalación rápida

```bash
pip install moviepy Pillow numpy imageio imageio-ffmpeg
```

## Uso

```bash
# 1. Coloca tus 5 fotos en la carpeta images/
mkdir images
cp jeans_grises.jpg     images/img1.jpg
cp jacket_velvet.jpg    images/img2.jpg
cp jeans_moto.jpg       images/img3.jpg
cp hoodie_crema.jpg     images/img4.jpg
cp bomber_camo.jpg      images/img5.jpg

# 2. Genera el video
python3 generate_video.py

# 3. El video queda en:
# output/AMVISIONARY_AD.mp4
```

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `generate_video.py` | Script principal de generación |
| `save_images.py` | Auxiliar para mover imágenes a la carpeta correcta |
| `STORYBOARD.md` | Guión completo, storyboard y dirección creativa |
| `images/` | Carpeta donde van tus fotos (no incluida en repo) |
| `output/` | Video generado (no incluido en repo) |

## Estructura de Escenas

```
[0:00–0:02]  HOOK  → "NO ES ROPA COMÚN."
[0:02–0:06]  Premium details  → "PREMIUM STREETWEAR · IMPORTADO · EXCLUSIVO"
[0:06–0:11]  Urgencia  → "AGENDANDO PEDIDOS · STOCK LIMITADO"
[0:11–0:16]  Actitud  → "NO SIGAS TENDENCIAS. IMPÓNLAS."
[0:16–0:20]  CTA épico  → "DM PARA ORDENAR · LIMITED DROP · PIDE HOY"
```

---
*AMVISIONARY Luxury Streetwear · Campaña "NOT FOR EVERYONE"*
