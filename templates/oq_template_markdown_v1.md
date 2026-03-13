# Operational Qualification (OQ) Protocol

| Test | Objective | Setup | Steps | Data to record | Acceptance |
|------|-----------|-------|-------|----------------|------------|
{% for t in OQ.tests %}
| {{ t.title }} | {{ t.objective }} | {{ t.setup }} | {% for s in t.steps %}{{ s }}{% if not loop.last %}; {% endif %}{% endfor %} | {{ t.dataToRecord }} | {{ t.acceptanceCriteria }} |
{% endfor %}
{% if not OQ.tests %}
| — | No OQ tests mapped | — | — | — | — |
{% endif %}
