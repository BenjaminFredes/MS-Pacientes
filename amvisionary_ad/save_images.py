#!/usr/bin/env python3
"""
Script auxiliar: descarga las imágenes del chat y las guarda en images/
para poder ejecutar generate_video.py
"""
import urllib.request, os, sys

os.makedirs("images", exist_ok=True)

# Si las imágenes están disponibles localmente como argumentos
if len(sys.argv) > 1:
    import shutil
    for i, src in enumerate(sys.argv[1:], 1):
        dst = f"images/img{i}.jpg"
        shutil.copy(src, dst)
        print(f"Copiado: {src} → {dst}")
    print(f"\n✓ {len(sys.argv)-1} imágenes guardadas en images/")
    print("  Ahora ejecuta:  python3 generate_video.py")
else:
    print("Uso: python3 save_images.py foto1.jpg foto2.jpg foto3.jpg foto4.jpg foto5.jpg")
    print("\nO copia manualmente tus fotos a la carpeta images/:")
    print("  images/img1.jpg  →  Jeans grises stacked")
    print("  images/img2.jpg  →  Jacket velvet negro")
    print("  images/img3.jpg  →  Jeans moto acid wash")
    print("  images/img4.jpg  →  Hoodie crema con bordado")
    print("  images/img5.jpg  →  Bomber camo abstracto")
