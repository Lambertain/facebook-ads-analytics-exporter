import { useEffect, useMemo, useRef, useState } from 'react'
import {
  AppBar, Box, Button, Container, Dialog, DialogActions, DialogContent, DialogTitle,
  Grid2 as Grid, IconButton, LinearProgress, Snackbar, Tab, Tabs, TextField, Tooltip, Typography, InputAdornment,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper
} from '@mui/material'
import HelpOutlineIcon from '@mui/icons-material/HelpOutline'
import FolderOpenIcon from '@mui/icons-material/FolderOpen'
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs'
import { DatePicker, LocalizationProvider } from '@mui/x-date-pickers'
import dayjs, { Dayjs } from 'dayjs'
import { ConfigMap, getConfig, inspectExcelHeaders, listAlfaCompanies, listNetHuntFolders, openEventStream, startJob, updateConfig } from './api'

type TabKey = 'run' | 'settings'
type DataTabKey = 'students' | 'teachers' | 'ads'

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
          <Button onClick={() => setOpen(false)}>Понятно</Button>
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

  useEffect(() => { (async () => {
    try {
      const data = await getConfig()
      setCfg(data)
      if (data.GOOGLE_SHEET_ID?.value) setSheetId(data.GOOGLE_SHEET_ID.value)
    } catch (e) { setSnack('Не удалось загрузить конфиг') }
  })() }, [])

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
      setSnack('Настройки сохранены')
    } catch { setSnack('Ошибка сохранения настроек') }
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
      const data = await startJob({
        start_date: start?.format('YYYY-MM-DD') || '',
        end_date: end?.format('YYYY-MM-DD') || '',
        sheet_id: storageBackend === 'sheets' ? sheetId : undefined
      })
      if (esRef.current) esRef.current.close()
      esRef.current = openEventStream(data.job_id, (s) => setLogs(l => [...l, s]), (p) => {
        setProgress(p.percent || 0)
        setStatus(p.status || 'running')
      })
    } catch (e: any) {
      setSnack('Не удалось запустить задачу: ' + (e?.message || ''))
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

  async function onDownloadExcel() {
    if (status !== 'done') {
      setSnack('Сначала запустите процесс и дождитесь завершения')
      return
    }
    try {
      const response = await fetch('/api/download-excel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          start_date: start?.format('YYYY-MM-DD'),
          end_date: end?.format('YYYY-MM-DD')
        })
      })
      if (!response.ok) throw new Error('Ошибка скачивания')

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `ecademy_export_${start?.format('YYYY-MM-DD')}_${end?.format('YYYY-MM-DD')}.xlsx`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      setSnack('Excel файл скачан')
    } catch (e: any) {
      setSnack('Ошибка скачивания: ' + (e?.message || ''))
    }
  }

  const runTab = (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <Box sx={{ mt: 2 }}>
        {/* Управление и прогресс */}
        <Grid container spacing={2}>
          <Grid xs={12} md={4}><DatePicker label="Период c" value={start} onChange={setStart} format="YYYY-MM-DD"/></Grid>
          <Grid xs={12} md={4}><DatePicker label="Период по" value={end} onChange={setEnd} format="YYYY-MM-DD"/></Grid>
          <Grid xs={12}>
            <Button variant="contained" onClick={onStart}>Старт</Button>
            <Button sx={{ ml: 1 }} onClick={onInspectHeaders}>Проверить заголовки</Button>
            <Button sx={{ ml: 1 }} onClick={onListNetHunt}>NetHunt папки</Button>
            <Button sx={{ ml: 1 }} variant="outlined" color="success" onClick={onDownloadExcel} disabled={status !== 'done'}>
              Скачать Excel
            </Button>
          </Grid>
          <Grid xs={12}>
            <Box sx={{ display:'flex', alignItems:'center', gap:2 }}>
              <Box sx={{ flex: 1 }}><LinearProgress variant="determinate" value={progress} /></Box>
              <Typography variant="body2">{progress}%</Typography>
              <Typography variant="body2">{status}</Typography>
            </Box>
          </Grid>
        </Grid>

        {/* Вкладки с данными */}
        <Box sx={{ mt: 3 }}>
          <Tabs value={dataTab} onChange={(_,v)=>setDataTab(v)} sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tab label="Реклама" value="ads" />
            <Tab label="Студенты" value="students" />
            <Tab label="Учителя" value="teachers" />
          </Tabs>

          <Box sx={{ mt: 2 }}>
            {dataTab === 'ads' && (
              <TableContainer component={Paper}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Дата начала</TableCell>
                      <TableCell>Дата конца</TableCell>
                      <TableCell>ID кампании</TableCell>
                      <TableCell>Название кампании</TableCell>
                      <TableCell>Показы</TableCell>
                      <TableCell>Клики</TableCell>
                      <TableCell>Расходы</TableCell>
                      <TableCell>CPC</TableCell>
                      <TableCell>CPM</TableCell>
                      <TableCell>CTR</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {adsData.length === 0 ? (
                      <TableRow><TableCell colSpan={10} align="center">Нет данных. Запустите процесс.</TableCell></TableRow>
                    ) : adsData.map((row, i) => (
                      <TableRow key={i}>
                        <TableCell>{row.date_start}</TableCell>
                        <TableCell>{row.date_stop}</TableCell>
                        <TableCell>{row.campaign_id}</TableCell>
                        <TableCell>{row.campaign_name}</TableCell>
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
            )}

            {dataTab === 'students' && (
              <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
                <Table size="small" stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell>Ссылка на РК</TableCell>
                      <TableCell>Дата анализа</TableCell>
                      <TableCell>Бюджет $</TableCell>
                      <TableCell>Локация</TableCell>
                      <TableCell>Лидов</TableCell>
                      <TableCell>Куплено</TableCell>
                      <TableCell>% конверсия</TableCell>
                      <TableCell>Цена/лид</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {studentsData.length === 0 ? (
                      <TableRow><TableCell colSpan={8} align="center">Нет данных. Запустите процесс.</TableCell></TableRow>
                    ) : studentsData.map((row, i) => (
                      <TableRow key={i}>
                        <TableCell>{row['Посилання на рекламну компанію']}</TableCell>
                        <TableCell>{row['Дата аналізу']}</TableCell>
                        <TableCell>{row['Витрачений бюджет в $']}</TableCell>
                        <TableCell>{row['Місце знаходження (країни чи міста)']}</TableCell>
                        <TableCell>{row['Кількість лідів']}</TableCell>
                        <TableCell>{row['Купили (ЦА)']}</TableCell>
                        <TableCell>{row['% конверсія']}</TableCell>
                        <TableCell>{row['Ціна / ліда']}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}

            {dataTab === 'teachers' && (
              <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
                <Table size="small" stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell>Название РК</TableCell>
                      <TableCell>Ссылка</TableCell>
                      <TableCell>Дата анализа</TableCell>
                      <TableCell>Бюджет $</TableCell>
                      <TableCell>Лидов</TableCell>
                      <TableCell>СП</TableCell>
                      <TableCell>Стажеров</TableCell>
                      <TableCell>% СП</TableCell>
                      <TableCell>Цена/лид</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {teachersData.length === 0 ? (
                      <TableRow><TableCell colSpan={9} align="center">Нет данных. Запустите процесс.</TableCell></TableRow>
                    ) : teachersData.map((row, i) => (
                      <TableRow key={i}>
                        <TableCell>{row['Назва РК']}</TableCell>
                        <TableCell>{row['Посилання на рекламну компанію']}</TableCell>
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
            )}
          </Box>
        </Box>

        {/* Логи */}
        <Box sx={{ mt: 3, bgcolor:'#f7f7f7', p:2, borderRadius:1, height:200, overflow:'auto', fontFamily:'monospace', whiteSpace:'pre-wrap' }}>
          {logs.map((l,i)=>(<div key={i}>[{new Date().toLocaleTimeString()}] {l}</div>))}
        </Box>
      </Box>
    </LocalizationProvider>
  )

  const settingsTab = cfg && (
    <Box sx={{ mt: 2, maxWidth: 600 }}>
      {/* Facebook */}
      <Typography variant="h6" sx={{ mb: 2 }}>Facebook</Typography>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <TextField type="password" fullWidth label="META_ACCESS_TOKEN" value={cfg.META_ACCESS_TOKEN?.value || ''} onChange={e=>updateField('META_ACCESS_TOKEN', e.target.value)} />
        <Help title="Где взять токен?">
          <Typography>Meta for Developers → Marketing API → System User or App → Generate access token с нужными правами (ads_read, leads_retrieval и доступ к страницам/аккаунту).</Typography>
        </Help>
      </Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <TextField fullWidth label="META_AD_ACCOUNT_ID (act_*)" value={cfg.META_AD_ACCOUNT_ID?.value || ''} onChange={e=>updateField('META_AD_ACCOUNT_ID', e.target.value)} />
        <Help title="Где взять act_*?">
          <Typography>В Ads Manager в URL (act_XXXX) или через API: GET /me/adaccounts.</Typography>
        </Help>
      </Box>

      {/* NetHunt */}
      <Typography variant="h6" sx={{ mb: 2, mt: 3 }}>NetHunt (Учителя)</Typography>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <TextField type="password" fullWidth label="NETHUNT_BASIC_AUTH (Basic ...)" value={cfg.NETHUNT_BASIC_AUTH?.value || ''} onChange={e=>updateField('NETHUNT_BASIC_AUTH', e.target.value)} />
        <Help title="Где взять Basic?">
          <Typography>В NetHunt: используйте email и API ключ. Формат заголовка: Basic base64(email:api_key). Можно сформировать в любом Base64-генераторе.</Typography>
        </Help>
      </Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <TextField fullWidth label="NETHUNT_FOLDER_ID" value={cfg.NETHUNT_FOLDER_ID?.value || ''} onChange={e=>updateField('NETHUNT_FOLDER_ID', e.target.value)} />
        <Help title="Где взять folder_id?">
          <Typography>Нажмите «NetHunt папки» во вкладке Запуск — возьмите ID нужной папки для учителей.</Typography>
        </Help>
      </Box>

      {/* AlfaCRM */}
      <Typography variant="h6" sx={{ mb: 2, mt: 3 }}>AlfaCRM (Студенты)</Typography>
      <TextField fullWidth label="ALFACRM_BASE_URL" value={cfg.ALFACRM_BASE_URL?.value || ''} onChange={e=>updateField('ALFACRM_BASE_URL', e.target.value)} sx={{ mb: 2 }} />
      <TextField fullWidth label="ALFACRM_EMAIL" value={cfg.ALFACRM_EMAIL?.value || ''} onChange={e=>updateField('ALFACRM_EMAIL', e.target.value)} sx={{ mb: 2 }} />
      <TextField type="password" fullWidth label="ALFACRM_API_KEY" value={cfg.ALFACRM_API_KEY?.value || ''} onChange={e=>updateField('ALFACRM_API_KEY', e.target.value)} sx={{ mb: 2 }} />
      <TextField fullWidth label="ALFACRM_COMPANY_ID" value={cfg.ALFACRM_COMPANY_ID?.value || ''} onChange={e=>updateField('ALFACRM_COMPANY_ID', e.target.value)} sx={{ mb: 3 }} />

      {/* Excel/Sheets Storage */}
      <Typography variant="h6" sx={{ mb: 2, mt: 3 }}>Хранилище</Typography>
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

      <Button disabled={saving} variant="contained" onClick={onSave} sx={{ mt: 2 }}>Сохранить</Button>
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
            <Tab label="Настройки" value="settings" />
          </Tabs>
        </Box>
      </AppBar>
      <Container maxWidth="lg" sx={{ mt: 2, mb: 4 }}>
        {tab === 'run' ? runTab : settingsTab}
      </Container>
      <Snackbar open={!!snack} onClose={()=>setSnack(null)} message={snack||''} autoHideDuration={3000} />
    </Box>
  )
}
