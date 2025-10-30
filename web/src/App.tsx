import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Alert, AppBar, Box, Button, Container, Dialog, DialogActions, DialogContent, DialogTitle,
  Grid2 as Grid, IconButton, LinearProgress, Snackbar, Tab, Tabs, TextField, Tooltip, Typography, InputAdornment,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Link, Checkbox
} from '@mui/material'
import HelpOutlineIcon from '@mui/icons-material/HelpOutline'
import FolderOpenIcon from '@mui/icons-material/FolderOpen'
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs'
import { DatePicker, LocalizationProvider } from '@mui/x-date-pickers'
import dayjs, { Dayjs } from 'dayjs'
import { ConfigMap, getConfig, inspectExcelHeaders, listAlfaCompanies, listNetHuntFolders, openEventStream, startJob, runAnalytics, updateConfig, getMetaData, exportMetaExcel, saveRunHistory, saveSearchResults, getSearchHistory, SearchHistoryItem, getSearchResults, SearchResultsResponse } from './api'
import StudentsTable from './StudentsTable'

type TabKey = 'instructions' | 'run' | 'settings' | 'history'
type DataTabKey = 'students' | 'teachers' | 'ads'

interface PipelineRun {
  id: number
  job_id: string
  start_time: string | null
  end_time: string | null
  status: string
  start_date: string
  end_date: string
  sheet_id: string | null
  storage_backend: string | null
  insights_count: number
  students_count: number
  teachers_count: number
  error_message: string | null
}

interface RunLog {
  id: number
  timestamp: string
  level: string
  message: string
}

function Help({ title, children }: { title: string, children: JSX.Element }) {
  const [open, setOpen] = useState(false)
  return (
    <>
      <Tooltip title={title}><IconButton size="small" onClick={() => setOpen(true)}><HelpOutlineIcon fontSize="small"/></IconButton></Tooltip>
      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{title}</DialogTitle>
        <DialogContent dividers>
          {children}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Зрозуміло</Button>
        </DialogActions>
      </Dialog>
    </>
  )
}

