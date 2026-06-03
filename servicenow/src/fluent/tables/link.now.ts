import { Table, StringColumn, ReferenceColumn } from '@servicenow/sdk/core'

// Link — a URL resource attached to a client.
export const x_atlas_sn_link = Table({
    name: 'x_atlas_sn_link',
    label: 'Link',
    display: 'title',
    allowWebServiceAccess: true,
    schema: {
        title: StringColumn({ label: 'Title', maxLength: 200, mandatory: true }),
        url: StringColumn({ label: 'URL', maxLength: 1000 }),
        client: ReferenceColumn({ label: 'Client', referenceTable: 'x_atlas_sn_client' }),
    },
})
