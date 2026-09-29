import logging
import os
from typing import Any
from bson import ObjectId
import chromadb
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.ai.base import AIProvider
from app.ai.groq_provider import GroqProvider
from app.schemas.rag import RAGIndexStatusResponse, RAGQueryResponse, RAGSourceDocument

logger = logging.getLogger(__name__)


class RAGService:
    """Service to handle vector embedding, ChromaDB indexing, and RAG Q&A over historical emails."""

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        ai_provider: AIProvider | None = None,
        chroma_client: Any | None = None,
    ):
        self.db = db
        self.emails_col = db["emails"]
        self.ai_provider = ai_provider or GroqProvider()

        # Initialize ChromaDB persistent client
        if chroma_client:
            self.chroma_client = chroma_client
        else:
            persist_dir = os.path.join(os.getcwd(), "chroma_data")
            os.makedirs(persist_dir, exist_ok=True)
            self.chroma_client = chromadb.PersistentClient(path=persist_dir)

        # Unified collection with strict metadata filtering by user_id
        self.collection = self.chroma_client.get_or_create_collection(
            name="mailsentinel_emails",
            metadata={"hnsw:space": "cosine"},
        )

    def _prepare_document_text(self, email_doc: dict) -> str:
        """Construct rich semantic text block for vector embedding."""
        sender = f"{email_doc.get('sender_name', '')} <{email_doc.get('sender_email', '')}>".strip()
        subject = email_doc.get("subject", "")
        summary = email_doc.get("summary", "")
        action = email_doc.get("action", "")
        deadline = email_doc.get("deadline", "")
        body = email_doc.get("body_text", "") or email_doc.get("snippet", "")

        parts = [
            f"Sender: {sender}",
            f"Subject: {subject}",
            f"Date: {email_doc.get('received_at', '')}",
        ]
        if summary:
            parts.append(f"AI Summary: {summary}")
        if action:
            parts.append(f"Action: {action}")
        if deadline:
            parts.append(f"Deadline: {deadline}")
        parts.append(f"Content: {body[:1500]}")

        return "\n".join(parts)

    async def index_single_email(self, user_id: str, email_doc: dict) -> bool:
        """Upsert a single email into the ChromaDB vector store."""
        try:
            email_id = str(email_doc["_id"])
            doc_text = self._prepare_document_text(email_doc)

            metadata = {
                "user_id": user_id,
                "email_id": email_id,
                "subject": str(email_doc.get("subject", ""))[:200],
                "sender": str(email_doc.get("sender_email", ""))[:150],
                "sender_name": str(email_doc.get("sender_name", ""))[:150],
                "received_at": str(email_doc.get("received_at", ""))[:100],
                "category": str(email_doc.get("category", "GENERAL")),
                "importance": int(email_doc.get("final_importance") or email_doc.get("rule_score", 0)),
            }

            self.collection.upsert(
                ids=[email_id],
                documents=[doc_text],
                metadatas=[metadata],
            )
            return True
        except Exception as e:
            logger.error("Error indexing email %s into ChromaDB: %s", email_doc.get("_id"), e)
            return False

    async def reindex_all_user_emails(self, user_id: str) -> RAGIndexStatusResponse:
        """Re-index all emails for the user into the vector database."""
        cursor = self.emails_col.find({"user_id": user_id})
        docs = await cursor.to_list(length=1000)

        indexed_count = 0
        ids = []
        documents = []
        metadatas = []

        for doc in docs:
            email_id = str(doc["_id"])
            ids.append(email_id)
            documents.append(self._prepare_document_text(doc))
            metadatas.append({
                "user_id": user_id,
                "email_id": email_id,
                "subject": str(doc.get("subject", ""))[:200],
                "sender": str(doc.get("sender_email", ""))[:150],
                "sender_name": str(doc.get("sender_name", ""))[:150],
                "received_at": str(doc.get("received_at", ""))[:100],
                "category": str(doc.get("category", "GENERAL")),
                "importance": int(doc.get("final_importance") or doc.get("rule_score", 0)),
            })

        if ids:
            try:
                self.collection.upsert(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas,
                )
                indexed_count = len(ids)
            except Exception as e:
                logger.error("Batch upsert to ChromaDB failed: %s", e)

        return RAGIndexStatusResponse(
            indexed_emails=indexed_count,
            total_emails=len(docs),
            status="completed",
            collection_name="mailsentinel_emails",
        )

    async def query_and_answer(
        self,
        user_id: str,
        query: str,
        top_k: int = 5,
    ) -> RAGQueryResponse:
        """Execute semantic search with user_id filter and synthesize grounded answer via Groq."""
        # Check total emails in MongoDB for this user
        total_user_emails = await self.emails_col.count_documents({"user_id": user_id})
        if total_user_emails == 0:
            return RAGQueryResponse(
                query=query,
                answer="You have not ingested any emails yet. Please click 'Simulate Ingestion' on the Dashboard or connect your Gmail account in the Connect tab to populate your inbox.",
                sources=[],
                context_emails_count=0,
            )

        # 1. Semantic Search with strict multi-user metadata filtering
        retrieved_results = None
        try:
            retrieved_results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where={"user_id": user_id},  # MANDATORY SECURITY BOUNDARY
            )
        except Exception as e:
            logger.warning("ChromaDB query encountered issue: %s", e)

        sources: list[RAGSourceDocument] = []
        context_blocks = []

        doc_ids = []
        if retrieved_results and "ids" in retrieved_results and retrieved_results["ids"]:
            doc_ids = retrieved_results["ids"][0]

        # If vector index returned 0 results but user has emails, auto-index and re-query
        if not doc_ids and total_user_emails > 0:
            logger.info("Vector store empty for user %s. Auto-indexing %d emails...", user_id, total_user_emails)
            await self.reindex_all_user_emails(user_id)
            try:
                retrieved_results = self.collection.query(
                    query_texts=[query],
                    n_results=top_k,
                    where={"user_id": user_id},
                )
                if retrieved_results and "ids" in retrieved_results and retrieved_results["ids"]:
                    doc_ids = retrieved_results["ids"][0]
            except Exception as e:
                logger.warning("Retry ChromaDB query failed: %s", e)

        # 2. If vector DB has matches, fetch rich email documents from MongoDB
        if doc_ids:
            object_ids = [ObjectId(i) for i in doc_ids if ObjectId.is_valid(i)]
            cursor = self.emails_col.find({"_id": {"$in": object_ids}, "user_id": user_id})
            matched_emails = {str(d["_id"]): d for d in await cursor.to_list(length=len(object_ids))}

            for i, email_id in enumerate(doc_ids):
                email_doc = matched_emails.get(email_id)
                if not email_doc:
                    continue

                dist = None
                if retrieved_results and "distances" in retrieved_results and retrieved_results["distances"]:
                    dist = round(float(retrieved_results["distances"][0][i]), 3)

                source_item = RAGSourceDocument(
                    email_id=email_id,
                    subject=email_doc.get("subject", "(No Subject)"),
                    sender=f"{email_doc.get('sender_name', '')} <{email_doc.get('sender_email', '')}>".strip(),
                    received_at=str(email_doc.get("received_at", "")),
                    snippet=email_doc.get("summary") or email_doc.get("snippet", ""),
                    similarity_score=dist,
                    category=email_doc.get("category"),
                    importance=email_doc.get("final_importance") or email_doc.get("rule_score"),
                    deadline=email_doc.get("deadline"),
                    action=email_doc.get("action"),
                )
                sources.append(source_item)

                context_blocks.append(
                    f"--- EMAIL #{i+1} ---\n"
                    f"From: {source_item.sender}\n"
                    f"Subject: {source_item.subject}\n"
                    f"Date: {source_item.received_at}\n"
                    f"Category: {source_item.category}\n"
                    f"AI Summary: {email_doc.get('summary', 'None')}\n"
                    f"Deadline: {email_doc.get('deadline', 'None')}\n"
                    f"Action Required: {email_doc.get('action', 'None')}\n"
                    f"Body: {email_doc.get('body_text', '')[:1000]}\n"
                )

        # 3. Robust Fallback: Keyword search matching any query term or recent emails
        if not sources:
            query_words = [w.strip() for w in query.split() if len(w.strip()) > 2]
            regex_patterns = [{"subject": {"$regex": w, "$options": "i"}} for w in query_words]
            regex_patterns += [{"sender_name": {"$regex": w, "$options": "i"}} for w in query_words]
            regex_patterns += [{"body_text": {"$regex": w, "$options": "i"}} for w in query_words]
            regex_patterns += [{"summary": {"$regex": w, "$options": "i"}} for w in query_words]

            filter_query = {"user_id": user_id}
            if regex_patterns:
                filter_query["$or"] = regex_patterns

            cursor = self.emails_col.find(filter_query).sort("received_at", -1).limit(top_k)
            fb_docs = await cursor.to_list(length=top_k)

            # If still nothing, fetch the latest emails so the LLM can give contextual answer
            if not fb_docs:
                fb_docs = await self.emails_col.find({"user_id": user_id}).sort("received_at", -1).limit(top_k).to_list(length=top_k)

            for i, doc in enumerate(fb_docs):
                src = RAGSourceDocument(
                    email_id=str(doc["_id"]),
                    subject=doc.get("subject", ""),
                    sender=doc.get("sender_email", ""),
                    received_at=str(doc.get("received_at", "")),
                    snippet=doc.get("summary") or doc.get("snippet", ""),
                    category=doc.get("category"),
                    importance=doc.get("final_importance") or doc.get("rule_score"),
                    deadline=doc.get("deadline"),
                    action=doc.get("action"),
                )
                sources.append(src)
                context_blocks.append(
                    f"--- EMAIL #{i+1} ---\n"
                    f"From: {src.sender}\n"
                    f"Subject: {src.subject}\n"
                    f"Date: {src.received_at}\n"
                    f"Category: {doc.get('category', 'GENERAL')}\n"
                    f"AI Summary: {doc.get('summary', 'None')}\n"
                    f"Deadline: {doc.get('deadline', 'None')}\n"
                    f"Action: {doc.get('action', 'None')}\n"
                    f"Body: {doc.get('body_text', '')[:1000]}\n"
                )

        if not context_blocks:
            return RAGQueryResponse(
                query=query,
                answer="No relevant emails found in your connected inboxes for this query.",
                sources=[],
                context_emails_count=0,
            )

        # 4. Generate Grounded Answer via Groq Provider
        full_context = "\n\n".join(context_blocks)
        answer_text = await self.ai_provider.answer_rag_query(query=query, context=full_context)

        return RAGQueryResponse(
            query=query,
            answer=answer_text,
            sources=sources,
            context_emails_count=len(sources),
        )
