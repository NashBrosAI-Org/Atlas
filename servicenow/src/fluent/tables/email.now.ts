import { Table, StringColumn, ReferenceColumn, DateTimeColumn } from '@servicenow/sdk/core'

// Email — the retained content (subject/body/graph_message_id). graph_message_id is unique.
export const x_atlas_sn_email = Table({
    name: 'x_atlas_sn_email',
    label: 'Email',
    display: 'subject',
    allowWebServiceAccess: true,
    schema: {
        subject: StringColumn({ label: 'Subject', maxLength: 300, mandatory: true }),
        client: ReferenceColumn({ label: 'Client', referenceTable: 'x_atlas_sn_client' }),
        from_addr: StringColumn({ label: 'From', maxLength: 200 }),
        to_addr: StringColumn({ label: 'To', maxLength: 1000 }),
        received_date: DateTimeColumn({ label: 'Received Date' }),
        body: StringColumn({ label: 'Body', maxLength: 1000000 }),
        graph_message_id: StringColumn({ label: 'Graph Message ID', maxLength: 200, unique: true }),
    },
})
