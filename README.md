# 🖼️ Reddit Image Scraper

**Téléchargez des images depuis Reddit sans avoir besoin de clés API !**

Ce scraper utilise les flux JSON publics de Reddit, ce qui signifie qu'aucune authentification n'est requise.

## ✨ Fonctionnalités

- ✅ **Aucune API requise** - Utilise les endpoints JSON publics
- ✅ **Téléchargement parallèle** - Rapide et efficace
- ✅ **Filtres avancés** - Par score, dimensions, NSFW
- ✅ **Support multi-sources** - Reddit, Imgur, previews
- ✅ **Évite les doublons** - Ne re-télécharge pas les fichiers existants
- ✅ **Interface CLI et GUI** - Choisissez votre mode préféré
- ✅ **Gestion des erreurs** - Rate limiting, timeouts, etc.

## 📦 Installation

```bash
# Aucune dépendance externe requise !
# Le script utilise uniquement la bibliothèque standard Python.

# Optionnel: Pour l'interface graphique
pip install tk  # Si non inclus avec votre Python
```

## 🚀 Utilisation

### Mode Ligne de Commande (CLI)

```bash
# Usage basique - télécharge 25 images "hot"
python reddit_image_scraper.py wallpapers

# Télécharger 100 images du top all-time
python reddit_image_scraper.py earthporn --sort top --time all --limit 100

# Images récentes avec score minimum
python reddit_image_scraper.py pics --sort new --min-score 500 --limit 50

# Images HD uniquement (1920px minimum)
python reddit_image_scraper.py wallpapers --min-width 1920 --limit 30

# Inclure NSFW
python reddit_image_scraper.py art --nsfw --limit 25
```

### Options CLI

| Option | Description | Défaut |
|--------|-------------|--------|
| `subreddit` | Nom du subreddit (obligatoire) | - |
| `-o, --output` | Dossier de destination | `downloads` |
| `-l, --limit` | Nombre d'images | `25` |
| `-s, --sort` | Tri: hot, new, top, rising | `hot` |
| `-t, --time` | Période: hour, day, week, month, year, all | `week` |
| `--min-score` | Score minimum | `0` |
| `--min-width` | Largeur minimum | `0` |
| `--min-height` | Hauteur minimum | `0` |
| `--nsfw` | Inclure le contenu NSFW | `false` |
| `--no-skip` | Re-télécharger les existants | `false` |
| `-w, --workers` | Téléchargements parallèles | `5` |
| `-q, --quiet` | Mode silencieux | `false` |

### Mode Interface Graphique (GUI)

```bash
python reddit_scraper_gui.py
```

L'interface graphique offre :
- Champ de saisie du subreddit
- Options de tri et filtrage
- Barre de progression
- Log en temps réel
- Bouton pour ouvrir le dossier

## 📁 Structure des fichiers

```
reddit_scraper/
├── reddit_image_scraper.py  # Script principal (CLI)
├── reddit_scraper_gui.py    # Interface graphique
├── README.md
└── downloads/               # Dossier de sortie par défaut
    └── wallpapers/          # Un sous-dossier par subreddit
        ├── abc123_titre.jpg
        └── def456_autre.png
```

## 🔧 Comment ça marche

Le script exploite les endpoints JSON publics de Reddit :

```
https://www.reddit.com/r/{subreddit}/{sort}.json
```

Ces endpoints ne nécessitent pas d'authentification et retournent les données des posts au format JSON.

### Sources d'images supportées

- `i.redd.it` - Images Reddit natives
- `i.imgur.com` - Imgur direct
- `preview.redd.it` - Previews Reddit
- Images avec extensions directes (.jpg, .png, .gif, .webp)
- Reddit Galleries (première image)

## ⚠️ Limitations

- **Rate Limiting** : Reddit peut limiter les requêtes si vous en faites trop. Le script attend automatiquement en cas de limite.
- **100 posts par page** : Reddit limite à 100 résultats par requête, mais le script gère automatiquement la pagination.
- **Pas de vidéos** : Seules les images sont téléchargées, pas les vidéos.
- **Galleries partielles** : Pour les galleries Reddit, seule la première image est téléchargée.

## 📝 Exemples d'utilisation

### Télécharger des fonds d'écran HD

```bash
python reddit_image_scraper.py wallpapers \
    --sort top \
    --time month \
    --min-width 1920 \
    --min-height 1080 \
    --limit 50
```

### Constituer une collection d'art

```bash
python reddit_image_scraper.py art \
    --sort top \
    --time year \
    --min-score 5000 \
    --limit 200
```

### Récupérer les images du jour

```bash
python reddit_image_scraper.py pics \
    --sort top \
    --time day \
    --limit 25
```

## 🐛 Dépannage

### "Rate limited"
Le script attend automatiquement 60 secondes. Vous pouvez aussi réduire `--workers`.

### Images non téléchargées
Certaines images peuvent être inaccessibles (supprimées, privées). Le script continue avec les suivantes.

### Erreurs SSL
Le script désactive la vérification SSL pour éviter les problèmes de certificats. 

## 📜 Licence

MIT License - Utilisez librement ce script.

## ⚡ Conseils

1. **Commencez petit** : Testez avec `--limit 10` avant de lancer de gros téléchargements
2. **Utilisez les filtres** : `--min-score` aide à obtenir du contenu de qualité
3. **Soyez patient** : Respectez les limites de Reddit pour éviter d'être bloqué
4. **Vérifiez les droits** : Les images restent la propriété de leurs auteurs originaux
