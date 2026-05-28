#!/usr/bin/env python3
"""Note schema definitions and validation for the SecondLife Obsidian vault.

Self-contained module — no dependency on migration scripts.

Public API:
    validate_create(note_type, fields) -> ValidationResult
    validate_update(note_type, field_name, value) -> ValidationResult
    get_schema(note_type) -> NoteSchema | None

Usage:
    from note_schemas import validate_create, validate_update, get_schema

Run directly for self-tests:
    python note_schemas.py
"""

import re
import sys
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class FieldDef:
    """Schema definition for a single frontmatter field."""
    name: str
    ftype: str  # string|date|number|bool|url|wikilink|list|wikilink_list|enum
    required: bool = False
    enum_values: list = field(default_factory=list)


@dataclass
class NoteSchema:
    """Schema for a note type."""
    note_type: str
    folder: str
    fields: dict  # name -> FieldDef
    body_sections: list = field(default_factory=list)  # list of heading strings


@dataclass
class ValidationResult:
    """Result of a validation check."""
    errors: list = field(default_factory=list)   # blocking
    warnings: list = field(default_factory=list)  # non-blocking

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


# Fields silently allowed on all note types (legacy/system fields)
LEGACY_FIELDS = {"notion_id"}


# ---------------------------------------------------------------------------
# Enum value sets
# ---------------------------------------------------------------------------

JS_STATUTS = [
    "📝 À postuler",
    "✉️ Candidature envoyée",
    "📞 Entretien prévu",
    "🔄 Relance à faire",
    "🔍 À analyser",
    "❌ Refus",
    "✅ Offre reçue",
    "⏸️ En pause",
]

BG_STAGES = [
    "Customer discovery",
    "Prospecting",
    "Qualifying / Value Proposition",
    "Writing Proposal",
    "Proposal sent",
    "Closed Win ✨",
    "Closed Lost 🪦",
]

TACHE_ETATS = [
    "Pas commencée",
    "Today",
    "En cours",
    "Terminé",
    "Archivé",
]

TACHE_PRIORITES = [
    "Basse",
    "Moyenne",
    "Haute",
    "Urgent",
]

PROJET_ETATS = [
    "Pas commencé",
    "En cours",
    "Terminé",
    "Annulé",
    "En pause",
]

SPRINT_ETATS = [
    "Passés",
    "Dernier",
    "Actuel",
    "Suivant",
    "À venir",
]


# ---------------------------------------------------------------------------
# Helper: build fields dict from list of FieldDefs
# ---------------------------------------------------------------------------

def _fields(*defs: FieldDef) -> dict:
    return {d.name: d for d in defs}


# ---------------------------------------------------------------------------
# Schema definitions — all 11 note types
# ---------------------------------------------------------------------------

SCHEMAS: dict[str, NoteSchema] = {}


def _register(schema: NoteSchema):
    SCHEMAS[schema.note_type] = schema


# --- Job Search CRM ---

_register(NoteSchema(
    note_type="opportunite-js",
    folder="CRM-JobSearch/Opportunites",
    fields=_fields(
        FieldDef("statut", "enum", enum_values=JS_STATUTS),
        FieldDef("entreprise", "wikilink"),
        FieldDef("contact_principal", "wikilink"),
        FieldDef("date_candidature", "date"),
        FieldDef("date_relance", "date"),
        FieldDef("prochain_rdv", "date"),
        FieldDef("source", "string"),
        FieldDef("score_match", "number"),
        FieldDef("priorite", "string"),
        FieldDef("type_contrat", "string"),
        FieldDef("teletravail", "string"),
        FieldDef("salaire_propose", "string"),
        FieldDef("localisation", "string"),
        FieldDef("lien_offre", "url"),
    ),
))

_register(NoteSchema(
    note_type="entreprise-js",
    folder="CRM-JobSearch/Entreprises",
    fields=_fields(
        FieldDef("secteur", "string"),
        FieldDef("taille", "string"),
        FieldDef("interet", "string"),
        FieldDef("localisation_hq", "string"),
        FieldDef("site_web", "url"),
        FieldDef("linkedin", "url"),
        FieldDef("glassdoor", "url"),
    ),
))

