import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from core.database import SessionLocal, create_tables
from models.pipeline import PipelineItem, PipelineStatus, AgentType
from models.leads import Lead, LeadStatus, BuyingStage

def seed_db():
    print("Creating tables...")
    create_tables()
    
    db: Session = SessionLocal()
    
    # Clear existing data
    db.query(PipelineItem).delete()
    db.query(Lead).delete()
    
    now = datetime.now(timezone.utc)
    
    print("Seeding Leads...")
    leads = [
        Lead(
            status=LeadStatus.NEW,
            name="Alex Mercer",
            email="alex.mercer@fintechstart.io",
            company="FinTechStart IO",
            title="Founder & CEO",
            linkedin_url="https://linkedin.com/in/alex-mercer-fintech",
            buying_stage=BuyingStage.AWARENESS,
            icp_score=8.5,
            touchpoints=0,
            notes="Interested in scaling their budget app architecture."
        ),
        Lead(
            status=LeadStatus.IN_SEQUENCE,
            name="Sarah Jenkins",
            email="s.jenkins@learnhub.edu",
            company="LearnHub EdTech",
            title="Director of Platform Engineering",
            linkedin_url="https://linkedin.com/in/sarah-jenkins-lms",
            buying_stage=BuyingStage.CONSIDERATION,
            icp_score=9.2,
            touchpoints=2,
            notes="Needs a mobile app extension for their existing web LMS. Following up on previous SaaS proposals."
        ),
        Lead(
            status=LeadStatus.BOOKED,
            name="Marcus Chen",
            email="m.chen@budgetpro.co",
            company="BudgetPro Solutions",
            title="CTO",
            linkedin_url="https://linkedin.com/in/marcus-chen-cto",
            buying_stage=BuyingStage.DECISION,
            icp_score=8.0,
            touchpoints=3,
            notes="Call booked to discuss custom API integration for their new budgeting tool."
        ),
        Lead(
            status=LeadStatus.CLOSED,
            name="Elena Rodriguez",
            email="elena@saasinnovate.net",
            company="SaaS Innovate",
            title="VP of Product",
            linkedin_url="https://linkedin.com/in/elena-rodriguez",
            buying_stage=BuyingStage.DECISION,
            icp_score=7.5,
            touchpoints=5,
            notes="Closed the deal for the custom web dashboard."
        )
    ]
    
    db.add_all(leads)
    
    print("Seeding Pipeline Items...")
    pipeline_items = [
        PipelineItem(
            agent_type=AgentType.CMO,
            status=PipelineStatus.PENDING,
            title="The Future of FinTech Budgeting Apps in 2026",
            content="""Recent trends indicate that AI-driven budgeting apps are seeing a 40% higher retention rate. 
If you are still relying on manual entry, you are losing users. 
Here are 3 ways we help SaaS founders build sticky FinTech apps...""",
            platform="LinkedIn",
            stage="Awareness",
            created_at=now - timedelta(hours=2)
        ),
        PipelineItem(
            agent_type=AgentType.CMO,
            status=PipelineStatus.APPROVED,
            title="Why Your LMS Needs a Mobile-First Strategy",
            content="""Is your Learning Management System accessible on the go? 
70% of learners prefer micro-learning on their mobile devices. 
Building a custom mobile extension for your SaaS can increase engagement by 2x. Let's talk about our mobile dev services.""",
            platform="X",
            stage="Consideration",
            created_at=now - timedelta(hours=5),
            approved_at=now - timedelta(hours=1)
        ),
        PipelineItem(
            agent_type=AgentType.CMO,
            status=PipelineStatus.SCHEDULED,
            title="Custom SaaS Development: Web vs Mobile",
            content="A deep dive into whether you should build a web app or mobile app first for your new software startup.",
            platform="LinkedIn",
            stage="Awareness",
            created_at=now - timedelta(days=1),
            scheduled_at=now + timedelta(days=1)
        ),
        PipelineItem(
            agent_type=AgentType.RESEARCH,
            status=PipelineStatus.POSTED,
            title="FinTech Engagement Trend Analysis Q2",
            content="Detailed analysis of FinTech features that drive the most engagement on social media.",
            platform="Internal",
            stage="Research",
            created_at=now - timedelta(days=3),
            posted_at=now - timedelta(days=2)
        )
    ]
    
    db.add_all(pipeline_items)
    
    db.commit()
    db.close()
    print("Database seeding completed.")

if __name__ == "__main__":
    seed_db()
