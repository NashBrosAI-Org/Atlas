import { Table, StringColumn, ChoiceColumn, ReferenceColumn, DateColumn, BooleanColumn } from '@servicenow/sdk/core'

// Task — the spine of the "Now" view. Commitments = is_commitment + promised_date.
export const x_atlas_sn_task = Table({
    name: 'x_atlas_sn_task',
    label: 'Task',
    display: 'title',
    allowWebServiceAccess: true,
    schema: {
        title: StringColumn({ label: 'Title', maxLength: 200, mandatory: true }),
        client: ReferenceColumn({ label: 'Client', referenceTable: 'x_atlas_sn_client' }),
        engagement: ReferenceColumn({ label: 'Engagement', referenceTable: 'x_atlas_sn_engagement' }),
        theme: ReferenceColumn({ label: 'Theme', referenceTable: 'x_atlas_sn_theme' }),
        priority: ChoiceColumn({
            label: 'Priority',
            choices: { critical: 'Critical', high: 'High', medium: 'Medium', low: 'Low' },
            default: 'medium',
        }),
        due_date: DateColumn({ label: 'Due Date' }),
        promised_date: DateColumn({ label: 'Promised Date' }),
        is_commitment: BooleanColumn({ label: 'Is Commitment', default: false }),
        status: ChoiceColumn({
            label: 'Status',
            choices: { open: 'Open', in_progress: 'In Progress', waiting: 'Waiting', done: 'Done' },
            default: 'open',
        }),
        source: ChoiceColumn({
            label: 'Source',
            choices: { manual: 'Manual', email: 'Email', meeting: 'Meeting' },
            default: 'manual',
        }),
    },
})
