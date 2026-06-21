from toll.prompt.repository import PromptProfile, PromptProfileRepository


def test_create_and_get_profile(cm):
    repo = PromptProfileRepository(cm)
    p = PromptProfile(id="test:ad", name="Test Ad", media_types=["image"],
                      template="Show {subject} nicely")
    created = repo.create(p)
    assert created.id == "test:ad"

    got = repo.get("test:ad")
    assert got is not None
    assert got.name == "Test Ad"
    assert got.template == "Show {subject} nicely"


def test_get_missing(cm):
    repo = PromptProfileRepository(cm)
    assert repo.get("nonexistent") is None


def test_list_profiles(cm):
    repo = PromptProfileRepository(cm)
    repo.create(PromptProfile(id="p1", name="P1", media_types=["image"]))
    repo.create(PromptProfile(id="p2", name="P2", media_types=["text"]))
    all_profiles = repo.list()
    assert len(all_profiles) == 2


def test_list_filter_by_media_type(cm):
    repo = PromptProfileRepository(cm)
    repo.create(PromptProfile(id="p1", name="P1", media_types=["image"]))
    repo.create(PromptProfile(id="p2", name="P2", media_types=["text"]))
    images = repo.list(media_type="image")
    assert len(images) == 1
    assert images[0].id == "p1"


def test_list_filter_by_tag(cm):
    repo = PromptProfileRepository(cm)
    repo.create(PromptProfile(id="p1", name="P1", tags=["advertising"]))
    repo.create(PromptProfile(id="p2", name="P2", tags=["food"]))
    ads = repo.list(tag="advertising")
    assert len(ads) == 1


def test_update_profile_increments_version(cm):
    repo = PromptProfileRepository(cm)
    repo.create(PromptProfile(id="t:u", name="Original"))
    updated = repo.update("t:u", {"name": "Updated"})
    assert updated is not None
    assert updated.name == "Updated"
    assert updated.version == 2


def test_update_missing(cm):
    repo = PromptProfileRepository(cm)
    assert repo.update("nonexistent", {"name": "X"}) is None


def test_delete_profile(cm):
    repo = PromptProfileRepository(cm)
    repo.create(PromptProfile(id="t:d", name="Delete me"))
    assert repo.delete("t:d") is True
    assert repo.get("t:d") is None


def test_get_version_history(cm):
    repo = PromptProfileRepository(cm)
    repo.create(PromptProfile(id="t:v", name="V1"))
    repo.update("t:v", {"name": "V2"})
    versions = repo.get_version_history("t:v")
    assert len(versions) >= 1
