-- ==========================================
-- AVISCOMPARE
-- Schéma relationnel PostgreSQL
-- ==========================================

-- ==========================================
-- TABLE PRODUCTS
-- ==========================================

CREATE TABLE IF NOT EXISTS products (

    product_id INTEGER PRIMARY KEY,

    parent_asin VARCHAR(20) UNIQUE NOT NULL,

    name TEXT NOT NULL,

    brand VARCHAR(255),

    category VARCHAR(255),

    price NUMERIC(10, 2),

    average_rating NUMERIC(3, 2),

    rating_number INTEGER,

    source VARCHAR(100) NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- TABLE SHOPS
-- ==========================================

CREATE TABLE IF NOT EXISTS shops (

    shop_id SERIAL PRIMARY KEY,

    name VARCHAR(255) UNIQUE NOT NULL,

    website_url TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- TABLE REVIEWS
-- ==========================================

CREATE TABLE IF NOT EXISTS reviews (

    review_id INTEGER PRIMARY KEY,

    product_id INTEGER NOT NULL,

    rating NUMERIC(2, 1) NOT NULL,

    title TEXT,

    review_text TEXT NOT NULL,

    review_date DATE,

    helpful_vote INTEGER DEFAULT 0,

    verified_purchase BOOLEAN DEFAULT FALSE,

    source VARCHAR(100) NOT NULL,

    CONSTRAINT fk_review_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
        ON DELETE CASCADE,

    CONSTRAINT valid_review_rating
        CHECK (rating >= 1 AND rating <= 5),

    CONSTRAINT positive_helpful_vote
        CHECK (helpful_vote >= 0)
);

-- ==========================================
-- TABLE OFFERS
-- ==========================================

CREATE TABLE IF NOT EXISTS offers (

    offer_id SERIAL PRIMARY KEY,

    product_id INTEGER NOT NULL,

    shop_id INTEGER NOT NULL,

    price NUMERIC(10, 2),

    availability VARCHAR(100),

    product_url TEXT,

    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_offer_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_offer_shop
        FOREIGN KEY (shop_id)
        REFERENCES shops(shop_id)
        ON DELETE CASCADE,

    CONSTRAINT positive_price
        CHECK (price IS NULL OR price >= 0)
);

-- ==========================================
-- INDEX
-- ==========================================

CREATE INDEX IF NOT EXISTS idx_products_name
ON products(name);

CREATE INDEX IF NOT EXISTS idx_products_brand
ON products(brand);

CREATE INDEX IF NOT EXISTS idx_reviews_product
ON reviews(product_id);

CREATE INDEX IF NOT EXISTS idx_reviews_rating
ON reviews(rating);

CREATE INDEX IF NOT EXISTS idx_offers_product
ON offers(product_id);

CREATE INDEX IF NOT EXISTS idx_offers_shop
ON offers(shop_id);