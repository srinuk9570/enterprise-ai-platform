| content | TEXT | NOT NULL | Message content |
| sequence_number | INTEGER | NOT NULL | Order in conversation |
| token_count | INTEGER | DEFAULT 0 | Token count |
| model_used | TEXT | | Model that generated response |
| generation_time_ms | REAL | | Response generation time |
| finish_reason | TEXT | | stop/length/error |
| is_edited | INTEGER | DEFAULT 0 | Boolean |
| edited_at | TIMESTAMP | | Edit timestamp |
| original_content | TEXT | | Pre-edit content |
| metadata | TEXT | DEFAULT '{}' | JSON metadata |
| created_at | TIMESTAMP | NOT NULL | Creation time |

**Indexes:**
- `idx_messages_conversation_id` ON (conversation_id)
- `idx_messages_created_at` ON (created_at)
- UNIQUE `uq_conversation_sequence` ON (conversation_id, sequence_number)

### assets
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | UUID |
| user_id | TEXT | FOREIGN KEY (users.id) | Owner |
| asset_type | TEXT | NOT NULL | image/chart/export |
| file_path | TEXT | NOT NULL | File location |
| file_name | TEXT | NOT NULL | Original filename |
| file_size | INTEGER | NOT NULL | Size in bytes |
| mime_type | TEXT | NOT NULL | MIME type |
| title | TEXT | | Optional title |
| description | TEXT | | Optional description |
| prompt | TEXT | | Generation prompt |
| model_used | TEXT | | Model used |
| generation_params | TEXT | DEFAULT '{}' | JSON parameters |
| generation_time_ms | REAL | | Generation time |
| tags | TEXT | DEFAULT '[]' | JSON array |
| is_favorite | INTEGER | DEFAULT 0 | Boolean |
| is_public | INTEGER | DEFAULT 0 | Boolean |
| view_count | INTEGER | DEFAULT 0 | Views counter |
| download_count | INTEGER | DEFAULT 0 | Downloads counter |
| conversation_id | TEXT | FOREIGN KEY (conversations.id) | Source conversation |
| chart_configuration_id | TEXT | | Related chart config |
| created_at | TIMESTAMP | NOT NULL | Creation time |

**Indexes:**
- `idx_assets_user_id` ON (user_id)
- `idx_assets_asset_type` ON (asset_type)
- `idx_assets_created_at` ON (created_at)

### chart_configurations
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | UUID |
| user_id | TEXT | FOREIGN KEY (users.id) | Owner |
| name | TEXT | NOT NULL | Configuration name |
| chart_type | TEXT | NOT NULL | line/bar/scatter/etc |
| data_source | TEXT | NOT NULL | Data source path/URL |
| x_axis_column | TEXT | NOT NULL | X-axis field |
| y_axis_columns | TEXT | NOT NULL | JSON array of Y fields |
| group_by_column | TEXT | | Grouping field |
| aggregation_function | TEXT | DEFAULT 'sum' | sum/avg/count/min/max |
| title | TEXT | | Chart title |
| x_axis_label | TEXT | | X-axis label |
| y_axis_label | TEXT | | Y-axis label |
| color_scheme | TEXT | DEFAULT 'default' | Color scheme |
| theme | TEXT | DEFAULT 'dark' | dark/light |
| width | INTEGER | DEFAULT 800 | Width in pixels |
| height | INTEGER | DEFAULT 400 | Height in pixels |
| show_legend | INTEGER | DEFAULT 1 | Boolean |
| show_grid | INTEGER | DEFAULT 1 | Boolean |
| show_tooltips | INTEGER | DEFAULT 1 | Boolean |
| stacked | INTEGER | DEFAULT 0 | Boolean |
| normalized | INTEGER | DEFAULT 0 | Boolean |
| cumulative | INTEGER | DEFAULT 0 | Boolean |
| time_range_start | TIMESTAMP | | Filter start |
| time_range_end | TIMESTAMP | | Filter end |
| filters | TEXT | DEFAULT '{}' | JSON filters |
| limit_rows | INTEGER | | Row limit |
| description | TEXT | | Optional description |
| tags | TEXT | DEFAULT '[]' | JSON array |
| is_public | INTEGER | DEFAULT 0 | Boolean |
| created_at | TIMESTAMP | NOT NULL | Creation time |
| updated_at | TIMESTAMP | NOT NULL | Last update |
| last_used_at | TIMESTAMP | | Last usage |

**Indexes:**
- `idx_chart_configs_user_id` ON (user_id)

### api_keys
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | UUID |
| user_id | TEXT | FOREIGN KEY (users.id) | Owner |
| key_hash | TEXT | UNIQUE, NOT NULL | SHA-256 hash |
| name | TEXT | NOT NULL | Key name |
| prefix | TEXT | NOT NULL | Key prefix |
| scopes | TEXT | NOT NULL | JSON array of scopes |
| is_active | INTEGER | DEFAULT 1 | Boolean |
| last_used_at | TIMESTAMP | | Last usage |
| expires_at | TIMESTAMP | | Expiration |
| created_at | TIMESTAMP | NOT NULL | Creation time |

**Indexes:**
- `idx_api_keys_key_hash` ON (key_hash)
- `idx_api_keys_user_id` ON (user_id)

### audit_logs
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | UUID |
| user_id | TEXT | FOREIGN KEY (users.id) | Actor |
| action | TEXT | NOT NULL | Action performed |
| resource_type | TEXT | NOT NULL | Target resource type |
| resource_id | TEXT | | Target resource ID |
| details | TEXT | | JSON details |
| ip_address | TEXT | | Client IP |
| user_agent | TEXT | | Client user agent |
| created_at | TIMESTAMP | NOT NULL | Event time |

**Indexes:**
- `idx_audit_logs_user_id` ON (user_id)
- `idx_audit_logs_created_at` ON (created_at)

## 🔄 Migration Strategy

### Version Control
- All migrations stored in `data/database/migrations/versions/`
- Use Alembic for schema management
- Each migration is reversible

### Migration Commands
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

💾 Backup Strategy
Automated Backups
bash
# Daily backup via cron
0 2 * * * /opt/enterprise-ai-platform/scripts/backup.sh

# Backup script creates timestamped copies
# Keeps last 30 days of backups
Point-in-Time Recovery
SQLite WAL mode enables point-in-time recovery

Combine full backup with WAL files for PITR


---

### `docs/architecture/DEPLOYMENT_GUIDE.md`
```markdown
# Deployment Guide

## 🚀 Deployment Options

### 1. Docker Compose (Recommended)
Simplest deployment with all services containerized.

### 2. Systemd Services
Native Linux deployment with systemd supervision.

### 3. Kubernetes
For large-scale deployments (see `deployment/kubernetes/`).

---

## 📦 Docker Compose Deployment

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Container Toolkit (for GPU support)

### Quick Start
```bash
# Clone repository
git clone https://github.com/yourusername/enterprise-ai-platform.git
cd enterprise-ai-platform

# Configure environment
cp .env.example .env
nano .env  # Edit configuration

# Build and start
docker-compose -f deployment/docker/docker-compose.yml up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# docker-compose.prod.yml overrides
version: '3.8'

services:
  backend:
    environment:
      - DEBUG=false
      - LOG_LEVEL=WARNING
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

  nginx:
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deployment/nginx/nginx-ssl.conf:/etc/nginx/nginx.conf:ro
      - /etc/letsencrypt:/etc/nginx/ssl:ro