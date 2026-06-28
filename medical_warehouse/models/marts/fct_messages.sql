with messages as (
    select * from {{ ref('stg_telegram_messages') }}
),
channels as (
    select channel_key, channel_name
    from {{ ref('dim_channels') }}
),
dates as (
    select date_key, full_date
    from {{ ref('dim_dates') }}
),
final as (
    select
        m.message_id,
        c.channel_key,
        d.date_key,
        m.channel_name,
        m.message_text,
        m.message_length,
        m.views,
        m.forwards,
        m.has_media,
        m.has_image,
        m.message_date,
        m.loaded_at
    from messages m
    left join channels c using (channel_name)
    left join dates d on d.full_date = m.message_date::date
)
select * from final