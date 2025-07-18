import os
import uuid
from abc import ABC, abstractmethod
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from src.core.settings import APP_SETTINGS, KB_FOLDER


class FileStorageInterface(ABC):
    """Abstract interface for file storage"""

    @abstractmethod
    def save_file(self, file: BinaryIO, filename: str, file_type: str) -> dict:
        """Save file and return storage info"""
        pass

    @abstractmethod
    def delete_file(self, file_path: str) -> bool:
        """Delete file from storage"""
        pass

    @abstractmethod
    def get_file_url(self, file_path: str) -> str:
        """Get file URL for download"""
        pass

    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists"""
        pass

    @abstractmethod
    def save_text_as_file(self, text_content: str, filename: str) -> dict:
        """Save text content as a file"""
        pass


class LocalFileStorage(FileStorageInterface):
    """Local file storage implementation"""

    def __init__(self):
        self.storage_path = KB_FOLDER
        os.makedirs(self.storage_path, exist_ok=True)

    def save_file(self, file: BinaryIO, filename: str, file_type: str) -> dict:
        """Save file locally"""
        try:
            # Generate unique filename
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(self.storage_path, unique_filename)

            # Save file
            with open(file_path, "wb") as f:
                content = file.read()
                f.write(content)

            return {
                "file_path": file_path,
                "filename": unique_filename,
                "file_size": len(content),
                "storage_type": "local",
            }
        except Exception as e:
            raise Exception(f"Error saving file locally: {str(e)}")

    def save_text_as_file(self, text_content: str, filename: str) -> dict:
        """Save text content as a .txt file locally"""
        try:
            # Generate unique filename
            unique_filename = f"{uuid.uuid4()}_{filename}.txt"
            file_path = os.path.join(self.storage_path, unique_filename)

            # Save text content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text_content)

            return {
                "file_path": file_path,
                "filename": unique_filename,
                "file_size": len(text_content.encode("utf-8")),
                "storage_type": "local",
            }
        except Exception as e:
            raise Exception(f"Error saving text file locally: {str(e)}")

    def delete_file(self, file_path: str) -> bool:
        """Delete file from local storage"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting local file: {e}")
            return False

    def get_file_url(self, file_path: str) -> str:
        """Get local file URL"""
        # Return relative path for local files
        filename = os.path.basename(file_path)
        return f"/static/knowledge/{filename}"

    def file_exists(self, file_path: str) -> bool:
        """Check if local file exists"""
        return os.path.exists(file_path)


class S3FileStorage(FileStorageInterface):
    """AWS S3 file storage implementation"""

    def __init__(self):
        self.bucket_name = APP_SETTINGS.AWS_S3_BUCKET_NAME
        self.region = APP_SETTINGS.AWS_REGION
        self.bucket_url = APP_SETTINGS.AWS_S3_BUCKET_URL

        try:
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=APP_SETTINGS.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=APP_SETTINGS.AWS_SECRET_ACCESS_KEY,
                region_name=self.region,
            )
        except NoCredentialsError:
            raise Exception("AWS credentials not found")

    def save_file(self, file: BinaryIO, filename: str, file_type: str) -> dict:
        """Save file to S3"""
        try:
            # Generate unique S3 key
            unique_filename = f"{uuid.uuid4()}_{filename}"
            s3_key = f"knowledge_base/{unique_filename}"

            # Read file content
            content = file.read()

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=content,
                ContentType=self._get_content_type(file_type),
            )

            return {
                "file_path": s3_key,
                "filename": unique_filename,
                "file_size": len(content),
                "storage_type": "s3",
                "bucket_name": self.bucket_name,
            }
        except ClientError as e:
            raise Exception(f"Error uploading to S3: {str(e)}")

    def save_text_as_file(self, text_content: str, filename: str) -> dict:
        """Save text content as a .txt file to S3"""
        try:
            # Generate unique S3 key
            unique_filename = f"{uuid.uuid4()}_{filename}.txt"
            s3_key = f"knowledge_base/{unique_filename}"

            # Convert text to bytes
            content_bytes = text_content.encode("utf-8")

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=content_bytes,
                ContentType="text/plain",
            )

            return {
                "file_path": s3_key,
                "filename": unique_filename,
                "file_size": len(content_bytes),
                "storage_type": "s3",
                "bucket_name": self.bucket_name,
            }
        except ClientError as e:
            raise Exception(f"Error uploading text to S3: {str(e)}")

    def delete_file(self, file_path: str) -> bool:
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_path)
            return True
        except ClientError as e:
            print(f"Error deleting S3 file: {e}")
            return False

    def get_file_url(self, file_path: str) -> str:
        """Get S3 file URL"""
        if self.bucket_url:
            return f"{self.bucket_url}/{file_path}"
        return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{file_path}"

    def get_presigned_url(self, file_path: str, expiration: int = 3600) -> str:
        """Get presigned URL for secure download"""
        try:
            response = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": file_path},
                ExpiresIn=expiration,
            )
            return response
        except ClientError as e:
            raise Exception(f"Error generating presigned URL: {str(e)}")

    def file_exists(self, file_path: str) -> bool:
        """Check if S3 file exists"""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=file_path)
            return True
        except ClientError:
            return False

    def _get_content_type(self, file_type: str) -> str:
        """Get content type based on file extension"""
        content_types = {
            "pdf": "application/pdf",
            "csv": "text/csv",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "xls": "application/vnd.ms-excel",
            "txt": "text/plain",
            "json": "application/json",
            "md": "text/markdown",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        return content_types.get(file_type.lower(), "application/octet-stream")


class FileStorageFactory:
    """Factory to create appropriate file storage based on granular setting"""

    @staticmethod
    def create_storage() -> FileStorageInterface:
        if APP_SETTINGS.use_aws_storage:
            return S3FileStorage()
        else:
            return LocalFileStorage()


# Global file storage instance
file_storage = FileStorageFactory.create_storage()
