# User Requirements Specification (URS)

## User Inputs

| Area | Details |
|------|---------|
| Intended use | {{ URS.intendedUse }} |
| Critical process parameters | {{ URS.criticalProcessParameters }} |
| Environmental needs | {{ URS.environmentNeeds }} |
| Throughput rationale | {{ URS.throughputRationale }} |
| Acceptance criteria | {{ URS.acceptanceCriteria }} |

## Selected URS Requirements

| URS ID | Title | Statement | Criticality | Regulatory tags |
|--------|-------|-----------|-------------|-----------------|
{% for r in URS.requirements %}
| {{ r.ursId }} | {{ r.title }} | {{ r.statement }} | {{ r.criticality }} | {{ r.regulatoryTags | join(", ") }} |
{% endfor %}
{% if not URS.requirements %}
| — | No URS selected | — | — | — |
{% endif %}
