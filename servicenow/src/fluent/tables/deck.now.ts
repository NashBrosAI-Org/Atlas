import { Table, StringColumn, ChoiceColumn, ReferenceColumn } from '@servicenow/sdk/core'

// Deck — generated output (pptx or web site).
export const x_atlas_sn_deck = Table({
    name: 'x_atlas_sn_deck',
    label: 'Deck',
    display: 'title',
    allowWebServiceAccess: true,
    schema: {
        title: StringColumn({ label: 'Title', maxLength: 200, mandatory: true }),
        client: ReferenceColumn({ label: 'Client', referenceTable: 'x_atlas_sn_client' }),
        engagement: ReferenceColumn({ label: 'Engagement', referenceTable: 'x_atlas_sn_engagement' }),
        output_type: ChoiceColumn({
            label: 'Output Type',
            choices: { pptx: 'PowerPoint', site: 'Web Site' },
        }),
        location_url: StringColumn({ label: 'Location URL', maxLength: 1000 }),
        status: ChoiceColumn({
            label: 'Status',
            choices: { draft: 'Draft', final: 'Final' },
            default: 'draft',
        }),
    },
})
