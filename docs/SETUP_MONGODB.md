# MongoDB Memory Setup Guide

This guide explains how to set up and use MongoDB-based conversation memory for the Personal Loan Advisor Agent.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11+
- OpenAI API key

## Quick Start

### 1. Start MongoDB with Docker Compose

```bash
# Start MongoDB and Mongo Express (web UI)
docker-compose up -d

# Check if containers are running
docker-compose ps
```

This will start:
- **MongoDB** on `localhost:27017`
- **Mongo Express** (web UI) on `http://localhost:8081`

### 2. Install Dependencies

```bash
# Install Python dependencies including pymongo
uv sync
```

### 3. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-...
```

### 4. Run the Agent

```bash
python main.py
```

## Features

### Multi-User Support

Each user has their own conversation history:

```
👤 Enter your user ID (e.g., email or username): john@example.com
```

### Session Management

- **New Sessions**: Automatically created for new users
- **Resume Sessions**: Previous conversations are listed and can be resumed
- **Session History**: All messages are persistently stored

### MongoDB Collections

The system uses two collections:

1. **sessions**: Stores session metadata
   - session_id
   - user_id
   - created_at
   - last_active
   - message_count

2. **messages**: Stores conversation messages
   - session_id
   - user_id
   - role (user/assistant)
   - content
   - timestamp

## MongoDB Web UI

Access Mongo Express at `http://localhost:8081`:

- **Username**: admin
- **Password**: admin123

You can browse collections, view messages, and manage data through the web interface.

## Docker Commands

```bash
# Start MongoDB
docker-compose up -d

# Stop MongoDB
docker-compose down

# View logs
docker-compose logs -f mongodb

# Remove all data (WARNING: deletes all conversations)
docker-compose down -v
```

## Configuration

### MongoDB Connection

Default settings in `main.py`:

```python
memory = ConversationMemory(
    mongodb_uri="mongodb://admin:password123@localhost:27017/",
    database_name="loan_advisor"
)
```

### Change MongoDB Password

Edit `docker-compose.yml`:

```yaml
environment:
  MONGO_INITDB_ROOT_USERNAME: admin
  MONGO_INITDB_ROOT_PASSWORD: your_secure_password
```

Then update the connection URI in `main.py`.

## Production Deployment

For production use:

1. **Use environment variables** for MongoDB credentials:
   ```python
   mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
   ```

2. **Enable authentication** and use strong passwords

3. **Use MongoDB Atlas** (managed cloud MongoDB) or deploy MongoDB on a server

4. **Add connection pooling** for better performance with multiple users

## Troubleshooting

### MongoDB Connection Failed

**Error**: `MongoDB connection failed: [Errno 61] Connection refused`

**Solution**:
```bash
# Make sure MongoDB is running
docker-compose up -d

# Check container status
docker-compose ps

# View logs
docker-compose logs mongodb
```

### Port Already in Use

**Error**: `port is already allocated`

**Solution**:
```bash
# Check what's using port 27017
lsof -i :27017

# Stop the conflicting service or change the port in docker-compose.yml
```

### Permission Issues

**Error**: `Permission denied`

**Solution**:
```bash
# On Linux/Mac, add your user to docker group
sudo usermod -aG docker $USER

# Log out and back in
```

## Data Backup

### Backup MongoDB Data

```bash
# Backup all data
docker exec loan-advisor-mongodb mongodump --out=/backup

# Copy backup to host
docker cp loan-advisor-mongodb:/backup ./mongodb_backup
```

### Restore MongoDB Data

```bash
# Copy backup to container
docker cp ./mongodb_backup loan-advisor-mongodb:/backup

# Restore data
docker exec loan-advisor-mongodb mongorestore /backup
```

## Architecture

```
┌─────────────┐
│   User 1    │────┐
└─────────────┘    │
                   │    ┌──────────────────┐
┌─────────────┐    ├───→│  Agent + Memory  │
│   User 2    │────┤    └──────────────────┘
└─────────────┘    │             │
                   │             ↓
┌─────────────┐    │    ┌──────────────────┐
│   User N    │────┘    │     MongoDB      │
└─────────────┘         │   ┌──────────┐   │
                        │   │ sessions │   │
                        │   └──────────┘   │
                        │   ┌──────────┐   │
                        │   │ messages │   │
                        │   └──────────┘   │
                        └──────────────────┘
```

## Performance

- **Indexed queries**: Fast message retrieval by session_id
- **Efficient storage**: Only stores role and content
- **Scalable**: Handles multiple concurrent users
- **Connection pooling**: MongoDB driver handles connections efficiently

## Next Steps

- [ ] Add user authentication
- [ ] Implement message search
- [ ] Add conversation analytics
- [ ] Export conversation history
- [ ] Add message deletion/editing
- [ ] Implement conversation summarization
