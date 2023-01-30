from datetime import date, timedelta
from enum import Enum
from typing import Any, Dict, Optional, cast

from hibiapi.api.pixiv.constants import PixivConstants
from hibiapi.api.pixiv.net import NetRequest as PixivNetClient
from hibiapi.utils.cache import cache_config
from hibiapi.utils.decorators import enum_auto_doc
from hibiapi.utils.net import catch_network_error
from hibiapi.utils.routing import BaseEndpoint, dont_route, request_headers


@enum_auto_doc
class IllustType(str, Enum):
    """画作类型"""

    illust = "illust"
    """插画"""
    manga = "manga"
    """漫画"""


@enum_auto_doc
class RankingType(str, Enum):
    """排行榜内容类型"""

    day = "day"
    """日榜"""
    week = "week"
    """周榜"""
    month = "month"
    """月榜"""
    day_male = "day_male"
    """男性向"""
    day_female = "day_female"
    """女性向"""
    week_original = "week_original"
    """原创"""
    week_rookie = "week_rookie"
    """新人"""
    day_ai = "day_ai"
    """AI"""
    day_r18 = "day_r18"
    day_male_r18 = "day_male_r18"
    day_female_r18 = "day_female_r18"
    week_r18 = "week_r18"
    week_r18g = "week_r18g"
    day_r18_ai = "day_r18_ai"
    day_manga = "day_manga"


@enum_auto_doc
class SearchModeType(str, Enum):
    """搜索匹配类型"""

    partial_match_for_tags = "partial_match_for_tags"
    """标签部分一致"""
    exact_match_for_tags = "exact_match_for_tags"
    """标签完全一致"""
    title_and_caption = "title_and_caption"
    """标题说明文"""


@enum_auto_doc
class SearchNovelModeType(str, Enum):
    """搜索匹配类型"""

    partial_match_for_tags = "partial_match_for_tags"
    """标签部分一致"""
    exact_match_for_tags = "exact_match_for_tags"
    """标签完全一致"""
    text = "text"
    """正文"""
    keywords = "keywords"
    """关键词"""


@enum_auto_doc
class SearchSortType(str, Enum):
    """搜索排序类型"""

    date_desc = "date_desc"
    """按日期倒序"""
    date_asc = "date_asc"
    """按日期正序"""
    popular_desc = "popular_desc"
    """受欢迎降序(Premium功能)"""


@enum_auto_doc
class SearchDurationType(str, Enum):
    """搜索时段类型"""

    within_last_day = "within_last_day"
    """一天内"""
    within_last_week = "within_last_week"
    """一周内"""
    within_last_month = "within_last_month"
    """一个月内"""


class RankingDate(date):
    @classmethod
    def yesterday(cls) -> "RankingDate":
        yesterday = cls.today() - timedelta(days=1)
        return cls(yesterday.year, yesterday.month, yesterday.day)

    def toString(self) -> str:
        return self.strftime(r"%Y-%m-%d")

    @classmethod
    def new(cls, date: date) -> "RankingDate":
        return cls(date.year, date.month, date.day)


