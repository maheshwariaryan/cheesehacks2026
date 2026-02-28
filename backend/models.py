from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship, DeclarativeBase
from datetime import datetime


class Base(DeclarativeBase):
    pass


class Deal(Base):
    __tablename__ = "deals"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    target_company = Column(String(255), nullable=False)
    industry = Column(String(100), nullable=True)
    deal_size = Column(Float, nullable=True)
    status = Column(String(50), default="pending")  # pending | analyzing | completed | failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    documents = relationship("Document", back_populates="deal", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="deal", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="deal", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, xlsx, csv, docx, txt, png, jpg, etc.
    file_size = Column(Integer, default=0)
    extracted_text = Column(Text, nullable=True)
    doc_type = Column(String(100), nullable=True)  # income_statement, balance_sheet, etc.
    doc_type_confidence = Column(Float, nullable=True)
    financial_data = Column(Text, nullable=True)  # JSON string
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    deal = relationship("Deal", back_populates="documents")


class Analysis(Base):
    __tablename__ = "analyses"
    id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=False)
    analysis_type = Column(String(50), nullable=False)  # qoe | working_capital | ratios | dcf | red_flags | anomalies | ai_insights
    results = Column(Text, nullable=True)  # JSON string
    status = Column(String(50), default="pending")  # pending | running | completed | failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    deal = relationship("Deal", back_populates="analyses")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user | assistant
    content = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    deal = relationship("Deal", back_populates="chat_messages")


class GeneratedReport(Base):
    __tablename__ = "generated_reports"
    id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=False)
    report_type = Column(String(50), nullable=False)  # iar | dcf | red_flag
    file_path = Column(String(1000), nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
