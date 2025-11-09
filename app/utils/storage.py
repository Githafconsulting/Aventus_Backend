"""
Supabase Storage utilities for handling file uploads
"""
from supabase import create_client, Client
from app.config import settings
from fastapi import UploadFile
from typing import Optional
import uuid
from datetime import datetime


class SupabaseStorage:
    """Handle file uploads to Supabase Storage"""

    def __init__(self):
        # Use service_role_key for storage operations to bypass RLS
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key
        )
        self.bucket = settings.supabase_bucket

    async def upload_document(
        self,
        file: UploadFile,
        contractor_id: str,
        document_type: str
    ) -> str:
        """
        Upload a document to Supabase Storage

        Args:
            file: The uploaded file
            contractor_id: ID of the contractor
            document_type: Type of document (passport, photo, visa, etc.)

        Returns:
            The public URL of the uploaded file
        """
        try:
            # Generate unique filename
            file_ext = file.filename.split('.')[-1] if '.' in file.filename else ''
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            filename = f"{contractor_id}/{document_type}_{timestamp}_{unique_id}.{file_ext}"

            # Read file content
            content = await file.read()

            # Upload to Supabase Storage
            response = self.client.storage.from_(self.bucket).upload(
                filename,
                content,
                file_options={"content-type": file.content_type}
            )

            # Get public URL
            public_url = self.client.storage.from_(self.bucket).get_public_url(filename)

            return public_url

        except Exception as e:
            print(f"Error uploading file: {str(e)}")
            raise Exception(f"Failed to upload document: {str(e)}")

    def delete_document(self, file_path: str) -> bool:
        """
        Delete a document from Supabase Storage

        Args:
            file_path: Path to the file in storage

        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract the path from the URL
            if file_path.startswith('http'):
                # Extract path from URL
                path_parts = file_path.split(f'/{self.bucket}/')
                if len(path_parts) > 1:
                    file_path = path_parts[1]

            self.client.storage.from_(self.bucket).remove([file_path])
            return True

        except Exception as e:
            print(f"Error deleting file: {str(e)}")
            return False


# Global storage instance
storage = SupabaseStorage()
