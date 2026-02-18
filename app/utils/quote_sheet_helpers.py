"""
Helpers for QuoteSheet cost line normalization.

Maps flat form field names (e.g. vacation_one_time) to/from
QuoteSheetCostLine rows.
"""

# Each entry: category_prefix -> (section, label, sort_order)
COST_CATEGORY_MAP = {
    # Section C: Employee Cost
    "vacation": ("employee", "Employee Vacation Cost", 0),
    "flight": ("employee", "Flight Cost", 1),
    "eosb": ("employee", "EOSB - End of Service Benefits", 2),
    "gosi": ("employee", "GOSI", 3),
    "medical": ("employee", "Medical Insurance Cost", 4),
    "exit_reentry": ("employee", "Exit Re-Entry Cost", 5),
    "salary_transfer": ("employee", "Salary Transfer Cost", 6),
    "sick_leave": ("employee", "Sick Leave Cost", 7),
    # Section D: Family Cost
    "family_medical": ("family", "Family Medical Cost", 0),
    "family_flight": ("family", "Family Flight Cost", 1),
    "family_exit": ("family", "Family Exit Cost", 2),
    "family_joining": ("family", "Family Joining Cost", 3),
    "family_visa": ("family", "Family Visa Cost", 4),
    "family_levy": ("family", "Family Levy", 5),
    # Section E: Government Related Charges
    "sce": ("government", "SCE", 0),
    "medical_test": ("government", "Medical Test Cost", 1),
    "visa_cost": ("government", "Visa Cost", 2),
    "ewakala": ("government", "Ewakala", 3),
    "chamber_mofa": ("government", "Chamber / MOFA", 4),
    "iqama": ("government", "Iqama Cost", 5),
    "saudi_admin": ("government", "Saudi Admin Cost", 6),
    "ajeer": ("government", "Ajeer Cost", 7),
    # Section F: Mobilization Cost
    "visa_processing": ("mobilization", "Visa Processing", 0),
    "recruitment": ("mobilization", "Recruitment Cost", 1),
    "joining_ticket": ("mobilization", "Joining Ticket", 2),
    "relocation": ("mobilization", "Relocation Cost", 3),
    "other_cost": ("mobilization", "Other Cost", 4),
}

# Build set of all flat field names that correspond to cost lines
COST_FIELD_SUFFIXES = ("_one_time", "_annual", "_monthly")
COST_FLAT_FIELDS = set()
for cat in COST_CATEGORY_MAP:
    for suffix in COST_FIELD_SUFFIXES:
        COST_FLAT_FIELDS.add(f"{cat}{suffix}")


def split_form_data(form_dict: dict) -> tuple:
    """
    Split flat form dict into (parent_fields, cost_lines_data).

    parent_fields: dict of fields that belong on the QuoteSheet model.
    cost_lines_data: dict of {category: {one_time, annual, monthly}}.
    """
    parent_fields = {}
    cost_lines_data = {}

    for key, value in form_dict.items():
        if key in COST_FLAT_FIELDS:
            # Determine category and suffix
            for suffix in COST_FIELD_SUFFIXES:
                if key.endswith(suffix):
                    category = key[: -len(suffix)]
                    amount_key = suffix.lstrip("_")  # "one_time", "annual", "monthly"
                    cost_lines_data.setdefault(category, {})[amount_key] = value
                    break
        else:
            parent_fields[key] = value

    return parent_fields, cost_lines_data


def flatten_cost_lines(cost_lines) -> dict:
    """
    Convert a list of QuoteSheetCostLine objects back to a flat dict
    for PDF generation (same keys the form originally sent).
    """
    result = {}
    for line in cost_lines:
        result[f"{line.category}_one_time"] = line.one_time
        result[f"{line.category}_annual"] = line.annual
        result[f"{line.category}_monthly"] = line.monthly
    return result


def create_cost_line_rows(quote_sheet_id: str, cost_lines_data: dict):
    """
    Create QuoteSheetCostLine model instances from cost_lines_data dict.

    Returns list of QuoteSheetCostLine instances (not yet added to session).
    """
    from app.models.quote_sheet import QuoteSheetCostLine

    rows = []
    for category, amounts in cost_lines_data.items():
        if category not in COST_CATEGORY_MAP:
            continue
        section, label, sort_order = COST_CATEGORY_MAP[category]
        rows.append(QuoteSheetCostLine(
            quote_sheet_id=quote_sheet_id,
            section=section,
            category=category,
            label=label,
            one_time=amounts.get("one_time"),
            annual=amounts.get("annual"),
            monthly=amounts.get("monthly"),
            sort_order=sort_order,
        ))
    return rows
