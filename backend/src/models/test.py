import json
import os
import sys
from datetime import datetime
from uuid import UUID, uuid4
import pytest
from .user import User, UserSettings
from .knowledge_base import KnowledgeBase
from ..core.rag import rag_service

# Add the backend src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestUser:
    """Test cases for User model"""

    def test_user_creation_with_required_fields(self):
        """Test creating user with only required fields"""
        user = User(username="testuser", hashed_password="hashed_password_123")

        assert user.username == "testuser"
        assert user.hashed_password == "hashed_password_123"
        assert isinstance(user.id, UUID)
        assert user.email == ""
        assert user.full_name == ""
        assert user.role == "user"
        assert user.is_active is True
        assert isinstance(user.created_at, datetime)
        assert user.updated_at is None
        assert user.cognito_user_id is None

    def test_user_creation_with_all_fields(self):
        """Test creating user with all fields"""
        user_id = uuid4()
        cognito_id = "cognito_123"
        created_time = datetime.utcnow()
        updated_time = datetime.utcnow()

        user = User(
            id=user_id,
            username="fulluser",
            hashed_password="hashed_password_456",
            email="test@example.com",
            full_name="Test User",
            role="admin",
            is_active=False,
            created_at=created_time,
            updated_at=updated_time,
            cognito_user_id=cognito_id,
        )

        assert user.id == user_id
        assert user.username == "fulluser"
        assert user.hashed_password == "hashed_password_456"
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.role == "admin"
        assert user.is_active is False
        assert user.created_at == created_time
        assert user.updated_at == updated_time
        assert user.cognito_user_id == cognito_id

    def test_user_default_values(self):
        """Test user default values are set correctly"""
        user = User(username="defaultuser", hashed_password="password123")

        # Test default values
        assert user.email == ""
        assert user.full_name == ""
        assert user.role == "user"
        assert user.is_active is True
        assert user.updated_at is None
        assert user.cognito_user_id is None

        # Test auto-generated values
        assert isinstance(user.id, UUID)
        assert isinstance(user.created_at, datetime)

    def test_user_table_name(self):
        """Test user table name is correct"""
        assert User.__tablename__ == "users"


class TestUserSettings:
    """Test cases for UserSettings model"""

    def test_user_settings_creation_with_defaults(self):
        """Test creating user settings with default values"""
        user_id = uuid4()

        settings = UserSettings(user_id=user_id)

        assert settings.user_id == user_id
        assert isinstance(settings.id, UUID)
        assert settings.vai_tro == "Nhân viên"
        assert settings.chi_nhanh == "Hà Nội"
        assert settings.pham_vi == "Cá nhân"
        assert settings.du_lieu == "Dữ liệu cơ bản"
        assert settings.datasource_permissions == "[]"
        assert isinstance(settings.created_at, datetime)
        assert settings.updated_at is None

    def test_user_settings_creation_with_custom_values(self):
        """Test creating user settings with custom values"""
        user_id = uuid4()
        settings_id = uuid4()
        created_time = datetime.utcnow()
        updated_time = datetime.utcnow()
        permissions = json.dumps(["permission1", "permission2"])

        settings = UserSettings(
            id=settings_id,
            user_id=user_id,
            vai_tro="Quản lý",
            chi_nhanh="TP.HCM",
            pham_vi="Toàn bộ",
            du_lieu="Dữ liệu nâng cao",
            datasource_permissions=permissions,
            created_at=created_time,
            updated_at=updated_time,
        )

        assert settings.id == settings_id
        assert settings.user_id == user_id
        assert settings.vai_tro == "Quản lý"
        assert settings.chi_nhanh == "TP.HCM"
        assert settings.pham_vi == "Toàn bộ"
        assert settings.du_lieu == "Dữ liệu nâng cao"
        assert settings.datasource_permissions == permissions
        assert settings.created_at == created_time
        assert settings.updated_at == updated_time

    def test_user_settings_datasource_permissions_json(self):
        """Test datasource_permissions as JSON string"""
        user_id = uuid4()

        # Test with empty list
        settings1 = UserSettings(user_id=user_id)
        permissions_list1 = json.loads(settings1.datasource_permissions)
        assert permissions_list1 == []

        # Test with custom permissions
        permissions = ["read_customers", "write_transactions", "admin_reports"]
        permissions_json = json.dumps(permissions)

        settings2 = UserSettings(user_id=user_id, datasource_permissions=permissions_json)

        permissions_list2 = json.loads(settings2.datasource_permissions)
        assert permissions_list2 == permissions

    def test_user_settings_table_name(self):
        """Test user settings table name is correct"""
        assert UserSettings.__tablename__ == "user_settings"


