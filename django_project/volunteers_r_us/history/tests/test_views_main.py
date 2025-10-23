# volunteers_r_us/tests/test_views_main.py
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_project.settings")
django.setup()

import pytest
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.models import AnonymousUser
from volunteers_r_us import views as main_views

@pytest.fixture
def rf(): 
    return RequestFactory()

def _msg_setup(request):
    # real session (has .flush()) + messages
    mw = SessionMiddleware(lambda r: None)
    mw.process_request(request)
    request.session.save()
    setattr(request, "_messages", FallbackStorage(request))

@pytest.fixture
def patch_render(monkeypatch):
    captured = {}
    def fake_render(request, template_name, context=None):
        from django.http import HttpResponse
        captured["template"] = template_name
        captured["context"] = context or {}
        return HttpResponse("OK")
    monkeypatch.setattr(main_views, "render", fake_render)
    return captured

def test_home_ok(rf, patch_render):
    req = rf.get("/")
    req.user = AnonymousUser()
    _msg_setup(req)
    resp = main_views.home(req)
    assert resp.status_code == 200

def test_login_get_ok(rf, patch_render):
    req = rf.get("/login/")
    req.user = AnonymousUser()
    _msg_setup(req)
    resp = main_views.login_view(req)
    assert resp.status_code == 200

def test_login_post_success(monkeypatch, rf):
    class DummyForm:
        def __init__(self, data): self.cleaned_data={"email":"a@b.c","password":"x"}
        def is_valid(self): return True
    class DummyUser: pass
    monkeypatch.setattr(main_views, "LoginForm", DummyForm)
    monkeypatch.setattr(main_views, "authenticate", lambda req, email=None, password=None: DummyUser())
    monkeypatch.setattr(main_views, "login", lambda req, user, backend=None: None)
    req = rf.post("/login/", {"email":"a@b.c","password":"x"})
    req.user = AnonymousUser()
    _msg_setup(req)
    resp = main_views.login_view(req)
    assert resp.status_code in (200, 301, 302)

def test_login_post_invalid(monkeypatch, rf, patch_render):
    class DummyForm:
        def __init__(self, data): self.cleaned_data={"email":"a@b.c","password":"x"}
        def is_valid(self): return True
    monkeypatch.setattr(main_views, "LoginForm", DummyForm)
    monkeypatch.setattr(main_views, "authenticate", lambda *a, **k: None)
    req = rf.post("/login/", {"email":"a@b.c","password":"x"})
    req.user = AnonymousUser()
    _msg_setup(req)
    resp = main_views.login_view(req)
    assert resp.status_code == 200
    assert patch_render["template"] == "login.html"

def test_register_get(monkeypatch, rf, patch_render):
    class DummyForm:
        def __init__(self, data=None): pass
        def is_valid(self): return False
    monkeypatch.setattr(main_views, "RegisterForm", DummyForm)
    req = rf.get("/register/")
    req.user = AnonymousUser()
    _msg_setup(req)
    resp = main_views.register(req)   # <-- register (not register_view)
    assert resp.status_code == 200
    assert patch_render["template"] == "register.html"

def test_register_post_success(monkeypatch, rf):
    class DummyForm:
        def __init__(self, data=None): self.cleaned_data={"email":"x@y.z","password":"p","password_confirm":"p"}
        def is_valid(self): return True
    monkeypatch.setattr(main_views, "RegisterForm", DummyForm)

    
    req = rf.post("/register/", {"email":"x@y.z","password":"p","password_confirm":"p"})
    req.user = AnonymousUser()
    _msg_setup(req)
    resp = main_views.register(req)   # <-- register
    assert resp.status_code in (200, 301, 302)

def test_logout_redirects(rf):
    req = rf.post("/logout/")   # POST (not GET)
    req.user = AnonymousUser()
    _msg_setup(req)
    resp = main_views.logout_view(req)
    assert resp.status_code in (200, 301, 302)

def test_match_volunteer_get(monkeypatch, rf):
    monkeypatch.setattr(
        main_views, "Notification",
        type("N", (), {"objects": type("M", (), {"create": staticmethod(lambda **k: None)})})
    )
    def fake_render(request, tpl, ctx):
        from django.http import HttpResponse
        assert "volunteers" in ctx and "events" in ctx
        return HttpResponse("ok")
    monkeypatch.setattr(main_views, "render", fake_render)
    req = rf.get("/match/")
    req.user = AnonymousUser()
    _msg_setup(req)
    resp = main_views.match_volunteer(req)
    assert resp.status_code == 200

def test_match_volunteer_post_assign_notify_with_override(monkeypatch, rf):
    monkeypatch.setattr(
        main_views, "Notification",
        type("N", (), {"objects": type("M", (), {"create": staticmethod(lambda **k: None)})})
    )
    def fake_render(request, tpl, ctx):
        from django.http import HttpResponse
        assert ctx["saved"] is not None
        return HttpResponse("ok")
    monkeypatch.setattr(main_views, "render", fake_render)
    class DummyUser: is_authenticated = True
    req = rf.post("/match/", {
        "volunteer_id": "1",
        "matched_event": "1",
        "action": "assign_notify",
        "override": "on",
        "override_reason": "ok",
    })
    req.user = DummyUser()
    _msg_setup(req)
    resp = main_views.match_volunteer(req)
    assert resp.status_code == 200
