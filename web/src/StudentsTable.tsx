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

// 38 статусів AlfaCRM у порядку воронки
// Основна воронка (20 статусів)
const STATUS_COLUMNS_MAIN = [
  { key: 'status_13', label: 'Не розібраний' },
  { key: 'status_11', label: 'Недодзвон' },
  { key: 'status_10', label: 'Недозвон 2' },
  { key: 'status_27', label: 'Недозвон 3' },
  { key: 'status_1', label: 'Вст контакт невідомо' },
  { key: 'status_32', label: 'Вст контакт зацікавлений' },
  { key: 'status_26', label: 'Зник після контакту' },
  { key: 'status_12', label: 'Розмовляли, чекаємо відповідь' },
  { key: 'status_6', label: 'Чекає пробного' },
  { key: 'status_2', label: 'Призначено пробне' },
  { key: 'status_3', label: 'Проведено пробне' },
  { key: 'status_5', label: 'Не відвідав пробне' },
  { key: 'status_9', label: 'Чекаємо оплату' },
  { key: 'status_4', label: 'Отримана оплата' },
  { key: 'status_29', label: 'Сплатить через 2 тижні >' },
  { key: 'status_25', label: 'Передзвонити через 2 тижні' },
  { key: 'status_30', label: 'Передзвон через місяць' },
  { key: 'status_31', label: 'Передзвон 2 місяці і більше' },
  { key: 'status_8', label: 'Опрацювати заперечення' },
  { key: 'status_50', label: 'Старі клієнти' }
] as const

// Вторинна воронка (18 статусів)
const STATUS_COLUMNS_SECONDARY = [
  { key: 'status_18', label: 'Недозвон (втор.)' },
  { key: 'status_40', label: 'Недозвон 2 (втор.)' },
  { key: 'status_42', label: 'недозвон 3 (втор.)' },
  { key: 'status_43', label: 'Встан коннт невідомо (втор.)' },
  { key: 'status_22', label: 'Встан контакт зацікавлений (втор.)' },
  { key: 'status_44', label: 'Зник після контакту (втор.)' },
  { key: 'status_24', label: 'Розмовляли чекаємо відповіді (втор.)' },
  { key: 'status_34', label: 'Чекає пробного (втор.)' },
  { key: 'status_35', label: 'Призначено пробне (втор.)' },
  { key: 'status_37', label: 'Проведено пробне (втор.)' },
  { key: 'status_36', label: 'Не відвідав пробне (втор.)' },
  { key: 'status_38', label: 'Чекає оплату (втор.)' },
  { key: 'status_39', label: 'Отримана оплата (втор.)' },
  { key: 'status_45', label: 'Сплатить через 2 тижні (втор.)' },
  { key: 'status_46', label: 'Передзвонити через 2 тижні (втор.)' },
  { key: 'status_47', label: 'Передз через місяць (втор.)' },
  { key: 'status_48', label: 'Передзвон 2 місяці і більше (втор.)' },
  { key: 'status_49', label: 'Опрацювати заперечення (втор.)' }
] as const

const ALL_STATUS_COLUMNS = [...STATUS_COLUMNS_MAIN, ...STATUS_COLUMNS_SECONDARY]

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

                {/* 38 CRM статусів */}
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
