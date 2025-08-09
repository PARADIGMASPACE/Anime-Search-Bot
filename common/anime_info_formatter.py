from utils.utils import classify_airing_schedule


class AnimeInfo:
    def __init__(self, shikimori_data: dict, anilist_data: dict):
        self.shikimori = shikimori_data
        self.anilist = anilist_data.get("data", {}).get("Media", {})

    @property
    def ids(self):
        return {
            "shikimori_id": self.shikimori.get("id", ""),
            "anilist_id": self.anilist.get("id", ""),
        }

    def title(self):
        return {
            "native": self.anilist.get("title", {}).get("native", ""),
            "romaji": self.anilist.get("title", {}).get("romaji", ""),
            "english": self.shikimori.get("name", ""),
            "russian": self.shikimori.get("russian", ""),
        }

    def id(self):
        return {
            "shikimori_id": self.shikimori.get("id", ""),
            "anilist_id": self.anilist.get("id", ""),
        }

    def description(self):
        return {
            "desc_shikimori": self.shikimori.get("description"),
            "desc_anilist": self.anilist.get("description"),
        }

    def cover_image(self):
        return {
            "image_shikimori": "https://shikimori.one"
            + self.shikimori.get("image", {}).get("original", ""),
            "image_anilist": self.anilist.get("coverImage", {}).get("extraLarge", ""),
        }

    def genres(self):
        genres_anilist = self.anilist.get("genres", [])
        genres_shikimori_raw = self.shikimori.get("genres", [])
        genres_shikimori = [
            g.get("russian", g.get("name", "")) for g in genres_shikimori_raw
        ]

        return {"genres_shikimori": genres_shikimori, "genres_anilist": genres_anilist}

    def rating(self):
        rating_shikimori = float(self.shikimori.get("score", 0)) * 10

        return {
            "rating_shikimori": rating_shikimori,
            "rating_anilist": self.anilist.get("averageScore", 0),
        }

    def episode_count(self):
        return {
            "episode_count_shikimori": self.shikimori.get("episodes", 0),
            "episode_count_anilist": self.anilist.get("episodes", 0),
        }

    def release_date(self):
        start_date = self.anilist.get("startDate", {})
        y = start_date.get("year")
        m = start_date.get("month")
        d = start_date.get("day")

        if y and m and d:
            release_date_anilist = f"{y:04d}-{m:02d}-{d:02d}"
        elif y and m:
            release_date_anilist = f"{y:04d}-{m:02d}"
        elif y:
            release_date_anilist = f"{y:04d}"
        else:
            release_date_anilist = ""

        return {
            "release_date_shikimori": self.shikimori.get("aired_on", ""),
            "release_date_anilist": release_date_anilist,
        }

    def airing_schedule(self):
        airing_schedule_shikimori = self.shikimori.get("episodes", [])
        airing_schedule_anilist = self.anilist.get("airingSchedule", {}).get(
            "nodes", []
        )

        airing_schedule_classified = classify_airing_schedule(airing_schedule_anilist)
        airing_schedule_coming = airing_schedule_classified.get("upcoming", [])

        return {
            "airing_schedule_shikimori": airing_schedule_shikimori,
            "airing_schedule_anilist": airing_schedule_anilist,
            "airing_schedule_coming": airing_schedule_coming,
        }

    def type(self):
        return {
            "type_shikimori": self.shikimori.get("kind", ""),
            "type_anilist": self.anilist.get("type", ""),
        }

    def status(self):
        return {
            "status_shikimori": self.shikimori.get("status"),
            "status_anilist": self.anilist.get("status"),
        }
