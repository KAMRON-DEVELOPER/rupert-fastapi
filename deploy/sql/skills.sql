-- ============================================================
-- Skill taxonomy seed data for the `skills` table
-- Covers all Specialization enum values (frontend, backend, ios,
-- android, devops, ml, security, game, qa, ui_ux, etc.)
--
-- Notes:
--   * gen_random_uuid() is built into PostgreSQL core since v13.
--     If you're on an older version, uncomment the line below.
--   * Skills are de-duplicated across specializations (e.g. "Python"
--     is listed once even though it's relevant to backend, data
--     science, and ML) since `skills.name` has a UNIQUE index.
--   * ON CONFLICT (name) DO NOTHING makes this script safely
--     re-runnable.
-- ============================================================

-- CREATE EXTENSION IF NOT EXISTS pgcrypto; -- only needed on PostgreSQL < 13

INSERT INTO skills (id, name, created_at, updated_at) VALUES
-- ---------- frontend ----------
(gen_random_uuid(), 'JavaScript', now(), now()),
(gen_random_uuid(), 'TypeScript', now(), now()),
(gen_random_uuid(), 'React', now(), now()),
(gen_random_uuid(), 'Vue.js', now(), now()),
(gen_random_uuid(), 'Angular', now(), now()),
(gen_random_uuid(), 'Svelte', now(), now()),
(gen_random_uuid(), 'HTML5', now(), now()),
(gen_random_uuid(), 'CSS3', now(), now()),
(gen_random_uuid(), 'Sass/SCSS', now(), now()),
(gen_random_uuid(), 'Tailwind CSS', now(), now()),
(gen_random_uuid(), 'Next.js', now(), now()),
(gen_random_uuid(), 'Webpack', now(), now()),
(gen_random_uuid(), 'Vite', now(), now()),
(gen_random_uuid(), 'Redux', now(), now()),
(gen_random_uuid(), 'Web Accessibility (WCAG)', now(), now()),
(gen_random_uuid(), 'Progressive Web Apps', now(), now()),
(gen_random_uuid(), 'jQuery', now(), now()),
(gen_random_uuid(), 'Three.js', now(), now()),

-- ---------- backend ----------
(gen_random_uuid(), 'Python', now(), now()),
(gen_random_uuid(), 'Java', now(), now()),
(gen_random_uuid(), 'Node.js', now(), now()),
(gen_random_uuid(), 'Go', now(), now()),
(gen_random_uuid(), 'Ruby', now(), now()),
(gen_random_uuid(), 'PHP', now(), now()),
(gen_random_uuid(), 'C#', now(), now()),
(gen_random_uuid(), '.NET', now(), now()),
(gen_random_uuid(), 'Django', now(), now()),
(gen_random_uuid(), 'FastAPI', now(), now()),
(gen_random_uuid(), 'Flask', now(), now()),
(gen_random_uuid(), 'Express.js', now(), now()),
(gen_random_uuid(), 'Spring Boot', now(), now()),
(gen_random_uuid(), 'Ruby on Rails', now(), now()),
(gen_random_uuid(), 'Laravel', now(), now()),
(gen_random_uuid(), 'NestJS', now(), now()),
(gen_random_uuid(), 'REST API Design', now(), now()),
(gen_random_uuid(), 'GraphQL', now(), now()),
(gen_random_uuid(), 'Microservices', now(), now()),
(gen_random_uuid(), 'gRPC', now(), now()),
(gen_random_uuid(), 'RabbitMQ', now(), now()),
(gen_random_uuid(), 'Apache Kafka', now(), now()),
(gen_random_uuid(), 'PostgreSQL', now(), now()),
(gen_random_uuid(), 'MySQL', now(), now()),
(gen_random_uuid(), 'MongoDB', now(), now()),
(gen_random_uuid(), 'Redis', now(), now()),

-- ---------- ios ----------
(gen_random_uuid(), 'Swift', now(), now()),
(gen_random_uuid(), 'Objective-C', now(), now()),
(gen_random_uuid(), 'SwiftUI', now(), now()),
(gen_random_uuid(), 'UIKit', now(), now()),
(gen_random_uuid(), 'Xcode', now(), now()),
(gen_random_uuid(), 'Core Data', now(), now()),
(gen_random_uuid(), 'Combine', now(), now()),
(gen_random_uuid(), 'ARKit', now(), now()),

