-- =====================================================================
-- Central Asia: countries + cities seed data
-- Idempotent — safe to run multiple times, only inserts rows that don't
-- already exist (checked by country code, and by country_id + city name).
--
-- Standard / UN definition of Central Asia = these 5 countries:
--   KZ  Kazakhstan
--   KG  Kyrgyzstan
--   TJ  Tajikistan
--   TM  Turkmenistan
--   UZ  Uzbekistan
--
-- Uses gen_random_uuid(), built into Postgres 13+.
-- If your server is older, run this first:
--   CREATE EXTENSION IF NOT EXISTS pgcrypto;
-- =====================================================================

BEGIN;

-- 1. Countries -----------------------------------------------------------
INSERT INTO countries (code, name, id, created_at, updated_at)
SELECT v.code, v.name, gen_random_uuid(), now(), now()
FROM (VALUES
    ('KZ', 'Kazakhstan'),
    ('KG', 'Kyrgyzstan'),
    ('TJ', 'Tajikistan'),
    ('TM', 'Turkmenistan'),
    ('UZ', 'Uzbekistan')
) AS v(code, name)
WHERE NOT EXISTS (
    SELECT 1 FROM countries c WHERE c.code = v.code
);

-- 2. Cities ----------------------------------------------------------------
-- Major cities per country. Names match the spellings already in your DB
-- (e.g. Türkmenbaşy, Türkmenabat) so this won't create spelling-variant
-- duplicates of rows that already exist.
INSERT INTO cities (country_id, name, id, created_at, updated_at)
SELECT c.id, v.name, gen_random_uuid(), now(), now()
FROM (VALUES
    -- Kazakhstan (largest city, capital, all 17 region capitals + cities of republican significance)
    ('KZ','Almaty'),
    ('KZ','Astana'),
    ('KZ','Shymkent'),
    ('KZ','Karaganda'),
    ('KZ','Aktobe'),
    ('KZ','Taraz'),
    ('KZ','Pavlodar'),
    ('KZ','Oskemen'),
    ('KZ','Semey'),
    ('KZ','Atyrau'),
    ('KZ','Kostanay'),
    ('KZ','Kyzylorda'),
    ('KZ','Oral'),
    ('KZ','Petropavl'),
    ('KZ','Turkistan'),
    ('KZ','Kokshetau'),
    ('KZ','Taldykorgan'),
    ('KZ','Zhezkazgan'),
    ('KZ','Aktau'),

    -- Kyrgyzstan (capital + Osh + all 7 oblast/city-significance centers)
    ('KG','Bishkek'),
    ('KG','Osh'),
    ('KG','Jalal-Abad'),
    ('KG','Karakol'),
    ('KG','Talas'),
    ('KG','Naryn'),
    ('KG','Batken'),
    ('KG','Tokmok'),

    -- Tajikistan (capital + region centers + other major historic cities)
    ('TJ','Dushanbe'),
    ('TJ','Khujand'),
    ('TJ','Bokhtar'),
    ('TJ','Kulob'),
    ('TJ','Istaravshan'),
    ('TJ','Panjakent'),
    ('TJ','Khorugh'),

    -- Turkmenistan (capital + all 5 welayat administrative centers)
    ('TM','Ashgabat'),
    ('TM','Türkmenabat'),
    ('TM','Dashoguz'),
    ('TM','Mary'),
    ('TM','Balkanabat'),
    ('TM','Türkmenbaşy'),

    -- Uzbekistan (capital + all 12 region capitals + Karakalpakstan + other major cities)
    ('UZ','Tashkent'),
    ('UZ','Samarkand'),
    ('UZ','Bukhara'),
    ('UZ','Namangan'),
    ('UZ','Andijan'),
    ('UZ','Fergana'),
    ('UZ','Nukus'),
    ('UZ','Karshi'),
    ('UZ','Urgench'),
    ('UZ','Termez'),
    ('UZ','Navoi'),
    ('UZ','Jizzakh'),
    ('UZ','Gulistan'),
    ('UZ','Nurafshon'),
    ('UZ','Chirchiq'),
    ('UZ','Kokand'),
    ('UZ','Margilan'),
    ('UZ','Shahrisabz')
) AS v(country_code, name)
JOIN countries c ON c.code = v.country_code
WHERE NOT EXISTS (
    SELECT 1 FROM cities ci WHERE ci.country_id = c.id AND ci.name = v.name
);

COMMIT;

-- 3. Verify ------------------------------------------------------------------
SELECT co.code, co.name AS country, ci.name AS city
FROM countries co
JOIN cities ci ON ci.country_id = co.id
WHERE co.code IN ('KZ','KG','TJ','TM','UZ')
ORDER BY co.name, ci.name;


-- =====================================================================
-- OPTIONAL: Afghanistan
-- Strict Central Asia is the 5 countries above. Afghanistan is included
-- in some broader regional groupings (UN-SPECA, CAREC). Uncomment if you
-- want it on your platform too.
-- =====================================================================
-- INSERT INTO countries (code, name, id, created_at, updated_at)
-- SELECT 'AF', 'Afghanistan', gen_random_uuid(), now(), now()
-- WHERE NOT EXISTS (SELECT 1 FROM countries WHERE code = 'AF');
--
-- INSERT INTO cities (country_id, name, id, created_at, updated_at)
-- SELECT c.id, v.name, gen_random_uuid(), now(), now()
-- FROM (VALUES
--     ('Kabul'),
--     ('Kandahar'),
--     ('Herat'),
--     ('Mazar-i-Sharif'),
--     ('Jalalabad'),
--     ('Kunduz'),
--     ('Ghazni')
-- ) AS v(name)
-- JOIN countries c ON c.code = 'AF'
-- WHERE NOT EXISTS (
--     SELECT 1 FROM cities ci WHERE ci.country_id = c.id AND ci.name = v.name
-- );