_register(NoteSchema(
    note_type="contact-js",
    folder="CRM-JobSearch/Contacts",
    fields=_fields(
        FieldDef("entreprise", "wikilink"),
        FieldDef("role", "string"),
        FieldDef("email", "string"),
        FieldDef("telephone", "string"),
        FieldDef("linkedin", "url"),
    ),
))

_register(NoteSchema(
    note_type="entretien",
    folder="CRM-JobSearch/Entretiens",
    fields=_fields(
        FieldDef("date", "date"),
        FieldDef("date_suivi", "date"),
        FieldDef("opportunite", "wikilink"),
        FieldDef("interviewer", "wikilink"),
        FieldDef("type_entretien", "string"),
        FieldDef("feeling", "string"),
        FieldDef("suivi_envoye", "bool"),
    ),
    body_sections=["## Notes clés", "## Questions posées", "## Next steps"],
))

# --- Blue Green CRM ---

_register(NoteSchema(
    note_type="entreprise-bg",
    folder="CRM-BlueGreen/Entreprises",
    fields=_fields(
        FieldDef("ecosysteme", "string"),
        FieldDef("type_activite", "string"),
        FieldDef("hq", "string"),
        FieldDef("nb_employees", "string"),
        FieldDef("site_web", "url"),
        FieldDef("address", "string"),
        FieldDef("description", "string"),
        FieldDef("note", "string"),
        FieldDef("bg_id", "string"),
    ),
))

_register(NoteSchema(
    note_type="contact-bg",
    folder="CRM-BlueGreen/Contacts",
    fields=_fields(
        FieldDef("entreprise", "wikilink"),
        FieldDef("poste", "string"),
        FieldDef("email", "string"),
        FieldDef("telephone", "string"),
        FieldDef("linkedin", "url"),
        FieldDef("ton", "string"),
        FieldDef("etiquettes", "list"),
        FieldDef("dernier_contact", "date"),
        FieldDef("departement", "string"),
        FieldDef("bio", "string"),
    ),
))

_register(NoteSchema(
    note_type="opportunite-bg",
    folder="CRM-BlueGreen/Opportunites",
    fields=_fields(
        FieldDef("entreprise", "wikilink"),
        FieldDef("contact", "wikilink"),
        FieldDef("stage", "enum", enum_values=BG_STAGES),
        FieldDef("type_offre", "string"),
        FieldDef("montant_ht", "number"),
        FieldDef("premier_contact", "date"),
        FieldDef("expected_closing", "date"),
        FieldDef("contrat_signe", "date"),
        FieldDef("projet", "wikilink"),
        FieldDef("contexte", "string"),
        FieldDef("deal_docs", "string"),
        FieldDef("final_note", "string"),
    ),
))

_register(NoteSchema(
    note_type="interaction-bg",
    folder="CRM-BlueGreen/Interactions",
    fields=_fields(
        FieldDef("date_entretien", "date"),
        FieldDef("entreprise", "wikilink"),
        FieldDef("opportunite", "wikilink"),
        FieldDef("participants_customer", "wikilink_list"),
        FieldDef("type_acteur", "string"),
        FieldDef("segment", "string"),
        FieldDef("compte_rendu", "string"),
    ),
    body_sections=["## Principales informations", "## Validation des hypothèses"],
))

# --- Project Management ---

_register(NoteSchema(
    note_type="tache",
    folder="Taches",
    fields=_fields(
        FieldDef("id_tache", "string"),
        FieldDef("etat", "enum", enum_values=TACHE_ETATS),
        FieldDef("priorite", "enum", enum_values=TACHE_PRIORITES),
        FieldDef("echeance", "date"),
        FieldDef("etiquettes", "list"),
        FieldDef("projet", "wikilink"),
        FieldDef("cycle", "wikilink"),
        FieldDef("opportunite", "wikilink"),
        FieldDef("contacts", "wikilink_list"),
        FieldDef("sous_taches", "wikilink_list"),
        FieldDef("tache_parent", "wikilink"),
        FieldDef("personne_assignee", "string"),
    ),
    body_sections=["## Résumé"],
))