class TestUserKnowledgeBaseIntegration:
    """Test integration between User and KnowledgeBase through RAG service"""

    def test_user_with_knowledge_base_processing(self):
        """Test user creating and processing knowledge base"""
        # Create user
        user = User(
            username="kb_user",
            hashed_password="password123",
            email="kb@example.com",
            full_name="Knowledge Base User",
        )

        # Test text for knowledge base
        test_text = """
        Kiến thức cơ bản về tài chính
        
        1. Cổ phiếu là gì?
        Cổ phiếu là chứng chỉ xác nhận quyền sở hữu một phần vốn của công ty cổ phần.
        
        2. Trái phiếu là gì?
        Trái phiếu là công cụ nợ, người mua trái phiếu cho công ty vay tiền.
        
        3. Đầu tư là gì?
        Đầu tư là việc bỏ tiền ra để mua tài sản với mục đích sinh lời.
        """

        kb_id = str(uuid4())

        try:
            # Process text with RAG service
            rag_result = rag_service.process_text(text=test_text, kb_id=kb_id, user_id=user.id)

            assert rag_result["status"] == "success"
            assert rag_result["chunks_count"] > 0
            assert rag_result["text_length"] > 0
            assert "processed_content" in rag_result

            # Create knowledge base and update with RAG result
            kb = KnowledgeBase(
                user_id=user.id,
                filename="tai_chinh_co_ban.txt",
                original_filename="tai_chinh_co_ban.txt",
                file_path="/test/tai_chinh_co_ban.txt",
                file_type="txt",
                file_size=len(test_text),
            )

            kb.update_from_rag_result(rag_result)

            assert kb.processing_status == "completed"
            assert kb.chunks_count == rag_result["chunks_count"]
            assert kb.text_length == rag_result["text_length"]
            assert kb.processing_time == rag_result["processing_time"]
            assert kb.processed_content is not None

            # Test search functionality
            search_results = rag_service.search_knowledge_base(
                query="cổ phiếu là gì", user_id=user.id, k=3
            )

            assert len(search_results) > 0
            assert any("cổ phiếu" in result["text"].lower() for result in search_results)

            # Test document stats
            stats = rag_service.get_document_stats(user.id)
            assert stats["total_documents"] >= 1
            assert stats["total_chunks"] >= 1
            assert stats["vector_count"] >= 1

            # Cleanup
            rag_service.remove_knowledge_base(kb_id, user.id)

        except Exception as e:
            # Cleanup on failure
            try:
                rag_service.remove_knowledge_base(kb_id, user.id)
            except:
                pass
            raise e

    def test_user_with_multiple_knowledge_bases(self):
        """Test user with multiple knowledge bases"""
        user = User(username="multi_kb_user", hashed_password="password456")

        kb_ids = []
        test_texts = [
            "Kiến thức về ngân hàng: Ngân hàng là tổ chức tài chính.",
            "Kiến thức về bảo hiểm: Bảo hiểm giúp bảo vệ tài sản.",
            "Kiến thức về đầu tư: Đầu tư giúp gia tăng tài sản.",
        ]

        try:
            # Process multiple texts
            for i, text in enumerate(test_texts):
                kb_id = str(uuid4())
                kb_ids.append(kb_id)

                rag_result = rag_service.process_text(text=text, kb_id=kb_id, user_id=user.id)

                assert rag_result["status"] == "success"

            # Test comprehensive search
            search_results = rag_service.search_knowledge_base(
                query="kiến thức", user_id=user.id, k=5
            )

            assert len(search_results) > 0

            # Test document stats
            stats = rag_service.get_document_stats(user.id)
            assert stats["total_documents"] == len(test_texts)
            assert stats["total_chunks"] >= len(test_texts)

            # Cleanup all knowledge bases
            for kb_id in kb_ids:
                rag_service.remove_knowledge_base(kb_id, user.id)

            # Verify cleanup
            final_stats = rag_service.get_document_stats(user.id)
            assert final_stats["total_documents"] == 0
            assert final_stats["total_chunks"] == 0

        except Exception as e:
            # Cleanup on failure
            for kb_id in kb_ids:
                try:
                    rag_service.remove_knowledge_base(kb_id, user.id)
                except:
                    pass
            raise e

    def test_user_context_retrieval(self):
        """Test context retrieval for user queries"""
        user = User(username="context_user", hashed_password="password789")

        kb_id = str(uuid4())
        financial_knowledge = """
        Tài liệu hướng dẫn tài chính cá nhân
        
        Chương 1: Tiết kiệm
        Tiết kiệm là việc dành ra một phần thu nhập để dự trữ cho tương lai.
        Nên tiết kiệm ít nhất 20% thu nhập hàng tháng.
        
        Chương 2: Đầu tư
        Đầu tư là cách làm tiền sinh tiền.
        Có nhiều hình thức đầu tư: cổ phiếu, trái phiếu, bất động sản.
        
        Chương 3: Bảo hiểm
        Bảo hiểm giúp chuyển giao rủi ro tài chính.
        Nên có bảo hiểm nhân thọ và bảo hiểm y tế.
        """

        try:
            # Process knowledge
            rag_result = rag_service.process_text(
                text=financial_knowledge, kb_id=kb_id, user_id=user.id
            )

            assert rag_result["status"] == "success"

            # Test context retrieval for different queries
            queries_and_expected = [
                ("tôi nên tiết kiệm bao nhiêu", "tiết kiệm"),
                ("đầu tư cổ phiếu như thế nào", "đầu tư"),
                ("bảo hiểm có tác dụng gì", "bảo hiểm"),
                ("làm sao để quản lý tài chính", "tài chính"),
            ]

            for query, expected_keyword in queries_and_expected:
                context = rag_service.get_context_for_query(
                    query=query, user_id=user.id, max_context_length=1000
                )

                assert len(context) > 0
                assert expected_keyword.lower() in context.lower()

            # Test context length limit
            short_context = rag_service.get_context_for_query(
                query="tài chính", user_id=user.id, max_context_length=100
            )

            assert len(short_context) <= 150  # Allow some buffer for formatting

            # Cleanup
            rag_service.remove_knowledge_base(kb_id, user.id)

        except Exception as e:
            # Cleanup on failure
            try:
                rag_service.remove_knowledge_base(kb_id, user.id)
            except:
                pass
            raise e


