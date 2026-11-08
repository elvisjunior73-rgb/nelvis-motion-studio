# MOTION DESIGN NELVIS

Dans GitHub Actions, ouvrez **MOTION DESIGN NELVIS — rendu vidéo** puis **Run workflow**. Le brief par défaut génère le spot fictif VOLT RIFT 01 en 9:16 et 16:9. Les MP4, sous-titres et projets sont disponibles dans **Artifacts → motion-design-nelvis** pendant 14 jours. La variante `core` produit le spot et les projets de montage avec les moteurs de base. La variante `full` active les étapes supplémentaires.

## Produire une vidéo

1. Copiez `examples/volt.json` dans un nouveau dossier sous `motion/`.
2. Ajoutez vos trois images, réglez les textes et retirez `demo_orbit`. Les chemins des images sont relatifs au brief.
3. Ajoutez éventuellement une narration WAV ou des sous-titres SRT/ASS avec le même nom que le brief. Exemple pour `produit.json` et `produit.wav`.
4. Lancez le workflow avec le chemin du brief relatif à `motion/`.

Le dépôt est public. Pour une production confidentielle, exécutez le pipeline localement ou dans un dépôt privé.

## Logiciels et fichiers

| Outil | Intégration |
|---|---|
| Blender / Cycles | Reconstruit le modèle, les trois angles et la rotation du test VOLT. |
| Inkscape | Exporte le logo SVG. |
| Glaxnimate | Son module MLT rend le Lottie de l’ouverture. |
| Natron | Le script Python construit le graphe et rend un plan PNG du détail utilisé par le spot VOLT. |
| GIMP / Krita | GIMP écrit un XCF à calques. Krita ouvre le projet OpenRaster et exporte le PNG. |
| Kdenlive | Ouvrir le projet OTIO. Le moteur MLT rend aussi la playlist et ses quatre plans dans Actions. |
| Shotcut | Ouvrir la playlist MLT en tant que clip ou importer les quatre plans. |
| Olive | Ouvrir le projet OTIO avec une version compilée avec OpenTimelineIO. Ouvrez Olive depuis le dossier de montage pour que les chemins relatifs désignent les quatre plans. Si nécessaire, reliez les médias à ce dossier. |
| Whisper | Transcription locale facultative d’un WAV, avec SRT et ASS. Le test VOLT utilise une voix française eSpeak NG. Le sous-titrage incrusté a été calé sur le texte de la voix. La transcription automatique de Whisper reste disponible dans `whisper-brut/`. |
| Subtitle Edit | SeConv convertit le SRT en VTT quand le binaire de la version épinglée est disponible. |
| AutoSub | La variante locale de ThXrimson, basée sur Whisper, transcrit le WAV en SRT dans le dossier `autosub/` des résultats. `python autosub_import.py source.wav dossier-sortie` permet de la lancer séparément. |
| Remotion | Rend le carton final VOLT dans les deux formats et le fournit à FFmpeg. |
| FFmpeg / FFprobe | Export et contrôle des deux MP4, à 30 i/s pendant 12 secondes, avec une piste AAC. |

## Interface locale

Après préparation des ressources avec `bash bootstrap.sh` dans ce dossier et installation des dépendances Python, lancez `python server.py`. Ouvrez `http://127.0.0.1:8765`. Le profil VOLT est préchargé.

## Exécuter le workflow en local

Les commandes du workflow GitHub documentent les dépendances Debian. Avec ces dépendances installées, lancez `bash produce.sh examples/volt.json both core`. Pour la chaîne complète, installez aussi Whisper, les dépendances Remotion et les logiciels de création, puis renseignez les chemins absolus `NELVIS_NATRON` et `NELVIS_SECONV`.
