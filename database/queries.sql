-- ==========================================
-- AVISCOMPARE
-- Requêtes SQL d'analyse
-- ==========================================


-- 1. Nombre de produits
SELECT COUNT(*) AS nombre_produits
FROM products;


-- 2. Nombre d'avis
SELECT COUNT(*) AS nombre_avis
FROM reviews;


-- 3. Produits les plus commentés
SELECT
    p.name,
    COUNT(r.review_id) AS nb_avis,
    ROUND(AVG(r.rating), 2) AS note_moyenne
FROM products p
JOIN reviews r
    ON p.product_id = r.product_id
GROUP BY p.product_id, p.name
ORDER BY nb_avis DESC
LIMIT 10;


-- 4. Répartition des notes
SELECT
    rating,
    COUNT(*) AS nombre_avis
FROM reviews
GROUP BY rating
ORDER BY rating;


-- 5. Nombre d'achats vérifiés
SELECT
    COUNT(*) AS achats_verifies
FROM reviews
WHERE verified_purchase = TRUE;


-- 6. Produits les mieux notés
SELECT
    p.name,
    p.brand,
    ROUND(AVG(r.rating), 2) AS note_moyenne,
    COUNT(r.review_id) AS nb_avis
FROM products p
JOIN reviews r
    ON p.product_id = r.product_id
GROUP BY
    p.product_id,
    p.name,
    p.brand
HAVING COUNT(r.review_id) >= 2
ORDER BY
    note_moyenne DESC,
    nb_avis DESC
LIMIT 20;