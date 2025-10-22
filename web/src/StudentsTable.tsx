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

// Кольори для різних груп колонок
const COLOR_META = '#ADD8E6'       // Світло-голубий (Meta дані)
const COLOR_CRM = '#FFB6C1'         // Світло-рожевий (CRM статуси)
const COLOR_CALC = '#90EE90'        // Світло-зелений (розрахунки)

// 11 агрегованих статусів AlfaCRM (замість 38 окремих)
// Синхронізовано з backend AGGREGATED_STATUSES (alfacrm_tracking.py)
const AGGREGATED_STATUS_COLUMNS = [
  { key: 'Не розібраний', label: 'Не розібраний' },
  { key: 'Недозвон', label: 'Недозвон' },
  { key: 'Встановлено контакт', label: 'Встановлено контакт' },
  { key: 'Зник після контакту', label: 'Зник після контакту' },
  { key: 'В опрацюванні', label: 'В опрацюванні' },
  { key: 'Призначено пробне', label: 'Призначено пробне' },      // Cumulative counting
  { key: 'Проведено пробне', label: 'Проведено пробне' },        // Cumulative counting
  { key: 'Чекає оплату', label: 'Чекає оплату' },                // Cumulative counting
  { key: 'Отримана оплата', label: 'Отримана оплата' },
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
