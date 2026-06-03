import { Table, StringColumn } from '@servicenow/sdk/core'

// Tag — cross-cutting label. Name is unique.
export const x_atlas_sn_tag = Table({
    name: 'x_atlas_sn_tag',
    label: 'Tag',
    display: 'name',
    allowWebServiceAccess: true,
    schema: {
        name: StringColumn({ label: 'Name', maxLength: 60, mandatory: true, unique: true }),
    },
})
