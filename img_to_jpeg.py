#!/usr/bin/env python3
"""
Conversion d'images → JPEG optimisé pour e-commerce
Supporte: HEIC, PNG, WEBP, TIFF, BMP, GIF, AVIF, etc.
Usage: python heic_to_jpeg.py <dossier_source> [options]
"""

import argparse
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from PIL import Image
    import pillow_heif
except ImportError:
    print("Installation des dépendances...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", 
                          "Pillow", "pillow-heif", "--break-system-packages", "-q"])
    from PIL import Image
    import pillow_heif

# Enregistrer le support HEIF/AVIF dans Pillow
pillow_heif.register_heif_opener()
pillow_heif.register_avif_opener()

# Formats supportés (Pillow + pillow_heif)
SUPPORTED_EXTENSIONS = {
    '.heic', '.heif',       # Apple
    '.avif',                # AV1 Image
    '.png',                 # PNG
    '.webp',                # WebP
    '.tiff', '.tif',        # TIFF
    '.bmp',                 # Bitmap
    '.gif',                 # GIF (première frame)
    '.jpg', '.jpeg',        # JPEG (réoptimisation)
    '.jp2', '.j2k',         # JPEG 2000
    '.ico',                 # Icon
    '.ppm', '.pgm', '.pbm', # Netpbm
    '.dds',                 # DirectDraw Surface
    '.pcx',                 # PCX
    '.tga',                 # Targa
}


def convert_image(input_path: Path, output_dir: Path, quality: int, 
                  max_width: int | None, max_height: int | None) -> tuple[bool, str, int]:
    """
    Convertit une image en JPEG optimisé.
    Retourne (succès, message, taille_finale_kb)
    """
    try:
        output_path = output_dir / f"{input_path.stem}.jpg"
        
        # Skip si c'est déjà un JPEG et qu'on écrirait au même endroit
        if input_path.suffix.lower() in {'.jpg', '.jpeg'} and output_path == input_path:
            return False, f"⊘ {input_path.name}: skip (même fichier)", 0
        
        with Image.open(input_path) as img:
            # Convertir en RGB (HEIC peut être en RGBA)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Redimensionner si nécessaire
            original_size = img.size
            if max_width or max_height:
                img.thumbnail((max_width or 9999, max_height or 9999), Image.LANCZOS)
            
            # Sauvegarder en JPEG optimisé
            img.save(
                output_path,
                'JPEG',
                quality=quality,
                optimize=True,
                progressive=True  # Chargement progressif = mieux pour le web
            )
        
        original_kb = input_path.stat().st_size / 1024
        final_kb = output_path.stat().st_size / 1024
        reduction = ((original_kb - final_kb) / original_kb) * 100
        src_format = input_path.suffix.upper().replace('.', '')
        
        msg = f"✓ {input_path.name} ({src_format}) → {output_path.name} | {original_size[0]}x{original_size[1]} → {img.size[0]}x{img.size[1]} | {original_kb:.0f}KB → {final_kb:.0f}KB (-{reduction:.0f}%)"
        return True, msg, int(final_kb)
        
    except Exception as e:
        return False, f"✗ {input_path.name}: {e}", 0


def main():
    parser = argparse.ArgumentParser(
        description="Convertit les images en JPEG optimisés pour e-commerce",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Formats supportés: HEIC, AVIF, PNG, WEBP, TIFF, BMP, GIF, JPEG, JP2, etc.

Exemples:
  python heic_to_jpeg.py ./photos
  python heic_to_jpeg.py ./photos -q 75 -w 1200
  python heic_to_jpeg.py ./photos --output ./optimized --quality 80
        """
    )
    parser.add_argument("source", type=Path, help="Dossier contenant les fichiers HEIC")
    parser.add_argument("-o", "--output", type=Path, help="Dossier de sortie (défaut: source/optimized)")
    parser.add_argument("-q", "--quality", type=int, default=82, 
                        help="Qualité JPEG 1-100 (défaut: 82, bon compromis qualité/poids)")
    parser.add_argument("-w", "--max-width", type=int, default=1600,
                        help="Largeur max en pixels (défaut: 1600, 0=pas de limite)")
    parser.add_argument("-H", "--max-height", type=int, default=1600,
                        help="Hauteur max en pixels (défaut: 1600, 0=pas de limite)")
    parser.add_argument("-t", "--threads", type=int, default=4,
                        help="Nombre de threads (défaut: 4)")
    parser.add_argument("-r", "--recursive", action="store_true",
                        help="Chercher dans les sous-dossiers")
    
    args = parser.parse_args()
    
    # Validation
    if not args.source.exists():
        print(f"Erreur: {args.source} n'existe pas")
        sys.exit(1)
    
    # Dossier de sortie
    output_dir = args.output or (args.source / "optimized")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Trouver les fichiers image
    image_files = []
    for ext in SUPPORTED_EXTENSIONS:
        if args.recursive:
            image_files.extend(args.source.glob(f"**/*{ext}"))
            image_files.extend(args.source.glob(f"**/*{ext.upper()}"))
        else:
            image_files.extend(args.source.glob(f"*{ext}"))
            image_files.extend(args.source.glob(f"*{ext.upper()}"))
    
    # Dédupliquer (au cas où)
    image_files = list(set(image_files))
    
    if not image_files:
        print(f"Aucune image trouvée dans {args.source}")
        sys.exit(0)
    
    # Compter par format
    formats = {}
    for f in image_files:
        ext = f.suffix.lower()
        formats[ext] = formats.get(ext, 0) + 1
    format_summary = ", ".join(f"{v} {k}" for k, v in sorted(formats.items(), key=lambda x: -x[1]))
    
    print(f"📁 Source: {args.source}")
    print(f"📂 Sortie: {output_dir}")
    print(f"🖼️  Fichiers trouvés: {len(image_files)} ({format_summary})")
    print(f"⚙️  Qualité: {args.quality} | Max: {args.max_width}x{args.max_height}px")
    print("-" * 60)
    
    # Conversion parallèle
    success_count = 0
    total_size = 0
    max_w = args.max_width if args.max_width > 0 else None
    max_h = args.max_height if args.max_height > 0 else None
    
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = {
            executor.submit(convert_image, f, output_dir, args.quality, max_w, max_h): f 
            for f in image_files
        }
        
        for future in as_completed(futures):
            success, msg, size_kb = future.result()
            print(msg)
            if success:
                success_count += 1
                total_size += size_kb
    
    print("-" * 60)
    print(f"✅ {success_count}/{len(image_files)} fichiers convertis")
    print(f"📦 Taille totale: {total_size/1024:.1f} MB")


if __name__ == "__main__":
    main()
