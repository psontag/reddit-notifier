from pydantic import BaseSettings, SecretStr


class Settings(BaseSettings):
    class Config:
        env_file = ".env"

    version: str = "0.0.5"

    api_root: str = "https://www.reddit.com"

    reddit_username: str
    reddit_password: SecretStr
    reddit_client_id: SecretStr
    reddit_client_secret: SecretStr
    email_username: str
    email_password: SecretStr

    interval_hours: int = 12

    # https://www.reddit.com/wiki/search/
    # can just try it out via the UI and then look at the URL
    search_query: str

    @property
    def default_headers(self) -> dict[str, str]:
        return {
            "User-Agent": f"reddit-notifier/{self.version} by {self.reddit_username}"
        }