export default function App() {
  const [tab, setTab] = useState<TabKey>('instructions')
  const [dataTab, setDataTab] = useState<DataTabKey>('ads')
  const [cfg, setCfg] = useState<ConfigMap | null>(null)
  const [saving, setSaving] = useState(false)
  const [snack, setSnack] = useState<string | null>(null)

  const [start, setStart] = useState<Dayjs | null>(dayjs().startOf('month'))
  const [end, setEnd] = useState<Dayjs | null>(dayjs())
  const [sheetId, setSheetId] = useState('')
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState('idle')
  const [logs, setLogs] = useState<string[]>([])
  const esRef = useRef<EventSource | null>(null)

  // Data states
  const [studentsData, setStudentsData] = useState<any[]>([])
  const [teachersData, setTeachersData] = useState<any[]>([])
  const [adsData, setAdsData] = useState<any[]>([])
  const [filterInfo, setFilterInfo] = useState<any>(null)

  // History states (OLD - pipeline runs, keeping for reference)
  const [runs, setRuns] = useState<PipelineRun[]>([])
  const [selectedRun, setSelectedRun] = useState<{ run: PipelineRun; logs: RunLog[] } | null>(null)
  const [historyFilter, setHistoryFilter] = useState<string>('')
  const [selectedRunIds, setSelectedRunIds] = useState<Set<number>>(new Set())

  // NEW History states - search history
  const [searchHistory, setSearchHistory] = useState<SearchHistoryItem[]>([])
  const [selectedSearch, setSelectedSearch] = useState<SearchResultsResponse | null>(null)
  const [tabFilter, setTabFilter] = useState<'all' | 'ads' | 'students' | 'teachers'>('all')

  useEffect(() => { (async () => {
    try {
      const data = await getConfig()
      setCfg(data)
      if (data.GOOGLE_SHEET_ID?.value) setSheetId(data.GOOGLE_SHEET_ID.value)
    } catch (e) { setSnack('Не вдалося завантажити конфігурацію') }
  })() }, [])

  // Load NEW search history when history tab is opened or filter changes
  useEffect(() => {
    if (tab === 'history') {
      loadSearchHistory()
    }
  }, [tab, tabFilter])

  async function loadSearchHistory() {
    try {
      const params: any = { limit: 100 }
      if (tabFilter !== 'all') {
        params.tab_type = tabFilter
      }
      const data = await getSearchHistory(params)
      setSearchHistory(data.history || [])
    } catch (e) {
      setSnack('Не вдалося завантажити історію пошуків')
    }
  }

  async function loadRunDetails(runId: number) {
    try {
      const response = await fetch(`/api/runs/${runId}`)
      const data = await response.json()
      setSelectedRun(data)
    } catch (e) {
      setSnack('Не вдалося завантажити деталі запуску')
    }
  }

  function toggleRunSelection(runId: number) {
    setSelectedRunIds(prev => {
      const newSet = new Set(prev)
      if (newSet.has(runId)) {
        newSet.delete(runId)
      } else {
        newSet.add(runId)
      }
      return newSet
    })
  }

  function toggleAllRuns() {
    if (selectedRunIds.size === runs.length) {
      setSelectedRunIds(new Set())
    } else {
      setSelectedRunIds(new Set(runs.map(r => r.id)))
    }
  }

  async function deleteSelectedRuns() {
    console.log('Delete button clicked, selected IDs:', Array.from(selectedRunIds))

    if (selectedRunIds.size === 0) {
      setSnack('Виберіть записи для видалення')
      return
    }

    if (!window.confirm(`Видалити ${selectedRunIds.size} записів?`)) {
      console.log('User cancelled deletion')
      return
    }

    try {
      setSnack('Видалення записів...')

      const deletePromises = Array.from(selectedRunIds).map(async id => {
        console.log(`Deleting run ${id}...`)
        const response = await fetch(`/api/runs/${id}`, { method: 'DELETE' })
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}))
          throw new Error(errorData.error || `Помилка видалення запису ${id}`)
        }
        return response.json()
      })

      await Promise.all(deletePromises)
      console.log('All runs deleted successfully')

      setSnack(`Видалено ${selectedRunIds.size} записів`)
      setSelectedRunIds(new Set())
      setSelectedRun(null)
      await loadSearchHistory()
    } catch (e: any) {
      console.error('Delete error:', e)
      setSnack('Помилка видалення записів: ' + (e?.message || ''))
    }
  }

  // NEW function - load full search results details
  async function loadSearchResultsDetails(searchId: number) {
    try {
      const data = await getSearchResults(searchId)
      setSelectedSearch(data)
    } catch (e) {
      setSnack('Не вдалося завантажити деталі пошуку')
    }
  }

  // NEW function - download Excel using SAVED results (not re-fetching from Meta)
  async function onDownloadSearchExcel(search: SearchHistoryItem) {
    try {
      console.log('Downloading Excel for search:', search)

      // Завантажуємо ЗБЕРЕЖЕНІ результати з БД
      setSnack('Завантаження збережених результатів...')
      const searchResults = await getSearchResults(search.id)

      if (!searchResults.results || searchResults.results.length === 0) {
        setSnack('Немає даних для експорту')
        return
      }

      // Готуємо дані для експорту залежно від типу вкладки
      const exportData: any = {
        ads: [],
        students: [],
        teachers: []
      }

      if (searchResults.tab_type === 'ads') {
        exportData.ads = searchResults.results
      } else if (searchResults.tab_type === 'students') {
        exportData.students = searchResults.results
      } else if (searchResults.tab_type === 'teachers') {
        exportData.teachers = searchResults.results
      }

      setSnack('Генерація Excel файлу...')

      // Експортуємо в Excel
      await exportMetaExcel(exportData)

      setSnack(null)
    } catch (e: any) {
      console.error('Excel export error:', e)
      setSnack('Помилка завантаження: ' + (e?.message || e?.toString() || 'Невідома помилка'))
    }
  }

  const storageBackend = cfg?.STORAGE_BACKEND?.value || 'excel'

  async function onSave() {
    if (!cfg) return
    setSaving(true)
    try {
      const payload: Record<string,string> = {}
      for (const [k, v] of Object.entries(cfg)) {
        // Do not send masked secrets
        if (v.secret && v.value === '••••••••') continue
        payload[k] = v.value
      }
      await updateConfig(payload)
      setSnack('Налаштування збережено')
    } catch { setSnack('Помилка збереження налаштувань') }
    finally { setSaving(false) }
  }

  function updateField(key: string, value: string) {
    if (!cfg) return
    setCfg({ ...cfg, [key]: { ...cfg[key], value, has_value: !!value } })
  }

  async function onStart() {
    setLogs([])
    setProgress(5)
    setStatus('running')
    try {
      // Використовуємо новий єдиний endpoint /api/meta-data для всіх 3 вкладок
      const startDate = start?.format('YYYY-MM-DD') || ''
      const endDate = end?.format('YYYY-MM-DD') || ''

      setLogs(l => [...l, `Завантаження даних з Meta API за період ${startDate} - ${endDate}...`])
      setProgress(20)

      const metaData = await getMetaData({
        start_date: startDate,
        end_date: endDate
      })

      setProgress(60)
      setLogs(l => [...l, `Отримано рекламних кампаній: ${metaData.ads.length}`])
      setLogs(l => [...l, `Отримано студентських кампаній: ${metaData.students.length}`])
      setLogs(l => [...l, `Отримано викладацьких кампаній: ${metaData.teachers.length}`])

      // Оновлюємо всі 3 вкладки одночасно
      setAdsData(metaData.ads)
      setStudentsData(metaData.students)
      setTeachersData(metaData.teachers)
      setFilterInfo(metaData.filter_info || null)

      setProgress(100)
      setStatus('done')
      setLogs(l => [...l, `Завантаження завершено: ${metaData.fetched_at}`])
      setSnack('Дані успішно завантажено з Meta API')

      // Зберігаємо в історію
      try {
        await saveRunHistory({
          start_date: startDate,
          end_date: endDate,
          insights_count: metaData.ads.length,
          students_count: metaData.students.length,
          teachers_count: metaData.teachers.length,
          status: 'success'
        })
      } catch (e) {
        console.error('Failed to save history:', e)
      }

      // Зберігаємо результати кожної вкладки окремо в нову БД search_history
      try {
        setLogs(l => [...l, 'Збереження результатів у БД...'])

        const savePromises = []

        if (metaData.ads.length > 0) {
          savePromises.push(
            saveSearchResults({
              start_date: startDate,
              end_date: endDate,
              tab_type: 'ads',
              results_data: metaData.ads
            })
          )
        }

        if (metaData.students.length > 0) {
          savePromises.push(
            saveSearchResults({
              start_date: startDate,
              end_date: endDate,
              tab_type: 'students',
              results_data: metaData.students
            })
          )
        }

        if (metaData.teachers.length > 0) {
          savePromises.push(
            saveSearchResults({
              start_date: startDate,
              end_date: endDate,
              tab_type: 'teachers',
              results_data: metaData.teachers
            })
          )
        }

        await Promise.all(savePromises)
        setLogs(l => [...l, `Результати збережено в БД: ${savePromises.length} вкладок`])
      } catch (e) {
        console.error('Failed to save search results:', e)
        setLogs(l => [...l, `Помилка збереження результатів: ${e}`])
      }

    } catch (e: any) {
      setSnack('Не вдалося запустити завдання: ' + (e?.message || ''))
      setStatus('error')
      setLogs(l => [...l, `Помилка: ${e?.message || ''}`])

      // Зберігаємо помилку в історію
      try {
        await saveRunHistory({
          start_date: start?.format('YYYY-MM-DD') || '',
          end_date: end?.format('YYYY-MM-DD') || '',
          insights_count: 0,
          students_count: 0,
          teachers_count: 0,
          status: 'error',
          error_message: e?.message || 'Unknown error'
        })
      } catch (err) {
        console.error('Failed to save error history:', err)
      }
    }
  }

  async function onInspectHeaders() {
    const res = await inspectExcelHeaders()
    setLogs(l => [...l, 'Excel headers: ' + JSON.stringify(res)])
  }
  async function onListNetHunt() {
    const res = await listNetHuntFolders()
    setLogs(l => [...l, 'NetHunt folders: ' + JSON.stringify(res)])
  }

  async function onClearResults() {
    if (status !== 'done') {
      setSnack('Немає завершених результатів для очищення')
      return
    }
    // Очищуємо стан
    setStudentsData([])
    setTeachersData([])
    setAdsData([])
    setProgress(0)
    setStatus('idle')
    setLogs([])
    setSnack('Результати очищено та перенесено в історію')
    // Перезавантажуємо історію пошуків
    loadSearchHistory()
  }

  async function onDownloadExcel() {
    if (status !== 'done') {
      setSnack('Спочатку запустіть процес і дочекайтесь завершення')
      return
    }
    if (adsData.length === 0 && studentsData.length === 0 && teachersData.length === 0) {
      setSnack('Немає даних для експорту')
      return
    }
    try {
      await exportMetaExcel({
        ads: adsData,
        students: studentsData,
        teachers: teachersData
      })
      setSnack('Excel файл завантажено')
    } catch (e: any) {
      setSnack('Помилка завантаження: ' + (e?.message || ''))
    }
  }

  async function onDownloadHistoryExcel(run: PipelineRun) {
    try {
      console.log('Downloading Excel for run:', run)

      if (!run.start_date || !run.end_date) {
        setSnack('Помилка: відсутні дати в записі історії')
        return
      }

      // Показуємо прогрес
      const loadingSnack = 'Отримання даних з Meta API...'
      setSnack(loadingSnack)

      // Перезавантажуємо дані з Meta API за той самий період
      const metaData = await getMetaData({
        start_date: run.start_date,
        end_date: run.end_date
      })

      console.log('Meta data received:', metaData)

      if ((!metaData.ads || metaData.ads.length === 0) &&
          (!metaData.students || metaData.students.length === 0) &&
          (!metaData.teachers || metaData.teachers.length === 0)) {
        setSnack('Немає даних для експорту за цей період')
        return
      }

      // Показуємо що генеруємо файл
      setSnack('Генерація Excel файлу...')

      // Експортуємо в Excel - це завантажить файл автоматично
      await exportMetaExcel({
        ads: metaData.ads || [],
        students: metaData.students || [],
        teachers: metaData.teachers || []
      })

      // Успішно - закриваємо snackbar
      setSnack(null)
    } catch (e: any) {
      console.error('Excel export error:', e)
      setSnack('Помилка завантаження: ' + (e?.message || e?.toString() || 'Невідома помилка'))
    }
  }

  const runTab = (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <Box sx={{ mt: 2 }}>
        {/* Керування та прогрес */}
        <Grid container spacing={2} alignItems="center">
          <Grid xs={12} md={4}>
            <DatePicker
              label="Період з"
              value={start}
              onChange={setStart}
              format="YYYY-MM-DD"
              slotProps={{ textField: { size: 'medium' } }}
            />
          </Grid>
          <Grid xs={12} md={4}>
            <DatePicker
              label="Період до"
              value={end}
              onChange={setEnd}
              format="YYYY-MM-DD"
              slotProps={{ textField: { size: 'medium' } }}
            />
          </Grid>
          <Grid xs={12}>
            <Button variant="contained" onClick={onStart} size="medium">Старт</Button>
            <Button sx={{ ml: 1 }} variant="outlined" color="success" onClick={onDownloadExcel} disabled={status !== 'done'} size="medium">
              Завантажити Excel
            </Button>
            <Button sx={{ ml: 1 }} variant="outlined" color="error" onClick={onClearResults} disabled={status !== 'done'} size="medium">
              Очистити
            </Button>
          </Grid>
          <Grid xs={12}>
            <Box sx={{ display:'flex', alignItems:'center', gap:2 }}>
              <Box sx={{ flex: 1 }}>
                <LinearProgress
                  variant={progress > 0 && progress < 100 ? "determinate" : "indeterminate"}
                  value={progress}
                  sx={{ height: 10, borderRadius: 1 }}
                />
              </Box>
              <Typography variant="body2" sx={{ minWidth: 60, textAlign: 'right' }}>
                {progress > 0 ? `${progress}%` : ''}
              </Typography>
              <Typography
                variant="body2"
                sx={{
                  minWidth: 80,
                  color: status === 'done' ? 'success.main' : status === 'error' ? 'error.main' : 'text.secondary'
                }}
              >
                {status === 'idle' ? 'Очікування' : status === 'running' ? 'Виконується' : status === 'done' ? 'Завершено' : status}
              </Typography>
            </Box>
          </Grid>
        </Grid>

        {/* Вкладки з даними */}
        <Box sx={{ mt: 3 }}>
          <Tabs value={dataTab} onChange={(_,v)=>setDataTab(v)} sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tab label="Реклама" value="ads" />
            <Tab label="Студенти" value="students" />
            <Tab label="Викладачі" value="teachers" />
          </Tabs>

          <Box sx={{ mt: 2 }}>
            {dataTab === 'ads' && (
              <>
                {adsData.length === 0 && (
                  <Alert severity="info" sx={{ mb: 2 }}>Немає даних реклами</Alert>
                )}
                <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
                  <Table size="small" stickyHeader>
                    <TableHead>
                      <TableRow>
                        <TableCell>Назва РК</TableCell>
                        <TableCell>Період аналізу</TableCell>
                        <TableCell>Дата первинного аналізу</TableCell>
                        <TableCell>Дата вторинного аналізу</TableCell>
                        <TableCell>Дата оновлення інформації</TableCell>
                        <TableCell>Назва Оголошень компаній</TableCell>
                        <TableCell>Креатив (картинка)</TableCell>
                        <TableCell>Текст до картинки креативу</TableCell>
                        <TableCell>CTR (%)</TableCell>
                        <TableCell>CPL ($)</TableCell>
                        <TableCell>CPM ($)</TableCell>
                        <TableCell>Витрачено ($)</TableCell>
                        <TableCell>Кількість лідів</TableCell>
                        <TableCell>Кількість цільових лідів</TableCell>
                        <TableCell>Кількість не цільових лідів</TableCell>
                        <TableCell>Кількість не дозвонів</TableCell>
                        <TableCell>Кількість в опрацюванні</TableCell>
                        <TableCell>% цільових лідів</TableCell>
                        <TableCell>% Не цільових лідів</TableCell>
                        <TableCell>% Не дозвонів</TableCell>
                        <TableCell>% В опрацюванні</TableCell>
                        <TableCell>Ціна в $ за ліда</TableCell>
                        <TableCell>Ціна в $ за цільового ліда</TableCell>
                        <TableCell>Рекомендація</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {adsData.map((row, i) => (
                        <TableRow key={i}>
                          <TableCell>
                            <Link
                              href={`https://facebook.com/campaign/${row.campaign_id}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              sx={{ textDecoration: 'none', '&:hover': { textDecoration: 'underline' } }}
                            >
                              {row.campaign_name || row.campaign_id || "Без назви"}
                            </Link>
                          </TableCell>
                          <TableCell>{row.period || '-'}</TableCell>
                          <TableCell>{row.first_analysis_date || '-'}</TableCell>
                          <TableCell>{row.last_analysis_date || '-'}</TableCell>
                          <TableCell>{row.date_update || '-'}</TableCell>
                          <TableCell>{row.ad_name || '-'}</TableCell>
                          <TableCell>
                            {row.creative_image || row.image_url ? (
                              <img src={row.creative_image || row.image_url} alt="Creative" style={{ maxWidth: '100px', maxHeight: '60px', objectFit: 'contain' }} />
                            ) : '-'}
                          </TableCell>
                          <TableCell>{row.creative_text || row.creative_body || '-'}</TableCell>
                          <TableCell>{row.ctr || 0}</TableCell>
                          <TableCell>{row.cpl || 0}</TableCell>
                          <TableCell>{row.cpm || 0}</TableCell>
                          <TableCell>{row.spend || 0}</TableCell>
                          <TableCell>{row.leads_count || 0}</TableCell>
                          <TableCell>{row.leads_target || 0}</TableCell>
                          <TableCell>{row.leads_non_target || 0}</TableCell>
                          <TableCell>{row.leads_no_answer || 0}</TableCell>
                          <TableCell>{row.leads_in_progress || 0}</TableCell>
                          <TableCell>{row.percent_target || 0}</TableCell>
                          <TableCell>{row.percent_non_target || 0}</TableCell>
                          <TableCell>{row.percent_no_answer || 0}</TableCell>
                          <TableCell>{row.percent_in_progress || 0}</TableCell>
                          <TableCell>{row.price_per_lead || 0}</TableCell>
                          <TableCell>{row.price_per_target_lead || 0}</TableCell>
                          <TableCell>{row.recommendation || '-'}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </>
            )}

            {dataTab === 'students' && (
              <StudentsTable students={studentsData} filterInfo={filterInfo} />
            )}

            {dataTab === 'teachers' && (
              <>
                {teachersData.length === 0 && (
                  <Alert severity="info" sx={{ mb: 2 }}>Немає даних викладачів</Alert>
                )}
                <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
                  <Table size="small" stickyHeader>
                    <TableHead>
                      <TableRow>
                        <TableCell>Назва кампанії</TableCell>
                        <TableCell>Дата аналізу</TableCell>
                        <TableCell>Період аналізу запущеної компанії</TableCell>
                        <TableCell>Витрачений бюджет в $</TableCell>
                        <TableCell>Місце знаходження (країни чи міста)</TableCell>
                        <TableCell>Кількість лідів</TableCell>
                        <TableCell>Не розібрані ліди (в процесі опрацювання)</TableCell>
                        <TableCell>Взяті в роботу (в процесі опрацювання)</TableCell>
                        <TableCell>Контакт (в процесі опрацювання) ЦА</TableCell>
                        <TableCell>НЕ дозвон (в процесі опрацювання) НЕ ЦА</TableCell>
                        <TableCell>Співбесіда (в процесі опрацювання) ЦА</TableCell>
                        <TableCell>СП проведено (в процесі опрацювання) ЦА</TableCell>
                        <TableCell>Не з'явився на СП (в процесі опрацювання) ЦА</TableCell>
                        <TableCell>Завуч затрвердив кандидата (в процесі опрацювання) ЦА</TableCell>
                        <TableCell>Завуч не затвердив кандидата (відмовився) ЦА</TableCell>
                        <TableCell>Переговори (в процесі опрацювання) ЦА</TableCell>
                        <TableCell>Стажування ЦА</TableCell>
                        <TableCell>Не має учнів ЦА</TableCell>
                        <TableCell>Вчитель ЦА</TableCell>
                        <TableCell>Втрачений (відмовився) ЦА</TableCell>
                        <TableCell>Резерв стажування (в процесі опрацювання) ЦА</TableCell>
                        <TableCell>Резерв дзвінок (в процесі опрацювання) ЦА</TableCell>
                        <TableCell>Офбординг (відмовився) ЦА</TableCell>
                        <TableCell>Звільнився (відмовився) ЦА</TableCell>
                        <TableCell>Втрачений не цільовий (не цільовий) НЕ ЦА</TableCell>
                        <TableCell>Втрачений недозвон (не цільовий) НЕ ЦА</TableCell>
                        <TableCell>Втрачений не актуально (не цільовий) НЕ ЦА</TableCell>
                        <TableCell>Втрачений мала зп (відмовився) ЦА</TableCell>
                        <TableCell>Втрачений назавжди (не цільовий) НЕ ЦА</TableCell>
                        <TableCell>Втрачений перевірити Вайбер (не цільовий) НЕ ЦА</TableCell>
                        <TableCell>Втрачений ігнорує (відмовився) ЦА</TableCell>
                        <TableCell>Кількість прийшов на співбесіду</TableCell>
                        <TableCell>Кількість які не потрапили в Бот ТГ</TableCell>
                        <TableCell>Кількість "відмовився" загалом</TableCell>
                        <TableCell>Кількість (в процесці опрацювання) загалом</TableCell>
                        <TableCell>Кількість на етапі "Стажування"</TableCell>
                        <TableCell>Кількість цільових лідів</TableCell>
                        <TableCell>Кількість не цільових лідів</TableCell>
                        <TableCell>Конверсія відмов (%)</TableCell>
                        <TableCell>Конверсія в опрацюванні (%)</TableCell>
                        <TableCell>Конверсія з ліда у СП (%)</TableCell>
                        <TableCell>Конверсія з ліда у стажера (%)</TableCell>
                        <TableCell>Конверсія з прийшов на співбесіду в стажування</TableCell>
                        <TableCell>% цільових лідів</TableCell>
                        <TableCell>% не цільових лідів</TableCell>
                        <TableCell>Ціна в $ за ліда</TableCell>
                        <TableCell>Ціна в $ за цільового ліда</TableCell>
                        <TableCell>Статус рекламної кампанії</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {teachersData.map((row, i) => (
                      <TableRow key={i}>
                        <TableCell>
                          <Link
                            href={row.campaign_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            sx={{ textDecoration: 'none', '&:hover': { textDecoration: 'underline' } }}
                          >
                            {row.campaign_name || "Без назви"}
                          </Link>
                        </TableCell>
                        <TableCell>{row.analysis_date}</TableCell>
                        <TableCell>{row.period}</TableCell>
                        <TableCell>{row.budget}</TableCell>
                        <TableCell>{row.location}</TableCell>
                        <TableCell>{row.leads_count}</TableCell>
                        <TableCell>{row.not_processed}</TableCell>
                        <TableCell>{row.contacted}</TableCell>
                        <TableCell>{row.contacted}</TableCell>
                        <TableCell>{row.not_reached}</TableCell>
                        <TableCell>{row.trial_scheduled}</TableCell>
                        <TableCell>{row.trial_completed}</TableCell>
                        <TableCell>-</TableCell>
                        <TableCell>-</TableCell>
                        <TableCell>-</TableCell>
                        <TableCell>-</TableCell>
                        <TableCell>-</TableCell>
                        <TableCell>-</TableCell>
                        <TableCell>-</TableCell>
                        <TableCell>-</TableCell>
                        <TableCell>-</TableCell>
                        <TableCell>-</TableCell>
                        <TableCell>-</TableCell>
                        <TableCell>-</TableCell>
                        <TableCell>-</TableCell>
                        <TableCell>-</TableCell>
                        <TableCell>-</TableCell>
                        <TableCell>-</TableCell>
                        <TableCell>-</TableCell>
                        <TableCell>-</TableCell>
                        <TableCell>-</TableCell>
                        <TableCell>-</TableCell>
                        <TableCell>{row.target_leads}</TableCell>
                        <TableCell>{row.non_target_leads}</TableCell>
                        <TableCell>-</TableCell>
                        <TableCell>{row.in_progress_percent}</TableCell>
                        <TableCell>-</TableCell>
                        <TableCell>-</TableCell>
                        <TableCell>-</TableCell>
                        <TableCell>{row.target_percent}</TableCell>
                        <TableCell>{row.non_target_percent}</TableCell>
                        <TableCell>{row.cost_per_lead}</TableCell>
                        <TableCell>{row.cost_per_target_lead}</TableCell>
                        <TableCell>-</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              </>
            )}
          </Box>
        </Box>

        {/* Логи */}
        <Box sx={{ mt: 3, bgcolor:'#f7f7f7', p:2, borderRadius:1, height:200, overflow:'auto', fontFamily:'monospace', whiteSpace:'pre-wrap' }}>
          {logs.map((l,i)=>(<div key={i}>[{new Date().toLocaleTimeString('uk-UA')}] {l}</div>))}
        </Box>
      </Box>
    </LocalizationProvider>
  )

  const historyTab = (
    <Box sx={{ mt: 2 }}>
      <Alert severity="success" sx={{ mb: 2 }}>
        <strong>Нова історія пошуків!</strong> Результати з усіх 3 вкладок (РЕКЛАМА, СТУДЕНТИ, ВЧИТЕЛИ) зберігаються в PostgreSQL базі даних.
        Ви можете переглядати і завантажувати збережені результати в будь-який час.
      </Alert>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 2 }}>
        <Typography variant="h5">Історія пошуків</Typography>
        <Button
          variant={tabFilter === 'all' ? 'contained' : 'outlined'}
          size="small"
          onClick={() => setTabFilter('all')}
        >
          Усі
        </Button>
        <Button
          variant={tabFilter === 'ads' ? 'contained' : 'outlined'}
          size="small"
          onClick={() => setTabFilter('ads')}
        >
          Реклама
        </Button>
        <Button
          variant={tabFilter === 'students' ? 'contained' : 'outlined'}
          size="small"
          onClick={() => setTabFilter('students')}
        >
          Студенти
        </Button>
        <Button
          variant={tabFilter === 'teachers' ? 'contained' : 'outlined'}
          size="small"
          onClick={() => setTabFilter('teachers')}
        >
          Вчителі
        </Button>
        <Button variant="outlined" size="small" onClick={loadSearchHistory}>Оновити</Button>
      </Box>

      <Grid container spacing={2}>
        {/* Список пошуків */}
        <Grid size={6}>
          <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Період</TableCell>
                  <TableCell>Тип вкладки</TableCell>
                  <TableCell>Записів</TableCell>
                  <TableCell>Дата створення</TableCell>
                  <TableCell>Дії</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {searchHistory.length === 0 ? (
                  <TableRow><TableCell colSpan={6} align="center">Немає історії пошуків</TableCell></TableRow>
                ) : searchHistory.map((search) => (
                  <TableRow
                    key={search.id}
                    hover
                    selected={selectedSearch?.id === search.id}
                    sx={{ cursor: 'pointer' }}
                    onClick={() => loadSearchResultsDetails(search.id)}
                  >
                    <TableCell>{search.id}</TableCell>
                    <TableCell>{search.start_date} - {search.end_date}</TableCell>
                    <TableCell>
                      <Box sx={{
                        display: 'inline-block',
                        px: 1,
                        py: 0.5,
                        borderRadius: 1,
                        fontSize: '0.75rem',
                        bgcolor: search.tab_type === 'ads' ? '#e3f2fd' : search.tab_type === 'students' ? '#f3e5f5' : '#fff3e0',
                        color: search.tab_type === 'ads' ? '#1565c0' : search.tab_type === 'students' ? '#6a1b9a' : '#e65100'
                      }}>
                        {search.tab_type === 'ads' ? 'РЕКЛАМА' : search.tab_type === 'students' ? 'СТУДЕНТИ' : 'ВЧИТЕЛІ'}
                      </Box>
                    </TableCell>
                    <TableCell>{search.results_count}</TableCell>
                    <TableCell sx={{ fontSize: '0.75rem' }}>
                      {new Date(search.created_at).toLocaleString('uk-UA')}
                    </TableCell>
                    <TableCell onClick={(e) => e.stopPropagation()}>
                      <Button
                        variant="outlined"
                        size="small"
                        color="success"
                        onClick={() => onDownloadSearchExcel(search)}
                      >
                        Excel
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Grid>

        {/* Деталі обраного пошуку */}
        <Grid size={6}>
          {selectedSearch ? (
            <Box>
              <Paper sx={{ p: 2, mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">Деталі пошуку #{selectedSearch.id}</Typography>
                  <Button
                    variant="contained"
                    color="success"
                    size="medium"
                    onClick={() => onDownloadSearchExcel({
                      id: selectedSearch.id,
                      start_date: selectedSearch.start_date,
                      end_date: selectedSearch.end_date,
                      tab_type: selectedSearch.tab_type,
                      results_count: selectedSearch.results_count,
                      created_at: selectedSearch.created_at
                    })}
                  >
                    Завантажити Excel
                  </Button>
                </Box>
                <Grid container spacing={1}>
                  <Grid size={6}><Typography variant="body2"><strong>Період:</strong> {selectedSearch.start_date} - {selectedSearch.end_date}</Typography></Grid>
                  <Grid size={6}><Typography variant="body2"><strong>Тип вкладки:</strong> {
                    selectedSearch.tab_type === 'ads' ? 'РЕКЛАМА' :
                    selectedSearch.tab_type === 'students' ? 'СТУДЕНТИ' : 'ВЧИТЕЛІ'
                  }</Typography></Grid>
                  <Grid size={6}><Typography variant="body2"><strong>Записів:</strong> {selectedSearch.results_count}</Typography></Grid>
                  <Grid size={6}><Typography variant="body2"><strong>Створено:</strong> {new Date(selectedSearch.created_at).toLocaleString('uk-UA')}</Typography></Grid>
                </Grid>
              </Paper>

              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>Попередній перегляд результатів</Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                  Показано перші 5 записів з {selectedSearch.results_count}
                </Typography>
                <Box sx={{ maxHeight: 400, overflow: 'auto', fontFamily: 'monospace', fontSize: '0.75rem', bgcolor: '#f7f7f7', p: 1, borderRadius: 1 }}>
                  {selectedSearch.results.slice(0, 5).map((result: any, idx: number) => (
                    <Box key={idx} sx={{ mb: 1, pb: 1, borderBottom: idx < 4 ? '1px solid #ddd' : 'none' }}>
                      <strong>Запис #{idx + 1}:</strong>
                      <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>
                        {JSON.stringify(result, null, 2)}
                      </pre>
                    </Box>
                  ))}
                  {selectedSearch.results_count > 5 && (
                    <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mt: 1, textAlign: 'center' }}>
                      ... ще {selectedSearch.results_count - 5} записів (завантажте Excel для перегляду всіх)
                    </Typography>
                  )}
                </Box>
              </Paper>
            </Box>
          ) : (
            <Paper sx={{ p: 3, textAlign: 'center' }}>
              <Typography variant="body1" color="textSecondary">Оберіть пошук зі списку для перегляду деталей</Typography>
            </Paper>
          )}
        </Grid>
      </Grid>
    </Box>
  )

  const instructionsTab = (
    <Box sx={{ mt: 2 }}>
      <Typography variant="h4" sx={{ mb: 3 }}>Як користуватись системою eCademy Analytics</Typography>

      <Typography variant="h6" sx={{ mt: 3, mb: 2 }}>1. Налаштування</Typography>
      <Typography paragraph>
        Перейдіть у вкладку <strong>Налаштування</strong> та заповніть необхідні дані:
      </Typography>
      <Box component="ul" sx={{ pl: 3 }}>
        <li><strong>META_ACCESS_TOKEN</strong> - токен доступу до Facebook Meta API (отримайте в Meta for Developers)</li>
        <li><strong>META_AD_ACCOUNT_ID</strong> - ID рекламного акаунту (формат: act_XXXXX)</li>
        <li><strong>NETHUNT_BASIC_AUTH</strong> - токен Basic авторизації для NetHunt CRM (викладачі)</li>
        <li><strong>NETHUNT_FOLDER_ID</strong> - ID папки NetHunt для викладачів</li>
        <li><strong>ALFACRM_BASE_URL, ALFACRM_EMAIL, ALFACRM_API_KEY, ALFACRM_COMPANY_ID</strong> - дані AlfaCRM (студенти)</li>
        <li><strong>Ключові слова</strong> - слова для фільтрації кампаній викладачів та студентів</li>
      </Box>

      <Typography variant="h6" sx={{ mt: 3, mb: 2 }}>2. Збір даних з Meta Ads</Typography>
      <Typography paragraph>
        У вкладці <strong>Аналіз</strong>:
      </Typography>
      <Box component="ol" sx={{ pl: 3 }}>
        <li>Виберіть період дат (Період з → Період до)</li>
        <li>Натисніть кнопку <strong>Старт</strong></li>
        <li>Система автоматично завантажить дані з Meta API за вибраний період</li>
        <li>Дочекайтесь завершення процесу (прогрес-бар покаже 100%)</li>
      </Box>

      <Typography variant="h6" sx={{ mt: 3, mb: 2 }}>3. Перегляд результатів</Typography>
      <Typography paragraph>
        Після завершення збору даних ви побачите 3 вкладки з результатами:
      </Typography>
      <Box component="ul" sx={{ pl: 3 }}>
        <li><strong>РЕКЛАМА</strong> - детальна інформація по рекламних оголошеннях (CTR, CPM, витрати, креативи)</li>
        <li><strong>СТУДЕНТИ</strong> - статистика кампаній для студентів з аналізом лідів та конверсій</li>
        <li><strong>ВЧИТЕЛІ</strong> - статистика кампаній для викладачів з аналізом лідів та конверсій</li>
      </Box>
      <Typography paragraph>
        Всі таблиці мають вертикальний скрол для зручного перегляду великої кількості даних.
      </Typography>

      <Typography variant="h6" sx={{ mt: 3, mb: 2 }}>4. Експорт даних в Excel</Typography>
      <Typography paragraph>
        Після завершення збору даних натисніть кнопку <strong>Завантажити Excel</strong> поряд з кнопкою Старт.
      </Typography>
      <Typography paragraph>
        Ви отримаєте Excel файл з 3 листами:
      </Typography>
      <Box component="ul" sx={{ pl: 3 }}>
        <li><strong>Реклама</strong> (сині заголовки) - всі дані по оголошеннях</li>
        <li><strong>Студенти</strong> (зелені заголовки) - всі дані по студентським кампаніям</li>
        <li><strong>Вчителі</strong> (помаранчеві заголовки) - всі дані по викладацьким кампаніям</li>
      </Box>

      <Typography variant="h6" sx={{ mt: 3, mb: 2 }}>5. Історія запусків</Typography>
      <Typography paragraph>
        У вкладці <strong>Історія</strong> ви можете переглянути всі попередні запуски системи та їх результати.
      </Typography>

      <Typography variant="h6" sx={{ mt: 3, mb: 2 }}>Майбутні можливості (при повних правах API)</Typography>
      <Typography paragraph>
        При наявності розширених прав Meta API токена стане доступним:
      </Typography>
      <Box component="ul" sx={{ pl: 3 }}>
        <li>Автоматичне завантаження номерів телефонів лідів з груп оголошень</li>
        <li>Інтеграція з NetHunt CRM для автоматичного збагачення даних викладачів</li>
        <li>Інтеграція з AlfaCRM для автоматичного збагачення даних студентів</li>
        <li>Детальна аналітика по статусам лідів у воронці продажів</li>
        <li>Автоматичний розрахунок конверсій та вартості цільового ліда</li>
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mt: 4, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
        <strong>Примітка:</strong> На даний момент система працює з обмеженими правами Meta API токена.
        Для повної функціональності необхідно отримати токен з правами ads_read, leads_retrieval та доступом до сторінок/акаунту.
      </Typography>
    </Box>
  )

  const settingsTab = cfg && (
    <Box sx={{ mt: 2, maxWidth: 600 }}>
      {/* Facebook */}
      <Typography variant="h6" sx={{ mb: 2 }}>Facebook</Typography>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <TextField type="password" fullWidth label="META_ACCESS_TOKEN" value={cfg.META_ACCESS_TOKEN?.value || ''} onChange={e=>updateField('META_ACCESS_TOKEN', e.target.value)} />
        <Help title="Де взяти токен?">
          <Typography>Meta for Developers → Marketing API → System User or App → Generate access token з потрібними правами (ads_read, leads_retrieval та доступ до сторінок/акаунту).</Typography>
        </Help>
      </Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <TextField fullWidth label="META_AD_ACCOUNT_ID (act_*)" value={cfg.META_AD_ACCOUNT_ID?.value || ''} onChange={e=>updateField('META_AD_ACCOUNT_ID', e.target.value)} />
        <Help title="Де взяти act_*?">
          <Typography>В Ads Manager в URL (act_XXXX) або через API: GET /me/adaccounts.</Typography>
        </Help>
      </Box>

      {/* NetHunt */}
      <Typography variant="h6" sx={{ mb: 2, mt: 3 }}>NetHunt (Викладачі)</Typography>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <TextField type="password" fullWidth label="NETHUNT_BASIC_AUTH (Basic ...)" value={cfg.NETHUNT_BASIC_AUTH?.value || ''} onChange={e=>updateField('NETHUNT_BASIC_AUTH', e.target.value)} />
        <Help title="Де взяти Basic?">
          <Typography>В NetHunt: використовуйте email та API ключ. Формат заголовка: Basic base64(email:api_key). Можна сформувати в будь-якому Base64-генераторі.</Typography>
        </Help>
      </Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <TextField fullWidth label="NETHUNT_FOLDER_ID" value={cfg.NETHUNT_FOLDER_ID?.value || ''} onChange={e=>updateField('NETHUNT_FOLDER_ID', e.target.value)} />
        <Help title="Де взяти folder_id?">
          <Typography>Натисніть «NetHunt папки» у вкладці Аналіз — візьміть ID потрібної папки для викладачів.</Typography>
        </Help>
      </Box>

      {/* AlfaCRM */}
      <Typography variant="h6" sx={{ mb: 2, mt: 3 }}>AlfaCRM (Студенти)</Typography>
      <TextField fullWidth label="ALFACRM_BASE_URL" value={cfg.ALFACRM_BASE_URL?.value || ''} onChange={e=>updateField('ALFACRM_BASE_URL', e.target.value)} sx={{ mb: 2 }} />
      <TextField fullWidth label="ALFACRM_EMAIL" value={cfg.ALFACRM_EMAIL?.value || ''} onChange={e=>updateField('ALFACRM_EMAIL', e.target.value)} sx={{ mb: 2 }} />
      <TextField type="password" fullWidth label="ALFACRM_API_KEY" value={cfg.ALFACRM_API_KEY?.value || ''} onChange={e=>updateField('ALFACRM_API_KEY', e.target.value)} sx={{ mb: 2 }} />
      <TextField fullWidth label="ALFACRM_COMPANY_ID" value={cfg.ALFACRM_COMPANY_ID?.value || ''} onChange={e=>updateField('ALFACRM_COMPANY_ID', e.target.value)} sx={{ mb: 3 }} />

      {/* Excel/Sheets Storage */}
      <Typography variant="h6" sx={{ mb: 2, mt: 3 }}>Сховище</Typography>
      <TextField fullWidth label="STORAGE_BACKEND (excel|sheets)" value={cfg.STORAGE_BACKEND?.value || ''} onChange={e=>updateField('STORAGE_BACKEND', e.target.value)} sx={{ mb: 2 }} />
      { (cfg.STORAGE_BACKEND?.value || 'excel') === 'excel' ? (
        <>
          <TextField fullWidth label="EXCEL_CREATIVES_PATH" value={cfg.EXCEL_CREATIVES_PATH?.value || ''} onChange={e=>updateField('EXCEL_CREATIVES_PATH', e.target.value)} sx={{ mb: 2 }} />
          <TextField fullWidth label="EXCEL_STUDENTS_PATH" value={cfg.EXCEL_STUDENTS_PATH?.value || ''} onChange={e=>updateField('EXCEL_STUDENTS_PATH', e.target.value)} sx={{ mb: 2 }} />
          <TextField fullWidth label="EXCEL_TEACHERS_PATH" value={cfg.EXCEL_TEACHERS_PATH?.value || ''} onChange={e=>updateField('EXCEL_TEACHERS_PATH', e.target.value)} sx={{ mb: 3 }} />
        </>
      ) : (
        <>
          <TextField fullWidth label="GOOGLE_APPLICATION_CREDENTIALS (path to JSON)" value={cfg.GOOGLE_APPLICATION_CREDENTIALS?.value || ''} onChange={e=>updateField('GOOGLE_APPLICATION_CREDENTIALS', e.target.value)} sx={{ mb: 2 }} />
          <TextField fullWidth label="GOOGLE_SHEET_ID" value={cfg.GOOGLE_SHEET_ID?.value || ''} onChange={e=>updateField('GOOGLE_SHEET_ID', e.target.value)} sx={{ mb: 3 }} />
        </>
      )}

      <Typography variant="h6" sx={{ mt: 3, mb: 2 }}>Ключові слова для фільтрації кампаній</Typography>
      <TextField
        fullWidth
        label="Ключові слова для викладачів (через кому)"
        value={cfg.CAMPAIGN_KEYWORDS_TEACHERS?.value || ''}
        onChange={e=>updateField('CAMPAIGN_KEYWORDS_TEACHERS', e.target.value)}
        placeholder="Teacher,Vchitel"
        helperText="Введіть слова через кому. Кампанії з цими словами в назві будуть вважатись викладацькими."
        sx={{ mb: 2 }}
      />
      <TextField
        fullWidth
        label="Ключові слова для студентів (через кому)"
        value={cfg.CAMPAIGN_KEYWORDS_STUDENTS?.value || ''}
        onChange={e=>updateField('CAMPAIGN_KEYWORDS_STUDENTS', e.target.value)}
        placeholder="Student,Shkolnik"
        helperText="Введіть слова через кому. Кампанії з цими словами в назві будуть вважатись студентськими."
        sx={{ mb: 3 }}
      />

      <Button disabled={saving} variant="contained" onClick={onSave} sx={{ mt: 2 }}>Зберегти</Button>
    </Box>
  )

  return (
    <Box>
      <AppBar position="static">
        <Box sx={{ display: 'flex', alignItems: 'center', px: 2 }}>
          <Typography variant="h6" component="div" sx={{ mr: 'auto', fontWeight: 600 }}>
            eCademy analytics
          </Typography>
          <Tabs value={tab} onChange={(_,v)=>setTab(v)} textColor="inherit" indicatorColor="secondary">
            <Tab label="Як користуватись" value="instructions" />
            <Tab label="Аналіз" value="run" />
            <Tab label="Історія" value="history" />
            <Tab label="Налаштування" value="settings" />
          </Tabs>
        </Box>
      </AppBar>
      <Container maxWidth="xl" sx={{ mt: 2, mb: 4 }}>
        {tab === 'instructions' ? instructionsTab :
         tab === 'run' ? runTab :
         tab === 'history' ? historyTab :
         settingsTab}
      </Container>
      <Snackbar open={!!snack} onClose={()=>setSnack(null)} message={snack||''} autoHideDuration={3000} />
    </Box>
  )
}
