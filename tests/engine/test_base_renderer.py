import pytest
from toll.engine.renderers.base import BaseRenderer


def test_base_renderer_abstract():
    with pytest.raises(TypeError):
        BaseRenderer()


def test_base_renderer_render_method():
    class Concrete(BaseRenderer):
        def render(self, title: str, *args, **kwargs) -> str:
            return f"<h1>{title}</h1>"

    r = Concrete()
    assert r.render("Hello") == "<h1>Hello</h1>"