-- ---------- android ----------
(gen_random_uuid(), 'Kotlin', now(), now()),
(gen_random_uuid(), 'Android SDK', now(), now()),
(gen_random_uuid(), 'Jetpack Compose', now(), now()),
(gen_random_uuid(), 'Room', now(), now()),
(gen_random_uuid(), 'RxJava', now(), now()),
(gen_random_uuid(), 'Android NDK', now(), now()),

-- ---------- cross_platform_mobile ----------
(gen_random_uuid(), 'React Native', now(), now()),
(gen_random_uuid(), 'Flutter', now(), now()),
(gen_random_uuid(), 'Dart', now(), now()),
(gen_random_uuid(), 'Xamarin', now(), now()),
(gen_random_uuid(), 'Ionic', now(), now()),
(gen_random_uuid(), 'Kotlin Multiplatform', now(), now()),

-- ---------- desktop ----------
(gen_random_uuid(), 'Electron', now(), now()),
(gen_random_uuid(), 'Qt', now(), now()),
(gen_random_uuid(), 'WPF', now(), now()),
(gen_random_uuid(), 'JavaFX', now(), now()),
(gen_random_uuid(), '.NET MAUI', now(), now()),
(gen_random_uuid(), 'GTK', now(), now()),
(gen_random_uuid(), 'Tauri', now(), now()),

-- ---------- embedded ----------
(gen_random_uuid(), 'C', now(), now()),
(gen_random_uuid(), 'C++', now(), now()),
(gen_random_uuid(), 'Embedded C', now(), now()),
(gen_random_uuid(), 'RTOS', now(), now()),
(gen_random_uuid(), 'FreeRTOS', now(), now()),
(gen_random_uuid(), 'Embedded Linux', now(), now()),
(gen_random_uuid(), 'I2C/SPI/UART', now(), now()),
(gen_random_uuid(), 'Microcontrollers (ARM)', now(), now()),

-- ---------- systems ----------
(gen_random_uuid(), 'Rust', now(), now()),
(gen_random_uuid(), 'Operating Systems', now(), now()),
(gen_random_uuid(), 'Linux Kernel', now(), now()),
(gen_random_uuid(), 'Memory Management', now(), now()),
(gen_random_uuid(), 'Concurrency', now(), now()),
(gen_random_uuid(), 'Compilers', now(), now()),

-- ---------- firmware ----------
(gen_random_uuid(), 'Firmware Development', now(), now()),
(gen_random_uuid(), 'Bootloaders', now(), now()),
(gen_random_uuid(), 'Device Drivers', now(), now()),
(gen_random_uuid(), 'JTAG Debugging', now(), now()),
(gen_random_uuid(), 'Assembly Language', now(), now()),

-- ---------- devops ----------
(gen_random_uuid(), 'Docker', now(), now()),
(gen_random_uuid(), 'Kubernetes', now(), now()),
(gen_random_uuid(), 'CI/CD', now(), now()),
(gen_random_uuid(), 'Jenkins', now(), now()),
(gen_random_uuid(), 'GitHub Actions', now(), now()),
(gen_random_uuid(), 'GitLab CI', now(), now()),
(gen_random_uuid(), 'Terraform', now(), now()),
(gen_random_uuid(), 'Ansible', now(), now()),
(gen_random_uuid(), 'Linux Administration', now(), now()),
(gen_random_uuid(), 'Bash Scripting', now(), now()),
(gen_random_uuid(), 'Nginx', now(), now()),
(gen_random_uuid(), 'Prometheus', now(), now()),
(gen_random_uuid(), 'Loki', now(), now()),
(gen_random_uuid(), 'Grafana', now(), now()),
(gen_random_uuid(), 'Tempo', now(), now()),
(gen_random_uuid(), 'Mimir', now(), now()),
(gen_random_uuid(), 'Alloy', now(), now()),
(gen_random_uuid(), 'Traefik', now(), now()),

