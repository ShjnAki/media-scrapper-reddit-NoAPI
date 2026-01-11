#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                     Reddit Image Scraper (No API Required)                    ║
║                                                                               ║
║  Télécharge des images depuis Reddit sans nécessiter de clés API.            ║
║  Utilise les flux JSON publics de Reddit.                                     ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Usage:
    python reddit_image_scraper.py <subreddit> [options]
    
Exemples:
    python reddit_image_scraper.py wallpapers --limit 50
    python reddit_image_scraper.py earthporn --sort top --time all --limit 100
    python reddit_image_scraper.py cats --sort hot --limit 25

Auteur: Assistant IA
Version: 1.0.0
"""

import os
import re
import sys
import json
import time
import hashlib
import argparse
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Set
import ssl


# ═══════════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ScraperConfig:
    """Configuration du scraper."""
    subreddit: str
    output_dir: str = "downloads"
    limit: int = 25
    sort: str = "hot"  # hot, new, top, rising
    time_filter: str = "week"  # hour, day, week, month, year, all
    min_width: int = 0
    min_height: int = 0
    min_score: int = 0
    include_nsfw: bool = False
    max_workers: int = 5
    delay: float = 0.5  # Délai entre requêtes pour éviter le rate limiting
    skip_existing: bool = True
    verbose: bool = True


# ═══════════════════════════════════════════════════════════════════════════════
# Classes principales
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class RedditPost:
    """Représente un post Reddit."""
    id: str
    title: str
    author: str
    subreddit: str
    url: str
    permalink: str
    score: int
    created_utc: float
    is_nsfw: bool
    width: int = 0
    height: int = 0
    
    @property
    def filename(self) -> str:
        """Génère un nom de fichier sécurisé."""
        # Nettoyer le titre
        safe_title = re.sub(r'[<>:"/\\|?*]', '', self.title)
        safe_title = safe_title[:80].strip()
        
        # Extension depuis l'URL
        ext = self._get_extension()
        
        return f"{self.id}_{safe_title}{ext}"
    
    def _get_extension(self) -> str:
        """Extrait l'extension du fichier."""
        parsed = urllib.parse.urlparse(self.url)
        path = parsed.path.lower()
        
        for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.mp4']:
            if path.endswith(ext):
                return ext
        
        # Par défaut
        return '.jpg'


