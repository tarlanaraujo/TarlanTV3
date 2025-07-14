from app import db
from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class SearchHistory(db.Model):
    __tablename__ = 'search_history'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    title: Mapped[str] = mapped_column(String(200))
    channels_found: Mapped[int] = mapped_column(Integer, default=0)
    valid_channels: Mapped[int] = mapped_column(Integer, default=0)
    search_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(20), default='pending')

    # Relationship
    channels: Mapped[list["Channel"]] = relationship("Channel", back_populates="search_history")

class Channel(db.Model):
    __tablename__ = 'channel'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(100))
    logo: Mapped[str] = mapped_column(String(500))
    group: Mapped[str] = mapped_column(String(100))
    is_working: Mapped[bool] = mapped_column(Boolean)
    last_checked: Mapped[datetime] = mapped_column(DateTime)
    search_history_id: Mapped[int] = mapped_column(Integer, ForeignKey('search_history.id'))

    # Relationship
    search_history: Mapped["SearchHistory"] = relationship("SearchHistory", back_populates="channels")

class PlaylistExport(db.Model):
    __tablename__ = 'playlist_export'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text)
    channels_count: Mapped[int] = mapped_column(Integer, default=0)
    export_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    export_type: Mapped[str] = mapped_column(String(20), default='m3u')