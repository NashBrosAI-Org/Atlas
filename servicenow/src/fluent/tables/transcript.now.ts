import { Table, StringColumn, ChoiceColumn, ReferenceColumn, DateTimeColumn } from '@servicenow/sdk/core'

// Transcript — full text retained in SN (bulky raw kept per the backup rule).
export const x_atlas_sn_transcript = Table({
    name: 'x_atlas_sn_transcript',
    label: 'Transcript',
    allowWebServiceAccess: true,
    schema: {
        meeting: ReferenceColumn({ label: 'Meeting', referenceTable: 'x_atlas_sn_meeting' }),
        client: ReferenceColumn({ label: 'Client', referenceTable: 'x_atlas_sn_client' }),
        full_text: StringColumn({ label: 'Full Text', maxLength: 1000000 }),
        source: ChoiceColumn({
            label: 'Source',
            choices: { teams: 'Teams', zoom: 'Zoom', manual: 'Manual' },
            default: 'manual',
        }),
        captured_date: DateTimeColumn({ label: 'Captured Date' }),
    },
})
