import React, { useEffect, useState } from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
  Alert,
  Box
} from '@mui/material'
import { getStudents, Student } from './api'

export default function StudentsTable() {
  const [students, setStudents] = useState<Student[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadStudents()
  }, [])

  async function loadStudents() {
    try {
      setLoading(true)
      setError(null)
      const data = await getStudents({ enrich: true })
      setStudents(data.students)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Помилка завантаження даних')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>
  }

  if (students.length === 0) {
    return <Alert severity="info">Немає даних студентів</Alert>
  }

  return (
    <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
      <Table stickyHeader size="small">
        <TableHead>
          <TableRow>
            <TableCell>Посилання на РК</TableCell>
            <TableCell>Дата аналізу</TableCell>
            <TableCell>Період</TableCell>
            <TableCell>Витрачено $</TableCell>
            <TableCell>Локація</TableCell>
            <TableCell>К-сть лідів</TableCell>
            <TableCell>Перевірка лідів</TableCell>
            <TableCell>Не розібрані</TableCell>
            <TableCell>Встанов. контакт</TableCell>
            <TableCell>В опрацюванні</TableCell>
            <TableCell>Назначений пробний</TableCell>
            <TableCell>Проведений пробний</TableCell>
            <TableCell>Чекаємо оплату</TableCell>
            <TableCell>Купили</TableCell>
            <TableCell>Архів (ЦА)</TableCell>
            <TableCell>Недозвон</TableCell>
            <TableCell>Архів (не ЦА)</TableCell>
            <TableCell>К-сть цільових</TableCell>
            <TableCell>К-сть не цільових</TableCell>
            <TableCell>% цільових</TableCell>
            <TableCell>% не цільових</TableCell>
            <TableCell>% Встан. контакт</TableCell>
            <TableCell>% В опрацюванні</TableCell>
            <TableCell>% конверсія</TableCell>
            <TableCell>% архів</TableCell>
            <TableCell>% недозвон</TableCell>
            <TableCell>Ціна/ліда</TableCell>
            <TableCell>Ціна/цільового</TableCell>
            <TableCell>Нотатки</TableCell>
            <TableCell>% Назнач. пробний</TableCell>
            <TableCell>% Провед. пробний (заг.)</TableCell>
            <TableCell>% Провед. пробний (назнач.)</TableCell>
            <TableCell>Конверсія пробний→продаж</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {students.map((s, idx) => (
            <TableRow key={idx} hover>
              <TableCell>{s["Посилання на рекламну компанію"]}</TableCell>
              <TableCell>{s["Дата аналізу"]}</TableCell>
              <TableCell>{s["Період аналізу запущеної компанії"]}</TableCell>
              <TableCell>{s["Витрачений бюджет в $"]}</TableCell>
              <TableCell>{s["Місце знаходження (країни чи міста)"]}</TableCell>
              <TableCell>{s["Кількість лідів"]}</TableCell>
              <TableCell>{s["Перевірка лідів автоматичний"]}</TableCell>
              <TableCell>{s["Не розібрані"]}</TableCell>
              <TableCell>{s["Встанов. контакт (ЦА)"]}</TableCell>
              <TableCell>{s["В опрацюванні (ЦА)"]}</TableCell>
              <TableCell>{s["Назначений пробний\n(ЦА)"]}</TableCell>
              <TableCell>{s["Проведений пробний\n(ЦА)"]}</TableCell>
              <TableCell>{s["Чекаємо оплату"]}</TableCell>
              <TableCell>{s["Купили (ЦА)"]}</TableCell>
              <TableCell>{s["Архів (ЦА)"]}</TableCell>
              <TableCell>{s["Недозвон \n(не ЦА)"]}</TableCell>
              <TableCell>{s["Архів\n (не ЦА)"]}</TableCell>
              <TableCell>{s["Кількість цільових лідів"]}</TableCell>
              <TableCell>{s["Кількість не цільових лідів"]}</TableCell>
              <TableCell>{s["% цільових лідів"]}</TableCell>
              <TableCell>{s["% не цільових лідів"]}</TableCell>
              <TableCell>{s["% Встан. контакт"]}</TableCell>
              <TableCell>{s["% В опрацюванні (ЦА)"]}</TableCell>
              <TableCell>{s["% конверсія"]}</TableCell>
              <TableCell>{s["% архів"]}</TableCell>
              <TableCell>{s["% недозвон"]}</TableCell>
              <TableCell>{s["Ціна / ліда"]}</TableCell>
              <TableCell>{s["Ціна / цільового ліда"]}</TableCell>
              <TableCell>{s["Нотатки"]}</TableCell>
              <TableCell>{s["% Назначений пробний"]}</TableCell>
              <TableCell>{s["%\nПроведений пробний від загальних лідів\n(ЦА)"]}</TableCell>
              <TableCell>{s["%\nПроведений пробний від назначених пробних"]}</TableCell>
              <TableCell>{s["Конверсія з проведеного пробного в продаж"]}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  )
}