-- ---------- platform ----------
(gen_random_uuid(), 'Platform Engineering', now(), now()),
(gen_random_uuid(), 'Internal Developer Platforms', now(), now()),
(gen_random_uuid(), 'Backstage', now(), now()),
(gen_random_uuid(), 'Service Mesh (Istio)', now(), now()),
(gen_random_uuid(), 'Kubernetes Operators', now(), now()),

-- ---------- sre ----------
(gen_random_uuid(), 'Site Reliability Engineering', now(), now()),
(gen_random_uuid(), 'Incident Management', now(), now()),
(gen_random_uuid(), 'Observability', now(), now()),
(gen_random_uuid(), 'SLO/SLI Management', now(), now()),
(gen_random_uuid(), 'Chaos Engineering', now(), now()),
(gen_random_uuid(), 'PagerDuty', now(), now()),

-- ---------- cloud ----------
(gen_random_uuid(), 'AWS', now(), now()),
(gen_random_uuid(), 'Azure', now(), now()),
(gen_random_uuid(), 'Google Cloud Platform', now(), now()),
(gen_random_uuid(), 'Cloud Architecture', now(), now()),
(gen_random_uuid(), 'Serverless Computing', now(), now()),
(gen_random_uuid(), 'AWS Lambda', now(), now()),
(gen_random_uuid(), 'CloudFormation', now(), now()),
(gen_random_uuid(), 'Cloud Security', now(), now()),

-- ---------- data_engineering ----------
(gen_random_uuid(), 'ETL Pipelines', now(), now()),
(gen_random_uuid(), 'Apache Spark', now(), now()),
(gen_random_uuid(), 'Apache Airflow', now(), now()),
(gen_random_uuid(), 'Data Warehousing', now(), now()),
(gen_random_uuid(), 'dbt', now(), now()),
(gen_random_uuid(), 'Snowflake', now(), now()),
(gen_random_uuid(), 'BigQuery', now(), now()),
(gen_random_uuid(), 'Hadoop', now(), now()),

-- ---------- data_science ----------
(gen_random_uuid(), 'R', now(), now()),
(gen_random_uuid(), 'Pandas', now(), now()),
(gen_random_uuid(), 'NumPy', now(), now()),
(gen_random_uuid(), 'Statistical Analysis', now(), now()),
(gen_random_uuid(), 'Jupyter', now(), now()),
(gen_random_uuid(), 'Data Visualization', now(), now()),
(gen_random_uuid(), 'scikit-learn', now(), now()),
(gen_random_uuid(), 'A/B Testing', now(), now()),

-- ---------- machine_learning ----------
(gen_random_uuid(), 'Machine Learning', now(), now()),
(gen_random_uuid(), 'Deep Learning', now(), now()),
(gen_random_uuid(), 'TensorFlow', now(), now()),
(gen_random_uuid(), 'PyTorch', now(), now()),
(gen_random_uuid(), 'Computer Vision', now(), now()),
(gen_random_uuid(), 'Natural Language Processing', now(), now()),
(gen_random_uuid(), 'Reinforcement Learning', now(), now()),
(gen_random_uuid(), 'MLOps', now(), now()),
(gen_random_uuid(), 'Feature Engineering', now(), now()),

-- ---------- ai_engineering ----------
(gen_random_uuid(), 'LLM Integration', now(), now()),
(gen_random_uuid(), 'Prompt Engineering', now(), now()),
(gen_random_uuid(), 'Retrieval-Augmented Generation (RAG)', now(), now()),
(gen_random_uuid(), 'Vector Databases', now(), now()),
(gen_random_uuid(), 'LangChain', now(), now()),
(gen_random_uuid(), 'Model Fine-Tuning', now(), now()),
(gen_random_uuid(), 'AI Agents', now(), now()),
(gen_random_uuid(), 'OpenAI API', now(), now()),
(gen_random_uuid(), 'Hugging Face Transformers', now(), now()),

