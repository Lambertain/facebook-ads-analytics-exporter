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
  Box,
  Link
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

  return (
    <>
      {students.length === 0 && (
        <Alert severity="info" sx={{ mb: 2 }}>Немає даних студентів</Alert>
      )}
      <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              <TableCell>Назва кампанії</TableCell>
              <TableCell>Дата аналізу</TableCell>
              <TableCell>Період аналізу запущеної компанії</TableCell>
              <TableCell>Витрачений бюджет в $</TableCell>
              <TableCell>Місце знаходження (країни чи міста)</TableCell>
              <TableCell>Кількість лідів</TableCell>
              <TableCell>Перевірка лідів автоматичний</TableCell>
              <TableCell>Не розібрані</TableCell>
              <TableCell>Встанов. контакт (ЦА)</TableCell>
              <TableCell>В опрацюванні (ЦА)</TableCell>
              <TableCell>Назначений пробний (ЦА)</TableCell>
              <TableCell>Проведений пробний (ЦА)</TableCell>
              <TableCell>Чекаємо оплату</TableCell>
              <TableCell>Купили (ЦА)</TableCell>
              <TableCell>Архів (ЦА)</TableCell>
              <TableCell>Недозвон (не ЦА)</TableCell>
              <TableCell>Архів (не ЦА)</TableCell>
              <TableCell>Кількість цільових лідів</TableCell>
              <TableCell>Кількість не цільових лідів</TableCell>
              <TableCell>% цільових лідів</TableCell>
              <TableCell>% не цільових лідів</TableCell>
              <TableCell>% Встан. контакт</TableCell>
              <TableCell>% В опрацюванні (ЦА)</TableCell>
              <TableCell>% конверсія</TableCell>
              <TableCell>% архів</TableCell>
              <TableCell>% недозвон</TableCell>
              <TableCell>Ціна / ліда</TableCell>
              <TableCell>Ціна / цільового ліда</TableCell>
              <TableCell>Нотатки</TableCell>
              <TableCell>% Назначений пробний</TableCell>
              <TableCell>% Проведений пробний від загальних лідів (ЦА)</TableCell>
              <TableCell>% Проведений пробний від назначених пробних</TableCell>
              <TableCell>Конверсія з проведеного пробного в продаж</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {students.map((s, idx) => (
              <TableRow key={idx} hover>
                <TableCell>
                  <Link
                    href={s["Посилання на рекламну компанію"]}
                    target="_blank"
                    rel="noopener noreferrer"
                    sx={{ textDecoration: 'none', '&:hover': { textDecoration: 'underline' } }}
                  >
                    {s["Назва реклами"] || "Без назви"}
                  </Link>
                </TableCell>
                <TableCell>{s["Дата аналізу"]}</TableCell>
                <TableCell>{s["Період аналізу запущеної компанії"]}</TableCell>
                <TableCell>{s["Витрачений бюджет в $"]}</TableCell>
                <TableCell>{s["Місце знаходження (країни чи міста)"]}</TableCell>
                <TableCell>{s["Кількість лідів"]}</TableCell>
                <TableCell>{s["Перевірка лідів автоматичний"]}</TableCell>
                <TableCell>{s["Не розібрані"]}</TableCell>
                <TableCell>{s["Встанов. контакт (ЦА)"]}</TableCell>
                <TableCell>{s["В опрацюванні (ЦА)"]}</TableCell>
                <TableCell>{s["Назначений пробний (ЦА)"]}</TableCell>
                <TableCell>{s["Проведений пробний (ЦА)"]}</TableCell>
                <TableCell>{s["Чекаємо оплату"]}</TableCell>
                <TableCell>{s["Купили (ЦА)"]}</TableCell>
                <TableCell>{s["Архів (ЦА)"]}</TableCell>
                <TableCell>{s["Недозвон (не ЦА)"]}</TableCell>
                <TableCell>{s["Архів (не ЦА)"]}</TableCell>
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
                <TableCell>{s["% Проведений пробний від загальних лідів (ЦА)"]}</TableCell>
                <TableCell>{s["% Проведений пробний від назначених пробних"]}</TableCell>
                <TableCell>{s["Конверсія з проведеного пробного в продаж"]}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </>
  )
}
