# CRM Note Schemas — Frontmatter Reference

All 11 note types in the SecondLife vault. Each section lists:
- `type:` value in frontmatter
- Vault folder
- All frontmatter fields with allowed values

---

## Job Search CRM

### opportunite-js — `CRM-JobSearch/Opportunites/`

| Field | Type | Allowed values |
|-------|------|----------------|
| `type` | string | `"opportunite-js"` |
| `statut` | string | `📝 À postuler`, `✉️ Candidature envoyée`, `📞 Entretien prévu`, `🔄 Relance à faire`, `🔍 À analyser`, `❌ Refus`, `✅ Offre reçue`, `⏸️ En pause` |
| `entreprise` | wikilink | `"[[Company Name]]"` |
| `contact_principal` | wikilink | `"[[Contact Name]]"` |
| `date_candidature` | date | `YYYY-MM-DD` |
| `date_relance` | date | `YYYY-MM-DD` |
| `prochain_rdv` | date | `YYYY-MM-DD` |
| `source` | string | Free text (LinkedIn, Welcome, direct...) |
| `score_match` | number | 0-100 |
| `priorite` | string | Free text |
| `type_contrat` | string | CDI, Freelance, CDD... |
| `teletravail` | string | Free text |
| `salaire_propose` | string | Free text |
| `localisation` | string | Free text |
| `lien_offre` | url | Full URL |

### entreprise-js — `CRM-JobSearch/Entreprises/`

| Field | Type | Allowed values |
|-------|------|----------------|
| `type` | string | `"entreprise-js"` |
| `secteur` | string | Free text |
| `taille` | string | Free text |
| `interet` | string | Free text |
| `localisation_hq` | string | Free text |
| `site_web` | url | Full URL |
| `linkedin` | url | Full URL |
| `glassdoor` | url | Full URL |

Body: `Culture & Notes` section as markdown below frontmatter.

### contact-js — `CRM-JobSearch/Contacts/`

| Field | Type | Allowed values |
|-------|------|----------------|
| `type` | string | `"contact-js"` |
| `entreprise` | wikilink | `"[[Company Name]]"` |
| `role` | string | Free text |
| `email` | string | Email address |
| `telephone` | string | Phone number |
| `linkedin` | url | Full URL |

Body: `Notes` section as markdown below frontmatter.

### entretien — `CRM-JobSearch/Entretiens/`

| Field | Type | Allowed values |
|-------|------|----------------|
| `type` | string | `"entretien"` |
| `categorie` | string | `"Préparation"`, `"Compte-rendu"` |
| `date` | date | `YYYY-MM-DD` |
| `date_suivi` | date | `YYYY-MM-DD` |
| `opportunite` | wikilink | `"[[Opportunite Name]]"` |
| `interlocuteurs` | list | `"Prénom Nom (Rôle)"` |
| `interviewer` | wikilink | `"[[Contact Name]]"` |
| `type_entretien` | string | Free text (RH, Technique, Manager, Final...) |
| `feeling` | string | Free text (emoji-based: 😊, 😐, 😟...) — CR only |
| `suivi_envoye` | boolean | `true` / `false` — CR only |

**Naming convention:**
- Préparation: `Prep {Entreprise} — {Interlocuteurs} — {DD-MM-YYYY}.md`
- Compte-rendu: `CR {Entreprise} — {Interlocuteurs} — {DD-MM-YYYY}.md`

**Body sections (Préparation):** `## Contexte entreprise`, `## Interlocuteurs`, `## Points clés à aborder`, `## Questions à poser`, `## Stratégie`.

**Body sections (Compte-rendu):** `## Notes clés`, `## Questions posées`, `## Next steps`..

---

## Blue Green CRM

### entreprise-bg — `CRM-BlueGreen/Entreprises/`

| Field | Type | Allowed values |
|-------|------|----------------|
| `type` | string | `"entreprise-bg"` |
| `ecosysteme` | string | Free text |
| `type_activite` | string | Free text |
| `hq` | string | Free text |
| `nb_employees` | string/number | Free text |
| `site_web` | url | Full URL |
| `address` | string | Free text |
| `description` | string | Free text |
| `note` | string | Free text |
| `bg_id` | string | Unique ID (e.g. `BG-42`) |

### contact-bg — `CRM-BlueGreen/Contacts/`

| Field | Type | Allowed values |
|-------|------|----------------|
| `type` | string | `"contact-bg"` |
| `entreprise` | wikilink | `"[[Company Name]]"` |
| `poste` | string | Free text |
| `email` | string | Email address |
| `telephone` | string | Phone number |
| `linkedin` | url | Full URL |
| `ton` | string | Free text |
| `etiquettes` | list | Free text tags |
| `dernier_contact` | date | `YYYY-MM-DD` |
| `departement` | string | Free text |
| `bio` | string | Free text |

Body: `Notes` section as markdown below frontmatter.

### opportunite-bg — `CRM-BlueGreen/Opportunites/`

