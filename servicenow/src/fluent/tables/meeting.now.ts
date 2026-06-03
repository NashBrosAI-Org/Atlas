import { Table, StringColumn, ChoiceColumn, ReferenceColumn, DateTimeColumn } from '@servicenow/sdk/core'

// Meeting — has an attached Transcript (see transcript.now.ts).
export const x_atlas_sn_meeting = Table({
    name: 'x_atlas_sn_meeting',
    label: 'Meeting',
    display: 'title',
    allowWebServiceAccess: true,
    schema: {
        title: StringColumn({ label: 'Title', maxLength: 200, mandatory: true }),
        client: ReferenceColumn({ label: 'Client', referenceTable: 'x_atlas_sn_client' }),
        engagement: ReferenceColumn({ label: 'Engagement', referenceTable: 'x_atlas_sn_engagement' }),
        datetime: DateTimeColumn({ label: 'Date/Time' }),
        type: ChoiceColumn({
            label: 'Type',
            choices: { teams: 'Teams', zoom: 'Zoom', other: 'Other' },
            default: 'teams',
        }),
        attendees: StringColumn({ label: 'Attendees', maxLength: 1000 }),
        summary: StringColumn({ label: 'Summary', maxLength: 8000 }),
    },
})
