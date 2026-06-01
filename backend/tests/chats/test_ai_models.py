import pytest
from django.contrib.auth import get_user_model

from chats.models import AIConversation, AIMessage

User = get_user_model()


@pytest.mark.django_db
class TestAIConversationModel:
    def test_conversation_bound_to_owner(self):
        user = User.objects.create_user(email="a@test.com", username="a", password="Aa1!xy", is_active=True)
        conv = AIConversation.objects.create(owner=user)
        assert conv.owner == user
        assert conv.created_at is not None

    def test_conversation_can_have_title(self):
        user = User.objects.create_user(email="a@test.com", username="a", password="Aa1!xy", is_active=True)
        conv = AIConversation.objects.create(owner=user, title="福岡四天三夜")
        assert conv.title == "福岡四天三夜"


@pytest.mark.django_db
class TestAIMessageModel:
    def test_message_roles(self):
        user = User.objects.create_user(email="a@test.com", username="a", password="Aa1!xy", is_active=True)
        conv = AIConversation.objects.create(owner=user)
        user_msg = AIMessage.objects.create(conversation=conv, role=AIMessage.Role.USER, content="幫我規劃")
        model_msg = AIMessage.objects.create(conversation=conv, role=AIMessage.Role.MODEL, content="好的")
        assert user_msg.role == "user"
        assert model_msg.role == "model"

    def test_messages_ordered_by_created_at(self):
        user = User.objects.create_user(email="a@test.com", username="a", password="Aa1!xy", is_active=True)
        conv = AIConversation.objects.create(owner=user)
        first = AIMessage.objects.create(conversation=conv, role=AIMessage.Role.USER, content="First")
        second = AIMessage.objects.create(conversation=conv, role=AIMessage.Role.MODEL, content="Second")
        messages = list(AIMessage.objects.filter(conversation=conv))
        assert messages[0].id == first.id
        assert messages[1].id == second.id

    def test_messages_cascade_on_conversation_delete(self):
        user = User.objects.create_user(email="a@test.com", username="a", password="Aa1!xy", is_active=True)
        conv = AIConversation.objects.create(owner=user)
        AIMessage.objects.create(conversation=conv, role=AIMessage.Role.USER, content="hi")
        conv.delete()
        assert AIMessage.objects.count() == 0
