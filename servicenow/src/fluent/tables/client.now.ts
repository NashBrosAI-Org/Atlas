import { Table, StringColumn, ChoiceColumn } from '@servicenow/sdk/core'

// Client — the spine entity. Everything hangs off a Client (→ future CSM Account).
export const x_atlas_sn_client = Table({
    name: 'x_atlas_sn_client',
    label: 'Client',
    display: 'name',
    allowWebServiceAccess: true,
    schema: {
        name: StringColumn({ label: 'Name', maxLength: 120, mandatory: true }),
        short_code: StringColumn({ label: 'Short Code', maxLength: 12 }),
        status: ChoiceColumn({
            label: 'Status',
            choices: { active: 'Active', prospect: 'Prospect', dormant: 'Dormant' },
            default: 'active',
        }),
        email_domains: StringColumn({ label: 'Email Domains', maxLength: 500 }),
        // explicit full addresses a client also writes from (off-domain), for email/meeting matching
        email_aliases: StringColumn({ label: 'Email Aliases', maxLength: 500 }),
        notes: StringColumn({ label: 'Notes', maxLength: 4000 }),
    },
})