class RedditScraper:
    """
    Scraper d'images Reddit sans authentification API.
    
    Utilise les endpoints JSON publics de Reddit:
    - https://www.reddit.com/r/{subreddit}/{sort}.json
    """
    
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    
    # Domaines d'images supportés
    IMAGE_DOMAINS = {
        'i.redd.it',
        'i.imgur.com',
        'imgur.com',
        'preview.redd.it',
        'external-preview.redd.it',
    }
    
    # Extensions d'images
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    
    def __init__(self, config: ScraperConfig):
        self.config = config
        self.downloaded: Set[str] = set()
        self.failed: Set[str] = set()
        self.stats = {
            'found': 0,
            'downloaded': 0,
            'skipped': 0,
            'failed': 0
        }
        
        # Créer le dossier de sortie
        self.output_path = Path(config.output_dir) / config.subreddit
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Charger les fichiers existants si skip_existing
        if config.skip_existing:
            self._load_existing_files()
        
        # Configuration SSL pour éviter les erreurs de certificat
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
    
    def _load_existing_files(self) -> None:
        """Charge la liste des fichiers déjà téléchargés."""
        for file in self.output_path.glob('*'):
            if file.is_file():
                # Extraire l'ID du post depuis le nom de fichier
                post_id = file.stem.split('_')[0]
                self.downloaded.add(post_id)
        
        if self.downloaded and self.config.verbose:
            print(f"📁 {len(self.downloaded)} fichiers existants trouvés")
    
    def _make_request(self, url: str) -> Optional[Dict]:
        """
        Effectue une requête HTTP et retourne le JSON.
        
        Args:
            url: URL à requêter
            
        Returns:
            Données JSON ou None si erreur
        """
        headers = {
            'User-Agent': self.USER_AGENT,
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        try:
            request = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(request, timeout=30, context=self.ssl_context) as response:
                data = response.read().decode('utf-8')
                return json.loads(data)
                
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"⚠️  Rate limited! Attente de 60 secondes...")
                time.sleep(60)
                return self._make_request(url)
            print(f"❌ Erreur HTTP {e.code}: {url}")
        except urllib.error.URLError as e:
            print(f"❌ Erreur URL: {e.reason}")
        except json.JSONDecodeError:
            print(f"❌ Erreur parsing JSON: {url}")
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
        
        return None
    
    def _build_url(self, after: Optional[str] = None) -> str:
        """
        Construit l'URL de requête Reddit.
        
        Args:
            after: Token de pagination
            
        Returns:
            URL formatée
        """
        base = f"https://www.reddit.com/r/{self.config.subreddit}/{self.config.sort}.json"
        
        params = {
            'limit': min(100, self.config.limit),  # Reddit limite à 100 par requête
            'raw_json': 1,
        }
        
        if self.config.sort == 'top':
            params['t'] = self.config.time_filter
        
        if after:
            params['after'] = after
        
        query = urllib.parse.urlencode(params)
        return f"{base}?{query}"
    
    def _is_image_url(self, url: str) -> bool:
        """Vérifie si l'URL pointe vers une image."""
        if not url:
            return False
        
        parsed = urllib.parse.urlparse(url)
        
        # Vérifier le domaine
        if parsed.netloc in self.IMAGE_DOMAINS:
            return True
        
        # Vérifier l'extension
        path_lower = parsed.path.lower()
        return any(path_lower.endswith(ext) for ext in self.IMAGE_EXTENSIONS)
    
    def _extract_image_url(self, post_data: Dict) -> Optional[str]:
        """
        Extrait l'URL de l'image depuis les données du post.
        
        Args:
            post_data: Données du post Reddit
            
        Returns:
            URL de l'image ou None
        """
        url = post_data.get('url', '')
        
        # URL directe vers une image
        if self._is_image_url(url):
            return url
        
        # Reddit gallery
        if post_data.get('is_gallery'):
            media_metadata = post_data.get('media_metadata', {})
            if media_metadata:
                # Prendre la première image
                first_item = list(media_metadata.values())[0]
                if 's' in first_item:
                    return first_item['s'].get('u', '').replace('&amp;', '&')
        
        # Preview Reddit
        preview = post_data.get('preview', {})
        if preview:
            images = preview.get('images', [])
            if images:
                source = images[0].get('source', {})
                preview_url = source.get('url', '').replace('&amp;', '&')
                if preview_url:
                    return preview_url
        
        # Imgur sans extension
        if 'imgur.com' in url and not self._is_image_url(url):
            # Essayer d'ajouter .jpg
            if '/a/' not in url and '/gallery/' not in url:
                return url + '.jpg'
        
        return None
    
    def _parse_post(self, post_data: Dict) -> Optional[RedditPost]:
        """
        Parse les données d'un post Reddit.
        
        Args:
            post_data: Données brutes du post
            
        Returns:
            RedditPost ou None si invalide
        """
        data = post_data.get('data', {})
        
        # Filtrer les posts non-image
        if data.get('is_self', True):
            return None
        
        if data.get('is_video', True):
            return None
        
        # Filtrer NSFW si non inclus
        if data.get('over_18', True) and not self.config.include_nsfw:
            return None
        
        # Extraire l'URL de l'image
        image_url = self._extract_image_url(data)
        if not image_url:
            return None
        
        # Filtrer par score
        score = data.get('score', 0)
        if score < self.config.min_score:
            return None
        
        # Dimensions (si disponibles)
        width = 0
        height = 0
        preview = data.get('preview', {})
        if preview:
            images = preview.get('images', [])
            if images:
                source = images[0].get('source', {})
                width = source.get('width', 0)
                height = source.get('height', 0)
        
        # Filtrer par dimensions
        if width and self.config.min_width and width < self.config.min_width:
            return None
        if height and self.config.min_height and height < self.config.min_height:
            return None
        
        return RedditPost(
            id=data.get('id', ''),
            title=data.get('title', 'Untitled'),
            author=data.get('author', 'unknown'),
            subreddit=data.get('subreddit', self.config.subreddit),
            url=image_url,
            permalink=data.get('permalink', ''),
            score=score,
            created_utc=data.get('created_utc', 0),
            is_nsfw=data.get('over_18', True),
            width=width,
            height=height
        )
    
    def fetch_posts(self) -> List[RedditPost]:
        """
        Récupère les posts du subreddit.
        
        Returns:
            Liste des posts valides
        """
        posts = []
        after = None
        fetched = 0
        
        print(f"\n🔍 Recherche d'images dans r/{self.config.subreddit}...")
        print(f"   Tri: {self.config.sort} | Limite: {self.config.limit}")
        
        while fetched < self.config.limit:
            url = self._build_url(after)
            
            if self.config.verbose:
                print(f"   📡 Requête: page {len(posts) // 100 + 1}...")
            
            data = self._make_request(url)
            
            if not data:
                break
            
            children = data.get('data', {}).get('children', [])
            
            if not children:
                break
            
            for child in children:
                if fetched >= self.config.limit:
                    break
                
                post = self._parse_post(child)
                
                if post:
                    # Vérifier si déjà téléchargé
                    if post.id in self.downloaded:
                        self.stats['skipped'] += 1
                        continue
                    
                    posts.append(post)
                    fetched += 1
            
            # Pagination
            after = data.get('data', {}).get('after')
            if not after:
                break
            
            # Délai anti rate-limit
            time.sleep(self.config.delay)
        
        self.stats['found'] = len(posts)
        print(f"   ✅ {len(posts)} images trouvées")
        
        return posts
    
    def _download_image(self, post: RedditPost) -> bool:
        """
        Télécharge une image.
        
        Args:
            post: Post Reddit contenant l'URL
            
        Returns:
            True si téléchargement réussi
        """
        filepath = self.output_path / post.filename
        
        # Éviter les doublons
        if filepath.exists():
            return True
        
        headers = {
            'User-Agent': self.USER_AGENT,
            'Referer': 'https://www.reddit.com/',
        }
        
        try:
            request = urllib.request.Request(post.url, headers=headers)
            
            with urllib.request.urlopen(request, timeout=30, context=self.ssl_context) as response:
                # Vérifier le content-type
                content_type = response.headers.get('Content-Type', '')
                if not content_type.startswith('image/'):
                    return False
                
                # Télécharger
                with open(filepath, 'wb') as f:
                    f.write(response.read())
                
                return True
                
        except Exception as e:
            if self.config.verbose:
                print(f"   ❌ Erreur: {post.id} - {str(e)[:50]}")
            return False
    
    def download_all(self, posts: List[RedditPost]) -> None:
        """
        Télécharge toutes les images en parallèle.
        
        Args:
            posts: Liste des posts à télécharger
        """
        if not posts:
            print("⚠️  Aucune image à télécharger")
            return
        
        print(f"\n📥 Téléchargement de {len(posts)} images...")
        print(f"   Dossier: {self.output_path}")
        
        completed = 0
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = {
                executor.submit(self._download_image, post): post 
                for post in posts
            }
            
            for future in as_completed(futures):
                post = futures[future]
                
                try:
                    success = future.result()
                    
                    if success:
                        self.stats['downloaded'] += 1
                        self.downloaded.add(post.id)
                    else:
                        self.stats['failed'] += 1
                        self.failed.add(post.id)
                    
                    completed += 1
                    
                    # Afficher la progression
                    if self.config.verbose:
                        pct = (completed / len(posts)) * 100
                        bar = '█' * int(pct // 5) + '░' * (20 - int(pct // 5))
                        print(f"\r   [{bar}] {pct:.0f}% ({completed}/{len(posts)})", end='')
                    
                except Exception as e:
                    self.stats['failed'] += 1
        
        print()  # Nouvelle ligne après la barre de progression
    
    def print_summary(self) -> None:
        """Affiche le résumé du scraping."""
        print("\n" + "═" * 60)
        print("📊 RÉSUMÉ")
        print("═" * 60)
        print(f"   Subreddit:    r/{self.config.subreddit}")
        print(f"   Images trouvées: {self.stats['found']}")
        print(f"   Téléchargées:    {self.stats['downloaded']}")
        print(f"   Ignorées:        {self.stats['skipped']}")
        print(f"   Échouées:        {self.stats['failed']}")
        print(f"   Dossier:         {self.output_path}")
        print("═" * 60)
    
    def run(self) -> None:
        """Exécute le scraping complet."""
        start_time = time.time()
        
        # Récupérer les posts
        posts = self.fetch_posts()
        
        # Télécharger les images
        self.download_all(posts)
        
        # Afficher le résumé
        self.print_summary()
        
        elapsed = time.time() - start_time
        print(f"⏱️  Temps total: {elapsed:.1f}s")


# ═══════════════════════════════════════════════════════════════════════════════
# Interface CLI
# ═══════════════════════════════════════════════════════════════════════════════

def create_parser() -> argparse.ArgumentParser:
    """Crée le parser d'arguments CLI."""
    parser = argparse.ArgumentParser(
        description="📸 Reddit Image Scraper - Télécharge des images sans API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  %(prog)s wallpapers                    # 25 images hot de r/wallpapers
  %(prog)s earthporn -l 100 -s top -t all   # Top 100 all-time de r/earthporn
  %(prog)s cats -s new -l 50             # 50 nouvelles images de r/cats
  %(prog)s art --min-score 1000          # Images avec 1000+ upvotes
  %(prog)s pics --min-width 1920         # Images HD minimum
        """
    )
    
    parser.add_argument(
        'subreddit',
        help="Nom du subreddit (sans le r/)"
    )
    
    parser.add_argument(
        '-o', '--output',
        default='downloads',
        help="Dossier de sortie (défaut: downloads)"
    )
    
    parser.add_argument(
        '-l', '--limit',
        type=int,
        default=25,
        help="Nombre d'images à télécharger (défaut: 25)"
    )
    
    parser.add_argument(
        '-s', '--sort',
        choices=['hot', 'new', 'top', 'rising'],
        default='hot',
        help="Méthode de tri (défaut: hot)"
    )
    
    parser.add_argument(
        '-t', '--time',
        choices=['hour', 'day', 'week', 'month', 'year', 'all'],
        default='week',
        help="Période pour le tri 'top' (défaut: week)"
    )
    
    parser.add_argument(
        '--min-score',
        type=int,
        default=0,
        help="Score minimum des posts (défaut: 0)"
    )
    
    parser.add_argument(
        '--min-width',
        type=int,
        default=0,
        help="Largeur minimum des images (défaut: 0)"
    )
    
    parser.add_argument(
        '--min-height',
        type=int,
        default=0,
        help="Hauteur minimum des images (défaut: 0)"
    )
    
    parser.add_argument(
        '--nsfw',
        action='store_true',
        help="Inclure le contenu NSFW"
    )
    
    parser.add_argument(
        '--no-skip',
        action='store_true',
        help="Re-télécharger les fichiers existants"
    )
    
    parser.add_argument(
        '-w', '--workers',
        type=int,
        default=5,
        help="Nombre de téléchargements parallèles (défaut: 5)"
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help="Mode silencieux"
    )
    
    return parser


def main():
    """Point d'entrée principal."""
    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                     🖼️  Reddit Image Scraper v1.0                            ║
║                         No API Key Required                                   ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    parser = create_parser()
    args = parser.parse_args()
    
    # Créer la configuration
    config = ScraperConfig(
        subreddit=args.subreddit.replace('r/', ''),
        output_dir=args.output,
        limit=args.limit,
        sort=args.sort,
        time_filter=args.time,
        min_score=args.min_score,
        min_width=args.min_width,
        min_height=args.min_height,
        include_nsfw=args.nsfw,
        skip_existing=not args.no_skip,
        max_workers=args.workers,
        verbose=not args.quiet
    )
    
    # Exécuter le scraper
    scraper = RedditScraper(config)
    scraper.run()


if __name__ == "__main__":
    main()
