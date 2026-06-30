with detections as (
    select
        message_id,
        channel_name,
        detected_class,
        confidence_score::numeric(6,4)      as confidence_score,
        image_category,
        total_detections,
        processed_at::timestamptz           as processed_at
    from {{ source('raw', 'image_detections') }}
    where detected_class is not null
),
messages as (
    select
        message_id,
        channel_key,
        date_key,
        channel_name,
        views,
        forwards,
        has_image,
        message_date
    from {{ ref('fct_messages') }}
),
final as (
    select
        d.message_id,
        m.channel_key,
        m.date_key,
        d.channel_name,
        d.detected_class,
        d.confidence_score,
        d.image_category,
        d.total_detections,
        m.views,
        m.forwards,
        m.message_date,
        d.processed_at
    from detections d
    left join messages m
        on  m.message_id    = d.message_id
        and m.channel_name  = d.channel_name
)
select * from final