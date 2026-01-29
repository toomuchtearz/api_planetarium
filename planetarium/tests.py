import tempfile

from PIL import Image
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APIClient
from rest_framework import status

from planetarium.models import (
    Show,
    Theme,
    PlanetariumDome,
    Session,
    Order,
    Ticket
)

from planetarium.serializers import ShowListSerializer, DomeSerializer

# --- ENDPOINTS ---
SHOW_URL = reverse("planetarium:show-list")
SESSION_URL = reverse("planetarium:session-list")
ORDER_URL = reverse("planetarium:order-list")
DOME_URL = reverse("planetarium:planetariumdome-list")


# --- HELPERS ---
def sample_show(**params):
    defaults = {
        "title": "Sample Show",
        "description": "Sample Description",
    }
    defaults.update(params)
    return Show.objects.create(**defaults)


def sample_theme(**params):
    defaults = {"name": "Sample Theme"}
    defaults.update(params)
    return Theme.objects.create(**defaults)


def sample_dome(**params):
    defaults = {
        "name": "Sample Dome",
        "rows": 10,
        "seats_in_row": 10,
    }
    defaults.update(params)
    return PlanetariumDome.objects.create(**defaults)


def sample_session(**params):
    dome = params.pop("dome", None)
    if not dome:
        dome = sample_dome()

    show = params.pop("show", None)
    if not show:
        show = sample_show()

    defaults = {
        "show_time": timezone.now(),
        "dome": dome,
        "show": show,
    }
    defaults.update(params)
    return Session.objects.create(**defaults)


def image_upload_url(show_id):
    return reverse("planetarium:show-upload-image", args=[show_id])


# --- TESTS  ---


