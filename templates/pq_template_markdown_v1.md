# Performance Qualification (PQ) Protocol

**PQ Plan:** {{ PQ.plan }}

**Planned PQ Runs:** {{ PQ.pqCycles }}

| Test | Objective | Setup | Steps | Data to record | Acceptance |
|------|-----------|-------|-------|----------------|------------|
{% for t in PQ.tests %}
| {{ t.title }} | {{ t.objective }} | {{ t.setup }} | {% for s in t.steps %}{{ s }}{% if not loop.last %}; {% endif %}{% endfor %} | {{ t.dataToRecord }} | {{ t.acceptanceCriteria }} |
{% endfor %}
{% if not PQ.tests %}
| — | No PQ tests mapped | — | — | — | — |
{% endif %}
