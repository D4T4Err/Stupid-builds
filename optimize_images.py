#!/usr/bin/env python3
"""
Conversion et Optimisation d'images multi-usage (E-commerce, Web)
Supporte les entrées: HEIC, PNG, WEBP, TIFF, BMP, GIF, AVIF, JPEG, etc.
Supporte les sorties: JPEG, WEBP, PNG
Usage: python optimize_images.py <source> [options]
"""

import argparse
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from PIL import Image
    import pillow_heif
except ImportError:
    print("Installation des dépendances requises (Pillow, pillow-heif)...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", 
                          "Pillow", "pillow-heif", "--break-system-packages", "-q"])
    from PIL import Image
    import pillow_heif

# Enregistrer le support HEIF/AVIF dans Pillow
pillow_heif.register_heif_opener()
pillow_heif.register_avif_opener()

# Formats supportés en entrée (Pillow + pillow_heif)
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

SUPPORTED_OUTPUTS = ['jpeg', 'webp', 'png']


def process_image(input_path: Path, output_dir: Path, output_format: str, quality: int, 
                  max_width: int | None, max_height: int | None, keep_structure: bool, base_source_dir: Path) -> tuple[bool, str, int]:
    """
    Convertit une image dans le format demandé (WebP, JPEG, PNG).
    Retourne (succès, message, taille_finale_kb)
    """
    try:
        # Gérer l'arborescence (réplication des dossiers source)
        if keep_structure and base_source_dir.is_dir():
            # input_path.relative_to(base_source_dir) donne ex: "dossier/sous_dossier/img.jpg"
            rel_path = input_path.parent.relative_to(base_source_dir)
            final_out_dir = output_dir / rel_path
            final_out_dir.mkdir(parents=True, exist_ok=True)
        else:
            final_out_dir = output_dir

        output_path = final_out_dir / f"{input_path.stem}.{output_format}"
        
        # Skip si on écrase le fichier original sans avoir été demandé explicitement
        if output_path == input_path:
            return False, f"⊘ {input_path.name}: skip (fichier de destination identique à la source)", 0
        
        with Image.open(input_path) as img:
            # Convertir en RGB si on veut du JPEG et que l'image a de l'alpha (RGBA ou P)
            if output_format == 'jpeg' and img.mode in ('RGBA', 'P', 'LA'):
                img = img.convert('RGB')
                
            # Pour WebP/PNG, on peut garder le RGBA (transparence) !
            elif output_format in ('webp', 'png') and img.mode == 'P':
                img = img.convert('RGBA')
            
            # Redimensionner si nécessaire
            original_size = img.size
            if max_width or max_height:
                # thumbnail garde le ratio d'aspect, c'est parfait
                img.thumbnail((max_width or 99999, max_height or 99999), Image.Resampling.LANCZOS)
            
            # Paramètres de sauvegarde selon le format
            save_kwargs = {}
            if output_format == 'jpeg':
                save_kwargs = {'quality': quality, 'optimize': True, 'progressive': True}
            elif output_format == 'webp':
                save_kwargs = {'quality': quality, 'method': 4} # method=4 est un bon compromis vitesse/taille
            elif output_format == 'png':
                save_kwargs = {'optimize': True} # le PNG n'a pas de 'quality'
            
            # Sauvegarder
            img.save(output_path, output_format.upper(), **save_kwargs)
        
        original_kb = input_path.stat().st_size / 1024
        final_kb = output_path.stat().st_size / 1024
        
        # Parfois WebP fait des miracles, parfois non
        reduction = 0
        if original_kb > 0:
            reduction = ((original_kb - final_kb) / original_kb) * 100
            
        sign = "-" if reduction >= 0 else "+"
        
        src_format = input_path.suffix.upper().replace('.', '')
        msg = f"✓ {input_path.name} ({src_format}) → {output_path.name} | {original_size[0]}x{original_size[1]} → {img.size[0]}x{img.size[1]} | {original_kb:.0f}KB → {final_kb:.0f}KB ({sign}{abs(reduction):.0f}%)"
        
        return True, msg, int(final_kb)
        
    except Exception as e:
        return False, f"✗ {input_path.name}: Erreur lors du traitement - {e}", 0


