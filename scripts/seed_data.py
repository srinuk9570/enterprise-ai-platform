#!/usr/bin/env python3
"""
Seed the database with sample data for development/testing.
"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4
import random

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.database.sqlite.connection import db_connection
from src.infrastructure.repositories import (
    SQLiteUserRepository,
    SQLiteConversationRepository,
    FileAssetRepository,
)
from src.domain.entities.user import User
from src.domain.entities.conversation import Conversation
from src.domain.entities.message import Message
from src.domain.value_objects.email import Email
from src.shared.constants import UserRole, MessageRole, ConversationStatus


# Sample data
SAMPLE_USERS = [
    {
        "email": "admin@example.com",
        "username": "admin",
        "password": "Admin123!",
        "full_name": "Admin User",
        "role": UserRole.ADMIN,
    },
    {
        "email": "power@example.com",
        "username": "poweruser",
        "password": "Power123!",
        "full_name": "Power User",
        "role": UserRole.POWER_USER,
    },
    {
        "email": "user@example.com",
        "username": "testuser",
        "password": "User123!",
        "full_name": "Test User",
        "role": UserRole.USER,
    },
]

SAMPLE_CONVERSATIONS = [
    {
        "title": "AI Capabilities Discussion",
        "model_name": "deepseek-r1:7b",
        "messages": [
            ("user", "What can you help me with?"),
            ("assistant", "I can help with coding, writing, analysis, answering questions, and more!"),
            ("user", "Can you write Python code?"),
            ("assistant", "Yes! I can write, review, and debug Python code. What would you like me to help with?"),
        ],
    },
    {
        "title": "Learning about Machine Learning",
        "model_name": "llama3.2:7b",
        "messages": [
            ("user", "What is machine learning?"),
            ("assistant", "Machine learning is a subset of AI that enables systems to learn from data without explicit programming."),
            ("user", "What are the main types?"),
            ("assistant", "The main types are supervised learning, unsupervised learning, and reinforcement learning."),
        ],
    },
]


async def seed_users(password_hasher) -> list:
    """Seed users into database."""
    repo = SQLiteUserRepository()
    users = []
    
    print("\n👤 Seeding users...")
    
    for user_data in SAMPLE_USERS:
        # Check if user exists
        existing = await repo.get_by_email(user_data["email"])
        if existing:
            print(f"  ⏭️  User already exists: {user_data['email']}")
            users.append(existing)
            continue
        
        user = User(
            email=Email(user_data["email"]),
            username=user_data["username"],
            hashed_password=password_hasher.hash(user_data["password"]),
            full_name=user_data["full_name"],
            role=user_data["role"],
            is_verified=True,
        )
        
        created = await repo.add(user)
        users.append(created)
        print(f"  ✅ Created user: {user_data['email']} ({user_data['role'].value})")
    
    return users


async def seed_conversations(users: list) -> None:
    """Seed conversations and messages."""
    repo = SQLiteConversationRepository()
    
    print("\n💬 Seeding conversations...")
    
    for user in users:
        for conv_data in SAMPLE_CONVERSATIONS:
            conv = Conversation(
                user_id=user.id,
                title=conv_data["title"],
                model_name=conv_data["model_name"],
                status=ConversationStatus.ACTIVE,
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
            )
            
            created_conv = await repo.add(conv)
            
            # Add messages
            for i, (role_str, content) in enumerate(conv_data["messages"]):
                role = MessageRole.USER if role_str == "user" else MessageRole.ASSISTANT
                message = Message(
                    conversation_id=created_conv.id,
                    role=role,
                    content=content,
                    sequence_number=i,
                    token_count=len(content.split()) * 2,
                    created_at=created_conv.created_at + timedelta(minutes=i * 2),
                )
                await repo.add_message(created_conv.id, message)
            
            print(f"  ✅ Created conversation: {conv_data['title']} ({len(conv_data['messages'])} messages)")
    
    print(f"\n  Total conversations created: {len(users) * len(SAMPLE_CONVERSATIONS)}")


async def main():
    """Main seeding function."""
    from src.infrastructure.security.password_hasher import PasswordHasher
    
    print("\n🌱 Starting database seeding...")
    
    # Initialize database
    db_connection.initialize_database()
    
    # Create password hasher
    password_hasher = PasswordHasher()
    
    # Seed users
    users = await seed_users(password_hasher)
    
    # Seed conversations
    await seed_conversations(users)
    
    print("\n✅ Database seeding completed!\n")
    
    # Print summary
    print("Summary:")
    print(f"  - Users: {len(users)}")
    print(f"  - Conversations per user: {len(SAMPLE_CONVERSATIONS)}")
    print("\nLogin credentials:")
    print("  - Admin: admin@example.com / Admin123!")
    print("  - Power User: power@example.com / Power123!")
    print("  - User: user@example.com / User123!")


if __name__ == "__main__":
    asyncio.run(main())