class TestUserSettingsIntegration:
    """Test integration between User and UserSettings"""

    def test_user_with_settings_creation(self):
        """Test creating user with custom settings"""
        user = User(username="settings_user", hashed_password="password123", role="manager")

        settings = UserSettings(
            user_id=user.id,
            vai_tro="Quản lý chi nhánh",
            chi_nhanh="TP.HCM",
            pham_vi="Chi nhánh",
            du_lieu="Dữ liệu đầy đủ",
            datasource_permissions=json.dumps(
                ["read_all_customers", "write_transactions", "view_reports", "export_data"]
            ),
        )

        assert settings.user_id == user.id
        assert settings.vai_tro == "Quản lý chi nhánh"
        assert settings.chi_nhanh == "TP.HCM"

        # Test parsing permissions
        permissions = json.loads(settings.datasource_permissions)
        assert "read_all_customers" in permissions
        assert "export_data" in permissions

    def test_user_settings_permissions_management(self):
        """Test managing datasource permissions in user settings"""
        user = User(username="perm_user", hashed_password="pass123")

        # Start with basic permissions
        basic_permissions = ["read_basic_data"]
        settings = UserSettings(
            user_id=user.id, datasource_permissions=json.dumps(basic_permissions)
        )

        # Test getting permissions
        current_permissions = json.loads(settings.datasource_permissions)
        assert current_permissions == basic_permissions

        # Test updating permissions
        new_permissions = [
            "read_basic_data",
            "read_customer_data",
            "write_transactions",
            "generate_reports",
        ]
        settings.datasource_permissions = json.dumps(new_permissions)

        updated_permissions = json.loads(settings.datasource_permissions)
        assert updated_permissions == new_permissions
        assert len(updated_permissions) == 4

        # Test permission validation (custom logic)
        admin_permissions = [
            "read_all_data",
            "write_all_data",
            "delete_data",
            "manage_users",
            "system_admin",
        ]
        settings.datasource_permissions = json.dumps(admin_permissions)

        final_permissions = json.loads(settings.datasource_permissions)
        assert "system_admin" in final_permissions
        assert len(final_permissions) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
