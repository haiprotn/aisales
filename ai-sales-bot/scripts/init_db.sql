-- AI Sales Bot - Database Schema
-- PostgreSQL 15+

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    category VARCHAR(200),
    price DECIMAL(15, 2),
    original_price DECIMAL(15, 2),
    description TEXT,
    specifications JSONB DEFAULT '{}',
    images TEXT[] DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',
    source VARCHAR(100) DEFAULT 'manual',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_content (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    title VARCHAR(500),
    body TEXT,
    hashtags TEXT[] DEFAULT '{}',
    cta VARCHAR(300),
    tone VARCHAR(100) DEFAULT 'professional',
    language VARCHAR(10) DEFAULT 'vi',
    generated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    content_id INTEGER REFERENCES ai_content(id),
    platform VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'draft',
    scheduled_at TIMESTAMP,
    published_at TIMESTAMP,
    platform_post_id VARCHAR(200),
    platform_url TEXT,
    engagement JSONB DEFAULT '{"likes": 0, "comments": 0, "shares": 0}',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS schedules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200),
    platforms TEXT[] DEFAULT '{}',
    posts_per_day INTEGER DEFAULT 10,
    start_hour INTEGER DEFAULT 8,
    end_hour INTEGER DEFAULT 22,
    days_of_week INTEGER[] DEFAULT '{1,2,3,4,5,6,7}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS comments (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES posts(id),
    platform VARCHAR(50),
    platform_comment_id VARCHAR(200),
    author_name VARCHAR(200),
    author_id VARCHAR(200),
    content TEXT,
    ai_reply TEXT,
    reply_status VARCHAR(50) DEFAULT 'pending',
    replied_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS activity_log (
    id SERIAL PRIMARY KEY,
    action VARCHAR(100),
    entity_type VARCHAR(50),
    entity_id INTEGER,
    details JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'success',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_posts_status ON posts(status);
CREATE INDEX idx_posts_platform ON posts(platform);
CREATE INDEX idx_posts_scheduled ON posts(scheduled_at);
CREATE INDEX idx_comments_reply_status ON comments(reply_status);
CREATE INDEX idx_activity_log_created ON activity_log(created_at);
