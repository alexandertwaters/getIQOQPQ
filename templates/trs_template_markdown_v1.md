# Technical Requirements Specification (TRS)

| TRS ID | Phase | Title | Objective | Acceptance criteria | Verifies FRS |
|--------|-------|-------|-----------|---------------------|--------------|
{% for t in TRS.tests %}
| {{ t.trsId }} | {{ t.verificationPhase }} | {{ t.title }} | {{ t.objective }} | {{ t.acceptanceCriteria }} | {{ t.verifiesFRS | join(", ") }} |
{% endfor %}
{% if not TRS.tests %}
| — | — | No TRS selected | — | — | — |
{% endif %}
