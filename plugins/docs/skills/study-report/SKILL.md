---
name: study-report
description: >
  Rédaction d'un rapport d'étude Blue Green — structure, contenu attendu par
  partie, règles d'écriture — rendu en Word à la charte via docs:brand.
  Déclencher sur : "rapport d'étude", "rédige le rapport", "livrable d'étude",
  "rapport final pour <client>", "synthèse d'étude à la charte".
  NE PAS déclencher pour : une proposition commerciale (→ docs:proposal), une
  note ou un courrier simple (→ docs:brand).
allowed-tools: "Bash(uv *) Bash(python3 *) Bash(pandoc *) Bash(soffice *) Bash(pdftoppm *) Bash(mkdir *) Read Write Edit Glob"
---

# Rapport d'étude Blue Green

Ce skill porte le **contenu**. La mise en forme (page de garde, sommaire, en-tête, pied
de page) est automatique : elle vient de `docs:brand` avec `type: report`.

## Déroulé

1. Copier `template.md` (dossier de ce skill) dans le dossier de travail, sous le nom du livrable.
2. Remplir le front matter : `title` (nom du projet, ~40 caractères max pour tenir sur une ligne
   de garde), `client`, `date`. `subtitle` vaut « Rapport d'étude » par défaut.
3. Rédiger en suivant la structure ci-dessous.
4. Rendre avec le skill `docs:brand` (section « Rendu d'un document »), contrôler le PDF, livrer
   le .docx et le .md.

## Structure

1. **Contexte** — le besoin du client dans ses mots, le périmètre (inclus / exclu).
2. **Méthodologie** — démarche, sources de données, hypothèses ; un tableau Étape / Livrable /
   Échéance quand il y a des phases.
3. **Résultats** — un `##` par constat ; chaque constat s'appuie sur une donnée, une figure ou
   un tableau.
4. **Recommandations** — liste numérotée, priorisée, chaque item actionnable.
5. **Annexes** — données sources, glossaire, références.

## Règles d'écriture

- Le sommaire reprend `#` et `##` : les titrer pour qu'ils se lisent seuls.
- Au-delà de ~8 pages, ouvrir chaque grande partie par `\newpage`.
- Figures : PNG dans le dossier du .md, `![Légende](fig.png){width=80%}`.
- Chiffres : espace des milliers (`12 500`), unités SI, source sous chaque tableau emprunté.