-- ---------- data_analytics ----------
(gen_random_uuid(), 'SQL', now(), now()),
(gen_random_uuid(), 'Excel', now(), now()),
(gen_random_uuid(), 'Power BI', now(), now()),
(gen_random_uuid(), 'Tableau', now(), now()),
(gen_random_uuid(), 'Looker', now(), now()),
(gen_random_uuid(), 'Business Intelligence', now(), now()),

-- ---------- security ----------
(gen_random_uuid(), 'Network Security', now(), now()),
(gen_random_uuid(), 'Penetration Testing', now(), now()),
(gen_random_uuid(), 'Cryptography', now(), now()),
(gen_random_uuid(), 'SIEM', now(), now()),
(gen_random_uuid(), 'Security Auditing', now(), now()),
(gen_random_uuid(), 'Identity and Access Management (IAM)', now(), now()),
(gen_random_uuid(), 'Threat Modeling', now(), now()),

-- ---------- application_security ----------
(gen_random_uuid(), 'OWASP', now(), now()),
(gen_random_uuid(), 'Secure Code Review', now(), now()),
(gen_random_uuid(), 'Static Application Security Testing (SAST)', now(), now()),
(gen_random_uuid(), 'Dynamic Application Security Testing (DAST)', now(), now()),
(gen_random_uuid(), 'API Security', now(), now()),

-- ---------- blockchain ----------
(gen_random_uuid(), 'Solidity', now(), now()),
(gen_random_uuid(), 'Smart Contracts', now(), now()),
(gen_random_uuid(), 'Ethereum', now(), now()),
(gen_random_uuid(), 'Web3.js', now(), now()),
(gen_random_uuid(), 'Blockchain Architecture', now(), now()),
(gen_random_uuid(), 'NFT Development', now(), now()),
(gen_random_uuid(), 'DeFi Protocols', now(), now()),

-- ---------- game ----------
(gen_random_uuid(), 'Unity', now(), now()),
(gen_random_uuid(), 'Unreal Engine', now(), now()),
(gen_random_uuid(), 'Godot', now(), now()),
(gen_random_uuid(), 'Game Physics', now(), now()),
(gen_random_uuid(), '3D Graphics Programming', now(), now()),
(gen_random_uuid(), 'Shader Programming', now(), now()),
(gen_random_uuid(), 'Game AI', now(), now()),
(gen_random_uuid(), 'Multiplayer Networking', now(), now()),
(gen_random_uuid(), 'Bevy', now(), now()),

-- ---------- qa ----------
(gen_random_uuid(), 'Manual Testing', now(), now()),
(gen_random_uuid(), 'Test Automation', now(), now()),
(gen_random_uuid(), 'Selenium', now(), now()),
(gen_random_uuid(), 'Cypress', now(), now()),
(gen_random_uuid(), 'Playwright', now(), now()),
(gen_random_uuid(), 'Jest', now(), now()),
(gen_random_uuid(), 'Performance Testing', now(), now()),
(gen_random_uuid(), 'JMeter', now(), now()),
(gen_random_uuid(), 'Postman', now(), now()),

-- ---------- ui_ux ----------
(gen_random_uuid(), 'UI Design', now(), now()),
(gen_random_uuid(), 'UX Research', now(), now()),
(gen_random_uuid(), 'Figma', now(), now()),
(gen_random_uuid(), 'Wireframing', now(), now()),
(gen_random_uuid(), 'Prototyping', now(), now()),
(gen_random_uuid(), 'Interaction Design', now(), now()),
(gen_random_uuid(), 'Usability Testing', now(), now()),
(gen_random_uuid(), 'Design Systems', now(), now()),

-- ---------- developer_relations ----------
(gen_random_uuid(), 'Developer Advocacy', now(), now()),
(gen_random_uuid(), 'Community Management', now(), now()),
(gen_random_uuid(), 'Public Speaking', now(), now()),
(gen_random_uuid(), 'Open Source Contribution', now(), now()),

-- ---------- technical_writing ----------
(gen_random_uuid(), 'Technical Writing', now(), now()),
(gen_random_uuid(), 'API Documentation', now(), now()),
(gen_random_uuid(), 'Information Architecture', now(), now())

ON CONFLICT (name) DO NOTHING;