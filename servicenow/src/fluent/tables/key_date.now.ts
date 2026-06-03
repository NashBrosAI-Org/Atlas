import { Table, StringColumn, ChoiceColumn, ReferenceColumn, DateColumn, BooleanColumn, IntegerColumn } from '@servicenow/sdk/core'

// KeyDate — renewal / qbr / contract_end / birthday / milestone, with reminder lead time.
export const x_atlas_sn_key_date = Table({
    name: 'x_atlas_sn_key_date',
    label: 'Key Date',
    display: 'title',
    allowWebServiceAccess: true,
    schema: {
        title: StringColumn({ label: 'Title', maxLength: 200, mandatory: true }),
        type: ChoiceColumn({
            label: 'Type',
            choices: {
                renewal: 'Renewal',
                qbr: 'QBR',
                contract_end: 'Contract End',
                birthday: 'Birthday',
                milestone: 'Milestone',
            },
        }),
        date: DateColumn({ label: 'Date' }),
        recurring: BooleanColumn({ label: 'Recurring', default: false }),
        reminder_lead_days: IntegerColumn({ label: 'Reminder Lead Days', default: 7 }),
        client: ReferenceColumn({ label: 'Client', referenceTable: 'x_atlas_sn_client' }),
        contact: ReferenceColumn({ label: 'Contact', referenceTable: 'x_atlas_sn_contact' }),
    },
})
