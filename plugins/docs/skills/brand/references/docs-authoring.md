# Rédiger dans Claude Docs, livrer à la charte

Claude Docs sert à écrire, relire et commenter. Il ne connaît ni la charte, ni les pages de garde,
ni les champs à remplir. Le rendu Word/PDF reste celui de `md2docx.py`. Entre les deux,
`docs2md.py` convertit l'**export Word** du doc en Markdown source.

L'export Markdown de Docs n'est pas utilisé. Il écrase les cellules à plusieurs paragraphes,
échappe `\newpage` et les `_` des noms de champs, et perd les largeurs de colonnes.

## Écrire dans le doc

| Besoin | Dans Docs | Devient |
|---|---|---|
| Métadonnées (type, titre, client, date, en-tête) | un bloc de code `yaml` en tête, juste sous le titre | le front matter |
| Titre du document | le `#` du doc — supprimé s'il répète `title` | page de garde ou bloc titre |
| Saut de page | un paragraphe seul `[[saut de page]]` (ou `\newpage`) | `\newpage` |
| Page Blue Green (propale) | un paragraphe seul `[[page Blue Green]]` | `<!-- blue-green-page -->` |
| Champ à remplir | `{{?Libellé}}` ou `{{?Libellé#nom}}` tapé tel quel | case Word, champ PDF |
| Valeur de marque | `{{contact.email}}`, `{{company.legal_notice}}`… | la valeur de `brand.yaml` |
| Tableau | un tableau Docs ; la 1re ligne est l'en-tête | tableau à la charte, largeurs calculées sur le texte |
| Tableau libellé / valeur | 1re ligne laissée vide | tableau sans en-tête |
| Plusieurs paragraphes dans une cellule | Entrée dans la cellule | tableau grid |
| Légende de tableau | paragraphe `: Légende` juste sous le tableau | légende au-dessus du tableau |
| Image, figure | image insérée dans le doc, texte alternatif = légende | image centrée + légende, largeur en % |
| Encadré | citation (`>`) | italique, filet bleu |

## À éviter

- **Champ `{{?…}}` dans un tableau dont une cellule a plusieurs paragraphes** : le tableau reste
  en grid et le champ en casse l'alignement. Mettre les champs dans un tableau simple.
- **Puces de date, mentions, listes déroulantes** : converties en texte (date en français, nom
  sans `@`), sans plus. Écrire la date en toutes lettres.
- **Graphiques et schémas Docs** : absents de l'export Word. Les exporter en image et les insérer.
- **Notes de bas de page** : refusées par Docs. Les mettre entre parenthèses.
- **Filets horizontaux** : perdus à l'export Word.
- Les commentaires Docs ne sortent pas dans le livrable, c'est voulu.

## Livrer

1. **Récupérer l'export Word du doc**, de l'une de ces deux façons :
   - le demander à Claude : outil `export` des docs, `format: "docx"`, puis décoder le base64
     dans un fichier `.docx`. Cette voie convient à un doc de texte. Un doc riche en images pèse
     lourd, car les octets transitent par la conversation ;
   - l'exporter soi-même depuis Docs (nom du doc → Exporter → Word) dans un dossier que Claude
     voit. C'est la voie à privilégier dès qu'il y a des images.
2. **Convertir :**

   ```bash
   uv run --with python-docx --with pyyaml \
     python3 "$PLUGIN_DIR/scripts/docs2md.py" export.docx -o livrable.md
   ```

   Les images sont extraites à côté (`livrable_media/`). Les avertissements (tableau sans
   en-tête, marqueur `[[…]]` inconnu) sortent sur stderr.
3. **Rendre à la charte** comme tout Markdown (`SKILL.md` § Rendu d'un document) :
   `md2docx.py livrable.md -o livrable.docx --pdf`.
4. **Contrôler le PDF en image**, puis livrer le .docx, le .pdf et le .md.

Le doc Docs reste la version de travail. Une correction se fait dans le doc, puis on réexporte.
Le .md n'est pas à retoucher à la main, sauf urgence.
