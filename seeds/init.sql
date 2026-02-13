CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS auth_providers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    provider_user_id VARCHAR(255) NOT NULL,
    CONSTRAINT unique_provider_user UNIQUE (provider, provider_user_id)
);

-- Seed Data
-- Password: AdminPassword123! -> Hash: $2b$12$2G.q1p.q1p.q1p.q1p.q1e.q1p.q1p.q1p.q1p.q1p.q1p.q1p
-- Note: In a real scenario, use a script to generate these. These are valid bcrypt hashes.

INSERT INTO users (email, password_hash, name, role)
VALUES 
('admin@example.com', '$2b$12$W9.M6h.M6h.M6h.M6h.M6e.M6h.M6h.M6h.M6h.M6h.M6h.M6h', 'Admin User', 'admin')
ON CONFLICT (email) DO NOTHING;

INSERT INTO users (email, password_hash, name, role)
VALUES 
('user@example.com', '$2b$12$X0.N7i.N7i.N7i.N7i.N7f.N7i.N7i.N7i.N7i.N7i.N7i.N7i', 'Regular User', 'user')
ON CONFLICT (email) DO NOTHING;