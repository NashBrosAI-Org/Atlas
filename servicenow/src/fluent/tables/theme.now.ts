import { Table, StringColumn, ChoiceColumn, ReferenceColumn } from '@servicenow/sdk/core'

// Theme — a cross-cutting concern for a client (non-Agile sense).
export const x_atlas_sn_theme = Table({
    name: 'x_atlas_sn_theme',
    label: 'Theme',
    display: 'name',
    allowWebServiceAccess: true,
    schema: {
        name: StringColumn({ label: 'Name', maxLength: 120, mandatory: true }),
        client: ReferenceColumn({ label: 'Client', referenceTable: 'x_atlas_sn_client' }),
        status: ChoiceColumn({
            label: 'Status',
            choices: { open: 'Open', watching: 'Watching', resolved: 'Resolved' },
            default: 'open',
        }),
        description: StringColumn({ label: 'Description', maxLength: 4000 }),
    },
})
