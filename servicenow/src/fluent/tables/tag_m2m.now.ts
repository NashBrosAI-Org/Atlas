import { Table, ReferenceColumn, DocumentIdColumn } from '@servicenow/sdk/core'

// TagM2M — polymorphic many-to-many join: a Tag pinned to any record via Document ID.
export const x_atlas_sn_tag_m2m = Table({
    name: 'x_atlas_sn_tag_m2m',
    label: 'Tag M2M',
    allowWebServiceAccess: true,
    schema: {
        tag: ReferenceColumn({ label: 'Tag', referenceTable: 'x_atlas_sn_tag' }),
        target: DocumentIdColumn({ label: 'Target' }),
    },
})
