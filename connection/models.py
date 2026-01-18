from sqlalchemy import Column, Integer, String, Text, Numeric, Date, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from connection.database import Base


class TransactionType(enum.Enum):
    income = "income"
    expense = "expense"


class DocumentType(enum.Enum):
    invoice = "invoice"
    receipt = "receipt"
    statement = "statement"
    other = "other"


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())

    transactions = relationship("Transaction", back_populates="source")
    documents = relationship("Document", back_populates="source")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())

    transactions = relationship("Transaction", back_populates="category")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))
    transaction_date = Column(Date, nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(10), default="USD")
    type = Column(Enum(TransactionType), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())

    source = relationship("Source", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
    anomaly_flags = relationship("AnomalyFlag", back_populates="transaction")
    documents = relationship("Document", secondary="document_transactions", back_populates="transactions")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.id"))
    document_type = Column(Enum(DocumentType), nullable=False)
    provider = Column(Text)
    document_date = Column(Date)
    total_amount = Column(Numeric(14, 2))
    currency = Column(String(10), default="USD")
    file_path = Column(Text, nullable=False)
    extracted_text = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())

    source = relationship("Source", back_populates="documents")
    transactions = relationship("Transaction", secondary="document_transactions", back_populates="documents")


class DocumentTransaction(Base):
    __tablename__ = "document_transactions"

    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), primary_key=True)


class AnomalyFlag(Base):
    __tablename__ = "anomaly_flags"

    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"))
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp())

    transaction = relationship("Transaction", back_populates="anomaly_flags")
