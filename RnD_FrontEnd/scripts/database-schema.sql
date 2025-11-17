-- R&D Effort Estimator Database Schema
-- Multi-tenant architecture with proper relationships

-- Companies table (tenant isolation)
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) UNIQUE NOT NULL,
    subscription_plan VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users table with role-based access
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('super_admin', 'admin', 'user')),
    department VARCHAR(100),
    email_connected BOOLEAN DEFAULT FALSE,
    email_provider VARCHAR(50), -- 'google' or 'microsoft'
    email_token_encrypted TEXT,
    last_scan_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, email)
);

-- Email processing table
CREATE TABLE emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    email_id VARCHAR(255) NOT NULL, -- External email ID from provider
    subject TEXT,
    sender_email VARCHAR(255),
    sender_name VARCHAR(255),
    body_text TEXT,
    body_html TEXT,
    received_date TIMESTAMP NOT NULL,
    processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    word_count INTEGER DEFAULT 0,
    attachment_count INTEGER DEFAULT 0,
    INDEX(company_id, user_id, received_date),
    UNIQUE(user_id, email_id)
);

-- Document attachments table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_id UUID NOT NULL REFERENCES emails(id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size INTEGER,
    extracted_text TEXT,
    word_count INTEGER DEFAULT 0,
    ocr_processed BOOLEAN DEFAULT FALSE,
    processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX(company_id, file_type)
);

-- Keywords configuration per company
CREATE TABLE keywords (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    keyword VARCHAR(255) NOT NULL,
    category VARCHAR(100), -- 'technology', 'research', 'product', etc.
    weight_minutes INTEGER DEFAULT 15, -- effort weight in minutes
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, keyword)
);

-- Detected keywords in content
CREATE TABLE keyword_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    keyword_id UUID NOT NULL REFERENCES keywords(id) ON DELETE CASCADE,
    email_id UUID REFERENCES emails(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    match_count INTEGER DEFAULT 1,
    confidence_score DECIMAL(3,2), -- NLP confidence score
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX(company_id, keyword_id, detected_at),
    CHECK ((email_id IS NOT NULL) OR (document_id IS NOT NULL))
);

-- Effort calculation rules per company
CREATE TABLE effort_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    rule_name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(50) NOT NULL, -- 'word_count', 'keyword_weight', 'document_type'
    rule_value DECIMAL(10,2) NOT NULL, -- e.g., 0.3 for words-to-minutes ratio
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, rule_name)
);

-- Calculated effort results
CREATE TABLE effort_calculations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email_id UUID REFERENCES emails(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    base_effort_minutes INTEGER DEFAULT 0, -- from word count
    keyword_effort_minutes INTEGER DEFAULT 0, -- from keywords
    total_effort_minutes INTEGER NOT NULL,
    calculation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rules_version INTEGER DEFAULT 1, -- track which rules were used
    INDEX(company_id, user_id, calculation_date),
    CHECK ((email_id IS NOT NULL) OR (document_id IS NOT NULL))
);

-- Aggregated effort summaries (for performance)
CREATE TABLE effort_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    summary_date DATE NOT NULL,
    summary_type VARCHAR(20) NOT NULL, -- 'daily', 'weekly', 'monthly'
    total_effort_minutes INTEGER NOT NULL,
    email_count INTEGER DEFAULT 0,
    document_count INTEGER DEFAULT 0,
    keyword_matches INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, user_id, summary_date, summary_type)
);

-- System notifications and alerts
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    notification_type VARCHAR(50) NOT NULL, -- 'high_activity', 'scan_error', 'token_expired'
    title VARCHAR(255) NOT NULL,
    message TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    severity VARCHAR(20) DEFAULT 'info', -- 'info', 'warning', 'error'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX(company_id, user_id, is_read, created_at)
);

-- Audit log for tracking changes
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL, -- 'create_keyword', 'update_rule', 'delete_user'
    entity_type VARCHAR(50) NOT NULL, -- 'keyword', 'rule', 'user'
    entity_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX(company_id, user_id, created_at)
);

-- Scheduled jobs tracking
CREATE TABLE scheduled_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL, -- 'email_scan', 'document_process', 'effort_calc'
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    processed_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX(company_id, job_type, status, created_at)
);

-- Create indexes for performance
CREATE INDEX idx_emails_company_user_date ON emails(company_id, user_id, received_date DESC);
CREATE INDEX idx_documents_company_type ON documents(company_id, file_type);
CREATE INDEX idx_keyword_matches_company_date ON keyword_matches(company_id, detected_at DESC);
CREATE INDEX idx_effort_calculations_company_user_date ON effort_calculations(company_id, user_id, calculation_date DESC);
CREATE INDEX idx_notifications_company_unread ON notifications(company_id, is_read, created_at DESC);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_keywords_updated_at BEFORE UPDATE ON keywords FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_effort_rules_updated_at BEFORE UPDATE ON effort_rules FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
