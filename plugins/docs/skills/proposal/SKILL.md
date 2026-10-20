---
name: proposal
description: >
  Rédaction d'une proposition commerciale Blue Green (propale) — besoin,
  démarche, planning, budget, conditions — rendue en Word à la charte avec la
  page de présentation Blue Green via docs:brand. Déclencher sur : "propale",
  "proposition commerciale", "fais une offre pour <client>", "devis Blue Green
  en Word", "chiffre la mission".
  NE PAS déclencher pour : un rapport d'étude (→ docs:study-report), le suivi
  de l'opportunité dans le pipeline (→ gtm:crm).
allowed-tools: "Bash(uv *) Bash(python3 *) Bash(pandoc *) Bash(soffice *) Bash(pdftoppm *) Bash(mkdir *) Read Write Edit Glob mcp__plugin_hal_hal-mcp__whoami mcp__plugin_hal_hal-mcp__list_projects mcp__plugin_hal_hal-mcp__list_contacts mcp__plugin_hal_hal-mcp__list_companies mcp__plugin_hal_hal-mcp__list_interactions"
---

# Proposition commerciale Blue Green

Ce skill porte le **contenu**. La mise en forme et la page Blue Green (bandeau, présentation,
coordonnées) viennent de `docs:brand` avec `type: proposal`.

## Déroulé

1. **Contexte client** — si hal est connecté : `whoami`, puis l'opportunité (`list_projects`,
   `kind="opportunity"`), le contact (`list_contacts`) et les derniers échanges
   (`list_interactions`). Relever le champ `tone` du contact : vide ou inconnu → vouvoyer
   et le signaler.
2. Copier `template.md` (dossier de ce skill) dans le dossier de travail, sous le nom du livrable.
3. Rédiger en suivant la structure ci-dessous.
4. Rendre avec le skill `docs:brand` (section « Rendu d'un document »), contrôler le PDF, livrer
   le .docx et le .md.
5. Rattacher la propale à l'opportunité : c'est `gtm:crm` (`/crm doc`), pas ce skill.

## Structure

1. **Votre besoin** — reformulation en 3 à 5 lignes, dans les mots du client.
2. *Page Blue Green* — marqueur `<!-- blue-green-page -->` (sinon placée en fin).
3. **Notre proposition** — démarche en étapes, livrables concrets.
4. **Planning** — tableau Phase / Durée / Jalon.
5. **Budget** — tableau Poste / Jours / Montant HT, colonnes chiffrées alignées à droite
   (`---:`), ligne **Total** en gras.
6. **Conditions** — validité, modalités de paiement, TVA.

Pas de page de garde par défaut ; `cover: true` dans le front matter pour en ajouter une.

## Conventions

- Montants : `1 400 €` (espace des milliers, € après), toujours HT ; la TVA dans les conditions.
- Le texte de la page Blue Green se modifie dans `docs:brand` (`templates/blue-green-page.md`),
  jamais dans une propale.
