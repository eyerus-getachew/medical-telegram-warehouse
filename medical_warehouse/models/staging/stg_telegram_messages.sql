with source as (
    select * from {{ source('raw', 'telegram_messages') }}
),
cleaned as (
    select
        message_id,
        channel_name,
        message_date::timestamptz                           as message_date,
        nullif(trim(message_text), '')                      as message_text,
        coalesce(has_media, false)                          as has_media,
        nullif(trim(image_path), '')                        as image_path,
        greatest(coalesce(views, 0), 0)                     as views,
        greatest(coalesce(forwards, 0), 0)                  as forwards,
        length(trim(coalesce(message_text, '')))            as message_length,
        (image_path is not null and image_path != '')       as has_image,
        loaded_at
    from source
    where
        message_id is not null
        and channel_name is not null
        and message_date is not null
        and message_date <= now()
)
select * from cleaned