# Image Optimizer 🖼️🚀

Un script Python performant pour convertir et optimiser des images en masse (ou à l'unité) pour le web et le e-commerce.

Il prend en charge une grande variété de formats d'entrée (HEIC, AVIF, PNG, TIFF, etc.) et permet de générer des fichiers de sortie optimisés (JPEG, WebP, PNG) avec un contrôle précis sur la qualité et la taille maximale.

## ✨ Fonctionnalités

- **Multi-formats en entrée** : Supporte `HEIC`/`HEIF` (Apple), `AVIF`, `PNG`, `WEBP`, `TIFF`, `BMP`, `GIF`, `JPEG`, etc.
- **Conversion sur-mesure** : Exportez vers `JPEG` (progressif), `WebP` (méthode 4, compromis taille/vitesse au top), ou `PNG`.
- **Traitement par lots ou unitaire** : Indiquez un fichier unique ou un dossier complet.
- **Redimensionnement automatique** : Préservez le ratio tout en imposant une largeur/hauteur maximum.
- **Préservation de l'arborescence** : Option pour recréer la structure de vos dossiers sources lors d'un traitement récursif.
- **Extrêmement rapide** : Utilise le multithreading sous le capot pour traiter plusieurs images en parallèle.

## 📦 Installation

Assurez-vous d'avoir Python 3 installé.
Le script installera automatiquement les dépendances bloquantes (`Pillow`, `pillow-heif`) s'il ne les trouve pas, mais vous pouvez le faire manuellement :

```bash
pip install Pillow pillow-heif
```

## 🛠️ Utilisation

La commande globale suit ce format :

```bash
python optimize_images.py <source> [options]
```

### Exemples pratiques

**1. Optimiser un dossier avec les paramètres par défaut**
Convertira toutes les images supportées en JPEG (Qualité 82, Max 1600x1600px).
```bash
python optimize_images.py ./mes_photos
```
*(Les images seront créées dans un dossier `./mes_photos/optimized`)*

**2. Convertir un dossier entier en WebP (Haute qualité)**
```bash
python optimize_images.py ./mes_photos -f webp -q 90
```

**3. Convertir un fichier HEIC unique**
```bash
python optimize_images.py mon_image.heic -o mon_image_optimisee.jpg
```

**4. Optimiser tout un dossier avec de multiples sous-dossiers, et garder la structure**
```bash
python optimize_images.py ./gros_dossier -r -k -w 1200 -H 1200
```
*(L'option `-r` rend la recherche récursive, `-k` ("keep-structure") conserve vos sous-dossiers dans le dossier de sortie)*

## ⚙️ Options disponibles

| Option | Raccourci | Description | Défaut |
| :--- | :--- | :--- | :--- |
| `--output` | `-o` | Dossier ou fichier de destination. | `<source>/optimized` |
| `--format` | `-f` | Format de sortie cible (`jpeg`, `webp`, `png`). | `jpeg` |
| `--quality` | `-q` | Niveau de qualité (1-100) pour JPEG et WebP. | `82` |
| `--max-width` | `-w` | Largeur maximale autorisée en pixels (0 = infini). | `1600` |
| `--max-height`| `-H` | Hauteur maximale autorisée en pixels (0 = infini). | `1600` |
| `--recursive` | `-r` | Recherche les images y compris dans les sous-dossiers. | `False` |
| `--keep-structure`| `-k` | (Si `-r`) Reproduit l'arborescence source côté sortie. | `False` |
| `--threads` | `-t` | Nombre de processus parallèles pour la conversion. | `4` |

---
*Ce script a été créé pour gagner du temps lors de la préparation d'assets visuels.*
