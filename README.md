# NELVIS MOTION STUDIO

Atelier indépendant de motion design pour NELVIS. Pipeline : GSAP (animations déterministes), Playwright/Chromium (capture), FFmpeg (assemblage et audio), GitHub Actions (rendu).

## Démarrage
`npm ci && npx playwright install chromium && npm run render`

Les exports horizontaux et verticaux sont générés séparément. Le dépôt `nelvis-video` n'est pas utilisé.

## MOTION DESIGN NELVIS

Le générateur produit un spot à partir d’un brief JSON, avec un export vertical ou horizontal. Dans **Actions**, ouvrez **MOTION DESIGN NELVIS — rendu vidéo**, choisissez **Run workflow**, puis récupérez les fichiers dans **Artifacts → motion-design-nelvis**. Le brief VOLT lance la démonstration.

Le [guide du générateur](motion/README.md) détaille les logiciels, les formats de projet et le mode local.