_register(NoteSchema(
    note_type="projet",
    folder="Projets",
    fields=_fields(
        FieldDef("type_projet", "string"),
        FieldDef("etat", "enum", enum_values=PROJET_ETATS),
        FieldDef("priorite", "string"),
        FieldDef("dates", "date"),
        FieldDef("proprietaire", "string"),
        FieldDef("taches", "wikilink_list"),
        FieldDef("contacts", "wikilink_list"),
        FieldDef("entreprises", "wikilink_list"),
        FieldDef("bloque", "wikilink_list"),
        FieldDef("bloque_par", "wikilink_list"),
    ),
    body_sections=["## Résumé"],
))

_register(NoteSchema(
    note_type="sprint",
    folder="Sprints",
    fields=_fields(
        FieldDef("dates", "date"),
        FieldDef("id_sprint", "string"),
        FieldDef("taches", "wikilink_list"),
        FieldDef("etat", "enum", enum_values=SPRINT_ETATS),
    ),
))


# ---------------------------------------------------------------------------
# Validation functions
# ---------------------------------------------------------------------------

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
WIKILINK_RE = re.compile(r"^\[\[.+\]\]$")


def _validate_value(field_def: FieldDef, value, result: ValidationResult):
    """Validate a single field value against its FieldDef."""
    ftype = field_def.ftype
    name = field_def.name

    if value is None:
        return

    if ftype == "enum":
        if str(value) not in field_def.enum_values:
            allowed = ", ".join(f'"{v}"' for v in field_def.enum_values)
            result.errors.append(
                f'field "{name}": invalid value "{value}". '
                f"Allowed: [{allowed}]"
            )

    elif ftype == "date":
        if not DATE_RE.match(str(value)):
            result.errors.append(
                f'field "{name}": invalid date "{value}". Expected YYYY-MM-DD format.'
            )

    elif ftype == "wikilink":
        if not WIKILINK_RE.match(str(value)):
            result.errors.append(
                f'field "{name}": invalid wikilink "{value}". Expected [[Note Title]] format.'
            )

    elif ftype == "wikilink_list":
        # Accept a single wikilink or a list of wikilinks
        items = value if isinstance(value, list) else [value]
        for item in items:
            if not WIKILINK_RE.match(str(item)):
                result.errors.append(
                    f'field "{name}": invalid wikilink "{item}". '
                    f"Expected [[Note Title]] format."
                )

    elif ftype == "number":
        try:
            float(value)
        except (ValueError, TypeError):
            result.errors.append(
                f'field "{name}": invalid number "{value}".'
            )

    elif ftype == "bool":
        if value not in (True, False, "true", "false"):
            result.errors.append(
                f'field "{name}": invalid boolean "{value}". Expected true/false.'
            )

    elif ftype == "url":
        if not str(value).startswith("http"):
            result.warnings.append(
                f'field "{name}": value "{value}" does not look like a URL.'
            )

    # "string" and "list" — no validation needed


def validate_create(note_type: str, fields: dict) -> ValidationResult:
    """Validate fields for creating a note of the given type.

    Returns ValidationResult with .errors (blocking) and .warnings (non-blocking).
    """
    result = ValidationResult()

    schema = SCHEMAS.get(note_type)
    if schema is None:
        result.errors.append(f'unknown note type: "{note_type}"')
        return result

    for name, value in fields.items():
        if name in LEGACY_FIELDS:
            continue
        field_def = schema.fields.get(name)
        if field_def is None:
            result.warnings.append(
                f'unknown field "{name}" for type "{note_type}"'
            )
            continue
        _validate_value(field_def, value, result)

    # Check required fields
    for name, field_def in schema.fields.items():
        if field_def.required and name not in fields:
            result.warnings.append(
                f'missing required field "{name}" for type "{note_type}"'
            )

    return result


def validate_update(note_type: str, field_name: str, value) -> ValidationResult:
    """Validate a single field update for a note of the given type.

    Returns ValidationResult with .errors (blocking) and .warnings (non-blocking).
    """
    result = ValidationResult()

    schema = SCHEMAS.get(note_type)
    if schema is None:
        result.errors.append(f'unknown note type: "{note_type}"')
        return result

    if field_name in LEGACY_FIELDS:
        return result

    field_def = schema.fields.get(field_name)
    if field_def is None:
        result.warnings.append(
            f'unknown field "{field_name}" for type "{note_type}"'
        )
        return result

    _validate_value(field_def, value, result)
    return result


