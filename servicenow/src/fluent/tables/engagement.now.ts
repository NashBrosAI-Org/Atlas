import { Table, StringColumn, ChoiceColumn, ReferenceColumn, DateColumn } from '@servicenow/sdk/core'

// Engagement (→ future PPM Project). Lightweight custom table for now.
export const x_atlas_sn_engagement = Table({
    name: 'x_atlas_sn_engagement',
    label: 'Engagement',
    display: 'name',
    allowWebServiceAccess: true,
    schema: {
        name: StringColumn({ label: 'Name', maxLength: 120, mandatory: true }),
        client: ReferenceColumn({ label: 'Client', referenceTable: 'x_atlas_sn_client' }),
        status: ChoiceColumn({
            label: 'Status',
            choices: { on_track: 'On Track', at_risk: 'At Risk', blocked: 'Blocked', done: 'Done' },
            default: 'on_track',
        }),
        start_date: DateColumn({ label: 'Start Date' }),
        target_date: DateColumn({ label: 'Target Date' }),
        description: StringColumn({ label: 'Description', maxLength: 4000 }),
    },
})
