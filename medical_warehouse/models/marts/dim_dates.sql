with date_range as (
    select
        min(message_date::date) as min_date,
        max(message_date::date) as max_date
    from {{ ref('stg_telegram_messages') }}
),
date_series as (
    select generate_series(
        (select min_date from date_range),
        (select max_date from date_range),
        interval '1 day'
    )::date as full_date
),
final as (
    select
        to_char(full_date, 'YYYYMMDD')::integer         as date_key,
        full_date,
        extract(dow from full_date)::integer            as day_of_week,
        to_char(full_date, 'Day')                       as day_name,
        extract(day from full_date)::integer            as day_of_month,
        extract(week from full_date)::integer           as week_of_year,
        extract(month from full_date)::integer          as month,
        to_char(full_date, 'Month')                     as month_name,
        extract(quarter from full_date)::integer        as quarter,
        extract(year from full_date)::integer           as year,
        extract(dow from full_date) in (0, 6)           as is_weekend
    from date_series
)
select * from final