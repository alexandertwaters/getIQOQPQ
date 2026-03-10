'use client'

import { useState, useEffect } from 'react'

const API = `${process.env.NEXT_PUBLIC_API_URL || ''}/api/v1`

type Cohort = { cohortId: string; equipmentTypes: { equipmentTypeId: string; equipmentType: string }[] }
type Hazard = {
  hazardId: string
  title: string
  definition: string
  severityOptions?: { label: string }[]
  probabilityOptions?: { label: string }[]
  exposureOptions?: { label: string }[]
  detectabilityOptions?: { label: string }[]
  controlEffectivenessOptions?: { label: string }[]
  contextualTags?: string[]
  quickDefaults?: Record<string, string>
}

export default function WizardPage() {
  const [step, setStep] = useState(1)
  const [cohorts, setCohorts] = useState<Cohort[]>([])
  const [hazards, setHazards] = useState<Hazard[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Form state
  const [selectedCohort, setSelectedCohort] = useState('')
  const [selectedEquipment, setSelectedEquipment] = useState<{ id: string; name: string } | null>(null)
  const [equipmentId, setEquipmentId] = useState('')
  const [siteContext, setSiteContext] = useState({
    cleanroomClass: 'ISO 7',
    utilities: ['Steam', 'Electricity'] as string[],
    productContact: true,
    productionThroughput: 'Medium',
  })
  const [hazardRatings, setHazardRatings] = useState<Record<string, Record<string, string>>>({})
  const [catalog, setCatalog] = useState({ hazcatVersion: 'hazcat_v1.1', rulesetId: 'ruleset_v1.1' })

  // Result state
  const [generating, setGenerating] = useState(false)
  const [result, setResult] = useState<{ fingerprint: string; artifactPath: string } | null>(null)
  const [artifactUrls, setArtifactUrls] = useState<Record<string, string> | null>(null)

  useEffect(() => {
    fetch(`${API}/equipment-types`).then(r => r.json()).then(d => setCohorts(d.cohorts || [])).catch(e => setError(e.message)).finally(() => setLoading(false))
    fetch(`${API}/catalog/version`).then(r => r.json()).then(setCatalog).catch(() => {})
  }, [])

  useEffect(() => {
    if (!selectedEquipment) return
    fetch(`${API}/hazards?equipmentTypeId=${selectedEquipment.id}`)
      .then(r => r.json())
      .then(d => {
        const h = d.hazards || []
        setHazards(h)
        const ratings: Record<string, Record<string, string>> = {}
        h.forEach((x: Hazard) => {
          ratings[x.hazardId] = {
            Severity_label: x.quickDefaults?.defaultSeverity || '',
            ProbabilityOfOccurrence_label: x.quickDefaults?.defaultProbability || '',
            Exposure_label: x.quickDefaults?.defaultExposure || '',
            Detectability_label: x.quickDefaults?.defaultDetectability || '',
            ControlEffectiveness_label: x.quickDefaults?.defaultControlEffectiveness || '',
          }
        })
        setHazardRatings(ratings)
      })
  }, [selectedEquipment])

  const toggleUtility = (u: string) => {
    setSiteContext(s => ({ ...s, utilities: s.utilities.includes(u) ? s.utilities.filter(x => x !== u) : [...s.utilities, u] }))
  }

  const setHazardRating = (hazardId: string, field: string, value: string) => {
    setHazardRatings(r => ({ ...r, [hazardId]: { ...(r[hazardId] || {}), [field]: value } }))
  }

  const canGenerate = () => {
    if (!selectedEquipment || !catalog.rulesetId || !catalog.hazcatVersion) return false
    for (const h of hazards) {
      const r = hazardRatings[h.hazardId]
      if (!r?.Severity_label || !r?.ProbabilityOfOccurrence_label || !r?.Exposure_label || !r?.Detectability_label || !r?.ControlEffectiveness_label) return false
    }
    return true
  }

  const handleGenerate = async () => {
    if (!canGenerate() || !selectedEquipment) return
    setGenerating(true)
    setError(null)
    try {
      const payload = {
        equipmentId: equipmentId || `E-${selectedEquipment.id}-001`,
        cohort: selectedCohort,
        type: selectedEquipment.name,
        siteContext,
        controlArchitecture: 'PLC or SCADA',
        hazards: hazards.map(h => ({
          hazardId: h.hazardId,
          title: h.title,
          definition: h.definition,
          contextualTags: h.contextualTags || [],
          ruleId: (h as Hazard & { ruleId?: string }).ruleId || '',
          ...hazardRatings[h.hazardId],
        })),
        rulesetId: catalog.rulesetId,
        hazcatVersion: catalog.hazcatVersion,
      }
      const res = await fetch(`${API}/generate`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.error || `HTTP ${res.status}`)
      }
      const data = await res.json()
      setResult(data)
      const artRes = await fetch(`${API}/artifact?fingerprint=${encodeURIComponent(data.fingerprint)}`)
      const artData = await artRes.json()
      setArtifactUrls(artData.files || {})
      setStep(5)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Generation failed')
    } finally {
      setGenerating(false)
    }
  }

  if (loading) return <div className="flex min-h-screen items-center justify-center"><div className="text-slate-500">Loading...</div></div>

  return (
    <div className="mx-auto max-w-2xl px-4 py-12">
      <header className="mb-10">
        <h1 className="text-2xl font-bold text-slate-800">IQ/OQ/PQ Generator</h1>
        <p className="mt-1 text-slate-500">Create advisory qualification packages</p>
      </header>

      {error && <div className="mb-6 rounded-lg bg-red-50 p-4 text-red-700">{error}</div>}

      {/* Step indicator */}
      <div className="mb-8 flex gap-2">
        {[1, 2, 3, 4].map(s => (
          <button key={s} onClick={() => setStep(s)} className={`rounded px-3 py-1 text-sm font-medium ${step === s ? 'bg-slate-800 text-white' : 'bg-slate-200 text-slate-600 hover:bg-slate-300'}`}>
            {s === 1 ? 'Equipment' : s === 2 ? 'Site' : s === 3 ? 'Hazards' : 'Review'}
          </button>
        ))}
      </div>

      {/* Step 1: Equipment */}
      {step === 1 && (
        <div className="space-y-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold">Select equipment</h2>
          {cohorts.map(c => (
            <div key={c.cohortId}>
              <label className="block text-sm font-medium text-slate-600">{c.cohortId}</label>
              <div className="mt-2 flex flex-wrap gap-2">
                {c.equipmentTypes.map(et => (
                  <button
                    key={et.equipmentTypeId}
                    onClick={() => { setSelectedCohort(c.cohortId); setSelectedEquipment({ id: et.equipmentTypeId, name: et.equipmentType }); setStep(2) }}
                    className="rounded-lg border border-slate-200 px-4 py-2 text-left text-sm hover:border-slate-400 hover:bg-slate-50"
                  >
                    {et.equipmentType}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Step 2: Site context */}
      {step === 2 && selectedEquipment && (
        <div className="space-y-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold">Site context</h2>
          <p className="text-sm text-slate-500">Equipment: {selectedEquipment.name}</p>
          <div>
            <label className="block text-sm font-medium">Equipment ID</label>
            <input type="text" value={equipmentId} onChange={e => setEquipmentId(e.target.value)} placeholder="e.g. E-STER-PV-001" className="mt-1 w-full rounded border border-slate-200 px-3 py-2" />
          </div>
          <div>
            <label className="block text-sm font-medium">Cleanroom class</label>
            <select value={siteContext.cleanroomClass} onChange={e => setSiteContext(s => ({ ...s, cleanroomClass: e.target.value }))} className="mt-1 w-full rounded border border-slate-200 px-3 py-2">
              {['ISO 5', 'ISO 6', 'ISO 7', 'ISO 8'].map(v => <option key={v} value={v}>{v}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium">Utilities</label>
            <div className="mt-2 flex flex-wrap gap-2">
              {['Steam', 'Electricity', 'Compressed Air', 'WFI', 'Nitrogen'].map(u => (
                <label key={u} className="flex cursor-pointer items-center gap-2 rounded border border-slate-200 px-3 py-2 hover:bg-slate-50">
                  <input type="checkbox" checked={siteContext.utilities.includes(u)} onChange={() => toggleUtility(u)} />
                  <span>{u}</span>
                </label>
              ))}
            </div>
          </div>
          <div>
            <label className="flex cursor-pointer items-center gap-2"><input type="checkbox" checked={siteContext.productContact} onChange={e => setSiteContext(s => ({ ...s, productContact: e.target.checked }))} /> Product contact</label>
          </div>
          <div>
            <label className="block text-sm font-medium">Production throughput</label>
            <select value={siteContext.productionThroughput} onChange={e => setSiteContext(s => ({ ...s, productionThroughput: e.target.value }))} className="mt-1 w-full rounded border border-slate-200 px-3 py-2">
              {['Low', 'Medium', 'High'].map(v => <option key={v} value={v}>{v}</option>)}
            </select>
          </div>
          <div className="flex gap-2">
            <button onClick={() => setStep(1)} className="rounded bg-slate-200 px-4 py-2 text-sm font-medium hover:bg-slate-300">Back</button>
            <button onClick={() => setStep(3)} className="rounded bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700">Next</button>
          </div>
        </div>
      )}

      {/* Step 3: Hazards */}
      {step === 3 && selectedEquipment && (
        <div className="space-y-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold">Configure hazards</h2>
          {hazards.length === 0 && <p className="text-slate-500">Loading hazards...</p>}
          {hazards.map(h => (
            <div key={h.hazardId} className="rounded-lg border border-slate-100 bg-slate-50 p-4">
              <h3 className="font-medium">{h.title}</h3>
              <p className="mt-1 text-sm text-slate-600">{h.definition}</p>
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                {[
                  { key: 'Severity_label', label: 'Severity', opts: h.severityOptions?.map(o => o.label) || [] },
                  { key: 'ProbabilityOfOccurrence_label', label: 'Probability', opts: h.probabilityOptions?.map(o => o.label) || [] },
                  { key: 'Exposure_label', label: 'Exposure', opts: h.exposureOptions?.map(o => o.label) || [] },
                  { key: 'Detectability_label', label: 'Detectability', opts: h.detectabilityOptions?.map(o => o.label) || [] },
                  { key: 'ControlEffectiveness_label', label: 'Control effectiveness', opts: h.controlEffectivenessOptions?.map(o => o.label) || [] },
                ].map(({ key, label, opts }) => (
                  <div key={key}>
                    <label className="block text-xs font-medium text-slate-500">{label}</label>
                    <select value={hazardRatings[h.hazardId]?.[key] || ''} onChange={e => setHazardRating(h.hazardId, key, e.target.value)} className="mt-0.5 w-full rounded border border-slate-200 px-2 py-1.5 text-sm">
                      <option value="">Select...</option>
                      {opts.map(o => <option key={o} value={o}>{o}</option>)}
                    </select>
                  </div>
                ))}
              </div>
            </div>
          ))}
          <div className="flex gap-2">
            <button onClick={() => setStep(2)} className="rounded bg-slate-200 px-4 py-2 text-sm font-medium hover:bg-slate-300">Back</button>
            <button onClick={() => setStep(4)} className="rounded bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700">Next</button>
          </div>
        </div>
      )}

      {/* Step 4: Review & Generate */}
      {step === 4 && selectedEquipment && (
        <div className="space-y-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold">Review and generate</h2>
          <dl className="space-y-1 text-sm">
            <dt className="font-medium text-slate-500">Equipment</dt>
            <dd>{selectedEquipment.name}</dd>
            <dt className="mt-2 font-medium text-slate-500">Site</dt>
            <dd>{siteContext.cleanroomClass}, {siteContext.utilities.join(', ')}, Product contact: {siteContext.productContact ? 'Yes' : 'No'}</dd>
            <dt className="mt-2 font-medium text-slate-500">Hazards</dt>
            <dd>{hazards.length} configured</dd>
          </dl>
          <div className="flex gap-2">
            <button onClick={() => setStep(3)} className="rounded bg-slate-200 px-4 py-2 text-sm font-medium hover:bg-slate-300">Back</button>
            <button onClick={handleGenerate} disabled={!canGenerate() || generating} className="rounded bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50">
              {generating ? 'Generating...' : 'Generate package'}
            </button>
          </div>
        </div>
      )}

      {/* Step 5: Results */}
      {step === 5 && result && (
        <div className="space-y-6 rounded-xl border border-emerald-200 bg-emerald-50/50 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-emerald-800">Package generated</h2>
          <p className="text-sm text-slate-600">Fingerprint: <code className="rounded bg-slate-100 px-1 py-0.5 text-xs">{result.fingerprint}</code></p>
          {artifactUrls && Object.keys(artifactUrls).length > 0 && (
            <div>
              <h3 className="mb-2 font-medium">Download</h3>
              <div className="flex flex-col gap-2">
                {Object.entries(artifactUrls).map(([name, url]) => (
                  typeof url === 'string' && !url.includes('error') ? (
                    <a key={name} href={url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 rounded bg-slate-800 px-4 py-2 text-sm text-white hover:bg-slate-700">
                      Download {name.endsWith('.json') ? 'JSON' : name.endsWith('.md') ? 'Markdown report' : 'CSV'}
                    </a>
                  ) : null
                ))}
              </div>
            </div>
          )}
          <button onClick={() => { setStep(1); setResult(null); setArtifactUrls(null) }} className="rounded bg-slate-200 px-4 py-2 text-sm font-medium hover:bg-slate-300">Create another</button>
        </div>
      )}
    </div>
  )
}
