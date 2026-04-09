from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional, Dict
from datetime import datetime

class Attachment(BaseModel):
    type: str
    url: str

class ReceiverScope(str, Enum):
    ALL = "all"           
    GRADE = "grade"       
    CLASS = "class"       
    INDIVIDUAL = "student" 

class NotificationPayload(BaseModel):
    id: str
    sender: str
    timestamp: datetime
    title: str
    content: str
    attachments: List[Attachment] = []
    category: str
    receiver_scope: ReceiverScope
    receiver_ids: List[str] = []
    # Dữ liệu sau khi xử lý bởi AI sẽ được điền vào đây
    priority: Optional[str] = None  # Cao, Trung bình, Thấp
    summary: Optional[str] = None

class StudentProfile(BaseModel):
    student_id: str
    full_name: str
    student_class: str = Field(alias="class")
    parent_id: str
    interests: List[str]
    history_priority_engagement: Dict[str, str]