class UnauthenticatedPlanetariumApiTests(TestCase):
    """Test public access restrictions"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.post(ORDER_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedUserShowApiTests(TestCase):
    """Test Show API for authenticated users"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@test.com",
            "testpass"
        )
        self.client.force_authenticate(self.user)

    def test_list_shows(self):
        sample_show()
        sample_show(title="Another Show")

        res = self.client.get(SHOW_URL)

        shows = Show.objects.all()
        serializer = ShowListSerializer(shows, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_shows_by_themes(self):
        theme1 = sample_theme(name="Space")
        theme2 = sample_theme(name="History")

        show1 = sample_show(title="Space Show")
        show1.themes.add(theme1)

        show2 = sample_show(title="History Show")
        show2.themes.add(theme2)

        show3 = sample_show(title="Space & History")
        show3.themes.add(theme1, theme2)

        res = self.client.get(SHOW_URL, {"themes": f"{theme1.id}"})

        ids = [show["id"] for show in res.data["results"]]
        self.assertIn(show1.id, ids)
        self.assertIn(show3.id, ids)
        self.assertNotIn(show2.id, ids)

    def test_filter_shows_by_title(self):
        show1 = sample_show(title="Star Wars")
        show2 = sample_show(title="Star Trek")
        show3 = sample_show(title="Dune")

        res = self.client.get(SHOW_URL, {"title": "Star"})

        self.assertEqual(len(res.data["results"]), 2)

        ids = [show["id"] for show in res.data["results"]]
        self.assertIn(show1.id, ids)
        self.assertIn(show2.id, ids)
        self.assertNotIn(show3.id, ids)

    def test_retrieve_show_with_future_sessions(self):
        """Test custom Prefetch with to_attr='future_sessions'"""
        show = sample_show()
        dome = sample_dome(name="Test Dome")

        future_session = sample_session(
            show=show, show_time=timezone.now() + timedelta(days=1), dome=dome
        )

        past_session = sample_session(
            show=show, show_time=timezone.now() - timedelta(days=1), dome=dome
        )

        url = reverse("planetarium:show-detail", args=[show.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn("future_sessions", res.data)
        self.assertNotIn(past_session, res.data["future_sessions"])
        self.assertEqual(len(res.data["future_sessions"]), 1)
        self.assertEqual(
            res.data["future_sessions"][0]["id"],
            future_session.id
        )

    def test_create_show_forbidden(self):
        """Standard user cannot create a show"""
        payload = {
            "title": " Show",
            "description": "I should not be able to do this",
        }
        res = self.client.post(SHOW_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AuthenticatedUserSessionApiTests(TestCase):
    """Test Session API for authenticated users"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@test.com",
            "testpass"
        )
        self.client.force_authenticate(self.user)

    def test_list_sessions_with_seats_left(self):
        """Test annotate logic for calculating seats_left"""
        dome = sample_dome(rows=5, seats_in_row=10)
        session = sample_session(dome=dome)

        order = Order.objects.create(user=self.user)
        Ticket.objects.create(session=session, order=order, row=1, seat=1)
        Ticket.objects.create(session=session, order=order, row=1, seat=2)
        Ticket.objects.create(session=session, order=order, row=1, seat=3)

        res = self.client.get(SESSION_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        session_data = res.data["results"][0]
        self.assertEqual(session_data["seats_left"], 47)
        self.assertEqual(session_data["dome_capacity"], 50)

    def test_filter_sessions_by_date(self):
        """Test date filtering"""
        date_target = timezone.now().date()

        session1 = sample_session(show_time=timezone.now())

        res = self.client.get(SESSION_URL, {"date": date_target.isoformat()})

        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["id"], session1.id)

    def test_filter_sessions_by_invalid_date(self):
        """Test that invalid date format doesn't crash API"""
        res = self.client.get(SESSION_URL, {"date": "invalid-date-string"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)


class AuthenticatedUserDomeApiTests(TestCase):
    """Test Dome API for authenticated users"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_domes(self):
        sample_dome(name="Alpha")
        sample_dome(name="Beta")

        res = self.client.get(DOME_URL)

        domes = PlanetariumDome.objects.all().order_by("id")
        serializer = DomeSerializer(domes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_domes_by_name(self):
        dome1 = sample_dome(name="Alpha Dome")
        dome2 = sample_dome(name="Beta Dome")

        res = self.client.get(DOME_URL, {"name": "Alpha"})

        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["id"], dome1.id)
        self.assertNotIn(dome2, res.data["results"])

    def test_retrieve_dome_with_future_sessions(self):
        """Test that retrieve uses the correct serializer and prefetch"""
        dome = sample_dome()
        show = sample_show(title="Test Show")

        future_session = sample_session(
            dome=dome, show_time=timezone.now() + timedelta(days=1), show=show
        )

        past_session = sample_session(
            dome=dome, show_time=timezone.now() - timedelta(days=1), show=show
        )

        url = reverse("planetarium:planetariumdome-detail", args=[dome.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn("future_sessions", res.data)
        self.assertNotIn(past_session, res.data["future_sessions"])

        self.assertEqual(len(res.data["future_sessions"]), 1)
        self.assertEqual(
            res.data["future_sessions"][0]["id"],
            future_session.id
        )


class OrderTransactionApiTests(TestCase):
    """
    Test Order logic
    """

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "buyer@test.com",
            "testpass"
        )
        self.client.force_authenticate(self.user)

        self.dome = sample_dome(rows=5, seats_in_row=5)
        self.session = sample_session(dome=self.dome)

    def test_create_order_successful(self):
        payload = {
            "tickets": [
                {"row": 1, "seat": 1, "session": self.session.id},
                {"row": 2, "seat": 2, "session": self.session.id},
            ]
        }
        res = self.client.post(ORDER_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        order = Order.objects.get(id=res.data["id"])
        self.assertEqual(order.tickets.count(), 2)
        self.assertEqual(order.user, self.user)

    def test_ticket_validation_out_of_bounds(self):
        """Fail if row/seat is larger than dome capacity"""
        payload = {
            "tickets": [
                {"row": 10, "seat": 1, "session": self.session.id},
            ]
        }
        res = self.client.post(ORDER_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ticket_validation_already_sold(self):
        """Fail if ticket is already taken in DB"""
        order = Order.objects.create(user=self.user)
        Ticket.objects.create(session=self.session, order=order, row=1, seat=1)

        payload = {
            "tickets": [
                {"row": 1, "seat": 1, "session": self.session.id},
            ]
        }
        res = self.client.post(ORDER_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_validation_duplicate_tickets_in_payload(self):
        """Fail if user sends the exact same ticket twice in one JSON"""

        payload = {
            "tickets": [
                {"row": 3, "seat": 3, "session": self.session.id},
                {"row": 3, "seat": 3, "session": self.session.id},
            ]
        }
        res = self.client.post(ORDER_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_atomic_transaction_rollback(self):
        """
        If one ticket is valid and the second is invalid,
        the ENTIRE order must be rejected.
        """
        order = Order.objects.create(user=self.user)
        Ticket.objects.create(session=self.session, order=order, row=1, seat=1)

        payload = {
            "tickets": [
                {"row": 2, "seat": 2, "session": self.session.id},
                {"row": 1, "seat": 1, "session": self.session.id},
            ]
        }

        res = self.client.post(ORDER_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        exists = Ticket.objects.filter(
            session=self.session,
            row=2,
            seat=2
        ).exists()
        self.assertFalse(exists)


class AdminImageUploadTests(TestCase):
    """Test Admin capabilities including Image Upload"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@test.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_show(self):
        theme = sample_theme()
        payload = {
            "title": "Admin Show",
            "description": "Created by Admin",
            "themes": [
                theme.id,
            ],
        }
        res = self.client.post(SHOW_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_upload_image_to_show(self):
        """Test uploading an image file to the show"""
        show = sample_show()
        url = image_upload_url(show.id)

        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)

            res = self.client.post(url, {"image": ntf}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)

        show.refresh_from_db()
        self.assertTrue(show.image)

        # Cleanup
        if show.image:
            show.image.delete()

    def test_upload_image_bad_request(self):
        """Test uploading a non-image file"""
        show = sample_show()
        url = image_upload_url(show.id)

        res = self.client.post(
            url,
            {"image": "not-an-image"},
            format="multipart"
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
