import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Alert, AppBar, Box, Button, Container, Dialog, DialogActions, DialogContent, DialogTitle,
  Grid2 as Grid, IconButton, LinearProgress, Snackbar, Tab, Tabs, TextField, Tooltip, Typography, InputAdornment,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Link
} from '@mui/material'
import HelpOutlineIcon from '@mui/icons-material/HelpOutline'
import FolderOpenIcon from '@mui/icons-material/FolderOpen'
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs'
import { DatePicker, LocalizationProvider } from '@mui/x-date-pickers'
import dayjs, { Dayjs } from 'dayjs'
import { ConfigMap, getConfig, inspectExcelHeaders, listAlfaCompanies, listNetHuntFolders, openEventStream, startJob, runAnalytics, updateConfig } from './api'
import StudentsTable from './StudentsTable'

type TabKey = 'run' | 'settings' | 'history'
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
  const [tab, setTab] = useState<TabKey>('run')
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

  // History states
  const [runs, setRuns] = useState<PipelineRun[]>([])
  const [selectedRun, setSelectedRun] = useState<{ run: PipelineRun; logs: RunLog[] } | null>(null)
  const [historyFilter, setHistoryFilter] = useState<string>('')

  useEffect(() => { (async () => {
    try {
      const data = await getConfig()
      setCfg(data)
      if (data.GOOGLE_SHEET_ID?.value) setSheetId(data.GOOGLE_SHEET_ID.value)
    } catch (e) { setSnack('Не вдалося завантажити конфігурацію') }
  })() }, [])

  // Load history when history tab is opened
  useEffect(() => {
    if (tab === 'history') {
      loadHistory()
    }
  }, [tab])

  async function loadHistory() {
    try {
      const response = await fetch(`/api/runs?limit=100&status=${historyFilter}`)
      const data = await response.json()
      setRuns(data.runs || [])
    } catch (e) {
      setSnack('Не вдалося завантажити історію')
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
      let data: { job_id: string }

      // Використовуємо різні API залежно від вкладки
      if (dataTab === 'students' || dataTab === 'teachers') {
        // Нова логіка для студентів та викладачів
        data = await runAnalytics({
          campaign_type: dataTab === 'teachers' ? 'teachers' : 'students',
          date_start: start?.format('YYYY-MM-DD') || '',
          date_stop: end?.format('YYYY-MM-DD') || ''
        })
      } else {
        // Стара логіка для реклами (креативів)
        data = await startJob({
          start_date: start?.format('YYYY-MM-DD') || '',
          end_date: end?.format('YYYY-MM-DD') || '',
          sheet_id: storageBackend === 'sheets' ? sheetId : undefined
        })
      }

      if (esRef.current) esRef.current.close()
      esRef.current = openEventStream(data.job_id, (s) => setLogs(l => [...l, s]), (p) => {
        setProgress(p.percent || 0)
        setStatus(p.status || 'running')
      })
    } catch (e: any) {
      setSnack('Не вдалося запустити завдання: ' + (e?.message || ''))
      setStatus('error')
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
    // Перезавантажуємо історію
    loadHistory()
  }

  async function onDownloadExcel(dataType: 'ads' | 'students' | 'teachers' = 'ads') {
    if (status !== 'done' && dataType === 'ads') {
      setSnack('Спочатку запустіть процес і дочекайтесь завершення')
      return
    }
    try {
      const response = await fetch('/api/download-excel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          data_type: dataType,
          start_date: start?.format('YYYY-MM-DD'),
          end_date: end?.format('YYYY-MM-DD')
        })
      })
      if (!response.ok) throw new Error('Помилка завантаження')

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const filename = `${dataType}_export_${start?.format('YYYY-MM-DD')}_${end?.format('YYYY-MM-DD')}.xlsx`
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      setSnack('Excel файл завантажено')
    } catch (e: any) {
      setSnack('Помилка завантаження: ' + (e?.message || ''))
    }
  }

  const runTab = (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <Box sx={{ mt: 2 }}>
        {/* Керування та прогрес */}
        <Grid container spacing={2}>
          <Grid xs={12} md={4}><DatePicker label="Період з" value={start} onChange={setStart} format="YYYY-MM-DD"/></Grid>
          <Grid xs={12} md={4}><DatePicker label="Період до" value={end} onChange={setEnd} format="YYYY-MM-DD"/></Grid>
          <Grid xs={12}>
            <Button variant="contained" onClick={onStart}>Старт</Button>
            <Button sx={{ ml: 1 }} variant="outlined" color="success" onClick={onDownloadExcel} disabled={status !== 'done'}>
              Завантажити Excel
            </Button>
            <Button sx={{ ml: 1 }} variant="outlined" color="error" onClick={onClearResults} disabled={status !== 'done'}>
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
                <TableContainer component={Paper}>
                  <Table size="small">
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
                          <TableCell>{row.date_start}</TableCell>
                          <TableCell>{row.date_stop}</TableCell>
                          <TableCell>{row.impressions}</TableCell>
                          <TableCell>{row.clicks}</TableCell>
                          <TableCell>{row.spend}</TableCell>
                          <TableCell>{row.cpc}</TableCell>
                          <TableCell>{row.cpm}</TableCell>
                          <TableCell>{row.ctr}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </>
            )}

            {dataTab === 'students' && (
              <>
                <Box sx={{ mb: 2, display: 'flex', justifyContent: 'flex-end' }}>
                  <Button variant="outlined" color="success" onClick={() => onDownloadExcel('students')}>
                    Завантажити Students Excel
                  </Button>
                </Box>
                <StudentsTable />
              </>
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
                        <TableCell>Кількість лідів перевірка</TableCell>
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
                            href={row['Посилання на рекламну компанію']}
                            target="_blank"
                            rel="noopener noreferrer"
                            sx={{ textDecoration: 'none', '&:hover': { textDecoration: 'underline' } }}
                          >
                            {row['Назва реклами'] || row['Назва РК'] || "Без назви"}
                          </Link>
                        </TableCell>
                        <TableCell>{row['Дата аналізу']}</TableCell>
                        <TableCell>{row['Витрачений бюджет в $']}</TableCell>
                        <TableCell>{row['Кількість лідів']}</TableCell>
                        <TableCell>{row['Кількість СП']}</TableCell>
                        <TableCell>{row['Кількість найнятих стажерів']}</TableCell>
                        <TableCell>{row['Відсоток СП']}</TableCell>
                        <TableCell>{row['Ціна в $ за ліда']}</TableCell>
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
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 2 }}>
        <Typography variant="h5">Історія запусків</Typography>
        <Button variant="outlined" size="small" onClick={() => setHistoryFilter('')}>Усі</Button>
        <Button variant="outlined" size="small" onClick={() => setHistoryFilter('success')}>Успішні</Button>
        <Button variant="outlined" size="small" onClick={() => setHistoryFilter('error')}>Помилки</Button>
        <Button variant="outlined" size="small" onClick={loadHistory}>Оновити</Button>
      </Box>

      <Grid container spacing={2}>
        {/* Список запусків */}
        <Grid size={6}>
          <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Період</TableCell>
                  <TableCell>Статус</TableCell>
                  <TableCell>Час</TableCell>
                  <TableCell>Записи</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {runs.length === 0 ? (
                  <TableRow><TableCell colSpan={5} align="center">Немає історії запусків</TableCell></TableRow>
                ) : runs.map((run) => (
                  <TableRow
                    key={run.id}
                    hover
                    onClick={() => loadRunDetails(run.id)}
                    sx={{ cursor: 'pointer', bgcolor: selectedRun?.run.id === run.id ? '#f0f0f0' : 'inherit' }}
                  >
                    <TableCell>{run.id}</TableCell>
                    <TableCell>{run.start_date} - {run.end_date}</TableCell>
                    <TableCell>
                      <Box sx={{
                        display: 'inline-block',
                        px: 1,
                        py: 0.5,
                        borderRadius: 1,
                        fontSize: '0.75rem',
                        bgcolor: run.status === 'success' ? '#d4edda' : run.status === 'error' ? '#f8d7da' : '#fff3cd',
                        color: run.status === 'success' ? '#155724' : run.status === 'error' ? '#721c24' : '#856404'
                      }}>
                        {run.status}
                      </Box>
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.75rem' }}>
                      {run.start_time ? new Date(run.start_time).toLocaleString('uk-UA') : '-'}
                    </TableCell>
                    <TableCell>
                      {run.insights_count + run.students_count + run.teachers_count}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Grid>

        {/* Деталі обраного запуску */}
        <Grid size={6}>
          {selectedRun ? (
            <Box>
              <Paper sx={{ p: 2, mb: 2 }}>
                <Typography variant="h6" gutterBottom>Деталі запуску #{selectedRun.run.id}</Typography>
                <Grid container spacing={1}>
                  <Grid size={6}><Typography variant="body2"><strong>Job ID:</strong> {selectedRun.run.job_id}</Typography></Grid>
                  <Grid size={6}><Typography variant="body2"><strong>Статус:</strong> {selectedRun.run.status}</Typography></Grid>
                  <Grid size={6}><Typography variant="body2"><strong>Період:</strong> {selectedRun.run.start_date} - {selectedRun.run.end_date}</Typography></Grid>
                  <Grid size={6}><Typography variant="body2"><strong>Сховище:</strong> {selectedRun.run.storage_backend}</Typography></Grid>
                  <Grid size={6}><Typography variant="body2"><strong>Креативи:</strong> {selectedRun.run.insights_count}</Typography></Grid>
                  <Grid size={6}><Typography variant="body2"><strong>Студенти:</strong> {selectedRun.run.students_count}</Typography></Grid>
                  <Grid size={6}><Typography variant="body2"><strong>Викладачі:</strong> {selectedRun.run.teachers_count}</Typography></Grid>
                  <Grid size={6}><Typography variant="body2"><strong>Початок:</strong> {selectedRun.run.start_time ? new Date(selectedRun.run.start_time).toLocaleString('uk-UA') : '-'}</Typography></Grid>
                  <Grid size={6}><Typography variant="body2"><strong>Кінець:</strong> {selectedRun.run.end_time ? new Date(selectedRun.run.end_time).toLocaleString('uk-UA') : '-'}</Typography></Grid>
                  {selectedRun.run.error_message && (
                    <Grid size={12}>
                      <Typography variant="body2" color="error"><strong>Помилка:</strong> {selectedRun.run.error_message}</Typography>
                    </Grid>
                  )}
                </Grid>
              </Paper>

              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>Логи</Typography>
                <Box sx={{ maxHeight: 400, overflow: 'auto', fontFamily: 'monospace', fontSize: '0.8rem', bgcolor: '#f7f7f7', p: 1, borderRadius: 1 }}>
                  {selectedRun.logs.map((log) => (
                    <div key={log.id}>
                      <span style={{ color: log.level === 'error' ? 'red' : log.level === 'warning' ? 'orange' : 'inherit' }}>
                        [{log.timestamp ? new Date(log.timestamp).toLocaleTimeString('uk-UA') : '-'}]
                      </span>
                      {' '}[{log.level}] {log.message}
                    </div>
                  ))}
                </Box>
              </Paper>
            </Box>
          ) : (
            <Paper sx={{ p: 3, textAlign: 'center' }}>
              <Typography variant="body1" color="textSecondary">Оберіть запуск зі списку для перегляду деталей</Typography>
            </Paper>
          )}
        </Grid>
      </Grid>
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
          <Typography>Натисніть «NetHunt папки» у вкладці Запуск — візьміть ID потрібної папки для викладачів.</Typography>
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
            <Tab label="Запуск" value="run" />
            <Tab label="Історія" value="history" />
            <Tab label="Налаштування" value="settings" />
          </Tabs>
        </Box>
      </AppBar>
      <Container maxWidth="lg" sx={{ mt: 2, mb: 4 }}>
        {tab === 'run' ? runTab : tab === 'history' ? historyTab : settingsTab}
      </Container>
      <Snackbar open={!!snack} onClose={()=>setSnack(null)} message={snack||''} autoHideDuration={3000} />
    </Box>
  )
}