def get_schema(note_type: str) -> Optional[NoteSchema]:
    """Get the schema for a note type, or None if unknown."""
    return SCHEMAS.get(note_type)


# ---------------------------------------------------------------------------
# Self-tests (run with: python note_schemas.py)
# ---------------------------------------------------------------------------

def _self_test():
    """Run basic validation self-tests."""
    passed = 0
    failed = 0

    def check(label, condition):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  PASS: {label}")
        else:
            failed += 1
            print(f"  FAIL: {label}")

    print("Running self-tests...\n")

    # 1. Valid BG opportunity
    r = validate_create("opportunite-bg", {
        "stage": "Prospecting",
        "entreprise": "[[Acme]]",
        "montant_ht": 5000,
    })
    check("valid BG opportunity", r.ok and not r.warnings)

    # 2. Invalid BG stage
    r = validate_create("opportunite-bg", {"stage": "INVALID"})
    check("invalid BG stage → error", not r.ok and "invalid value" in r.errors[0])

    # 3. Invalid wikilink
    r = validate_create("contact-bg", {"entreprise": "NotALink"})
    check("invalid wikilink → error", not r.ok and "wikilink" in r.errors[0])

    # 4. Valid wikilink
    r = validate_create("contact-bg", {"entreprise": "[[TotalEnergies]]"})
    check("valid wikilink", r.ok)

    # 5. Invalid date
    r = validate_create("entretien", {"date": "17/02/2026"})
    check("invalid date → error", not r.ok and "date" in r.errors[0])

    # 6. Valid date
    r = validate_create("entretien", {"date": "2026-02-17"})
    check("valid date", r.ok)

    # 7. Unknown field → warning only
    r = validate_create("contact-bg", {"unknown_field": "value"})
    check("unknown field → warning (not error)", r.ok and len(r.warnings) == 1)

    # 8. Unknown note type → error
    r = validate_create("nonexistent-type", {"foo": "bar"})
    check("unknown note type → error", not r.ok)

    # 9. validate_update with valid enum
    r = validate_update("tache", "etat", "En cours")
    check("valid update enum", r.ok)

    # 10. validate_update with invalid enum
    r = validate_update("tache", "etat", "WRONG")
    check("invalid update enum → error", not r.ok)

    # 11. Legacy field accepted
    r = validate_create("contact-bg", {"notion_id": "abc-123"})
    check("legacy field notion_id accepted", r.ok and not r.warnings)

    # 12. Bool validation
    r = validate_create("entretien", {"suivi_envoye": True})
    check("valid bool true", r.ok)
    r = validate_create("entretien", {"suivi_envoye": "maybe"})
    check("invalid bool → error", not r.ok)

    # 13. Number validation
    r = validate_create("opportunite-bg", {"montant_ht": "not_a_number"})
    check("invalid number → error", not r.ok)

    # 14. URL warning
    r = validate_create("entreprise-js", {"site_web": "not-a-url"})
    check("bad URL → warning (not error)", r.ok and len(r.warnings) == 1)

    # 15. wikilink_list validation
    r = validate_create("interaction-bg", {
        "participants_customer": ["[[Alice]]", "[[Bob]]"]
    })
    check("valid wikilink_list", r.ok)
    r = validate_create("interaction-bg", {
        "participants_customer": ["[[Alice]]", "Bob"]
    })
    check("invalid wikilink_list item → error", not r.ok)

    # 16. wikilink_list single value (auto-OK)
    r = validate_create("interaction-bg", {
        "participants_customer": "[[Alice]]"
    })
    check("wikilink_list single value accepted", r.ok)

    # 17. get_schema
    check("get_schema returns NoteSchema", get_schema("tache") is not None)
    check("get_schema unknown returns None", get_schema("nope") is None)

    # 18. All 11 types registered
    check(f"11 schemas registered (got {len(SCHEMAS)})", len(SCHEMAS) == 11)

    # 19. Body sections
    s = get_schema("entretien")
    check("entretien has 3 body sections", len(s.body_sections) == 3)

    # 20. JS statut with emoji
    r = validate_create("opportunite-js", {"statut": "📞 Entretien prévu"})
    check("JS statut with emoji accepted", r.ok)

    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed:
        sys.exit(1)
    print("All tests passed!")


if __name__ == "__main__":
    _self_test()
