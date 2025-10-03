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
}

export default function StudentsTable({ students }: StudentsTableProps) {
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
              <TableCell>{s.leads_check}</TableCell>
              <TableCell>{s.not_processed}</TableCell>
              <TableCell>{s.contacted}</TableCell>
              <TableCell>{s.in_progress}</TableCell>
              <TableCell>{s.trial_scheduled}</TableCell>
              <TableCell>{s.trial_completed}</TableCell>
              <TableCell>{s.awaiting_payment}</TableCell>
              <TableCell>{s.purchased}</TableCell>
              <TableCell>{s.archived}</TableCell>
              <TableCell>{s.not_reached}</TableCell>
              <TableCell>{s.archived_non_target}</TableCell>
              <TableCell>{s.target_leads}</TableCell>
              <TableCell>{s.non_target_leads}</TableCell>
              <TableCell>{s.target_percent}</TableCell>
              <TableCell>{s.non_target_percent}</TableCell>
              <TableCell>{s.contact_percent}</TableCell>
              <TableCell>{s.in_progress_percent}</TableCell>
              <TableCell>{s.conversion_percent}</TableCell>
              <TableCell>{s.archive_percent}</TableCell>
              <TableCell>{s.not_reached_percent}</TableCell>
              <TableCell>{s.cost_per_lead}</TableCell>
              <TableCell>{s.cost_per_target_lead}</TableCell>
              <TableCell>{s.notes}</TableCell>
              <TableCell>{s.trial_scheduled_percent}</TableCell>
              <TableCell>{s.trial_completed_from_total_percent}</TableCell>
              <TableCell>{s.trial_completed_from_scheduled_percent}</TableCell>
              <TableCell>{s.trial_to_purchase_percent}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
    </>
  )
}
