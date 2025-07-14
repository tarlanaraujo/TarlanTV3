from app import db
from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class M3UPlaylist(db.Model):
    __tablename__ = 'm3u_playlist'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), nullable=True)
    source_type: Mapped[str] = mapped_column(String(20), default='url')  # url, file
    content_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    total_channels: Mapped[int] = mapped_column(Integer, default=0)
    valid_channels: Mapped[int] = mapped_column(Integer, default=0)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(20), default='processing')  # processing, completed, failed

    # Relationships
    channels: Mapped[list["Channel"]] = relationship("Channel", back_populates="playlist", cascade="all, delete-orphan")

class Channel(db.Model):
    __tablename__ = 'channel'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=True)
    category_type: Mapped[str] = mapped_column(String(20), default='live')  # live, movie, series
    logo: Mapped[str] = mapped_column(String(500), nullable=True)
    group_title: Mapped[str] = mapped_column(String(100), nullable=True)
    tvg_id: Mapped[str] = mapped_column(String(100), nullable=True)
    tvg_name: Mapped[str] = mapped_column(String(200), nullable=True)
    duration: Mapped[int] = mapped_column(Integer, default=-1)
    is_working: Mapped[bool] = mapped_column(Boolean, default=None, nullable=True)
    last_checked: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    playlist_id: Mapped[int] = mapped_column(Integer, ForeignKey('m3u_playlist.id'))

    # Relationships
    playlist: Mapped["M3UPlaylist"] = relationship("M3UPlaylist", back_populates="channels")

class SearchHistory(db.Model):
    __tablename__ = 'search_history'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    query: Mapped[str] = mapped_column(String(200), nullable=False)
    category_type: Mapped[str] = mapped_column(String(20), nullable=True)  # live, movie, series, all
    playlist_id: Mapped[int] = mapped_column(Integer, ForeignKey('m3u_playlist.id'), nullable=True)
    results_count: Mapped[int] = mapped_column(Integer, default=0)
    search_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class UserSession(db.Model):
    __tablename__ = 'user_session'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    current_playlist_id: Mapped[int] = mapped_column(Integer, ForeignKey('m3u_playlist.id'), nullable=True)
    last_activity: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    preferences: Mapped[str] = mapped_column(Text, nullable=True)  # JSON string for user preferences
