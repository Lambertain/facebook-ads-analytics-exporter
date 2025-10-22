import React from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
  Link
} from '@mui/material'
import { MetaStudent } from './api'

interface StudentsTableProps {
  students: MetaStudent[]
  filterInfo?: any
}

// ============ 9 ГРУП COLOR-CODING ЗІ СПЕЦИФІКАЦІЇ ============
const COLOR_WHITE = '#FFFFFF'           // 1. Біла - A-F основна інформація
const COLOR_LIGHT_YELLOW = '#FFFFE0'    // 2. Світло-жовта - G кількість лідів + W-AA розрахунки %
const COLOR_LIGHT_PURPLE = '#E6E6FA'    // 3. Світло-фіолетова - I,J,K,N,O,P CRM статуси + AE-AI метрики
const COLOR_ORANGE = '#FFA500'          // 4. Оранжева - L,M пробні (ЦА)
const COLOR_LIGHT_PINK = '#FFB6C1'      // 5. Світло-рожева - Q,R не ЦА + T кількість не цільових
const COLOR_LIGHT_GREEN = '#90EE90'     // 6. Світло-зелена - S,U,V цільові ліди
const COLOR_LIGHT_ORANGE = '#FFE4B5'    // 7. Світло-оранжева - AB,AC фінанси
const COLOR_BRIGHT_YELLOW = '#FFFF00'   // 8. Ярко-жовта - AD нотатки

// 12 агрегованих статусів AlfaCRM (замість 38 окремих)
// Синхронізовано з backend AGGREGATED_STATUSES (alfacrm_tracking.py)
const AGGREGATED_STATUS_COLUMNS = [
  { key: 'Не розібраний', label: 'Не розібраний' },
  { key: 'Встановлено контакт (ЦА)', label: 'Встановлено контакт (ЦА)' },
  { key: 'В опрацюванні (ЦА)', label: 'В опрацюванні (ЦА)' },
  { key: 'Призначено пробне (ЦА)', label: 'Призначено пробне (ЦА)' },      // Cumulative counting
  { key: 'Проведено пробне (ЦА)', label: 'Проведено пробне (ЦА)' },        // Cumulative counting
  { key: 'Чекає оплату', label: 'Чекає оплату' },                // Cumulative counting
  { key: 'Отримана оплата (ЦА)', label: 'Отримана оплата (ЦА)' },
  { key: 'Архів (ЦА)', label: 'Архів (ЦА)' },                    // НОВА КОЛОНКА P
  { key: 'Недозвон (не ЦА)', label: 'Недозвон (не ЦА)' },
  { key: 'Архів (не ЦА)', label: 'Архів (не ЦА)' },              // НОВА КОЛОНКА R
  { key: 'Передзвонити пізніше', label: 'Передзвонити пізніше' },
  { key: 'Старі клієнти', label: 'Старі клієнти' }
] as const

const ALL_STATUS_COLUMNS = AGGREGATED_STATUS_COLUMNS

export default function StudentsTable({ students, filterInfo }: StudentsTableProps) {
  // Отримуємо повідомлення з filter_info або використовуємо fallback
  const getMessage = () => {
    if (!filterInfo || !filterInfo.students) {
      return 'Немає даних студентів'
    }

    const { message, keywords, matched_campaigns, total_campaigns } = filterInfo.students || {}

    // Якщо є кастомне повідомлення з бекенду - використовуємо його
    if (message) {
      return (
        <>
          <div>{message}</div>
          <div style={{ marginTop: '8px', fontSize: '0.9em', opacity: 0.8 }}>
            Використані ключові слова: {keywords?.join(', ') || 'не налаштовані'}<br />
            Знайдено студентських кампаній: {matched_campaigns || 0} з {total_campaigns || 0} всього
          </div>
        </>
      )
    }

    // Fallback якщо немає повідомлення
    return 'Немає даних студентів'
  }

  return (
    <>
      {students.length === 0 && (
        <Alert severity="info" sx={{ mb: 2 }}>{getMessage()}</Alert>
      )}
      <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              {/* Група 1: Meta дані (світло-голубий) */}
              <TableCell sx={{ backgroundColor: COLOR_META, fontWeight: 'bold' }}>Назва кампанії</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_META }}>Дата аналізу</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_META }}>Період аналізу</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_META }}>Бюджет ($)</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_META }}>Локація</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_META }}>Кількість лідів</TableCell>

              {/* Група 2: 38 CRM статусів (світло-рожевий) */}
              {ALL_STATUS_COLUMNS.map(col => (
                <TableCell key={col.key} sx={{ backgroundColor: COLOR_CRM, fontWeight: 'bold' }}>
                  {col.label}
                </TableCell>
              ))}

              {/* Група 3: Розрахунки (світло-зелений) */}
              <TableCell sx={{ backgroundColor: COLOR_CALC }}>% цільових</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_CALC }}>% нецільових</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_CALC }}>% контакт</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_CALC }}>% конверсія</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_CALC }}>Ціна/ліда</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_CALC }}>Ціна/цільового</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_CALC }}>% пробний призначено</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_CALC }}>% пробний проведено</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_CALC }}>% пробний → продаж</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {students.map((s, idx) => (
              <TableRow key={idx} hover>
                {/* Meta дані */}
                <TableCell>
                  <Link
                    href={s.campaign_link}
                    target="_blank"
                    rel="noopener noreferrer"
                    sx={{ textDecoration: 'none', '&:hover': { textDecoration: 'underline' } }}
                  >
                    {s.campaign_name || "Без назви"}
                  </Link>
                </TableCell>
                <TableCell>{s.analysis_date}</TableCell>
                <TableCell>{s.period}</TableCell>
                <TableCell>{s.budget}</TableCell>
                <TableCell>{s.location}</TableCell>
                <TableCell>{s.leads_count}</TableCell>

                {/* 11 агрегованих CRM статусів */}
                {ALL_STATUS_COLUMNS.map(col => (
                  <TableCell key={col.key}>
                    {s[col.key as keyof MetaStudent] || 0}
                  </TableCell>
                ))}

                {/* Розрахунки */}
                <TableCell>{s.target_percent}</TableCell>
                <TableCell>{s.non_target_percent}</TableCell>
                <TableCell>{s.contact_percent}</TableCell>
                <TableCell>{s.conversion_percent}</TableCell>
                <TableCell>{s.cost_per_lead}</TableCell>
                <TableCell>{s.cost_per_target_lead}</TableCell>
                <TableCell>{s.trial_scheduled_percent}</TableCell>
                <TableCell>{s.trial_completed_from_total_percent}</TableCell>
                <TableCell>{s.trial_to_purchase_percent}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </>
  )
}
