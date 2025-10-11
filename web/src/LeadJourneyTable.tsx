import React, { useEffect, useState } from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
  Box,
  Typography,
  Chip,
  CircularProgress
} from '@mui/material'
import { EnrichedStudent, getStudentsWithJourney } from './api'

interface LeadJourneyTableProps {
  startDate?: string
  endDate?: string
}

// Полный список 38 статусов AlfaCRM с цветовой маркировкой
const ALL_STATUSES = [
  // Основная воронка (Главные этапы - синий)
  { id: 13, name: 'Не розібраний', color: '#2196F3', category: 'main' },

  // Недозвоны (красный)
  { id: 11, name: 'Недодзвон', color: '#f44336', category: 'main' },
  { id: 10, name: 'Недозвон 2', color: '#f44336', category: 'main' },
  { id: 27, name: 'Недозвон 3', color: '#f44336', category: 'main' },

  // Контакт установлен (зеленый)
  { id: 1, name: 'Вст контакт невідомо', color: '#4CAF50', category: 'main' },
  { id: 32, name: 'Вст контакт зацікавлений', color: '#4CAF50', category: 'main' },

  // Пропал после контакта (оранжевый)
  { id: 26, name: 'Зник після контакту', color: '#FF9800', category: 'main' },

  // В процессе (желтый)
  { id: 12, name: 'Розмовляли, чекаємо відповідь', color: '#FFC107', category: 'main' },
  { id: 6, name: 'Чекає пробного', color: '#FFC107', category: 'main' },

  // Пробные уроки (голубой)
  { id: 2, name: 'Призначено пробне', color: '#00BCD4', category: 'main' },
  { id: 3, name: 'Проведено пробне', color: '#00BCD4', category: 'main' },
  { id: 5, name: 'Не відвідав пробне', color: '#00BCD4', category: 'main' },

  // Ожидание оплаты (фиолетовый)
  { id: 9, name: 'Чекаємо оплату', color: '#9C27B0', category: 'main' },

  // КОНВЕРСИЯ - Оплата получена (темно-зеленый)
  { id: 4, name: 'Отримана оплата', color: '#1B5E20', category: 'main' },

  // Отложенные платежи (серый)
  { id: 29, name: 'Сплатить через 2 тижні >', color: '#9E9E9E', category: 'main' },
  { id: 25, name: 'Передзвонити через 2 тижні', color: '#9E9E9E', category: 'main' },
  { id: 30, name: 'Передзвон через місяць', color: '#9E9E9E', category: 'main' },
  { id: 31, name: 'Передзвон 2 місяці і більше', color: '#9E9E9E', category: 'main' },

  // Работа с возражениями (розовый)
  { id: 8, name: 'Опрацювати заперечення', color: '#E91E63', category: 'main' },

  // Старые клиенты (темно-синий)
  { id: 50, name: 'Старі клієнти', color: '#1A237E', category: 'main' },

  // ==== ВТОРАЯ ВОРОНКА (дубликаты) ====

  // Недозвоны вторая воронка (светло-красный)
  { id: 18, name: 'Недозвон [2]', color: '#EF5350', category: 'secondary' },
  { id: 40, name: 'Недозвон 2 [2]', color: '#EF5350', category: 'secondary' },
  { id: 42, name: 'недозвон 3 [2]', color: '#EF5350', category: 'secondary' },

  // Контакт вторая воронка (светло-зеленый)
  { id: 43, name: 'Встан коннт невідомо [2]', color: '#66BB6A', category: 'secondary' },
  { id: 22, name: 'Встан контакт зацікавлений [2]', color: '#66BB6A', category: 'secondary' },

  // Пропал после контакта вторая воронка (светло-оранжевый)
  { id: 44, name: 'Зник після контакту [2]', color: '#FFB74D', category: 'secondary' },

  // В процессе вторая воронка (светло-желтый)
  { id: 24, name: 'Розмовляли чекаємо відповіді [2]', color: '#FFD54F', category: 'secondary' },
  { id: 34, name: 'Чекає пробного [2]', color: '#FFD54F', category: 'secondary' },

  // Пробные уроки вторая воронка (светло-голубой)
  { id: 35, name: 'Призначено пробне [2]', color: '#4DD0E1', category: 'secondary' },
  { id: 37, name: 'Проведено пробне [2]', color: '#4DD0E1', category: 'secondary' },
  { id: 36, name: 'Не відвідав пробне [2]', color: '#4DD0E1', category: 'secondary' },

  // Ожидание оплаты вторая воронка (светло-фиолетовый)
  { id: 38, name: 'Чекає оплату [2]', color: '#BA68C8', category: 'secondary' },

  // КОНВЕРСИЯ вторая воронка (зеленый)
  { id: 39, name: 'Отримана оплата [2]', color: '#2E7D32', category: 'secondary' },

  // Отложенные платежи вторая воронка (светло-серый)
  { id: 45, name: 'Сплатить через 2 тижні [2]', color: '#BDBDBD', category: 'secondary' },
  { id: 46, name: 'Передзвонити через 2 тижні [2]', color: '#BDBDBD', category: 'secondary' },
  { id: 47, name: 'Передз через місяць [2]', color: '#BDBDBD', category: 'secondary' },
  { id: 48, name: 'Передзвон 2 місяці і більше [2]', color: '#BDBDBD', category: 'secondary' },

  // Работа с возражениями вторая воронка (светло-розовый)
  { id: 49, name: 'Опрацювати заперечення [2]', color: '#F06292', category: 'secondary' }
]

