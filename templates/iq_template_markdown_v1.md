# Installation Qualification (IQ) Protocol

| Test | Objective | Setup | Steps | Data to record | Acceptance |
|------|-----------|-------|-------|----------------|------------|
{% for t in IQ.testScripts %}
| {{ t.title }} | {{ t.objective }} | {{ t.setup }} | {{ t.steps }} | {{ t.dataToRecord }} | {{ t.acceptanceCriteria }} |
{% endfor %}
{% if not IQ.testScripts %}
| — | No IQ tests mapped | — | — | — | — |
{% endif %}
