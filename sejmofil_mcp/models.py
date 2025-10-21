"""Pydantic models for data validation"""

from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field


class PrintShort(BaseModel):
    """Shortened print information"""
    number: str
    title: str
    summary: Optional[str] = None
    documentDate: Optional[str] = None
    currentStage: Optional[str] = None
    stageDate: Optional[str] = None
    topics: List[str] = Field(default_factory=list)
    score: Optional[float] = None


class PrintDetail(BaseModel):
    """Detailed print information"""
    number: str
    title: str
    summary: Optional[str] = None
    documentDate: Optional[str] = None
    changeDate: Optional[str] = None
    documentType: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    subjects: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    organizations: List[str] = Field(default_factory=list)
    currentStage: Optional[str] = None
    stageDate: Optional[str] = None
    processNumber: Optional[str] = None
    attachments: List[str] = Field(default_factory=list)


class Comment(BaseModel):
    """Comment on a print"""
    author: str
    organization: Optional[str] = None
    sentiment: Optional[str] = None
    summary: str


class Person(BaseModel):
    """Person (MP) information"""
    id: Optional[int] = None
    name: str
    club: Optional[str] = None
    role: Optional[str] = None
    active: Optional[bool] = None


class PersonActivity(BaseModel):
    """MP legislative activity"""
    person: Person
    authoredPrints: List[PrintShort] = Field(default_factory=list)
    subjectPrints: List[PrintShort] = Field(default_factory=list)
    speechCount: int = 0
    committees: List[str] = Field(default_factory=list)


class Topic(BaseModel):
    """Topic information"""
    name: str
    description: Optional[str] = None
    printCount: Optional[int] = None
    similarity: Optional[float] = None


class VotingResult(BaseModel):
    """Voting result summary"""
    votingNumber: int
    sitting: int
    topic: Optional[str] = None
    yes: int
    no: int
    abstain: Optional[int] = None
    totalVoted: Optional[int] = None


class ProcessStage(BaseModel):
    """Legislative process stage"""
    stageName: str
    date: Optional[str] = None
    number: Optional[str] = None
    type: Optional[str] = None


class ProcessStatus(BaseModel):
    """Process status information"""
    processNumber: str
    status: str  # 'active' or 'finished'
    currentStage: Optional[str] = None
    stageDate: Optional[str] = None
    allStages: List[ProcessStage] = Field(default_factory=list)


class SearchResult(BaseModel):
    """Generic search result"""
    type: str  # 'print', 'person', 'topic'
    id: str
    title: str
    description: Optional[str] = None
    relevance: Optional[float] = None
