-- Seed data for R&D Effort Estimator
-- This creates sample data for testing and demonstration

-- Insert sample companies
INSERT INTO companies (id, name, domain, subscription_plan) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'TechCorp Inc', 'techcorp.com', 'enterprise'),
('550e8400-e29b-41d4-a716-446655440002', 'Research Labs', 'researchlabs.org', 'professional'),
('550e8400-e29b-41d4-a716-446655440003', 'Innovation Hub', 'innovationhub.io', 'free');

-- Insert sample users
INSERT INTO users (id, company_id, email, name, role, department, email_connected) VALUES
-- TechCorp Inc users
('660e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'admin@techcorp.com', 'John Admin', 'admin', 'IT', true),
('660e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440001', 'sarah.johnson@techcorp.com', 'Sarah Johnson', 'user', 'Research', true),
('660e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440001', 'mike.chen@techcorp.com', 'Mike Chen', 'user', 'Data Science', true),
('660e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440001', 'emily.davis@techcorp.com', 'Emily Davis', 'user', 'Research', true),

-- Research Labs users
('660e8400-e29b-41d4-a716-446655440005', '550e8400-e29b-41d4-a716-446655440002', 'admin@researchlabs.org', 'Dr. Lisa Admin', 'admin', 'Administration', true),
('660e8400-e29b-41d4-a716-446655440006', '550e8400-e29b-41d4-a716-446655440002', 'alex.rodriguez@researchlabs.org', 'Alex Rodriguez', 'user', 'ML Engineering', true);

-- Insert sample keywords for each company
INSERT INTO keywords (company_id, keyword, category, weight_minutes, created_by) VALUES
-- TechCorp Inc keywords
('550e8400-e29b-41d4-a716-446655440001', 'machine learning', 'technology', 20, '660e8400-e29b-41d4-a716-446655440001'),
('550e8400-e29b-41d4-a716-446655440001', 'artificial intelligence', 'technology', 25, '660e8400-e29b-41d4-a716-446655440001'),
('550e8400-e29b-41d4-a716-446655440001', 'data analysis', 'analytics', 15, '660e8400-e29b-41d4-a716-446655440001'),
('550e8400-e29b-41d4-a716-446655440001', 'algorithm', 'technology', 18, '660e8400-e29b-41d4-a716-446655440001'),
('550e8400-e29b-41d4-a716-446655440001', 'research', 'process', 12, '660e8400-e29b-41d4-a716-446655440001'),
('550e8400-e29b-41d4-a716-446655440001', 'innovation', 'process', 15, '660e8400-e29b-41d4-a716-446655440001'),
('550e8400-e29b-41d4-a716-446655440001', 'prototype', 'product', 22, '660e8400-e29b-41d4-a716-446655440001'),
('550e8400-e29b-41d4-a716-446655440001', 'experiment', 'process', 10, '660e8400-e29b-41d4-a716-446655440001'),

-- Research Labs keywords
('550e8400-e29b-41d4-a716-446655440002', 'neural network', 'technology', 25, '660e8400-e29b-41d4-a716-446655440005'),
('550e8400-e29b-41d4-a716-446655440002', 'deep learning', 'technology', 23, '660e8400-e29b-41d4-a716-446655440005'),
('550e8400-e29b-41d4-a716-446655440002', 'statistical analysis', 'analytics', 18, '660e8400-e29b-41d4-a716-446655440005'),
('550e8400-e29b-41d4-a716-446655440002', 'methodology', 'process', 12, '660e8400-e29b-41d4-a716-446655440005');

-- Insert sample effort rules
INSERT INTO effort_rules (company_id, rule_name, rule_type, rule_value, created_by) VALUES
-- TechCorp Inc rules
('550e8400-e29b-41d4-a716-446655440001', 'Words to Minutes Ratio', 'word_count', 0.30, '660e8400-e29b-41d4-a716-446655440001'),
('550e8400-e29b-41d4-a716-446655440001', 'PDF Document Multiplier', 'document_type', 1.5, '660e8400-e29b-41d4-a716-446655440001'),
('550e8400-e29b-41d4-a716-446655440001', 'Excel Document Multiplier', 'document_type', 1.2, '660e8400-e29b-41d4-a716-446655440001'),

-- Research Labs rules
('550e8400-e29b-41d4-a716-446655440002', 'Words to Minutes Ratio', 'word_count', 0.25, '660e8400-e29b-41d4-a716-446655440005'),
('550e8400-e29b-41d4-a716-446655440002', 'PDF Document Multiplier', 'document_type', 1.8, '660e8400-e29b-41d4-a716-446655440005'),
('550e8400-e29b-41d4-a716-446655440002', 'Research Paper Multiplier', 'document_type', 2.0, '660e8400-e29b-41d4-a716-446655440005');

-- Insert sample emails
INSERT INTO emails (id, user_id, company_id, email_id, subject, sender_email, sender_name, body_text, received_date, word_count, attachment_count) VALUES
('770e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440001', 'gmail_001', 'Machine Learning Research Findings', 'colleague@techcorp.com', 'Dr. Smith', 'Our latest research on machine learning algorithms shows promising results. The artificial intelligence model we developed demonstrates significant improvements in data analysis accuracy. We need to continue our innovation efforts and develop a prototype for testing.', '2024-01-15 09:30:00', 250, 2),
('770e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440001', 'gmail_002', 'Data Science Project Update', 'manager@techcorp.com', 'Project Manager', 'The data analysis phase is complete. Our algorithm performance has exceeded expectations. The research team should focus on the next experiment phase.', '2024-01-16 14:20:00', 180, 1),
('770e8400-e29b-41d4-a716-446655440003', '660e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440001', 'gmail_003', 'Innovation Workshop Results', 'workshop@techcorp.com', 'Workshop Lead', 'Great innovation ideas emerged from yesterdays workshop. The prototype concepts show real potential for our research and development efforts.', '2024-01-17 11:45:00', 120, 0);

-- Insert sample documents
INSERT INTO documents (id, email_id, company_id, filename, file_type, extracted_text, word_count, ocr_processed) VALUES
('880e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'ml_research_paper.pdf', 'pdf', 'This research paper explores advanced machine learning techniques and their applications in artificial intelligence systems. Our methodology involves comprehensive data analysis and algorithm optimization.', 450, false),
('880e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'experiment_results.xlsx', 'xlsx', 'Experimental data showing algorithm performance metrics, statistical analysis results, and research conclusions.', 200, false),
('880e8400-e29b-41d4-a716-446655440003', '770e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440001', 'project_analysis.docx', 'docx', 'Comprehensive project analysis including data science methodologies, innovation strategies, and prototype development plans.', 320, false);

-- Insert sample keyword matches
INSERT INTO keyword_matches (company_id, keyword_id, email_id, document_id, match_count, confidence_score) VALUES
-- Email keyword matches
('550e8400-e29b-41d4-a716-446655440001', (SELECT id FROM keywords WHERE keyword = 'machine learning' AND company_id = '550e8400-e29b-41d4-a716-446655440001'), '770e8400-e29b-41d4-a716-446655440001', NULL, 2, 0.95),
('550e8400-e29b-41d4-a716-446655440001', (SELECT id FROM keywords WHERE keyword = 'artificial intelligence' AND company_id = '550e8400-e29b-41d4-a716-446655440001'), '770e8400-e29b-41d4-a716-446655440001', NULL, 1, 0.92),
('550e8400-e29b-41d4-a716-446655440001', (SELECT id FROM keywords WHERE keyword = 'data analysis' AND company_id = '550e8400-e29b-41d4-a716-446655440001'), '770e8400-e29b-41d4-a716-446655440001', NULL, 1, 0.88),
('550e8400-e29b-41d4-a716-446655440001', (SELECT id FROM keywords WHERE keyword = 'innovation' AND company_id = '550e8400-e29b-41d4-a716-446655440001'), '770e8400-e29b-41d4-a716-446655440001', NULL, 1, 0.85),
('550e8400-e29b-41d4-a716-446655440001', (SELECT id FROM keywords WHERE keyword = 'prototype' AND company_id = '550e8400-e29b-41d4-a716-446655440001'), '770e8400-e29b-41d4-a716-446655440001', NULL, 1, 0.90),

-- Document keyword matches
('550e8400-e29b-41d4-a716-446655440001', (SELECT id FROM keywords WHERE keyword = 'machine learning' AND company_id = '550e8400-e29b-41d4-a716-446655440001'), NULL, '880e8400-e29b-41d4-a716-446655440001', 3, 0.97),
('550e8400-e29b-41d4-a716-446655440001', (SELECT id FROM keywords WHERE keyword = 'artificial intelligence' AND company_id = '550e8400-e29b-41d4-a716-446655440001'), NULL, '880e8400-e29b-41d4-a716-446655440001', 2, 0.94),
('550e8400-e29b-41d4-a716-446655440001', (SELECT id FROM keywords WHERE keyword = 'algorithm' AND company_id = '550e8400-e29b-41d4-a716-446655440001'), NULL, '880e8400-e29b-41d4-a716-446655440001', 2, 0.91),
('550e8400-e29b-41d4-a716-446655440001', (SELECT id FROM keywords WHERE keyword = 'research' AND company_id = '550e8400-e29b-41d4-a716-446655440001'), NULL, '880e8400-e29b-41d4-a716-446655440001', 4, 0.89);

-- Insert sample effort calculations
INSERT INTO effort_calculations (company_id, user_id, email_id, document_id, base_effort_minutes, keyword_effort_minutes, total_effort_minutes) VALUES
-- Email effort calculations
('550e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440001', NULL, 75, 105, 180), -- 250 words * 0.3 + 6 keywords * avg 17.5 min
('550e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440003', '770e8400-e29b-41d4-a716-446655440002', NULL, 54, 45, 99), -- 180 words * 0.3 + 3 keywords * 15 min
('550e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440004', '770e8400-e29b-41d4-a716-446655440003', NULL, 36, 37, 73), -- 120 words * 0.3 + 2 keywords * avg 18.5 min

-- Document effort calculations
('550e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440002', NULL, '880e8400-e29b-41d4-a716-446655440001', 135, 195, 330), -- 450 words * 0.3 + 11 keywords * avg 17.7 min
('550e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440002', NULL, '880e8400-e29b-41d4-a716-446655440002', 60, 30, 90), -- 200 words * 0.3 + 2 keywords * 15 min
('550e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440003', NULL, '880e8400-e29b-41d4-a716-446655440003', 96, 52, 148); -- 320 words * 0.3 + 3 keywords * avg 17.3 min

-- Insert sample effort summaries
INSERT INTO effort_summaries (company_id, user_id, summary_date, summary_type, total_effort_minutes, email_count, document_count, keyword_matches) VALUES
('550e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440002', '2024-01-15', 'daily', 510, 1, 2, 17),
('550e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440003', '2024-01-16', 'daily', 189, 1, 1, 5),
('550e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440004', '2024-01-17', 'daily', 73, 1, 0, 2);

-- Insert sample notifications
INSERT INTO notifications (company_id, user_id, notification_type, title, message, severity) VALUES
('550e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440001', 'high_activity', 'High R&D Activity Detected', 'Sarah Johnson has logged 510 minutes of R&D effort today, which is above the normal threshold.', 'info'),
('550e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440001', 'scan_complete', 'Daily Email Scan Complete', 'Successfully processed 3 emails and 3 documents for TechCorp Inc.', 'info'),
('550e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440005', 'token_expired', 'Email Token Expiring Soon', 'Alex Rodriguez email access token will expire in 7 days. Please re-authenticate.', 'warning');

-- Insert sample scheduled jobs
INSERT INTO scheduled_jobs (company_id, user_id, job_type, status, started_at, completed_at, processed_count) VALUES
('550e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440002', 'email_scan', 'completed', '2024-01-18 06:00:00', '2024-01-18 06:05:30', 1),
('550e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440003', 'email_scan', 'completed', '2024-01-18 06:00:00', '2024-01-18 06:03:15', 1),
('550e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440004', 'email_scan', 'completed', '2024-01-18 06:00:00', '2024-01-18 06:02:45', 1),
('550e8400-e29b-41d4-a716-446655440001', NULL, 'document_process', 'running', '2024-01-18 06:10:00', NULL, 2),
('550e8400-e29b-41d4-a716-446655440001', NULL, 'effort_calc', 'pending', NULL, NULL, 0);