export default function LeadJourneyTable({ startDate, endDate }: LeadJourneyTableProps) {
  const [students, setStudents] = useState<EnrichedStudent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [startDate, endDate])

  async function loadData() {
    try {
      setLoading(true)
      setError(null)
      const data = await getStudentsWithJourney({
        start_date: startDate,
        end_date: endDate
      })
      setStudents(data.students)
    } catch (e: any) {
      setError(e.message || 'Не вдалося завантажити дані')
    } finally {
      setLoading(false)
    }
  }

  // Проверка, прошел ли лид через данный статус
  const hasPassedStatus = (student: EnrichedStudent, statusId: number): boolean => {
    return student.journey_status_ids?.includes(statusId) || false
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Завантаження даних про історію лідів...</Typography>
      </Box>
    )
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Помилка: {error}
      </Alert>
    )
  }

  if (students.length === 0) {
    return (
      <Alert severity="info" sx={{ mb: 2 }}>
        Немає даних студентів з історією переходів
      </Alert>
    )
  }

  return (
    <>
      {/* Статистика */}
      <Box sx={{ mb: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <Chip
          label={`Всього лідів: ${students.length}`}
          color="primary"
        />
        <Chip
          label={`Конверсії: ${students.filter(s => s.journey_stats?.conversion_reached).length}`}
          color="success"
        />
        <Chip
          label={`Основна воронка: ${students.filter(s => s.journey_stats?.funnel_type === 'main').length}`}
          color="info"
        />
        <Chip
          label={`Вторинна воронка: ${students.filter(s => s.journey_stats?.funnel_type === 'secondary').length}`}
          color="warning"
        />
      </Box>

      {/* Легенда цветов */}
      <Box sx={{ mb: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
        <Typography variant="subtitle2" gutterBottom>Легенда:</Typography>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Chip size="small" label="Новий лід" sx={{ bgcolor: '#2196F3', color: 'white' }} />
          <Chip size="small" label="Недозвон" sx={{ bgcolor: '#f44336', color: 'white' }} />
          <Chip size="small" label="Контакт" sx={{ bgcolor: '#4CAF50', color: 'white' }} />
          <Chip size="small" label="В процесі" sx={{ bgcolor: '#FFC107', color: 'white' }} />
          <Chip size="small" label="Пробний" sx={{ bgcolor: '#00BCD4', color: 'white' }} />
          <Chip size="small" label="Оплата" sx={{ bgcolor: '#9C27B0', color: 'white' }} />
          <Chip size="small" label="КОНВЕРСІЯ" sx={{ bgcolor: '#1B5E20', color: 'white' }} />
        </Box>
      </Box>

      {/* Таблица с 38 столбцами */}
      <TableContainer component={Paper} sx={{ maxHeight: 600, overflowX: 'auto' }}>
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              {/* Информационные колонки */}
              <TableCell
                sx={{
                  minWidth: 150,
                  fontWeight: 'bold',
                  position: 'sticky',
                  left: 0,
                  zIndex: 3,
                  bgcolor: 'background.paper'
                }}
              >
                Ім'я ліда
              </TableCell>
              <TableCell
                sx={{
                  minWidth: 120,
                  fontWeight: 'bold',
                  position: 'sticky',
                  left: 150,
                  zIndex: 3,
                  bgcolor: 'background.paper'
                }}
              >
                Поточний статус
              </TableCell>
              <TableCell
                sx={{
                  minWidth: 80,
                  fontWeight: 'bold',
                  position: 'sticky',
                  left: 270,
                  zIndex: 3,
                  bgcolor: 'background.paper'
                }}
              >
                Кроків
              </TableCell>
              <TableCell
                sx={{
                  minWidth: 100,
                  fontWeight: 'bold',
                  position: 'sticky',
                  left: 350,
                  zIndex: 3,
                  bgcolor: 'background.paper'
                }}
              >
                Воронка
              </TableCell>

              {/* 38 столбцов статусов */}
              {ALL_STATUSES.map((status) => (
                <TableCell
                  key={status.id}
                  align="center"
                  sx={{
                    minWidth: 60,
                    maxWidth: 80,
                    bgcolor: status.color,
                    color: 'white',
                    fontWeight: 'bold',
                    fontSize: '0.75rem',
                    padding: '8px 4px',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                  }}
                  title={status.name}
                >
                  {status.id}
                </TableCell>
              ))}
            </TableRow>

            {/* Вторая строка заголовков с названиями */}
            <TableRow>
              <TableCell
                sx={{
                  position: 'sticky',
                  left: 0,
                  zIndex: 3,
                  bgcolor: 'background.paper',
                  fontSize: '0.7rem'
                }}
              ></TableCell>
              <TableCell
                sx={{
                  position: 'sticky',
                  left: 150,
                  zIndex: 3,
                  bgcolor: 'background.paper',
                  fontSize: '0.7rem'
                }}
              ></TableCell>
              <TableCell
                sx={{
                  position: 'sticky',
                  left: 270,
                  zIndex: 3,
                  bgcolor: 'background.paper',
                  fontSize: '0.7rem'
                }}
              ></TableCell>
              <TableCell
                sx={{
                  position: 'sticky',
                  left: 350,
                  zIndex: 3,
                  bgcolor: 'background.paper',
                  fontSize: '0.7rem'
                }}
              ></TableCell>

              {ALL_STATUSES.map((status) => (
                <TableCell
                  key={`name-${status.id}`}
                  align="center"
                  sx={{
                    fontSize: '0.65rem',
                    padding: '4px 2px',
                    maxWidth: 80,
                    whiteSpace: 'normal',
                    lineHeight: 1.2,
                    bgcolor: 'grey.100'
                  }}
                  title={status.name}
                >
                  {status.name}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>

          <TableBody>
            {students.map((student, idx) => (
              <TableRow key={student.id || idx} hover>
                {/* Информационные ячейки */}
                <TableCell
                  sx={{
                    position: 'sticky',
                    left: 0,
                    zIndex: 2,
                    bgcolor: 'background.paper',
                    fontWeight: 500
                  }}
                >
                  {student.name || `Лід ${student.id}`}
                </TableCell>
                <TableCell
                  sx={{
                    position: 'sticky',
                    left: 150,
                    zIndex: 2,
                    bgcolor: 'background.paper'
                  }}
                >
                  <Chip
                    label={student.journey_stats?.current_status_name || 'Невідомо'}
                    size="small"
                    sx={{
                      bgcolor: ALL_STATUSES.find(s => s.id === student.lead_status_id)?.color || '#9E9E9E',
                      color: 'white',
                      fontSize: '0.7rem'
                    }}
                  />
                </TableCell>
                <TableCell
                  align="center"
                  sx={{
                    position: 'sticky',
                    left: 270,
                    zIndex: 2,
                    bgcolor: 'background.paper'
                  }}
                >
                  {student.journey_stats?.total_steps || 0}
                </TableCell>
                <TableCell
                  align="center"
                  sx={{
                    position: 'sticky',
                    left: 350,
                    zIndex: 2,
                    bgcolor: 'background.paper'
                  }}
                >
                  <Chip
                    label={student.journey_stats?.funnel_type === 'main' ? 'Основна' : 'Вторинна'}
                    size="small"
                    color={student.journey_stats?.funnel_type === 'main' ? 'info' : 'warning'}
                    sx={{ fontSize: '0.7rem' }}
                  />
                </TableCell>

                {/* 38 столбцов статусов */}
                {ALL_STATUSES.map((status) => {
                  const passed = hasPassedStatus(student, status.id)
                  const isCurrent = student.lead_status_id === status.id

                  return (
                    <TableCell
                      key={`${student.id}-${status.id}`}
                      align="center"
                      sx={{
                        bgcolor: passed
                          ? (isCurrent ? status.color : `${status.color}40`) // 40 = 25% opacity
                          : 'transparent',
                        padding: '4px',
                        border: isCurrent ? `2px solid ${status.color}` : undefined,
                        fontWeight: isCurrent ? 'bold' : 'normal'
                      }}
                    >
                      {passed && (
                        isCurrent
                          ? <Box sx={{ fontSize: '1.2rem' }}>●</Box>  // Текущий статус - большая точка
                          : <Box sx={{ fontSize: '0.8rem', color: status.color }}>✓</Box>  // Пройденный - галочка
                      )}
                    </TableCell>
                  )
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Информация о трекинге */}
      <Alert severity="info" sx={{ mt: 2 }}>
        <Typography variant="body2">
          <strong>Трекінг історії лідів через воронку:</strong><br/>
          • ✓ - Лід пройшов через цей статус<br/>
          • ● - Поточний статус ліда<br/>
          • Колір комірки показує тип статусу (недодзвон, контакт, пробний, тощо)<br/>
          • Всього відстежується: 38 статусів AlfaCRM у 2 паралельних воронках
        </Typography>
      </Alert>
    </>
  )
}
