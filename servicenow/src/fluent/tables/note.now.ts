import { Table, StringColumn, ChoiceColumn, BooleanColumn, DocumentIdColumn } from '@servicenow/sdk/core'

// Note — polymorphic pin via Document ID `target`. note_type models RAID
// (general/risk/issue/decision) rather than a separate table.
export const x_atlas_sn_note = Table({
    name: 'x_atlas_sn_note',
    label: 'Note',
    display: 'title',
    allowWebServiceAccess: true,
    schema: {
        title: StringColumn({ label: 'Title', maxLength: 200, mandatory: true }),
        body: StringColumn({ label: 'Body', maxLength: 8000 }),
        note_type: ChoiceColumn({
            label: 'Note Type',
            choices: { general: 'General', risk: 'Risk', issue: 'Issue', decision: 'Decision' },
            default: 'general',
        }),
        target: DocumentIdColumn({ label: 'Target' }),
        pinned: BooleanColumn({ label: 'Pinned', default: false }),
    },
})
