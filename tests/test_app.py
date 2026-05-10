from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(deepcopy(original_activities))


def test_get_activities_returns_data():
    # Arrange
    expected_keys = {"Chess Club", "Programming Class"}

    # Act
    response = client.get("/activities")
    payload = response.json()

    # Assert
    assert response.status_code == 200
    assert expected_keys.issubset(payload)
    assert isinstance(payload["Chess Club"]["participants"], list)


def test_signup_success(reset_activities):
    # Arrange
    email = "teststudent@mergington.edu"
    activity = "Chess Club"
    url = f"/activities/{quote(activity)}/signup?email={quote(email)}"

    # Act
    response = client.post(url)

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity}"
    assert email in activities[activity]["participants"]


def test_signup_duplicate_returns_400(reset_activities):
    # Arrange
    email = "michael@mergington.edu"
    activity = "Chess Club"
    url = f"/activities/{quote(activity)}/signup?email={quote(email)}"

    # Act
    response = client.post(url)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_missing_activity_returns_404(reset_activities):
    # Arrange
    email = "missingstudent@mergington.edu"
    activity = "Nonexistent Club"
    url = f"/activities/{quote(activity)}/signup?email={quote(email)}"

    # Act
    response = client.post(url)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_success(reset_activities):
    # Arrange
    email = "michael@mergington.edu"
    activity = "Chess Club"
    url = f"/activities/{quote(activity)}/participants?email={quote(email)}"

    # Act
    response = client.delete(url)

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {email} from {activity}"
    assert email not in activities[activity]["participants"]


def test_remove_missing_participant_returns_404(reset_activities):
    # Arrange
    email = "notfound@mergington.edu"
    activity = "Chess Club"
    url = f"/activities/{quote(activity)}/participants?email={quote(email)}"

    # Act
    response = client.delete(url)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found in activity"


def test_remove_missing_activity_returns_404(reset_activities):
    # Arrange
    email = "teststudent@mergington.edu"
    activity = "Ghost Club"
    url = f"/activities/{quote(activity)}/participants?email={quote(email)}"

    # Act
    response = client.delete(url)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_activity_state_isolated(reset_activities):
    # Arrange
    original_count = len(activities["Chess Club"]["participants"])
    email = "isolated@mergington.edu"
    activity = "Chess Club"
    signup_url = f"/activities/{quote(activity)}/signup?email={quote(email)}"
    delete_url = f"/activities/{quote(activity)}/participants?email={quote(email)}"

    # Act
    client.post(signup_url)
    client.delete(delete_url)

    # Assert
    assert email not in activities[activity]["participants"]
    assert len(activities[activity]["participants"]) == original_count
