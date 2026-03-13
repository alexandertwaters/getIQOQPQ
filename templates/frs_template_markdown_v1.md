# Functional Requirements Specification (FRS)

| FRS ID | Title | Functional requirement | Derived from URS | Regulatory tags |
|--------|-------|------------------------|------------------|-----------------|
{% for r in FRS.functions %}
| {{ r.frsId }} | {{ r.title }} | {{ r.functionalRequirement }} | {{ r.derivedFromURS | join(", ") }} | {{ r.regulatoryTags | join(", ") }} |
{% endfor %}
{% if not FRS.functions %}
| — | No FRS selected | — | — | — |
{% endif %}
