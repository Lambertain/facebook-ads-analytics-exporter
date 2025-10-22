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

// ============ 12 АГРЕГОВАНИХ СТАТУСІВ ALFACRM ============
// Синхронізовано з backend AGGREGATED_STATUSES (alfacrm_tracking.py)
// Порядок столбців I-R + додаткові статуси згідно зі специфікацією

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
              {/* A-F: Основна інформація (біла заливка) */}
              <TableCell sx={{ backgroundColor: COLOR_WHITE, fontWeight: 'bold' }}>Назва кампанії</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_WHITE }}>Дата аналізу</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_WHITE }}>Період аналізу</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_WHITE }}>Бюджет ($)</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_WHITE }}>Локація</TableCell>

              {/* G: Кількість лідів (світло-жовта заливка) */}
              <TableCell sx={{ backgroundColor: COLOR_LIGHT_YELLOW, fontWeight: 'bold' }}>Кількість лідів</TableCell>

              {/* I-R: CRM статуси (різна заливка) */}
              <TableCell sx={{ backgroundColor: COLOR_LIGHT_PURPLE, fontWeight: 'bold' }}>Не розібраний</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_LIGHT_PURPLE, fontWeight: 'bold' }}>Встановлено контакт (ЦА)</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_LIGHT_PURPLE, fontWeight: 'bold' }}>В опрацюванні (ЦА)</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_ORANGE, fontWeight: 'bold' }}>Призначено пробне (ЦА)</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_ORANGE, fontWeight: 'bold' }}>Проведено пробне (ЦА)</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_LIGHT_PURPLE, fontWeight: 'bold' }}>Чекає оплату</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_LIGHT_PURPLE, fontWeight: 'bold' }}>Отримана оплата (ЦА)</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_LIGHT_PURPLE, fontWeight: 'bold' }}>Архів (ЦА)</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_LIGHT_PINK, fontWeight: 'bold' }}>Недозвон (не ЦА)</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_LIGHT_PINK, fontWeight: 'bold' }}>Архів (не ЦА)</TableCell>

              {/* S-T: Кількість (розрахунки) */}
              <TableCell sx={{ backgroundColor: COLOR_LIGHT_GREEN }}>Кількість цільових лідів</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_LIGHT_PINK }}>Кількість не цільових лідів</TableCell>

              {/* U-AA: Відсотки (розрахунки) */}
              <TableCell sx={{ backgroundColor: COLOR_LIGHT_GREEN }}>% цільових лідів</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_LIGHT_GREEN }}>% не цільових лідів</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_LIGHT_YELLOW }}>% Встан. контакт</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_LIGHT_YELLOW }}>% В опрацюванні (ЦА)</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_LIGHT_YELLOW }}>% конверсія</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_LIGHT_YELLOW }}>% архів</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_LIGHT_YELLOW }}>% недозвон</TableCell>

              {/* AB-AC: Фінансові показники (світло-оранжева заливка) */}
              <TableCell sx={{ backgroundColor: COLOR_LIGHT_ORANGE }}>Ціна / ліда</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_LIGHT_ORANGE }}>Ціна / цільового ліда</TableCell>

              {/* AD: Нотатки (яскраво-жовта заливка) */}
              <TableCell sx={{ backgroundColor: COLOR_BRIGHT_YELLOW }}>Нотатки</TableCell>

              {/* AE-AH: Додаткові метрики пробних (світло-фіолетова заливка) */}
              <TableCell sx={{ backgroundColor: COLOR_LIGHT_PURPLE }}>% Назначений пробний</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_LIGHT_PURPLE }}>% Проведений пробний від загальних лідів</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_LIGHT_PURPLE }}>% Проведений пробний від назначених</TableCell>
              <TableCell sx={{ backgroundColor: COLOR_LIGHT_PURPLE }}>Конверсія з пробного в продаж</TableCell>

              {/* AI: CPC (світло-фіолетова заливка) */}
              <TableCell sx={{ backgroundColor: COLOR_LIGHT_PURPLE }}>CPC</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {students.map((s, idx) => (
              <TableRow key={idx} hover>
                {/* A-F: Основна інформація */}
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

                {/* G: Кількість лідів */}
                <TableCell>{s.leads_count}</TableCell>

                {/* I-R: CRM статуси */}
                <TableCell>{s["Не розібраний"] || 0}</TableCell>
                <TableCell>{s["Встановлено контакт (ЦА)"] || 0}</TableCell>
                <TableCell>{s["В опрацюванні (ЦА)"] || 0}</TableCell>
                <TableCell>{s["Призначено пробне (ЦА)"] || 0}</TableCell>
                <TableCell>{s["Проведено пробне (ЦА)"] || 0}</TableCell>
                <TableCell>{s["Чекає оплату"] || 0}</TableCell>
                <TableCell>{s["Отримана оплата (ЦА)"] || 0}</TableCell>
                <TableCell>{s["Архів (ЦА)"] || 0}</TableCell>
                <TableCell>{s["Недозвон (не ЦА)"] || 0}</TableCell>
                <TableCell>{s["Архів (не ЦА)"] || 0}</TableCell>

                {/* S-T: Кількість (розрахунки) */}
                <TableCell>{s.target_leads || 0}</TableCell>
                <TableCell>{s.non_target_leads || 0}</TableCell>

                {/* U-AA: Відсотки (розрахунки) */}
                <TableCell>{s.percent_target || 0}</TableCell>
                <TableCell>{s.percent_non_target || 0}</TableCell>
                <TableCell>{s.percent_contact || 0}</TableCell>
                <TableCell>{s.percent_in_progress || 0}</TableCell>
                <TableCell>{s.percent_conversion || 0}</TableCell>
                <TableCell>{s.percent_archive || 0}</TableCell>
                <TableCell>{s.percent_no_answer || 0}</TableCell>

                {/* AB-AC: Фінансові показники */}
                <TableCell>{s.price_per_lead || 0}</TableCell>
                <TableCell>{s.price_per_target_lead || 0}</TableCell>

                {/* AD: Нотатки */}
                <TableCell>{s.notes || ""}</TableCell>

                {/* AE-AH: Додаткові метрики пробних */}
                <TableCell>{s.percent_trial_scheduled || 0}</TableCell>
                <TableCell>{s.percent_trial_completed || 0}</TableCell>
                <TableCell>{s.percent_trial_conversion || 0}</TableCell>
                <TableCell>{s.conversion_trial_to_sale || 0}</TableCell>

                {/* AI: CPC */}
                <TableCell>{s.cpc || 0}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </>
  )
}
