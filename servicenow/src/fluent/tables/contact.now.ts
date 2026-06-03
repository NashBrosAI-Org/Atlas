import { Table, StringColumn, ChoiceColumn, ReferenceColumn } from '@servicenow/sdk/core'

// Contact (→ future CSM Contact). reports_to is a self-reference for the org chart.
export const x_atlas_sn_contact = Table({
    name: 'x_atlas_sn_contact',
    label: 'Contact',
    display: 'name',
    allowWebServiceAccess: true,
    schema: {
        name: StringColumn({ label: 'Name', maxLength: 120, mandatory: true }),
        email: StringColumn({ label: 'Email', maxLength: 120 }),
        phone: StringColumn({ label: 'Phone', maxLength: 40 }),
        client: ReferenceColumn({ label: 'Client', referenceTable: 'x_atlas_sn_client' }),
        role_title: StringColumn({ label: 'Role / Title', maxLength: 120 }),
        reports_to: ReferenceColumn({ label: 'Reports To', referenceTable: 'x_atlas_sn_contact' }),
        personal_notes: StringColumn({ label: 'Personal Notes', maxLength: 4000 }),
        sentiment: ChoiceColumn({
            label: 'Sentiment',
            choices: { champion: 'Champion', neutral: 'Neutral', detractor: 'Detractor' },
            default: 'neutral',
        }),
    },
})