def main():
    parser = argparse.ArgumentParser(
        description="Convertit et optimise un dossier ou un fichier image pour le Web/E-commerce.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python optimize_images.py ./photos                        (Défaut: JPEG 82%, Max 1600px)
  python optimize_images.py ./photos -f webp -q 75          (Conversion en WebP de tous les fichiers du dossier)
  python optimize_images.py img.heic -o result.jpg          (Fichier unique)
  python optimize_images.py ./photos -w 800 -H 800          (Limiter a 800x800px max)
  python optimize_images.py ./photos -r -k                  (Dossiers récursifs et garde la structure de dossier)
        """
    )
    parser.add_argument("source", type=Path, help="Fichier image ou Dossier contenant des images")
    parser.add_argument("-o", "--output", type=Path, help="Dossier ou Fichier de sortie (défaut: dossier source/optimized)")
    parser.add_argument("-f", "--format", choices=SUPPORTED_OUTPUTS, default='jpeg', 
                        help="Format de sortie (défaut: jpeg)")
    parser.add_argument("-q", "--quality", type=int, default=82, 
                        help="Qualité (1-100) pour JPEG et WebP (défaut: 82)")
    parser.add_argument("-w", "--max-width", type=int, default=1600,
                        help="Largeur max en pixels (défaut: 1600, 0=pas de limite)")
    parser.add_argument("-H", "--max-height", type=int, default=1600,
                        help="Hauteur max en pixels (défaut: 1600, 0=pas de limite)")
    parser.add_argument("-t", "--threads", type=int, default=4,
                        help="Nombre de processus parallèles (défaut: 4)")
    parser.add_argument("-r", "--recursive", action="store_true",
                        help="Chercher dans les sous-dossiers (si source est un dossier)")
    parser.add_argument("-k", "--keep-structure", action="store_true",
                        help="Garder l'arborescence des sous-dossiers de sortie (utilisé avec -r)")
    
    args = parser.parse_args()
    
    # Validation Source
    if not args.source.exists():
        print(f"❌ Erreur: La source '{args.source}' n'existe pas.")
        sys.exit(1)
        
    start_time = time.time()
    
    # Mode Fichier Unique
    if args.source.is_file():
        if args.source.suffix.lower() not in SUPPORTED_EXTENSIONS:
            print(f"❌ Erreur: Format d'entrée non supporté pour {args.source.name}.")
            sys.exit(1)
            
        output_dir = args.output.parent if args.output and args.output.suffix else (args.output or args.source.parent)
        if args.output and args.output.suffix:
           final_format = args.output.suffix.lower().replace('.', '')
           if final_format in SUPPORTED_OUTPUTS:
               args.format = final_format
           # On force le nom de sortie s'il est spécifié !
           # Mais c'est plus simple de réutiliser le process, on va tricher un peu
        
        output_dir.mkdir(parents=True, exist_ok=True)
        max_w = args.max_width if args.max_width > 0 else None
        max_h = args.max_height if args.max_height > 0 else None
        
        print("Traitement du fichier unique...")
        success, msg, size = process_image(args.source, output_dir, args.format, args.quality, max_w, max_h, False, args.source.parent)
        print(msg)
        sys.exit(0 if success else 1)
    
    # Mode Dossier
    output_dir = args.output or (args.source / "optimized")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Trouver les fichiers image
    image_files = []
    print("🔍 Recherche des images en cours...")
    
    search_pattern = "**/*" if args.recursive else "*"
    all_files = list(args.source.glob(search_pattern))
    
    for f in all_files:
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
             # Ne pas s'auto-optimiser si on relance dans le même dossier
            if f.parts[-2] == "optimized" if len(f.parts) >= 2 else False:
                continue
            image_files.append(f)
            
    # Dédupliquer formellement a cause du globbing case insensitive windows parfois
    image_files = list(set(image_files))
    
    if not image_files:
        print(f"📭 Aucune image trouvée dans {args.source}")
        sys.exit(0)
    
    # Résumé
    print(f"📁 Source  : {args.source}")
    print(f"📂 Sortie  : {output_dir}")
    print(f"🖼️  Fichiers: {len(image_files)} trouvés")
    print(f"⚙️  Format  : {args.format.upper()} (Qualité {args.quality}) | Limite: {args.max_width}x{args.max_height}px")
    print(f"🚀 Threads : {args.threads}")
    print("-" * 75)
    
    # Lancement du Pool
    success_count = 0
    total_size_kb = 0
    max_w = args.max_width if args.max_width > 0 else None
    max_h = args.max_height if args.max_height > 0 else None
    
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = {
            executor.submit(
                process_image, f, output_dir, args.format, args.quality, 
                max_w, max_h, args.keep_structure, args.source
            ): f for f in image_files
        }
        
        for future in as_completed(futures):
            success, msg, size_kb = future.result()
            print(msg)
            if success:
                success_count += 1
                total_size_kb += size_kb
    
    elapsed = time.time() - start_time
    print("-" * 75)
    print(f"✅ Terminé ! {success_count}/{len(image_files)} fichiers optimisés avec succès en {elapsed:.1f}s.")
    print(f"📦 Taille totale de sortie: {total_size_kb/1024:.2f} MB")

if __name__ == "__main__":
    main()
