import pytest
from apps.emails.services import generate_reply_address, parse_reply_address, generate_quote_token, generate_request_code
from apps.requests.models import Request
from apps.suppliers.models import Supplier
from apps.quotes.models import RfqInvitation
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
class TestEmailService:
    def test_generate_request_code_unique(self):
        code1 = generate_request_code()
        code2 = generate_request_code()
        assert len(code1) == 6
        assert code1 != code2
        assert all(c not in '0O1IL' for c in code1)

    def test_generate_reply_address(self):
        addr = generate_reply_address('abc123def456')
        assert addr.startswith('rfq-abc123def456@')
        assert '@' in addr

    def test_parse_reply_address_roundtrip(self):
        addr = generate_reply_address('test_reply_123')
        code = parse_reply_address(addr)
        assert code == 'test_reply_123'

    def test_parse_reply_address_invalid(self):
        assert parse_reply_address('not-a-valid@email.com') is None
        assert parse_reply_address('plain@email.com') is None

    def test_generate_quote_token(self):
        t1 = generate_quote_token()
        t2 = generate_quote_token()
        assert len(t1) > 30
        assert t1 != t2

    def test_create_rfq_invitation(self):
        user = User.objects.create_user(email='em@test.com', password='pass', username='em@test.com')
        req = Request.objects.create(customer=user, code='EMTEST', raw_text='test')
        sup = Supplier.objects.create(name='EmailTest', email='supplier@test.ru')
        from apps.emails.services import create_rfq_invitation
        inv = create_rfq_invitation(req, sup)
        assert inv.code
        assert inv.reply_email
        assert inv.quote_token
        assert RfqInvitation.objects.count() == 1
