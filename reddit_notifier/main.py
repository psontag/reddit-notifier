from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import NamedTuple

import aiosmtplib
import httpx

from reddit_notifier.settings import Settings

settings = Settings()

auth = httpx.BasicAuth(
    settings.reddit_client_id.get_secret_value(),
    settings.reddit_client_secret.get_secret_value(),
)


async def get_token() -> str:
    async with httpx.AsyncClient(auth=auth, headers=settings.default_headers) as c:
        r = await c.post(
            f"{settings.api_root}/api/v1/access_token",
            data={
                "grant_type": "password",
                "username": settings.reddit_username,
                "password": settings.reddit_password.get_secret_value(),
            },
        )
        r.raise_for_status()
        token = r.json()["access_token"]
        return token


class Post(NamedTuple):
    title: str
    link: str
    body: str


async def search_posts(access_token: str) -> list[Post]:
    posts = []
    headers = {**settings.default_headers, "Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(auth=auth, headers=headers) as c:
        r = await c.get(
            f"{settings.api_root}/r/mechmarket/search.json",
            params={
                "q": settings.search_query,
                "t": "week",
                "sort": "new",
                "restrict_sr": "on",
            },
        )
        r.raise_for_status()

        skipped = 0
        for post in r.json()["data"]["children"]:
            data = post["data"]
            title = data["title"]

            created_at = datetime.fromtimestamp(data["created_utc"])
            last_run = datetime.utcnow() - timedelta(hours=settings.interval_hours)
            if created_at < last_run:
                skipped += 1
                print(f"Skipped {title} from {created_at}")
                continue

            link = f"{settings.api_root}/{data['permalink']}"
            posts.append(Post(title=title, body=data["selftext"], link=link))

        print(f"Found {len(posts)} new posts, skipped {skipped} posts")
        return posts


async def send_emails(posts: list[Post]) -> None:
    if len(posts) == 0:
        print("No posts, no email")
        return

    msg = MIMEMultipart()
    msg["Subject"] = "Found new Reddit posts"
    msg["From"] = settings.email_username
    msg["To"] = settings.email_username

    HEADER = f"""
    <html>
      <body>
        <p>Found the following new Reddit posts based on this query {settings.search_query}:
        </p>
        <ul>
    """

    post_listing = ""
    for p in posts:
        post_info = f"""
        <li><a href="{p.link}">{p.title}</a></li>
        """
        post_listing += post_info

    FOOTER = """
        </ul>
      </body>
    </html>
    """

    text = HEADER + post_listing + FOOTER
    msg.attach(MIMEText(text, "html", "utf-8"))

    async with aiosmtplib.SMTP(
        hostname="smtp.gmail.com", use_tls=True, timeout=10
    ) as smtp:
        await smtp.login(
            settings.email_username,
            settings.email_password.get_secret_value(),
        )
        await smtp.send_message(msg)

    print(f"Send an email to {settings.email_username}")


async def main() -> int:
    token = await get_token()
    posts = await search_posts(token)
    await send_emails(posts)
    return 0
