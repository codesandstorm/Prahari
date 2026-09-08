"""Transparent, local, approved-document retrieval for PRAHARI."""
from .assistant import UnifiedPrahariAssistant
from .contracts import Citation, DocumentChunk, RagResponse, SourceDocument
from .retriever import LexicalRetriever
from .router import QuestionRoute, route_question

__all__=["UnifiedPrahariAssistant","Citation","DocumentChunk","RagResponse","SourceDocument","LexicalRetriever","QuestionRoute","route_question"]