| Field | Type | Allowed values |
|-------|------|----------------|
| `type` | string | `"opportunite-bg"` |
| `entreprise` | wikilink | `"[[Company Name]]"` |
| `contact` | wikilink | `"[[Contact Name]]"` |
| `stage` | string | `Customer discovery`, `Prospecting`, `Qualifying / Value Proposition`, `Writing Proposal`, `Proposal sent`, `Closed Win ✨`, `Closed Lost 🪦` |
| `type_offre` | string | Free text |
| `montant_ht` | number | Amount in EUR |
| `premier_contact` | date | `YYYY-MM-DD` |
| `expected_closing` | date | `YYYY-MM-DD` |
| `contrat_signe` | date | `YYYY-MM-DD` |
| `projet` | wikilink | `"[[Project Name]]"` |
| `contexte` | string | Free text |
| `deal_docs` | string | Free text |
| `final_note` | string | Free text |

### interaction-bg — `CRM-BlueGreen/Interactions/`

| Field | Type | Allowed values |
|-------|------|----------------|
| `type` | string | `"interaction-bg"` |
| `date_entretien` | date | `YYYY-MM-DD` |
| `entreprise` | wikilink | `"[[Company Name]]"` |
| `opportunite` | wikilink | `"[[Opportunite Name]]"` |
| `participants_customer` | wikilink/list | `"[[Contact Name]]"` or list |
| `type_acteur` | string | Free text |
| `segment` | string | Free text |
| `compte_rendu` | string | Free text |

Body sections: `## Principales informations`, `## Validation des hypothèses`.

---

## Project Management

### tache — `Taches/`

| Field | Type | Allowed values |
|-------|------|----------------|
| `type` | string | `"tache"` |
| `id_tache` | string | Unique ID (e.g. `TASK-123`) |
| `etat` | string | `Pas commencée`, `Today`, `En cours`, `Terminé`, `Archivé` |
| `priorite` | string | `Basse`, `Moyenne`, `Haute`, `Urgent` |
| `echeance` | date | `YYYY-MM-DD` |
| `etiquettes` | list | `jobsearch`, `Prospection`, `Commercial`, `Marketing`, `Product`, `Company Growth`, `RosasLaborbe`... |
| `projet` | wikilink | `"[[Project Name]]"` |
| `cycle` | wikilink | `"[[Sprint Name]]"` |
| `opportunite` | wikilink | `"[[Opportunite Name]]"` |
| `contacts` | wikilink/list | `"[[Contact Name]]"` or list |
| `sous_taches` | wikilink/list | `"[[Task Name]]"` or list |
| `tache_parent` | wikilink | `"[[Task Name]]"` |
| `personne_assignee` | string | Free text |

Body section: `## Résumé`.

### projet — `Projets/`

| Field | Type | Allowed values |
|-------|------|----------------|
| `type` | string | `"projet"` |
| `type_projet` | string | Free text |
| `etat` | string | `Pas commencé`, `En cours`, `Terminé`, `Annulé`, `En pause` |
| `priorite` | string | Free text |
| `dates` | date | `YYYY-MM-DD` |
| `proprietaire` | string | Free text |
| `taches` | wikilink/list | `"[[Task Name]]"` or list |
| `contacts` | wikilink/list | `"[[Contact Name]]"` or list |
| `entreprises` | wikilink/list | `"[[Company Name]]"` or list |
| `bloque` | wikilink/list | `"[[Project Name]]"` or list |
| `bloque_par` | wikilink/list | `"[[Project Name]]"` or list |

Body section: `## Résumé`.

### sprint — `Sprints/`

| Field | Type | Allowed values |
|-------|------|----------------|
| `type` | string | `"sprint"` |
| `dates` | date | `YYYY-MM-DD` |
| `id_sprint` | string | Unique ID (e.g. `SPRINT-43`) |
| `taches` | wikilink/list | `"[[Task Name]]"` or list |
| `etat` | string | Free text |

---

## Vault Folder Structure

```
SecondLife/
├── CRM-JobSearch/
│   ├── Opportunites/     → opportunite-js
│   ├── Entreprises/      → entreprise-js
│   ├── Contacts/         → contact-js
│   └── Entretiens/       → entretien
├── CRM-BlueGreen/
│   ├── Opportunites/     → opportunite-bg
│   ├── Entreprises/      → entreprise-bg
│   ├── Contacts/         → contact-bg
│   └── Interactions/     → interaction-bg
├── Taches/               → tache
├── Projets/              → projet
├── Sprints/              → sprint
├── _config/views/        → Dataview dashboards & kanbans
└── Welcome.md            → Dashboard
```

## Wikilink Format

Relations between notes use Obsidian wikilinks: `"[[Note Title]]"`.
- The title must match the note filename (without `.md`)
- Filenames are sanitized: `<>:"/\|?*` replaced by `-`, Unicode NFC-normalized
- For lists of relations, use YAML list format:
  ```yaml
  contacts:
    - "[[Jean Dupont]]"
    - "[[Marie Martin]]"
  ```