class PixivEndpoints(BaseEndpoint):
    @staticmethod
    def _parse_accept_language(accept_language: str) -> str:
        first_language, *_ = accept_language.partition(",")
        language_code, *_ = first_language.partition(";")
        return language_code.lower().strip()

    @dont_route
    @catch_network_error
    async def request(
        self, endpoint: str, *, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        headers = self.client.headers.copy()
        if user := cast(PixivNetClient, self.client.net_client).user:
            headers["Authorization"] = f"Bearer {user.access_token}"
        if language := request_headers.get().get("Accept-Language"):
            language = self._parse_accept_language(language)
            headers["Accept-Language"] = language
        response = await self.client.get(
            self._join(
                base=PixivConstants.APP_HOST,
                endpoint=endpoint,
                params=params or {},
            ),
            headers=headers,
        )
        return response.json()

    @cache_config(ttl=timedelta(hours=6))
    async def illust(self, *, id: int):
        return await self.request("v1/illust/detail", params={"illust_id": id})

    @cache_config(ttl=timedelta(hours=6))
    async def member(self, *, id: int):
        return await self.request("v1/user/detail", params={"user_id": id})

    @cache_config(ttl=timedelta(hours=4))
    async def illust_recommended(
        self,
        *,
        filter: str = "for_ios",
        include_ranking_label: bool = True,
    ):
        return await self.request(
            "v1/illust/recommended",
            params={
                "filter": filter,
                "include_ranking_label": include_ranking_label,
            },
        )

    @cache_config(ttl=timedelta(hours=4))
    async def user_recommended(
        self,
        *,
        filter: str = "for_ios",
    ):
        return await self.request(
            "v1/user/recommended",
            params={
                "filter": filter,
            },
        )

    @cache_config(ttl=timedelta(minutes=30))
    async def illust_new(
        self,
        *,
        content_type: str = "illust",
        filter: str = "for_ios",
    ):
        return await self.request(
            "v1/illust/new",
            params={
                "content_type": content_type,
                "filter": filter,
            },
        )

    @cache_config(ttl=timedelta(hours=12))
    async def search_autocomplete(
        self,
        *,
        word: str,
        merge_plain_keyword_results: bool = True,
    ):
        return await self.request(
            "v2/search/autocomplete",
            params={
                "word": word,
                "merge_plain_keyword_results": merge_plain_keyword_results,
            },
        )

    @cache_config(ttl=timedelta(hours=6))
    async def spotlights(
        self,
        *,
        category: str = "all",
        filter: str = "for_ios",
        page: int = 1,
        size: int = 10,
    ):
        return await self.request(
            "v1/spotlight/articles",
            params={
                "filter": filter,
                "category": category,
                "offset": (page - 1) * size,
            },
        )

    @cache_config(ttl=timedelta(hours=6))
    async def popular_preview(
        self,
        *,
        word: str,
        start_date: str = None,
        end_date: str = None,
    ):
        return await self.request(
            "v1/search/popular-preview/illust",
            params={
                "word": word,
                "start_date": start_date,
                "end_date": end_date,
                "filter": "for_ios",
                "include_translated_tag_results": "true",
                "merge_plain_keyword_results": "true",
                "search_target": "partial_match_for_tags",
            },
        )

    @cache_config(ttl=timedelta(hours=1))
    async def search_user(
        self,
        *,
        word: str,
        page: int = 1,
        size: int = 30,
    ):
        return await self.request(
            "v1/search/user",
            params={
                "word": word,
                "offset": (page - 1) * size,
            },
        )

    @cache_config(ttl=timedelta(hours=1))
    async def member_illust(
        self,
        *,
        id: int,
        illust_type: IllustType = IllustType.illust,
        page: int = 1,
        size: int = 30,
    ):
        return await self.request(
            "v1/user/illusts",
            params={
                "user_id": id,
                "type": illust_type,
                "offset": (page - 1) * size,
            },
        )

    @cache_config(ttl=timedelta(hours=1))
    async def favorite(
        self,
        *,
        id: int,
        tag: Optional[str] = None,
        max_bookmark_id: Optional[int] = None,
    ):
        return await self.request(
            "v1/user/bookmarks/illust",
            params={
                "user_id": id,
                "tag": tag,
                "restrict": "public",
                "max_bookmark_id": max_bookmark_id or None,
            },
        )

    @cache_config(ttl=timedelta(hours=1))
    async def following(self, *, id: int, page: int = 1, size: int = 30):
        return await self.request(
            "v1/user/following",
            params={
                "user_id": id,
                "offset": (page - 1) * size,
            },
        )

    @cache_config(ttl=timedelta(hours=1))
    async def follower(self, *, id: int, page: int = 1, size: int = 30):
        return await self.request(
            "v1/user/follower",
            params={
                "user_id": id,
                "offset": (page - 1) * size,
            },
        )

    @cache_config(ttl=timedelta(hours=6))
    async def rank(
        self,
        *,
        mode: RankingType = RankingType.day,
        date: Optional[RankingDate] = None,
        page: int = 1,
        size: int = 30,
    ):
        return await self.request(
            "v1/illust/ranking",
            params={
                "mode": mode,
                "date": RankingDate.new(date or RankingDate.yesterday()).toString(),
                "offset": (page - 1) * size,
            },
        )

    @cache_config(ttl=timedelta(hours=1))
    async def search(
        self,
        *,
        word: str,
        mode: SearchModeType = SearchModeType.partial_match_for_tags,
        order: SearchSortType = SearchSortType.date_desc,
        duration: Optional[SearchDurationType] = None,
        start_date: str = None,
        end_date: str = None,
        include_translated_tag_results: str = 'true',
        merge_plain_keyword_results: str = 'true',
        page: int = 1,
        size: int = 30,
    ):
        return await self.request(
            "v1/search/illust",
            params={
                "word": word,
                "search_target": mode,
                "sort": order,
                "include_translated_tag_results": include_translated_tag_results,
                "merge_plain_keyword_results": merge_plain_keyword_results,
                "start_date": start_date,
                "end_date": end_date,
                "duration": duration,
                "offset": (page - 1) * size,
            },
        )

    @cache_config(ttl=timedelta(hours=6))
    async def tags(self):
        return await self.request("v1/trending-tags/illust")

    @cache_config(ttl=timedelta(hours=1))
    async def related(self, *, id: int, page: int = 1, size: int = 30):
        return await self.request(
            "v2/illust/related",
            params={
                "illust_id": id,
                "offset": (page - 1) * size,
            },
        )

    @cache_config(ttl=timedelta(days=3))
    async def ugoira_metadata(self, *, id: int):
        return await self.request(
            "v1/ugoira/metadata",
            params={
                "illust_id": id,
            },
        )

    async def walkthrough_illusts(self):
        return await self.request("v1/walkthrough/illusts")

    @cache_config(ttl=timedelta(hours=1))
    async def illust_comments(
        self,
        *,
        illust_id: int | str,
        offset: int | str | None = None,
        include_total_comments: str | bool | None = None,
    ):
        return await self.request(
            "v3/illust/comments",
            params={
                "illust_id": illust_id,
                "offset": offset,
                "include_total_comments": include_total_comments,
            },
        )

    @cache_config(ttl=timedelta(hours=1))
    async def novel_comments(
        self,
        *,
        novel_id: int | str,
        offset: int | str | None = None,
        include_total_comments: str | bool | None = None,
    ):
        return await self.request(
            "v3/novel/comments",
            params={
                "novel_id": novel_id,
                "offset": offset,
                "include_total_comments": include_total_comments,
            },
        )

    @cache_config(ttl=timedelta(hours=1))
    async def illust_comment_replies(
        self,
        *,
        comment_id: int | str,
    ):
        return await self.request(
            "v2/illust/comment/replies",
            params={
                "comment_id": comment_id,
            },
        )

    @cache_config(ttl=timedelta(hours=1))
    async def novel_comment_replies(
        self,
        *,
        comment_id: int | str,
    ):
        return await self.request(
            "v2/novel/comment/replies",
            params={
                "comment_id": comment_id,
            },
        )

    @cache_config(ttl=timedelta(hours=3))
    async def manga_recommended(
        self,
        *,
        filter: str = "for_ios",
        include_ranking_label: str = "true",
    ):
        return await self.request(
            "v1/manga/recommended",
            params={
                "filter": filter,
                "include_ranking_label": include_privacy_policy,
            },
        )

    @cache_config(ttl=timedelta(hours=6))
    async def rank_novel(
        self,
        *,
        mode: str,
        date: Optional[RankingDate] = None,
        page: int = 1,
        size: int = 30,
    ):
        return await self.request(
            "v1/novel/ranking",
            params={
                "mode": mode,
                "date": RankingDate.new(date or RankingDate.yesterday()).toString(),
                "offset": (page - 1) * size,
            },
        )

    @cache_config(ttl=timedelta(hours=1))
    async def member_novel(self, *, id: int, page: int = 1, size: int = 30):
        return await self.request(
            "v1/user/novels",
            params={
                "user_id": id,
                "offset": (page - 1) * size,
            },
        )

    @cache_config(ttl=timedelta(hours=3))
    async def novel_recommended(
        self,
        *,
        filter: str = "for_ios",
        include_privacy_policy: str = "true",
        include_ranking_novels: str = "true",
    ):
        return await self.request(
            "v1/novel/recommended",
            params={
                "filter": filter,
                "include_privacy_policy": include_privacy_policy,
                "include_ranking_novels": include_ranking_novels,
            },
        )

    @cache_config(ttl=timedelta(hours=1))
    async def favorite_novel(
        self,
        *,
        id: int,
    ):
        return await self.request(
            "v1/user/bookmarks/novel",
            params={
               "user_id": id,
               "restrict": "public",
            },
        )

    @cache_config(ttl=timedelta(hours=6))
    async def tags_novel(self):
        return await self.request("v1/trending-tags/novel")

    @cache_config(ttl=timedelta(hours=1))
    async def novel_series(self, *, id: int):
        return await self.request("/v2/novel/series", params={"series_id": id})

    @cache_config(ttl=timedelta(hours=1))
    async def novel_detail(self, *, id: int):
        return await self.request("/v2/novel/detail", params={"novel_id": id})

    @cache_config(ttl=timedelta(hours=1))
    async def novel_text(self, *, id: int):
        return await self.request("/v1/novel/text", params={"novel_id": id})

    @cache_config(ttl=timedelta(hours=1))
    async def search_novel(
        self,
        *,
        word: str,
        mode: SearchNovelModeType = SearchNovelModeType.partial_match_for_tags,
        sort: SearchSortType = SearchSortType.date_desc,
        merge_plain_keyword_results: bool = True,
        include_translated_tag_results: bool = True,
        start_date: str = None,
        end_date: str = None,
        duration: Optional[SearchDurationType] = None,
        page: int = 1,
        size: int = 30,
    ):
        return await self.request(
            "/v1/search/novel",
            params={
                "word": word,
                "search_target": mode,
                "sort": sort,
                "merge_plain_keyword_results": merge_plain_keyword_results,
                "include_translated_tag_results": include_translated_tag_results,
                "start_date": start_date,
                "end_date": end_date,
                "duration": duration,
                "offset": (page - 1) * size,
            },
        )

    @cache_config(ttl=timedelta(hours=6))
    async def popular_preview_novel(
        self,
        *,
        word: str,
        start_date: str = None,
        end_date: str = None,
    ):
        return await self.request(
            "v1/search/popular-preview/novel",
            params={
                "word": word,
                "start_date": start_date,
                "end_date": end_date,
                "filter": "for_ios",
                "include_translated_tag_results": "true",
                "merge_plain_keyword_results": "true",
                "search_target": "partial_match_for_tags",
            },
        )

    @cache_config(ttl=timedelta(minutes=10))
    async def novel_new(self, *, max_novel_id: Optional[int] = None):
        return await self.request(
            "/v1/novel/new", params={"max_novel_id": max_novel_id}
        )
