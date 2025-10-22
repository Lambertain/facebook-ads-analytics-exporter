const API_BASE = ''

export type ConfigMap = Record<string, { value: string; has_value: boolean; secret: boolean }>

export async function getConfig(): Promise<ConfigMap> {
  const r = await fetch(`${API_BASE}/api/config`)
  if (!r.ok) throw new Error('Failed to load config')
  return r.json()
}

export async function updateConfig(values: Record<string, string>): Promise<void> {
  const r = await fetch(`${API_BASE}/api/config`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(values)
  })
  if (!r.ok) throw new Error('Failed to update config')
}

export async function startJob(params: { start_date: string; end_date: string; sheet_id?: string }) {
  const r = await fetch(`${API_BASE}/api/start-job`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  })
  const data = await r.json()
  if (!r.ok) throw new Error(data.error || 'Failed to start job')
  return data as { job_id: string }
}

export async function runAnalytics(params: { campaign_type: 'teachers' | 'students'; date_start: string; date_stop: string }) {
  const r = await fetch(`${API_BASE}/api/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  })
  const data = await r.json()
  if (!r.ok) throw new Error(data.error || 'Failed to start analytics')
  return data as { job_id: string }
}

export function openEventStream(jobId: string, onLog: (s: string) => void, onProgress: (p: any) => void) {
  const es = new EventSource(`${API_BASE}/api/events/${jobId}`)
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
  const r = await fetch(`${API_BASE}/api/inspect/excel-headers`)
  return r.json()
}

export async function listNetHuntFolders() {
  const r = await fetch(`${API_BASE}/api/inspect/nethunt/folders`)
  return r.json()
}

export async function listAlfaCompanies() {
  const r = await fetch(`${API_BASE}/api/inspect/alfacrm/companies`)
  return r.json()
}

// Student data types (33 fields matching mapping.json)
export interface Student {
  "Посилання на рекламну компанію": string
  "Дата аналізу": string
  "Період аналізу запущеної компанії": string
  "Витрачений бюджет в $": number
  "Місце знаходження (країни чи міста)": string
  "Кількість лідів": number
  "Перевірка лідів автоматичний": string
  "Не розібрані": number
  "Встанов. контакт (ЦА)": number
  "В опрацюванні (ЦА)": number
  "Назначений пробний\n(ЦА)": number
  "Проведений пробний\n(ЦА)": number
  "Чекаємо оплату": number
  "Купили (ЦА)": number
  "Архів (ЦА)": number
  "Недозвон \n(не ЦА)": number
  "Архів\n (не ЦА)": number
  "Кількість цільових лідів": number
  "Кількість не цільових лідів": number
  "% цільових лідів": number
  "% не цільових лідів": number
  "% Встан. контакт": number
  "% В опрацюванні (ЦА)": number
  "% конверсія": number
  "% архів": number
  "% недозвон": number
  "Ціна / ліда": number
  "Ціна / цільового ліда": number
  "Нотатки": string
  "% Назначений пробний": number
  "%\nПроведений пробний від загальних лідів\n(ЦА)": number
  "%\nПроведений пробний від назначених пробних": number
  "Конверсія з проведеного пробного в продаж": number
}

export interface StudentsResponse {
  students: Student[]
  count: number
}

export async function getStudents(params?: {
  start_date?: string
  end_date?: string
  enrich?: boolean
}): Promise<StudentsResponse> {
  const queryParams = new URLSearchParams()
  if (params?.start_date) queryParams.append('start_date', params.start_date)
  if (params?.end_date) queryParams.append('end_date', params.end_date)
  if (params?.enrich !== undefined) queryParams.append('enrich', String(params.enrich))

  const url = `${API_BASE}/api/students${queryParams.toString() ? '?' + queryParams.toString() : ''}`
  const r = await fetch(url)
  if (!r.ok) throw new Error('Failed to load students data')
  return r.json()
}

// Meta Data types (matching backend /api/meta-data response)
export interface MetaAd {
  campaign_name: string
  campaign_id: string
  ad_name: string
  creative_image: string
  creative_text: string
  ctr: number
  cpm: number
  spend: number
  leads_count: string
  leads_target: string
  contacted: string
  in_progress: string
  trial_scheduled: string
  trial_completed: string
  awaiting_payment: string
  purchased: string
  archived: string
  not_reached: string
  archived_non_target: string
  target_leads_count: string
  non_target_leads_count: string
  target_leads_percent: string
  non_target_leads_percent: string
  contact_percent: string
  in_progress_percent: string
}

// СТРУКТУРА ТАБЛИЦІ: 35 КОЛОНОК A-AI + 2 ДОДАТКОВІ CRM СТАТУСИ
// Порядок відповідає специфікації "Анализ РК Студенти - Структура таблицы.md"
export interface MetaStudent {
  // ============ ОСНОВНА ІНФОРМАЦІЯ (A-F) - біла заливка ============
  campaign_name: string                      // A: Назва РК
  campaign_link: string                      // B: Посилання на РК
  analysis_date: string                      // C: Дата аналізу
  period: string                             // D: Період аналізу запущеної компанії
  budget: number                             // E: Витрачений бюджет в $
  location: string                           // F: Місце знаходження (країни чи міста)

  // ============ ДАНІ ПО ЛІДАМ (G) - світло-жовта заливка ============
  leads_count: string                        // G: Кількість лідів

  // ============ CRM СТАТУСИ (I-R) - світло-фіолетова/оранжева/світло-рожева ============
  "Не розібраний": number                    // I (світло-фіолетова)
  "Встановлено контакт (ЦА)": number         // J (світло-фіолетова)
  "В опрацюванні (ЦА)": number               // K (світло-фіолетова)
  "Призначено пробне (ЦА)": number           // L (оранжева) - Cumulative counting
  "Проведено пробне (ЦА)": number            // M (оранжева) - Cumulative counting
  "Чекає оплату": number                     // N (світло-фіолетова) - Cumulative counting
  "Отримана оплата (ЦА)": number             // O (світло-фіолетова)
  "Архів (ЦА)": number                       // P (світло-фіолетова)
  "Недозвон (не ЦА)": number                 // Q (світло-рожева)
  "Архів (не ЦА)": number                    // R (світло-рожева)

  // ============ РОЗРАХУНКОВІ МЕТРИКИ - КІЛЬКІСТЬ (S-T) ============
  target_leads: string                       // S: Кількість цільових лідів (світло-зелена)
  non_target_leads: string                   // T: Кількість не цільових лідів (світло-рожева)

  // ============ РОЗРАХУНКОВІ МЕТРИКИ - ВІДСОТКИ (U-AA) - світло-зелена/світло-жовта ============
  target_percent: string                     // U: % цільових лідів (світло-зелена)
  non_target_percent: string                 // V: % не цільових лідів (світло-зелена)
  contact_percent: string                    // W: % Встан. контакт (світло-жовта)
  in_progress_percent: string                // X: % В опрацюванні (ЦА) (світло-жовта)
  conversion_percent: string                 // Y: % конверсія (світло-жовта)
  archive_percent: string                    // Z: % архів (світло-жовта)
  not_reached_percent: string                // AA: % недозвон (світло-жовта)

  // ============ ФІНАНСОВІ ПОКАЗНИКИ (AB-AC) - світло-оранжева заливка ============
  cost_per_lead: string                      // AB: Ціна / ліда
  cost_per_target_lead: string               // AC: Ціна / цільового ліда

  // ============ ДОДАТКОВА ІНФОРМАЦІЯ (AD) - ярко-жовта заливка ============
  notes: string                              // AD: Нотатки

  // ============ ДОДАТКОВІ МЕТРИКИ ПРОБНИХ (AE-AH) - світло-фіолетова заливка ============
  trial_scheduled_percent: string            // AE: % Назначений пробний
  trial_completed_from_total_percent: string // AF: % Проведений пробний від загальних лідів
  trial_completed_from_scheduled_percent: string // AG: % Проведений пробний від назначених пробних
  trial_to_purchase_percent: string          // AH: Конверсія з проведеного пробного в продаж

  // ============ CPC (AI) - світло-фіолетова заливка ============
  cpc: number                                // AI: CPC (Cost Per Click)

  // ============ ДОДАТКОВІ CRM СТАТУСИ (поза A-AI) ============
  "Передзвонити пізніше": number
  "Старі клієнти": number
}

export interface MetaTeacher {
  campaign_name: string
  campaign_link: string
  analysis_date: string
  period: string
  budget: number
  location: string
  leads_count: string
  leads_check: string
  not_processed: string
  contacted: string
  in_progress: string
  trial_scheduled: string
  trial_completed: string
  awaiting_payment: string
  purchased: string
  archived: string
  not_reached: string
  archived_non_target: string
  target_leads: string
  non_target_leads: string
  target_percent: string
  non_target_percent: string
  contact_percent: string
  in_progress_percent: string
  conversion_percent: string
  archive_percent: string
  not_reached_percent: string
  cost_per_lead: string
  cost_per_target_lead: string
  notes: string
  trial_scheduled_percent: string
  trial_completed_from_total_percent: string
  trial_completed_from_scheduled_percent: string
  trial_to_purchase_percent: string
  // ДИНАМІЧНІ ПОЛЯ NetHunt CRM статусів
  // Статуси динамічно виявляються з реальних даних NetHunt API (не фіксований список)
  // Приклади: "Нові": 10, "Контакт встановлено": 8, "Кваліфіковані": 5, і т.д.
  [key: string]: string | number
}

export interface MetaDataResponse {
  ads: MetaAd[]
  students: MetaStudent[]
  teachers: MetaTeacher[]
  fetched_at: string
  period: string
}

export async function getMetaData(params: {
  start_date: string
  end_date: string
}): Promise<MetaDataResponse> {
  const queryParams = new URLSearchParams({
    start_date: params.start_date,
    end_date: params.end_date
  })

  const url = `${API_BASE}/api/meta-data?${queryParams.toString()}`
  const r = await fetch(url)
  if (!r.ok) throw new Error('Failed to load Meta data')
  return r.json()
}

export async function saveRunHistory(params: {
  start_date: string
  end_date: string
  insights_count: number
  students_count: number
  teachers_count: number
  status: 'success' | 'error'
  error_message?: string
}): Promise<{ success: boolean; run_id: number }> {
  const r = await fetch(`${API_BASE}/api/save-run-history`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  })
  if (!r.ok) throw new Error('Failed to save run history')
  return r.json()
}

export async function exportMetaExcel(data: {
  ads: MetaAd[]
  students: MetaStudent[]
  teachers: MetaTeacher[]
}): Promise<void> {
  const r = await fetch(`${API_BASE}/api/export-meta-excel`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  if (!r.ok) throw new Error('Failed to export Excel')

  const blob = await r.blob()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `ecademy_meta_data_${new Date().toISOString().slice(0, 10)}.xlsx`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  window.URL.revokeObjectURL(url)
}

// Lead Journey Tracking types
export interface JourneyStats {
  total_steps: number
  conversion_reached: boolean
  current_status: number
  current_status_name: string
  funnel_type: 'main' | 'secondary'
}

export interface EnrichedStudent {
  id: number
  name: string
  phone: string
  email: string
  lead_status_id: number
  journey_status_ids: number[]
  journey_status_names: string[]
  journey_stats: JourneyStats
  [key: string]: any
}

export interface StudentsWithJourneyResponse {
  students: EnrichedStudent[]
  count: number
  enrichment_info: {
    total_statuses_tracked: number
    funnels: string[]
  }
}

export async function getStudentsWithJourney(params?: {
  start_date?: string
  end_date?: string
}): Promise<StudentsWithJourneyResponse> {
  const queryParams = new URLSearchParams()
  if (params?.start_date) queryParams.append('start_date', params.start_date)
  if (params?.end_date) queryParams.append('end_date', params.end_date)

  const url = `${API_BASE}/api/students-with-journey${queryParams.toString() ? '?' + queryParams.toString() : ''}`
  const r = await fetch(url)
  if (!r.ok) throw new Error('Failed to load students with journey data')
  return r.json()
}

// Search History API
export async function saveSearchResults(params: {
  start_date: string
  end_date: string
  tab_type: 'ads' | 'students' | 'teachers'
  results_data: any[]
}): Promise<{ success: boolean; search_id: number }> {
  const r = await fetch(`${API_BASE}/api/save-search-results`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  })
  if (!r.ok) throw new Error('Failed to save search results')
  return r.json()
}

export interface SearchHistoryItem {
  id: number
  start_date: string
  end_date: string
  tab_type: 'ads' | 'students' | 'teachers'
  results_count: number
  created_at: string
}

export interface SearchHistoryResponse {
  success: boolean
  count: number
  history: SearchHistoryItem[]
}

export async function getSearchHistory(params?: {
  limit?: number
  tab_type?: 'ads' | 'students' | 'teachers'
}): Promise<SearchHistoryResponse> {
  const queryParams = new URLSearchParams()
  if (params?.limit) queryParams.append('limit', String(params.limit))
  if (params?.tab_type) queryParams.append('tab_type', params.tab_type)

  const url = `${API_BASE}/api/search-history${queryParams.toString() ? '?' + queryParams.toString() : ''}`
  const r = await fetch(url)
  if (!r.ok) throw new Error('Failed to load search history')
  return r.json()
}

export interface SearchResultsResponse {
  success: boolean
  id: number
  start_date: string
  end_date: string
  tab_type: 'ads' | 'students' | 'teachers'
  results_count: number
  results: any[]
  created_at: string
}

export async function getSearchResults(searchId: number): Promise<SearchResultsResponse> {
  const r = await fetch(`${API_BASE}/api/search-history/${searchId}`)
  if (!r.ok) throw new Error('Failed to load search results')
  return r.json()
}

