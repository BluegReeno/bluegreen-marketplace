# Markdown supporté

Ce qui passe proprement en Word, et ce qui est volontairement exclu.

## Supporté

| Élément | Syntaxe | Rendu Word |
|---|---|---|
| Titres | `#`, `##`, `###` | Titre 1 / 2 (bleu), Titre 3 (gris gras). `####` toléré, à éviter |
| Paragraphe | texte | Poppins 10 pt |
| Gras, italique | `**x**`, `*x*` | idem |
| Listes | `-`, `1.` (2 niveaux), précédées d'une ligne vide | puces / numéros Word |
| Lien | `[texte](url)` | lien bleu |
| Tableau | tableau pipe avec ligne `|---|` ; `---:` aligne à droite | en-tête bleu clair, lignes alternées, pleine largeur |
| Largeur des colonnes | proportionnelle au nombre de tirets (`|-----|-------------|`) | respectée |
| Tableau libellé / valeur | en-tête vide `| | |` puis lignes `| **Libellé** | valeur |` | sans ligne d'en-tête |
| Cellules à plusieurs paragraphes | tableau *grid* (`+---+`) | paragraphes et listes dans la cellule |
| Légende de tableau | `: Légende` juste après le tableau | au-dessus du tableau |
| Image | `![Légende](img.png){width=80%}` | image centrée + légende |
| Citation / encadré | `> texte` | italique, filet bleu à gauche |
| Filet | `---` seul, entouré de lignes vides | trait fin |
| Saut de page | `\newpage` seul | saut de page |
| Note de bas de page | `texte[^1]` puis `[^1]: note` | note Word |
| Code | `` `code` `` ou bloc ``` | police à chasse fixe |

## Exclu (perdu ou mal rendu)

- HTML (`<table>`, `<div>`, `<br>`, styles inline) — les commentaires `<!-- -->` sont ignorés,
  sauf le marqueur `<!-- blue-green-page -->`.
- Cellules fusionnées, tableaux imbriqués.
- Colonnes de texte, texte sur image, zones de texte.
- Mermaid, diagrammes, graphiques : les exporter en PNG et les insérer comme image.
- Emojis dans les titres.
- Titres de niveau 5 et 6.
- Titres simulés en gras (`**TITRE**`) : utiliser `#` pour qu'ils entrent dans le sommaire.
