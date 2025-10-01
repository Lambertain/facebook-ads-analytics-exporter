export type ConfigMap = Record<string, { value: string; has_value: boolean; secret: boolean }>

export async function getConfig(): Promise<ConfigMap> {
  const r = await fetch('/api/config')
  if (!r.ok) throw new Error('Failed to load config')
  return r.json()
}

export async function updateConfig(values: Record<string, string>): Promise<void> {
  const r = await fetch('/api/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(values)
  })
  if (!r.ok) throw new Error('Failed to update config')
}

export async function startJob(params: { start_date: string; end_date: string; sheet_id?: string }) {
  const r = await fetch('/api/start-job', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  })
  const data = await r.json()
  if (!r.ok) throw new Error(data.error || 'Failed to start job')
  return data as { job_id: string }
}

export function openEventStream(jobId: string, onLog: (s: string) => void, onProgress: (p: any) => void) {
  const es = new EventSource(`/api/events/${jobId}`)
  es.addEventListener('log', e => onLog((e as MessageEvent).data))
  es.addEventListener('progress', e => {
    try {
      const p = JSON.parse((e as MessageEvent).data)
      onProgress(p)
    } catch {}
  })
  es.onerror = () => es.close()
  return es
}

export async function inspectExcelHeaders() {
  const r = await fetch('/api/inspect/excel-headers')
  return r.json()
}

export async function listNetHuntFolders() {
  const r = await fetch('/api/inspect/nethunt/folders')
  return r.json()
}

export async function listAlfaCompanies() {
  const r = await fetch('/api/inspect/alfacrm/companies')
  return r.json()
}

